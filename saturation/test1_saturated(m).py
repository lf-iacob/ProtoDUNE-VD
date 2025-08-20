#Spreadsheet di riferimento: https://docs.google.com/spreadsheets/d/11ufw4duC8Kf_SqowBzzzF60panFZn33uF3xv-TiEZKI/edit?gid=0#gid=0


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





run = 38563
channels=None

wfset_full = open_processed(run, dettype, datadir, channels=channels, endpoints = [endpoint], nwaveforms=None, verbose=True, mergefiles=True)





diffvalues = [ wf.daq_window_timestamp - wf.timestamp for wf in wfset_full.waveforms ]
dmax = np.max(diffvalues)
dmin = np.min(diffvalues)
print(dmax, dmin, (dmax-dmin)*16e-9)
hc, hbins, _ = plt.hist(diffvalues, bins=np.linspace(-50, 50, 100));
plt.xlabel("daq_window_timestamp - timestamp [ticks]")





def adjust_offset(waveform:Waveform) -> bool:
    if -5 < waveform.daq_window_timestamp - waveform.timestamp < 25:
        return True
    return False
    
wfset_onbeam = WaveformSet.from_filtered_WaveformSet(wfset_full, adjust_offset, show_progress=True)
wfset_onbeam







from tqdm import tqdm
triggertypes = {}
triggergroups = {}
triggertypedaq = {}
daqtimestamps = {}
for wf in tqdm(wfset_full.waveforms):
    triggername=wf.trigger_type_names
    daqtimestamps[wf.daq_window_timestamp] = daqtimestamps.get(wf.daq_window_timestamp,0) + 1
    if daqtimestamps[wf.daq_window_timestamp] == 1:
        triggertypedaq[tuple(triggername)] =  triggertypedaq.get(tuple(triggername), 0) + 1
        
    triggergroups[tuple(triggername)] =  triggergroups.get(tuple(triggername), 0) + 1
    for tn in triggername:
        triggertypes[tn] = triggertypes.get(tn, 0) + 1

for triggername in triggertypedaq.keys():
    print(f"Trigger name {triggername} was done {triggertypedaq[triggername]} and have total of {triggergroups[triggername]}")
print(triggergroups)
triggertypes







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
    except:
        print(f"{specifictype} not in this run...\n")
        return None
    

wfset = WaveformSet.from_filtered_WaveformSet(wfset_onbeam, filter_offspill, avoidspill=True, show_progress=True)
print(wfset)
wfset_e = get_particle_wfset(wfset, specifictype = 'kCTBBeamChkvHL')
wfset_pi = get_particle_wfset(wfset, specifictype = 'kCTBBeamChkvHLx')
wfset_pr = get_particle_wfset(wfset, specifictype = 'kCTBBeamChkvHxLx')
wfset_why = get_particle_wfset(wfset, specifictype = 'kCTBBeamChkvHxL')





nbeamrecors_ch = {}
wfch_notspill = ChannelWsGrid.clusterize_waveform_set(WaveformSet.from_filtered_WaveformSet(wfset_full, filter_offspill, avoidspill=True, show_progress=True))
for ep, v in wfch_notspill.items():
    for ch in list_of_unch:
        nbeamrecors_ch[ch] = len(v[ch].record_numbers[run])






chwfob = ChannelWsGrid.clusterize_waveform_set(wfset_onbeam)
print("Triggered channels 'efficiency'")
print("Module, n records, n DAQ triggers, %")
nbeamrecors_ch_triggered = {}
for ep, wfsch in chwfob.items():
    for ch in list_of_unch:
        if ch not in wfsch:
            print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, 0, {nbeamrecors_ch.get(ch,0)}, {100*0/nbeamrecors_ch.get(ch,0):.2f}%")
            nbeamrecors_ch_triggered[ch] = 0
            continue
        recordschob = len(wfsch[ch].record_numbers[run])
        nbeamrecors_ch_triggered[ch] = recordschob
        if len(wfsch[ch].waveforms) != recordschob:
            raise ValueError("This should never happen...")
        print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, {recordschob}, {nbeamrecors_ch[ch]}, {100*recordschob/nbeamrecors_ch[ch]:.2f}%")





def remove_saturated(waveform:Waveform) -> bool:
    if np.any(waveform.adcs>16000):
        return False
    return True
    
wfset_onbeam_nonsat = WaveformSet.from_filtered_WaveformSet(wfset_onbeam, remove_saturated, show_progress=True)

chwfob_ns = ChannelWsGrid.clusterize_waveform_set(wfset_onbeam_nonsat)
list_of_devices = sorted([ m for m in dict_module_to_uniqch.keys() if m ])
list_of_unch = [ dict_module_to_uniqch[m].channel for m in list_of_devices if dict_module_to_uniqch[m].endpoint == endpoint ]
print("Triggered channels 'efficiency'")
print("Module, n records, n DAQ triggers, %")
nbeamrecors_ch_triggered_nosat = {}
for ep, wfsch in chwfob_ns.items():
    for ch in list_of_unch:
        if ch not in wfsch:
            print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, 0, {nbeamrecors_ch_triggered.get(ch,0)}, {100*0/nbeamrecors_ch_triggered.get(ch,0):.2f}%")
            nbeamrecors_ch_triggered_nosat[ch] = 0
            continue
        recordschob = len(wfsch[ch].record_numbers[run])
        nbeamrecors_ch_triggered_nosat[ch] = recordschob
        if len(wfsch[ch].waveforms) != recordschob:
            raise ValueError("This should never happen...")
        print(f"{dict_uniqch_to_module[str(UniqueChannel(ep,ch))]}, {recordschob}, {nbeamrecors_ch_triggered[ch]}, {100*recordschob/nbeamrecors_ch_triggered[ch]:.2f}%")






runBasicWfAnaNP02(wfset_onbeam_nonsat, onlyoptimal=False, baselinefinish=60, int_ll=60, int_ul=600, amp_ll=60, amp_ul=150, configyaml="")





argsheat = dict(
    mode="heatmap",
    analysis_label="std",
    adc_range_above_baseline=14000,
    adc_range_below_baseline=-3000,
    adc_bins=200,
    time_bins=wfset.points_per_wf//2,
    # time_range_lower_limit = 350,
    # time_range_upper_limit = 1350,
    filtering=2,
    share_y_scale=False,
    share_x_scale=True,
    wfs_per_axes=5000,
    zlog=True
)
detector=group1
plot_detectors(wfset_onbeam_nonsat, detector, **argsheat)
detector=group2
plot_detectors(wfset_onbeam_nonsat, detector, **argsheat)
detector=group3
plot_detectors(wfset_onbeam_nonsat, detector, **argsheat)
detector=group4
plot_detectors(wfset_onbeam_nonsat, detector, **argsheat)






for ch in list_of_unch:
    meancharge = 0
    if ch in  chwfob_ns[endpoint]:
        charges = [ wf.analyses['std'].result['integral'] for wf in chwfob_ns[endpoint][ch].waveforms ]
        meancharge = np.mean(charges)
        
    module = dict_uniqch_to_module[str(UniqueChannel(ep,ch))]
    print(f"{module}, {ep}, {ch}, {nbeamrecors_ch[ch]}, {nbeamrecors_ch_triggered[ch]}, {nbeamrecors_ch_triggered_nosat[ch]}, {meancharge:0.2f}")




