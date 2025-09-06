## Code to check Signal to Noise ratio (Gloria)


%load_ext autoreload
%autoreload 2
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
from waffles.np02_utils.AutoMap import generate_ChannelMap, dict_uniqch_to_module, dict_module_to_uniqch
from waffles.np02_utils.PlotUtils import np02_gen_grids, plot_grid, plot_detectors, genhist, fithist, runBasicWfAnaNP02



run = 38651
nwaveforms = 80000
dettype = "membrane"
dettype = "cathode"
hostname = 'np04-srv-004'

## Only change if necessary
output_dir = f"/eos/experiment/neutplatform/protodune/experiments/ProtoDUNE-VD/commissioning/"
ch = {}
save_single_file = False
max_files  = 4
det = "VD_Cathode_PDS" if dettype == "cathode" else "VD_Membrane_PDS"
endpoint = 106 if dettype == "cathode" else 107
trigger = "self_trigger"

# Way to low... keep scrollng
dletter = dettype.upper()[0] # C or M...
group1 = [ f"{dletter}{detnum}({chnum})" for detnum in range(1, 3) for chnum in range(1,3) ]
group2 = [ f"{dletter}{detnum}({chnum})" for detnum in range(3, 5) for chnum in range(1,3) ]
group3 = [ f"{dletter}{detnum}({chnum})" for detnum in range(5, 7) for chnum in range(1,3) ]
group4 = [ f"{dletter}{detnum}({chnum})" for detnum in range(7, 9) for chnum in range(1,3) ]




"""
wafflespath = waffles.__path__[0]
wafflespath = wafflespath.replace("src/waffles", "scripts")
configfile = shutil.copy(f"{wafflespath}/config.json", f"{wafflespath}/snrcheck_config.json")
with open(configfile, "r") as f:
    configdata = json.load(f)

configdata['runs'] = [run]
configdata['output_dir'] = output_dir
configdata['save_single_file'] = save_single_file
configdata['det'] = det
configdata['trigger'] = trigger
configdata['ch'] = ch
configdata['max_files'] = max_files

with open(configfile, "w") as f:
    json.dump(configdata, f, indent=4)
    print(f"Config file saved to {configfile}")

from pathlib import Path
plotntco = Path(output_dir) / f"plots/run{run:06d}_{dettype}/nTCO.html"
plottco = Path(output_dir) / f"plots/run{run:06d}_{dettype}/TCO.html"

doplot = "true"
# comment in case you want to force plotting
if plotntco.exists() and plottco.exists():
    print(f"Plots already exist:\n{plotntco}\n{plottco}")
    doplot = "false"
"""




"""
%%bash -s "$wafflespath" "$run" "$configfile" "$doplot" "$hostname" "$trigger"

wafflespath=$1
run=$2
configjson=$3
doplot=$4
hostname=$5
trigger=$6

user=$( whoami )
script08="${wafflespath}/08_np02vd_run_downloader_processor.py"
configfile="${wafflespath}/${configjson}"
if [ "${trigger}" != "self_trigger" ]; then
    echo "Please, run the following command in a terminal... IO not supported in notebook"
    echo "python ${script08} --runs ${run} --user ${user} --config-template ${configjson} --kerberos --hostname ${hostname} --headless"
    exit 0
fi

if [ -f ${script08} ]; then
    if [ "$doplot" == "true" ]; then
        echo "Running script with plotting enabled"
        python ${script08} --runs $run --user $user --config-template $configjson --kerberos --hostname ${hostname} --headless 
    else
        echo "Running script without plotting"
        python ${script08} --runs $run --user $user --config-template $configjson --kerberos --hostname ${hostname} 
    fi
else
    echo "Script not found: ${script08}"
fi
"""





from glob import glob
def open_processed(run, dettype, output_dir, nwaveforms=None, mergefiles = False):
    """
    Open the processed waveform set for a given run and detector type.
    """
    try: 
        wfset = load_structured_waveformset(f"{output_dir}/processed/run{run:0d}_{dettype}/processed_merged_run{run:06d}_structured_{dettype}.hdf5", max_waveforms=nwaveforms)
    except:
        files = glob(f"{output_dir}/processed/run{run:06d}_{dettype}/processed_*_run{run:06d}_*_{dettype}.hdf5")
        print("List of files found:")
        print(files)
        if not mergefiles or len(files)==1:
            files = files[0]
            wfset = load_structured_waveformset(files, max_waveforms=nwaveforms)
        else: # NOT TESTED!
            wfset = load_structured_waveformset(files[0], max_waveforms=nwaveforms)
            for f in files[1:]:
                tmpwf = load_structured_waveformset(f, max_waveforms=nwaveforms)
                wfset.merge(tmpwf)
    return wfset




wfset_full = open_processed(run, dettype, output_dir, nwaveforms=nwaveforms)
wfset_full



histargs = dict(    
    # doprocess = False,
    dofit = False,
    variable = 'integral',
    show_progress = True
)

# histargs['variable'] = 'amplitude'; histargs['bins'] = np.linspace(0,150,150);
  
detector=group1
plot_detectors(wfset_full, detector, plot_function=fithist, html=None, wf_func=histargs)
detector=group2
plot_detectors(wfset_full, detector, plot_function=fithist, html=None, wf_func=histargs)
detector=group3
plot_detectors(wfset_full, detector, plot_function=fithist, html=None, wf_func=histargs)
detector=group4
plot_detectors(wfset_full, detector, plot_function=fithist, html=None, wf_func=histargs)





def remove_bad_baseline(waveform:Waveform) -> bool:
    # comment the two lines below to not remove any waveform
    if 'std' in waveform.analyses and waveform.analyses["std"].result['amplitude'] is np.nan:
        return False
    return True
    
wfset = WaveformSet.from_filtered_WaveformSet(wfset_full, remove_bad_baseline)


print(f"After removing: {len(wfset.waveforms)} waveforms")
wfch_full = ChannelWsGrid.clusterize_waveform_set(wfset_full)
wfch = ChannelWsGrid.clusterize_waveform_set(wfset)
print("By channel..")
for ep, v in wfch.items():
    print("Endpoint:", ep)
    for ch, wfs in v.items():
        print(f"Ch: {ch}, {len(wfs.waveforms)}, total: {len(wfch_full[ep][ch].waveforms)}")




argsheat = dict(
    mode="heatmap",
    analysis_label="std",
    adc_range_above_baseline=200,
    adc_range_below_baseline=-50,
    adc_bins=125,
    time_bins=wfset.points_per_wf//2,
    filtering=4,
    share_y_scale=False,
    share_x_scale=True,
    wfs_per_axes=5000,
    zlog=True
)
detector=group1
plot_detectors(wfset, detector, **argsheat)

detector=group2
plot_detectors(wfset, detector, **argsheat)

detector=group3
plot_detectors(wfset, detector, **argsheat)

detector=group4
plot_detectors(wfset, detector, **argsheat)




# detectors=["M7(1)", "M7(2)", "M8(1)", "M8(2)"]
detectors=["C7(1)", "C7(2)"]

def get_channels(waveform:Waveform, detectors:list) -> bool:
    if dict_uniqch_to_module[str(UniqueChannel(waveform.endpoint, waveform.channel))] in detectors:
        return True
    return False

if nwaveforms is not None:
    wfset_tmp = open_processed(run, dettype, output_dir, nwaveforms=None)

wfset_fit = WaveformSet.from_filtered_WaveformSet(wfset_tmp, get_channels, detectors=detectors)




html = Path(f"./snr_plots/run{run:06d}_{dettype}.html")
html.parent.mkdir(parents=True, exist_ok=True)

fithistargs = dict(
    doprocess=False, 
    show_progress=True
)

setupargs=dict(
# default 1000x800
    width=1000,
    height=800
)
print("Run, Module, snr, gain, baseline std dev, 1pe std dev, integral_mean_in_pe")
plot_detectors(wfset_fit, detectors, plot_function=fithist, html=html, showplots=True, wf_func=fithistargs, **setupargs)

wfch_fit = ChannelWsGrid.clusterize_waveform_set(wfset_fit)
print("By channel..")
for ep, v in wfch_fit.items():
    print("Endpoint:", ep)
    for ch, wfs in v.items():
        ngoodwaves = [ 1 if wfs.analyses['std'].result['integral'] is not np.nan else 0 for wfs in wfs.waveforms ]
        print(f"Ch: {ch}, {np.sum(ngoodwaves)}, total: {len(wfch_fit[ep][ch].waveforms)}")




charges = [wf.analyses['std'].result['integral'] for wf in  wfch_fit[106][34].waveforms ]
with open("data.txt","w") as f:
    for c in charges:
        if c is not np.nan:
            f.write(f"{c}\n")
        
