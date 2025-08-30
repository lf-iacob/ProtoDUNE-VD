from pandas.core import base
from imports import * #ad Henrique non piace questo elemento

'''
Questo è il codice che riguarda il programma principale, dato che contiene il main. Al suo interno importa 
un file che contiene tutti gli import, un file con la classe della TimeResolution specifica che contiene tutti
i metodi necessari per operare l'analisi in questione, un file che contiene i parametri del run in questione,
poi uno per altri parametri di configurazione. Inoltre, si usano delle funzioni e dei metodi che provengono 
dalle classi base di Waveform e WaveformSet, che vengono impiegati per compiere operazioni di base, tipo il
filtraggio sul set o altro.
Il codice è stato implementato da Federico Galizzi per ProtoDUNE-HD. Adessso deve essere aggiornato da Henrique
per poterlo impiegare su ProtoDUNE-VD in modo coerente ai dati a disposizione ed ottimale.
'''
#Viene usato la classe Denoise() che ha implementato Henrique

'''
STUDIARE UN CODICE SCRITTO DA QUALCUNO
Comincia dal capire per il codice specifico quanti e quali sono i file e altri codici devi guardare perché sono
chiamati lì all'interno. Allora, dai un'occhiata alle classi principali per farti un'idea - non troppo approfondita
perché possibile che non ti serva tutto quello che c'è dentro - dei loro attributi e metodi.
Allora, lo studio vero deve essere fatto sul codice che contiene il main, di cui devi guardare ogni cosa e risalire
alle funzioni che sono definite in file diversi per comprenderlo veramente.
TIP_by_Henrique: Per capire bene cosa fa un codice, lo prendi (copia&incolla da un'altra parte) e ti metti a modificare
                 e stampare ogni cosa in modo da capire veramente cosa sta succedendo
Riassumendo: il codice lo devi smontare, distruggere e provare a rimontarlo, anche in maniera diversa, per vedere che
             cosa succede.
'''


# --- MAIN ----------------------------------------------------------
if __name__ == "__main__":

    
    # --- SETUP -----------------------------------------------------
    # 1. Setup variables according to the configs/time_resolution_config.yml file
    '''
    Apre il file time_resolution_configs.yml che contiene i path delle cartelle ed i file da aprire
    come stringhe che servono per operare la time resolution. Il file YAML viene aperto come config_stream
    e poi viene caricato nel codice con il nome della variabile "config_variables".
    Da questo file vengono caricate queste stringhe attraverso il metodo ".get()" attraverso delle variabili
    apposite. Si crea new_daphne_to_offline che è un dizionario riferito ai canali della daphne e scrive i corrispondenti
    valori di canali offline.
    '''
    '''
    OFFLINE_CH: C'era bisogno di mettere in corrispondenza i nomi dei canali della DAPHNE e gli altri - offline - però
    adesso non abbiamo più bisogno di questa informazione
    '''
    with open("./configs/time_resolution_configs.yml", 'r') as config_stream:
        config_variables = yaml.safe_load(config_stream)

    #YAML è un file che viene estratto come un dizionario
    data_folder = config_variables.get("data_folder")
    ana_folder = config_variables.get("ana_folder")
    raw_ana_folder = ana_folder+config_variables.get("raw_ana_folder")
    new_channel_map_file = config_variables.get("new_channel_map_file")
    mapping_df = pd.read_csv("configs/"+new_channel_map_file, sep=",")
    new_daphne_channels = mapping_df['daphne_ch'].values + 100*mapping_df['endpoint'].values
            #mappa che permette di dare il nome ai canali come endpoint+numero_canale
    new_daphne_to_offline = dict(zip(new_daphne_channels, mapping_df['offline_ch']))

    # 2. Setup variables according to the params.yml file
    '''
    La stessa cosa viene fatta per il file params.yml, il quale contiene il run, i canali e le informazioni
    associate, come i prepulse_ticks (quel 250 messo sulla saturazione), postpulse_ticks (che indica fino
    a quale punto prende la finestra), int_low e int_up che corrisponde al range di integrazione, min_pes è
    il valore minimo di fotoelettroni - forse come nella saturazione avevamo buttato i segnali che hanno sotto
    i 10. Si fa un get delle variabili ed, in particolare, i file csv vengono passati sotto forma di DataFrame
    e stampate le prime cinque righe (why?).
    '''
    with open("./params.yml", 'r') as params_stream:
        params_variables = yaml.safe_load(params_stream)

    runs = params_variables.get("runs")
    #Carica i file csv come DataFrame e fa un print delle prime cinque righe con head()
    noise_results_file = params_variables.get("noise_results_file")
    noise_df = pd.read_csv(noise_results_file, sep=",")
    print(noise_df.head(5))
    calibration_file = params_variables.get("calibration_file")
    calibration_df = pd.read_csv(calibration_file, sep=",")
    print(calibration_df.head(5))

    channels = params_variables.get("channels")    #lista dei canali che si vogliono analizzare
    global_prepulse_ticks = params_variables.get("prepulse_ticks")
    global_int_low = params_variables.get("int_low")
    global_int_up = params_variables.get("int_up")
    global_postpulse_ticks = params_variables.get("postpulse_ticks")
    min_pes = params_variables.get("min_pes")
    global_baseline_rms = params_variables.get("baseline_rms")
    methods = params_variables.get("methods")
    relative_thrs = params_variables.get("relative_thrs")
    filt_levels = params_variables.get("filt_levels")
    h2_nbins = params_variables.get("h2_nbins")
    stat_lost = params_variables.get("stat_lost")







    
    # --- EXTRA VARIABLES -------------------------------------------
    '''
    Vengono indicate altre variabili necessarie, per esempio inizializza delle liste, prende i file .hdf5 dei
    run voluti - indicati in .yml - e crea delle directories contenenti delle analisi - non so.
    '''
    #Crea un lista chiamata "files" che raccoglie i file .hdf5 dei run indicati in file params.yml
    #di questa cosa non abbiamo più bisogno noi per come è scritta
    files = [data_folder+"processed_merged_run_"+str(run)+"_structured.hdf5" for run in runs]
    #liste
    min_min_pe = []
    max_max_pe = []
    min_min_t0 = []
    max_max_t0 = []
    hp_t0_pes = []
    #makedirs(): method creates a directory recursively, come fossi da terminale
    #exist_ok=True: se la directory esiste già, non succede niente alla directory (False avrebbe dato errore)
    os.makedirs(ana_folder, exist_ok=True) 
    os.makedirs(raw_ana_folder, exist_ok=True)






    
    # --- LOOP OVER RUNS --------------------------------------------
    for file, run in zip(files, runs): #in zip che affianca le due liste files e runs, per ciascuna coppia di elementi
        #dato che le istruzioni sono nel blocco dentro il for, significa che tutto questo viene eseguito sul run spe=
        #cifico selezionato per questo stage del ciclo -> Run specifico in analisi
        print("Reading run ", run)
        try:
            '''
            Il metodo reader.load_structured_waveformset() proviene da waffles.input_output.hdf5_structured.
            Mettendo come argomento il path del file dei dati hdf5 strutturati del run che si sta guardando - qui
            lo cerca il for come "file" nella lista "files" definita sopra in EXTRA VARIABLES - riesci a passare
            all'oggetto wfset_run della classe WaveformSet il set di waveform associato al run in questione.
            '''
            wfset_run = reader.load_structured_waveformset(file)
        except FileNotFoundError:
            '''
            Carica il wfset a meno che non venga trovato.
            '''
            print(f"File {file} not found. Skipping.")
            continue

        '''
        La variabile "a" è un oggetto della classe TimeResolution che viene associato al wfset che è stato selezionato
        in questo stage del loop del ciclo for
        '''
        a = tr.TimeResolution(wf_set=wfset_run)  #"a": ad Henrique non piace questo elemento
                                                 #"tr.": ad Henrique non piace nemmeno questo elemento


        # --- LOOP OVER CHANNELS ------------------------------------------
        '''
        Per il run specifico selezionato si va a guardare un canale alla volta a partire dalla lista "channels" pre=
        cedentemente compilata. Se la lista è vuote, prende tutti i canali; se no analizza solo quelli specificati.
        Nella lista channels, viene quindi fatto partire il for sulla lista di canali, ad ogni canale si fa riferimento
        con il nome "daphne_ch".
        '''
        if (channels == []):
            print("No channels specified. Using all channels.")
        for daphne_ch in channels:
            if daphne_ch not in new_daphne_to_offline:
                print(f"Channel {daphne_ch} not in new channel map")
                continue
                
            #Dal dizionario new_daphne_to_offline si estrae l'info dell'offline_ch per il canale specifico che si guarda
            #ma non abbiamo più bisogno di questa cosa
            offline_ch = new_daphne_to_offline[daphne_ch]


            #Accede ai valori a prepulse_ticks, int_low, int_up, postpulse_ticks del canale selezionato dal DataFrame
            if global_prepulse_ticks != 0:
                prepulse_ticks = global_prepulse_ticks
            else:
                prepulse_ticks = int(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'prepulse_ticks'].values[0])

            if global_int_low != 0:
                int_low = global_int_low
            else:
                int_low = int(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'int_low'].values[0])

            if global_int_up != 0:
                int_up = global_int_up
            else:
                int_up = int(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'int_up'].values[0])

            if global_postpulse_ticks != 0:
                postpulse_ticks = global_postpulse_ticks
            else:
                postpulse_ticks = int(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'postpulse_ticks'].values[0])
            #spe=SinglePhotoElectron
            spe_charge = float(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'Gain'].values[0])
            spe_ampl = float(calibration_df.loc[calibration_df['DaphneCh'] == daphne_ch, 'SpeAmpl'].values[0])
            baseline_rms = float(noise_df.loc[noise_df['OfflineCh'] == offline_ch, 'RMS'].values[0])


            #I parametri estratti vengono settati nell'oggetto della classe TimeResolution per quel canale
            try:
                a.set_analysis_parameters(ch=daphne_ch, prepulse_ticks=prepulse_ticks,
                                          postpulse_ticks=postpulse_ticks, int_low=int_low,
                                          int_up=int_up, spe_charge=spe_charge,
                                          spe_ampl=spe_ampl, min_pes=min_pes,
                                          baseline_rms=baseline_rms)
            except ValueError as e: #controllo sanity_check() dei parametri che sta sulla classe TimeResolution
                print(f"Error: {e}")
                continue


            #Operazioni svolte sull'oggetto della classe TimeResolution
            a.create_wfs() #crea wfs a partire dal wfset dopo aver fatto operazione di filtraggio su canali permessi
            a.select_time_resolution_wfs()
                '''dopo aver fatto un controllo sul fatto che ciascuna wf non è saturata e la baseline è stata calcolata
                correttamente, conta quante wfs sono in effetti "sane" e quindi quante sono da analizzare per la time resolution
                '''


            
            #Crea file root con il nome corretto relativo al run ed al canale che si sta guardando
            out_root_file_name = raw_ana_folder+f"Run_{run}_DaphneCh_{daphne_ch}_OfflineCh_{offline_ch}_time_resolution.root"
            root_file = TFile(out_root_file_name, "RECREATE")

            

            
            #La time resolution viene valutata sul set solo nel caso in cui le wfs "sane" sono più di 500
                 #(numero arbitrario scelto a caso, può essere tranquillamente modificato)
            if a.n_select_wfs > 500: 
                n_pwfs = min(9000, a.n_select_wfs) #si decide di prendere sempre sotto le 9000 wfs (p?wfs)
                #Del wfset si selezionano le prime tot=n_pwfs che sono accettate dalla time_selection e se ne fa
                    #un array unidimensionale con .flatten() per averle tutte vicine
                all_wfs = np.array([wf.adcs_float for wf in a.wfs[:n_pwfs] if wf.time_resolution_selection]).flatten()
                #In corrispondenza dei canali dell'adc si scrivono, sempre in un array unidimensionale, i ticks corrispondenti
                all_ticks = np.array([np.arange(len(wf.adcs_float)) for wf in a.wfs[:n_pwfs] if wf.time_resolution_selection]).flatten()
                #Estrae counts, xedges, yedges per l'istogramma bidimensionale che poi fa il persistence plot
                counts, xedges, yedges = np.histogram2d(all_ticks, all_wfs, bins=(len(a.wfs[0].adcs_float),h2_nbins),
                                                        range=[[0, len(a.wfs[0].adcs_float)],
                                                               [np.min(all_wfs), np.max(all_wfs)]])


                # Histogram 2D of t0 vs pe (ROOT)
                h2_persistence = TH2F("Persistence", "; Time [ticks]; Amplitude [ADC]",
                                len(a.wfs[0].adcs_float), 0, len(a.wfs[0].adcs_float),
                                h2_nbins, np.min(all_wfs), np.max(all_wfs))

                for i in range(len(a.wfs[0].adcs_float)):
                    for j in range(h2_nbins):
                        h2_persistence.SetBinContent(i+1, j+1, counts[i, j])
                
                h2_persistence.Write()

                for method in methods:
                        if method == "denoise":
                            loop_filt_levels = filt_levels
                        else:
                            loop_filt_levels = [0]

                        for relative_thr in relative_thrs:

                            for filt_level in loop_filt_levels:
                                rel_thr = str(relative_thr).replace(".", "p")
                                root_file.mkdir(f"{method}_filt_{filt_level}_thr_{rel_thr}")
                                root_file.cd(f"{method}_filt_{filt_level}_thr_{rel_thr}")

                                print("Channel ", daphne_ch)
                                
                                if (method == "denoise" and filt_level > 0):
                                    a.create_denoised_wfs(filt_level=filt_level)
                               
                                t0s, pes, tss = a.set_wfs_t0(method=method, relative_thr=relative_thr)
                                
                                t = TTree("time_resolution", "time_resolution")
                                t0 = np.zeros(1, dtype=np.float64)
                                pe = np.zeros(1, dtype=np.float64)
                                ts = np.zeros(1, dtype=np.float64)
                                t.Branch("t0", t0, "t0/D")
                                t.Branch("pe", pe, "pe/D")
                                t.Branch("timestamp", ts, "timestamp/D")

                                for i in range(len(t0s)):
                                    t0[0] = t0s[i]
                                    pe[0] = pes[i]
                                    ts[0] = tss[i]
                                    t.Fill()

                                t.Write()
    
            root_file.Close()
        del a, wfset_run
