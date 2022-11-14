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
import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 0

# remote debug setup
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\129.22.143.88\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    # pydevd.settrace("dajo-compaqsff")
    pydevd.settrace("129.22.143.39")

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)

nmrObj.initNmrSystem()
# nmrObj.turnOnPower()
# nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
#                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk)
#nmrObj.setPreampTuning(-3.35, -1.4)
#nmrObj.setMatchingNetwork(19, 66)
# nmrObj.setSignalPath()
# nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
#                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)

# cpmg settings
cpmg_freq = 2  # 4.253 original 4.188
pulse2_us = 20  # pulse pi length
pulse2_dtcl = 0.5  # useless with current code
scan_spacing_us = 400000
samples_per_echo = 10  # number of points
number_of_iteration = 1  # number of averaging

nmrObj.fid(cpmg_freq, pulse2_us, pulse2_dtcl,
           scan_spacing_us, samples_per_echo, number_of_iteration)

# nmrObj.turnOffSystem()
# nmrObj.deassertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
#                             nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)
#nmrObj.setMatchingNetwork(0, 0)
#nmrObj.setPreampTuning(0, 0)
# nmrObj.deassertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
# nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
# nmrObj.PSU_5V_ANA_N_EN_msk)


#meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
#(a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
#    data_folder, meas_folder[0], 0, 0, 0, en_fig)
