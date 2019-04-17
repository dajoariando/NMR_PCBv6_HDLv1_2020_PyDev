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

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 0

# nmr object declaration
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# measurement settings
samp_freq = 25  # sampling frequency
samples = 50000  # number of points
min_freq = 0.5
max_freq = 5

# system setup
nmrObj.initNmrSystem()
nmrObj.assertControlSignal(
    nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk)
nmrObj.setPreampTuning(-2.75, 1.4)
nmrObj.setMatchingNetwork(250, 100)

while True:

    # nmrObj.turnOnPower()
    nmrObj.assertControlSignal(
        nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk |
        nmrObj.PSU_5V_TX_N_EN_msk | nmrObj.PSU_5V_ADC_EN_msk)

    # nmrObj.setSignalPath()
    nmrObj.assertControlSignal(
        nmrObj.AMP_HP_LT1210_EN_msk |
        nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)

    time.sleep(0.5)

    nmrObj.noise(samp_freq, samples)

    # nmrObj.turnOffSystem()
    nmrObj.deassertControlSignal(
        nmrObj.AMP_HP_LT1210_EN_msk |
        nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)

    nmrObj.deassertControlSignal(
        nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk |
        nmrObj.PSU_5V_TX_N_EN_msk | nmrObj.PSU_5V_ADC_EN_msk)

    # process the data
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    compute_noise(min_freq, max_freq, data_folder, meas_folder[0], en_fig)


nmrObj.setMatchingNetwork(0, 0)
nmrObj.setPreampTuning(0, 0)
