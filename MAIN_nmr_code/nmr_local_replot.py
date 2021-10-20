'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from scipy import signal

import matplotlib.pyplot as plt
from nmr_std_function.data_parser import parse_csv_float2col
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.nmr_functions import compute_iterate

# variables
data_folder = "D:\\NMR_Data"
en_fig = True
en_remote_dbg = False
use_latest_folder = False  # use latest experiment, otherwise specify the folder below

from nmr_std_function.sys_configs import UF_black_holder_brown_coil_PCB04 as conf
dconv_lpf_ord = conf.dconv_lpf_ord  # downconversion order
dconv_lpf_cutoff_kHz = conf.meas_bw_kHz  # downconversion lpf cutoff

nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg, 1 )

datain = []  # set datain to 0 because the data will be read from file instead
direct_read = 0  # perform direct read from SDRAM. use with caution above!

if ( use_latest_folder ):
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_fig )
else:
    meas_folder = '2021_10_19_00_33_22_cpmg_001'  # with scope probe placed at W45
    # meas_folder = '2019_05_26_21_24_41_cpmg'  # no scope probe placed at W45
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, data_folder, meas_folder, 0, 0, 0, direct_read, datain, en_fig , dconv_lpf_ord, dconv_lpf_cutoff_kHz )
