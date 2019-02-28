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
    client_path = 'C:\\AcquisitionSW\\python_code\\RemoteSystemsTempFiles\\192.168.2.101\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("192.168.2.1")

# OLD system setup
#nmrObj = tunable_nmr_system_2018(data_folder)
# nmrObj.initNmrSystem()
# nmrObj.turnOnPower()
#nmrObj.setPreampTuning(-3.46, -4.8)
#nmrObj.setMatchingNetwork(4, 55)

#nmrObj.setSignalPath(nmrObj.gnrl_cnt | nmrObj.AMP_HP_LT1210_EN_msk | nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)

nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
# nmrObj.turnOnPower()
nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk)
nmrObj.setPreampTuning(-3.35, -1.4)
nmrObj.setMatchingNetwork(19, 66)
# nmrObj.setSignalPath()
nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)

# cpmg settings
cpmg_freq = 4.156  # 4.253 original 4.188
pulse1_us = 2.4  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 120

scan_spacing_us = 400000
samples_per_echo = 1024  # number of points
echoes_per_scan = 256  # number of echos
init_adc_delay_compensation = 7  # acquisition shift microseconds
number_of_iteration = 100  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                    echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)

nmrObj.turnOffSystem()
'''
meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
    data_folder, meas_folder[0], 0, 0, 0, en_fig)
'''
