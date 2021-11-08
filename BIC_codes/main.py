from functions.dFC_funcs import *
import numpy as np
import time
import hdf5storage
import scipy.io as sio
import os
os.environ["MKL_NUM_THREADS"] = '64'
os.environ["NUMEXPR_NUM_THREADS"] = '64'
os.environ["OMP_NUM_THREADS"] = '64'

################################# Parameters #################################

###### DATA PARAMETERS ######
DATA_type = 'Gordon' # 'Gordon' or 'simulated' or 'ICA'

output_root = './../../../../../RESULTs/methods_implementation/'
# output_root = '/data/origami/dFC/RESULTs/methods_implementation/'
# output_root = '/Users/mte/Documents/McGill/Project/dFC/RESULTs/methods_implementation/'

data_root_simul = './../../../../DATA/TVB data/'
data_root_sample = './sampleDATA/'
data_root_gordon = './../../../../DATA/HCP/HCP_Gordon/'
data_root_ica = './../../../../DATA/HCP/HCP_PTN1200/node_timeseries/3T_HCP1200_MSMAll_d50_ts2/'

num_subj = 100
select_nodes = True
rand_node_slct = False
num_select_nodes = 50

###### MEASUREMENT PARAMETERS ######
n_states = 6 #12
n_subj_clstrs = 20
n_hid_states = 4
n_overlap = 0.5
W_sw = 44 # in seconds, 44, choose even Ws!?

###### PARALLELIZATION PARAMETERS ######
n_jobs = 8
n_jobs_methods = None
verbose=0



################################# FINDING SUBJECTs LIST #################################

# ICA
ALL_RECORDS = os.listdir(data_root_ica)
ALL_RECORDS = [i for i in ALL_RECORDS if '.txt' in i]
ALL_RECORDS.sort()
SUBJECTS_ica = list()
for s in ALL_RECORDS:
    num = s[:s.find('.')]
    SUBJECTS_ica.append(num)
SUBJECTS_ica = list(set(SUBJECTS_ica))
SUBJECTS_ica.sort()

# GORDON
ALL_RECORDS = os.listdir(data_root_gordon)
ALL_RECORDS = [i for i in ALL_RECORDS if 'Rest' in i]
ALL_RECORDS.sort()
SUBJECTS_gordon = list()
for s in ALL_RECORDS:
    num = s[:s.find('_')]
    SUBJECTS_gordon.append(num)
SUBJECTS_gordon = list(set(SUBJECTS_gordon))
SUBJECTS_gordon.sort()

SUBJECTS = intersection(SUBJECTS_gordon, SUBJECTS_ica)

print( str(len(SUBJECTS)) + ' subjects were found. ' + str(num_subj) + ' subjects were selected.')

SUBJECTS = SUBJECTS[0:num_subj]

################################# Load ICA BOLD data (HCP) #################################

if DATA_type=='ICA':

    SESSIONs = ['session_1']
    BOLD_Fs = 1/0.72

    BOLD = {}
    for session in SESSIONs:
        BOLD[session] = None
        for subject in SUBJECTS:
            time_series = np.loadtxt( \
                data_root_ica + subject + '.txt', dtype='float64' \
                )
            time_series = time_series.T
            
            # time_series = time_series - np.repeat(np.mean(time_series, axis=1)[:,None], time_series.shape[1], axis=1) # ???????????????????????

            if BOLD[session] is None:
                BOLD[session] = TIME_SERIES(data=time_series, subj_id=subject, Fs=BOLD_Fs, TS_name='BOLD ICA', session_name=session)
            else:
                BOLD[session].append_ts(new_time_series=time_series, subj_id=subject)

        print(BOLD[session].n_regions, BOLD[session].n_time)

################################# Load Real BOLD data (HCP) #################################

if DATA_type=='Gordon':

    SESSIONs = ['Rest1_LR' , 'Rest1_RL', 'Rest2_LR', 'Rest2_RL']
    BOLD_Fs = 1/0.72

    # LOAD Region Location DATA

    locs = sio.loadmat(data_root_gordon+'Gordon333_LOCS.mat')
    locs = locs['locs']

    # LOAD Region Data

    file = data_root_gordon+'Gordon333_Key.txt'
    f = open(file, 'r')

    atlas_data = []
    for line in f:
        row = line.split()
        atlas_data.append(row)

    BOLD = {}
    for session in SESSIONs:
        BOLD[session] = None
        for subject in SUBJECTS:

            subj_fldr = subject + '_' + session

            # LOAD BOLD Data

            DATA = hdf5storage.loadmat(data_root_gordon+subj_fldr+'/ROI_data_Gordon_333_surf.mat')
            time_series = DATA['ROI_data']

            time_series = time_series.T

            # time_series = time_series - np.repeat(np.mean(time_series, axis=1)[:,None], time_series.shape[1], axis=1) # ???????????????????????

            for n in range(time_series.shape[0]):
                time_series[n, :] = time_series[n, :] - np.mean(time_series[n, :])
                time_series[n, :] = np.divide(time_series[n, :], np.std(time_series[n, :]))

            if BOLD[session] is None:
                BOLD[session] = TIME_SERIES(data=time_series, subj_id=subject, \
                                    Fs=BOLD_Fs, \
                                    locs=locs, nodes_info=atlas_data, \
                                    TS_name='BOLD Real', session_name=session \
                                )
            else:
                BOLD[session].append_ts(new_time_series=time_series, subj_id=subject)

        print(BOLD[session].n_regions, BOLD[session].n_time)


        # select nodes

        if select_nodes:
            if rand_node_slct:
                nodes_idx = np.random.choice(range(BOLD[session].n_regions), size=num_select_nodes, replace=False)
                nodes_idx.sort()
            else:
                nodes_idx = np.array(list(range(47, 88)) + list(range(224, 263)))
            BOLD[session].select_nodes(nodes_idx=nodes_idx)

        print(BOLD[session].n_regions, BOLD[session].n_time)

################################# Load Sample BOLD data #################################

if DATA_type=='sample':

    BOLD_Fs = 1/0.5

    ###### BOLD DATA ######
    time_BOLD = np.load(data_root_sample+'bold_time.npy')/1e3    
    time_series = np.load(data_root_sample+'bold_data.npy')

    time_series = time_series.T

    BOLD = None
    for subject in range(5):

        if BOLD is None:
            BOLD = TIME_SERIES( \
                data=time_series[:, (subject)*1200:(subject+1)*1200], \
                subj_id=str(subject+1), Fs=BOLD_Fs, \
                time_array=time_BOLD[(subject)*1200:(subject+1)*1200], \
                TS_name='BOLD Sample' \
                )
        else:
            BOLD.append_ts( \
                new_time_series=time_series[:, (subject)*1200:(subject+1)*1200], \
                time_array=time_BOLD[(subject)*1200:(subject+1)*1200],
                subj_id=str(subject+1) \
                )

    print(BOLD.n_regions, BOLD.n_time)
        

################################# Load Simulated BOLD data #################################

if DATA_type=='simulated':
    time_BOLD = np.load(data_root_simul+'bold_time.npy')/1e3    
    time_series_BOLD = np.load(data_root_simul+'bold_data.npy')

    BOLD = TIME_SERIES(data=time_series_BOLD.T, subj_id='1', Fs=BOLD_Fs, time_array=time_BOLD, TS_name='BOLD Simulation')

################################# Load Simulated Tavg data #################################

if DATA_type=='simulated':
    time_Tavg = np.load(data_root_simul+'TVB data/tavg_time.npy')/1e3    
    time_series_Tavg = np.load(data_root_simul+'TVB data/tavg_data.npy')

    TAVG = TIME_SERIES(data=time_series_Tavg.T, subj_id='1', Fs=200, time_array=time_Tavg, TS_name='Tavg Simulation')

################################# Visualize BOLD #################################

for session in BOLD:
    BOLD[session].visualize(start_time=0, end_time=50, nodes_lst=list(range(10)), \
        save_image=True, fig_name=output_root+'BOLD_signal '+session)

################################# Measure dFC #################################

# todo get Fs of ts_dict
params = { \
    # Sliding Parameters
    'W': int(W_sw*BOLD_Fs), 'n_overlap': n_overlap, \
    # State Parameters
    'n_states': n_states, 'n_subj_clstrs': n_subj_clstrs, 'n_hid_states': n_hid_states, \
    # Parallelization Parameters
    'n_jobs': n_jobs_methods, 'verbose': 0, 'backend': 'loky' \
}

###### CONTINUOUS HMM ######
hmm_cont = HMM_CONT(**params)

###### WINDOW_LESS ######
windowless = WINDOWLESS(**params)

###### SLIDING WINDOW ######
sw_pc = SLIDING_WINDOW(sw_method='pear_corr', **params)
sw_mi = SLIDING_WINDOW(sw_method='MI', **params)

###### TIME FREQUENCY ######
time_freq_cwt = TIME_FREQ(method='CWT_mag', **params)
time_freq_wtc = TIME_FREQ(method='WTC', **params)

###### SLIDING WINDOW + CLUSTERING ######
swc_pc = SLIDING_WINDOW_CLUSTR(base_method='pear_corr', **params)

###### DISCRETE HMM ######
hmm_disc_pc = HMM_DISC(base_method='pear_corr', **params)


MEASURES = [

    hmm_cont, \

    windowless, \

    sw_pc, \
    # sw_mi, \
    # sw_gLasso, \

    time_freq_cwt, \
    # time_freq_cwt_r, \
    time_freq_wtc, \

    swc_pc, \
    # swc_gLasso, \

    hmm_disc_pc,\
    # hmm_disc_gLasso, \

]


sim_assess_params= { \
    'run_analysis': True, \
    'num_samples': 100, \
    'matching_method': 'score', \
    'n_jobs': n_jobs, 'backend': 'loky' \
}
dyn_conn_det_params = { \
    'run_analysis': False, \
    'N': 30, 'L': 1200, 'p': 100, \
    'n_jobs': n_jobs, 'backend': 'loky' \
}
params = { \
    # VISUALIZATION
    'vis_TR_idx': list(range(10, 20, 1)),'save_image': True, 'output_root': output_root, \
    # Parallelization Parameters
    'n_jobs': n_jobs, 'verbose': 1, 'backend': 'loky', \
    # Similarity Assessment Parameters
    'sim_assess_params': sim_assess_params, \
    # Dynamic Connection Detector Parameters
    'dyn_conn_det_params': dyn_conn_det_params \
}

dFC_analyzer = DFC_ANALYZER(MEASURES_lst=MEASURES, \
    analysis_name='reproducibility assessment', \
    **params \
)


tic = time.time()
print('Measurement Started ...')
SUBJs_dFC_session_sim_dict = dFC_analyzer.analyze(time_series_dict=BOLD)

# Save
np.save('./dFC_session_sim.npy', SUBJs_dFC_session_sim_dict) 

print('Measurement required %0.3f seconds.' % (time.time() - tic, ))

################################# SIMILARITY ASSESSMENT #################################

print_dict(dFC_analyzer.methods_corr)
dFC_analyzer.similarity_analyze(SUBJs_dFC_session_sim_dict)

################################# STATE MATCH #################################

state_match = dFC_analyzer.state_match()

#########################################################################################