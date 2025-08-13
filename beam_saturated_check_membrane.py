#CELL1: IMPORT
%load_ext autoreload
%autoreload 2
import waffles
import numpy as np
import json
import shutil 
from tqdm import tqdm
import mplhep
import matplotlib.pyplot as plt
mplhep.style.use(mplhep.style.ROOT)
plt.rcParams.update({'font.size': 20,
                        'grid.linestyle': '--',
                        'axes.grid': True,
                        'figure.autolayout': True,
                        'figure.figsize': [14,6]
                        })

import waffles
import numpy as np
import json
import shutil 
from tqdm import tqdm

from waffles.input_output.hdf5_structured import load_structured_waveformset
from waffles.data_classes.Waveform import Waveform
from waffles.data_classes.WaveformSet import WaveformSet
from waffles.data_classes.BasicWfAna import BasicWfAna
from waffles.data_classes.IPDict import IPDict
from waffles.data_classes.UniqueChannel import UniqueChannel
from waffles.data_classes.ChannelWsGrid import ChannelWsGrid
from waffles.utils.baseline.baseline import SBaseline
from waffles.np02_utils.AutoMap import generate_ChannelMap, dict_uniqch_to_module, dict_module_to_uniqch, strUch, ordered_channels_membrane, ordered_channels_cathode
from waffles.np02_utils.PlotUtils import np02_gen_grids, plot_grid, plot_detectors, genhist, fithist, runBasicWfAnaNP02





#CELL2: PRENDE I DATI (E FA DEI GRUPPI MA NON IMPORTA)
dettype = "membrane"
## Only change if necessary
datadir = f"/eos/experiment/neutplatform/protodune/experiments/ProtoDUNE-VD/commissioning/"
det = "VD_Cathode_PDS" if dettype == "cathode" else "VD_Membrane_PDS"
endpoint = 106 if dettype == "cathode" else 107

# Way to low... keep scrollng
dletter = dettype.upper()[0] # C or M...
group1 = [ f"{dletter}{detnum}({chnum})" for detnum in range(1, 3) for chnum in range(1,3) ]
group2 = [ f"{dletter}{detnum}({chnum})" for detnum in range(3, 5) for chnum in range(1,3) ]
group3 = [ f"{dletter}{detnum}({chnum})" for detnum in range(5, 7) for chnum in range(1,3) ]
group4 = [ f"{dletter}{detnum}({chnum})" for detnum in range(7, 9) for chnum in range(1,3) ]
groupall = group1+group2+group3+group4

list_of_unch = ordered_channels_membrane





#CELL3: APRE IL WAVEFORM SET DI DATI PROCESSATI PER UN DATO RUN E TIPO DI DETECTOR (M o C - endpoint)
from glob import glob
import copy
def open_processed(run, dettype, datadir, channels = None, endpoints=None, nwaveforms=None, mergefiles = False, verbose=True):
    """
    Open the processed waveform set for a given run and detector type.
    """
    try: 
        wfset = load_structured_waveformset(
            f"{datadir}/processed/run{run:0d}_{dettype}/processed_merged_run{run:06d}_structured_{dettype}.hdf5",
            max_to_load=nwaveforms,
            channels_filter=channels,
            endpoint_filter=endpoints
        )
    except:
        files = glob(f"{datadir}/processed/run{run:06d}_{dettype}/processed_*_run{run:06d}_*_{dettype}.hdf5")
        if verbose:
            print("List of files found:")
            print(files)
        if not mergefiles or len(files)==1:
            files = files[0]
            wfset = load_structured_waveformset(files, max_to_load=nwaveforms, channels_filter=channels, endpoint_filter=endpoints, verbose=verbose)
        else: 
            wfset = load_structured_waveformset(files[0], max_to_load=nwaveforms, channels_filter= channels, endpoint_filter=endpoints, verbose=verbose)
            for f in files[1:]:
                tmpwf = load_structured_waveformset(f, max_to_load=nwaveforms, channels_filter= channels, endpoint_filter=endpoints, verbose=verbose)
                wfset.merge(copy.deepcopy(tmpwf))
    return wfset





#CELL4: CHIAMA LA FUNZIONE
run = 38627
channels=None
wfset_full = open_processed(run, dettype, datadir, channels=channels, endpoints = [endpoint], nwaveforms=None, verbose=True, mergefiles=True)





#CELL5: SPECIFICA IN QUALE CONFIGURAZIONE DI PRESSIONE DEL TARGET CHERENKOV SI TROVA LA PARTICELLA CORRISPONDENTE
particle_by_type = {}
particle_by_type['total'] = 'total'
particle_by_type['e']   = 'kCTBBeamChkvHL'
particle_by_type['pi']  = 'kCTBBeamChkvHxLx'
particle_by_type['pr']  = 'kCTBBeamChkvHxLx'
particle_by_type['why'] = 'kCTBBeamChkvHxL'




#CELL6: FA ISTOGRAMMA PER VALUTARE GLI EVENTI CORRISPONDENTI A 20 TICKS - CIOè I SEGNALI CORRISPONDENTI AL BEAM - CIOè QUELLI TRIGGERATI DAL DAQT
diffvalues = [ wf.daq_window_timestamp - wf.timestamp for wf in wfset_full.waveforms ]
dmax = np.max(diffvalues)
dmin = np.min(diffvalues)
print(dmax, dmin, (dmax-dmin)*16e-9)
hc, hbins, _ = plt.hist(diffvalues, bins=np.linspace(-50, 50, 100));
plt.xlabel("daq_window_timestamp - timestamp [ticks]")




#CELL7: SELEZIONA DEL WFSET SOLO LE WAVEFORM TRIGGERATE CORRETTAMENTE - CIOè CORRISPONDENTI AL BEAM
def adjust_offset(waveform:Waveform) -> bool:
    if -5 < waveform.daq_window_timestamp - waveform.timestamp < 25:
        return True
    return False
    
wfset_triggered_all = WaveformSet.from_filtered_WaveformSet(wfset_full, adjust_offset, show_progress=True)
wfset_triggered_all




#CELL8: ATTRAVERSO IL CONTEGGIO, FACENDO ANCHE DOVUTO CONTROLLO, INDIVIDUA DELLE WF DEL BEAM QUALI SONO LE SPECIFICHE DI CIASCUN TIPO DI PARTICELLA
#OS: se nel dizionario la chiave è una lista che contiene più di un singolo elemento, non va bene e restituisce errore
from tqdm import tqdm
triggertypes = {} # just for checking..
triggergroups = {} # to check if more than one...
triggertypedaq = {}
daqtimestamps = {}
for wf in tqdm(wfset_full.waveforms):
    triggername=wf.trigger_type_names
    firsttime = False
    if wf.daq_window_timestamp not in daqtimestamps:
        firsttime=True
        daqtimestamps[wf.daq_window_timestamp] = 1
        tname = triggername[0]
        triggertypedaq[tname] =  triggertypedaq.get(tname,0) + 1
    else:
        daqtimestamps[wf.daq_window_timestamp] += 1

    if (len(triggername)) > 1:
        raise ValueError("This should never happen!!!!")
    triggergroups[tuple(triggername)] =  triggergroups.get(tuple(triggername), 0) + 1
    for tn in triggername:
        triggertypes[tn] = triggertypes.get(tn, 0) + 1

for triggername in triggertypedaq.keys():
    print(f"Trigger name {triggername} was done {triggertypedaq[triggername]} and have total of {triggergroups[tuple([triggername])]}")
print(triggergroups)




#CELL9: CARICA IL CONTEGGIO IN UN DIZIONARIO APPOSITO
triggertypedaq['total'] = np.sum( [ value for key, value in triggertypedaq.items() if key != 'kCTBOffSpillSnapshot' ] ) 
triggertypedaq




#CELL10: ESTRAPOLA INFORMAZIONI DI WFSET PER CIASCUNA PARTICELLA
def filter_offspill(waveform: Waveform, avoidspill:bool, specifictype="") -> bool:
    if avoidspill and 'kCTBOffSpillSnapshot' in waveform.trigger_type_names:
        return False
    return True
def filter_types(waveform: Waveform, specifictype) -> bool:
    if specifictype in waveform.trigger_type_names:
        return True
    return False

def get_particle_wfset(wfset, specifictype):
    try:
        wftmp = WaveformSet.from_filtered_WaveformSet(wfset, filter_types, specifictype, show_progress=False)
        print(specifictype, wftmp)
        return wftmp
    except:
        print(f"{specifictype} not in this run...\n")
        return None
    
def remove_saturated(waveform:Waveform) -> bool:
    if np.any(waveform.adcs>16000):
        return False
    return True

wfset_triggered_types = {}
wfset_triggered_types['total']= WaveformSet.from_filtered_WaveformSet(wfset_triggered_all, filter_offspill, avoidspill=True, show_progress=True)
print("total...", wfset_triggered_types['total'])
wfset_triggered_types['e']   = get_particle_wfset(wfset_triggered_types['total'], specifictype = particle_by_type['e'] )
wfset_triggered_types['pi']  = get_particle_wfset(wfset_triggered_types['total'], specifictype = particle_by_type['pi'] )
wfset_triggered_types['pr']  = get_particle_wfset(wfset_triggered_types['total'], specifictype = particle_by_type['pr'] )
wfset_triggered_types['why'] = get_particle_wfset(wfset_triggered_types['total'], specifictype = particle_by_type['why'] )






#CELL11: DEFINISCE LA FUNZIONE CHE PROCESSA I DATI PRELIMINARI TOTALI E PER CIASCUNA PARTICELLA, POI APPLICA LA FUNZIONE E STAMPA I DATI
def processes_analysis_by_type(wfset, dkey, daqtriggerdict:dict, output_infos, verbose=True):
    
    global list_of_unch
    global particle_by_type
    output_infos[dkey] = {}
    output_infos[dkey]['DAQ_Trigger'] = {}
    output_infos[dkey]['Triggered_Events'] = {}
    output_infos[dkey]['No_saturated'] = {}
    output_infos[dkey]['Charge'] = {}
    output_infos[dkey]['wfsetnosat'] = {}
    for ch in list_of_unch: #inital values all set 
        output_infos[dkey]['DAQ_Trigger'][ch] = 0
        output_infos[dkey]['Triggered_Events'][ch] = 0
        output_infos[dkey]['No_saturated'][ch] = 0
        output_infos[dkey]['Charge'][ch] = 0
        output_infos[dkey]['wfsetnosat'][ch] = None
        

    if wfset is None:
        return
    daqtrigger = daqtriggerdict[particle_by_type[dkey]]
    chwfob = ChannelWsGrid.clusterize_waveform_set(wfset)
    if verbose:
        print("\nTriggered channels 'efficiency'")
        print("Module, n records, n DAQ triggers, %")
    nbeamrecors_ch_triggered = {}
    for ep, wfsch in chwfob.items():
        for ch in list_of_unch:
            if ch not in wfsch:
                nbeamrecors_ch_triggered[ch] = 0
            else:
                recordschob = len(wfsch[ch].record_numbers[run])
                nbeamrecors_ch_triggered[ch] = recordschob
                if len(wfsch[ch].waveforms) != recordschob:
                    raise ValueError("This should never happen...")
            if verbose:
                print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, {nbeamrecors_ch_triggered[ch]}, {daqtrigger}, {100*nbeamrecors_ch_triggered[ch]/daqtrigger:.2f}%")
            output_infos[dkey]['DAQ_Trigger'][ch] = daqtrigger
            output_infos[dkey]['Triggered_Events'][ch] = nbeamrecors_ch_triggered[ch]
            

    wfset_onbeam_nonsat = WaveformSet.from_filtered_WaveformSet(wfset, remove_saturated, show_progress=False)
    runBasicWfAnaNP02(wfset_onbeam_nonsat, threshold=50, onlyoptimal=False, baselinefinish=60, int_ll=60, int_ul=600, amp_ll=60, amp_ul=150, configyaml="", show_progress=verbose)

    chwfob_ns = ChannelWsGrid.clusterize_waveform_set(wfset_onbeam_nonsat)
    list_of_devices = sorted([ m for m in dict_module_to_uniqch.keys() if m ])
    list_of_unch = [ dict_module_to_uniqch[m].channel for m in list_of_devices if dict_module_to_uniqch[m].endpoint == endpoint ]
    if verbose:
        print("\nTriggered channels saturation")
        print("Module, n not saturated, n triggers, %")
    nbeamrecors_ch_triggered_nosat = {}
    for ep, wfsch in chwfob_ns.items():
        for ch in list_of_unch:
            meancharge = 0
            if ch not in wfsch:
                nbeamrecors_ch_triggered_nosat[ch] = 0
            else:
                recordschob = len(wfsch[ch].record_numbers[run])
                nbeamrecors_ch_triggered_nosat[ch] = recordschob
                if len(wfsch[ch].waveforms) != recordschob:
                    raise ValueError("This should never happen...")
                charges = [ wf.analyses['std'].result['integral'] for wf in chwfob_ns[endpoint][ch].waveforms if not wf.analyses['std'].result['integral'] is np.nan ]
                if len(charges) > 0:
                    meancharge = np.nanmean(charges)
            if verbose:
                nperc = 0 if nbeamrecors_ch_triggered[ch] ==0 else 100*nbeamrecors_ch_triggered_nosat[ch]/nbeamrecors_ch_triggered[ch]
                print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, {nbeamrecors_ch_triggered_nosat[ch]}, {nbeamrecors_ch_triggered[ch]}, {nperc:.2f}%")

            output_infos[dkey]['No_saturated'][ch] = nbeamrecors_ch_triggered_nosat[ch]
            output_infos[dkey]['Charge'][ch] = meancharge
        output_infos[dkey]['wfsetnosat'] = wfset_onbeam_nonsat
        print("\n")
            
            
output_infos = {}
for dkey, wfset in wfset_triggered_types.items():
    processes_analysis_by_type(wfset, dkey, triggertypedaq, output_infos=output_infos)






#CELL12: PRINT DEI DATI NECESSARI DA METTERE NELLO SPREADSHEET - TOTALI E DELLE SINGOLE PARTICELLE
mnames = [ mname for mname in list(output_infos['total'])[:-1] ] 
print(', '.join(mnames))
for ttype, outp in output_infos.items():
    
    for ch in list_of_unch:
        for mname in list(output_infos[ttype])[:-1]:
            if mname != "Charge":
                print(f"{output_infos[ttype][mname][ch]}", end=", ")
            else:
                print(f"{output_infos[ttype][mname][ch]:.2f}")

#Qui si deve dare un'occhiata ai dati per verificare che sia tutto a norma, per esempio che la carica (=energia) sia positiva.
#Il canale M2(1) dà problemi sempre, per cui, se ha dei valori strani, non importa.



#CELL13: CONTROLLO GRAFICO IN CASO DI NECESSITà SE I DATI SEMBRANO STRANI
argsheat = dict(
    mode="heatmap",
    analysis_label="std",
    adc_range_above_baseline=1000,
    adc_range_below_baseline=-300,
    adc_bins=200,
    time_bins=wfset.points_per_wf//2,
    filtering=4,
    share_y_scale=False,
    share_x_scale=True,
    wfs_per_axes=5000,
    zlog=True
)
wftmp = output_infos['%%%%']['wfsetnosat']     #qui, al posto di '%%%%', si deve scrivere 'total', 'e', 'pi', 'pr', 'why' in base a cioò che si vuole guardare

detector=group1
plot_detectors(wftmp, detector, **argsheat)
detector=group2
plot_detectors(wftmp, detector, **argsheat)
detector=group3
plot_detectors(wftmp, detector, **argsheat)
detector=group4
plot_detectors(wftmp, detector, **argsheat)
