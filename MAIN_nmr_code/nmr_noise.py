'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal
import pydevd
from datetime import datetime

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 1

# nmr object declaration
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# measurement settings
samp_freq = 25  # sampling frequency
samples = 400000  # number of points
min_freq = 0.001
max_freq = 12.5

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk | 
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | 
                           nmrObj.PSU_5V_ANA_N_EN_msk)
nmrObj.deassertControlSignal(
    nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk)

nmrObj.setPreampTuning(-2.7, 0.3)  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork(2381, 440)  # 4.25 MHz AFE

nmrObj.assertControlSignal(
    nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.RX_SEL1_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.PAMP_IN_SEL2_msk)
# nmrObj.deassertControlSignal(nmrObj.PAMP_IN_SEL2_msk)

while True:

    # time.sleep(0.5)

    nmrObj.noise(samp_freq, samples)

    # process the data
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    compute_noise(min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig)

nmrObj.setMatchingNetwork(0, 0)
nmrObj.setPreampTuning(0, 0)
