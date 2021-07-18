'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal

# variables
data_folder = "Y:\\NMR_Data"
en_fig = True
en_remote_dbg = False
use_latest_folder = True  # use latest experiment, otherwise specify the folder below

nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg, 1 )

datain = []  # set datain to 0 because the data will be read from file instead
direct_read = 0  # perform direct read from SDRAM. use with caution above!

if ( use_latest_folder ):
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_fig )
else:
    meas_folder = '2020_09_29_15_03_13_cpmg'  # with scope probe placed at W45
    # meas_folder = '2019_05_26_21_24_41_cpmg'  # no scope probe placed at W45
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, data_folder, meas_folder, 0, 0, 0, direct_read, datain, en_fig )
