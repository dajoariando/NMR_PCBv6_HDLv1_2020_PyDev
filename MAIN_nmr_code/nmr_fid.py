'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
from nmr_std_function.nmr_functions import compute_stats

import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 0

# cpmg settings
cpmg_freq = 4.191  # 4.253 original 4.188
pulse2_us = 10  # pulse pi length
pulse2_dtcl = 0.5  # useless with current code
scan_spacing_us = 100
samples_per_echo = 10000  # number of points
number_of_iteration = 1  # number of averaging
tx_opa_sd = 1  # put 1 to shutdown tx opamp during reception or 0 to keep it on
min_freq = 1
max_freq = cpmg_freq * 2

nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg )

nmrObj.setPreampTuning( -2.7, 0.3 )  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork( 2381, 439 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 2381, 439 )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.assertControlSignal( 
        nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX2_H_msk | nmrObj.RX_FH_msk )

while True:
    nmrObj.fid( cpmg_freq, pulse2_us, pulse2_dtcl,
               scan_spacing_us, samples_per_echo, number_of_iteration, tx_opa_sd )
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'fid_plot.png', en_fig )

nmrObj.deassertAll()
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 0, 0 )

