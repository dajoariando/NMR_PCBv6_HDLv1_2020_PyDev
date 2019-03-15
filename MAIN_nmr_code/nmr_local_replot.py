'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
#from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal
# import pydevd

# variables
data_folder = "X:\\NMR_Data"
en_fig = 1
en_remote_dbg = 0

# meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
meas_folder = '2018_12_03_18_12_32_cpmg'
(a, _, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
    data_folder, meas_folder, 0, 0, 0, en_fig)
