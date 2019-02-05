'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

#from nmr_std_function.data_parser import parse_simple_info
#from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018
#from nmr_std_function.data_parser import parse_csv_float2col
#import matplotlib.pyplot as plt
#from scipy import signal
import pydevd
import sys

# variables
data_folder = "/root/NMR_DATA"
en_fig = 0
en_remote_dbg = 0

# remote debug setup
server_ip = '129.22.143.88'
client_ip = '129.22.143.39'
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    # client_path = 'C:\\AcquisitionSW\\python_code\\RemoteSystemsTempFiles\\192.168.2.101\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    client_path = 'X:\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'  # client path with samba
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    # pydevd.settrace("192.168.2.1")
    pydevd.settrace(client_ip)

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)
nmrObj.initNmrSystem()
nmrObj.turnOnPower()
nmrObj.setPreampTuning(float(sys.argv[8]), float(sys.argv[9]))
nmrObj.setMatchingNetwork(
    float(sys.argv[10]), float(sys.argv[11]))  # good new ones
#nmrObj.setMatchingNetwork(3, 67)

# nmrObj.setSignalPath(nmrObj.gnrl_cnt | nmrObj.AMP_HP_LT1210_EN_msk |
#                     nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)


# Chad added "nmrObj.gnrl_cnt | " above
# cpmg settings
cpmg_freq = float(sys.argv[1])  # 4.253 original
pulse1_us = float(sys.argv[6])  # pulse pi/2 length
pulse2_us = float(sys.argv[7])  # pulse pi length

# pulse1_us = 18  # pulse pi/2 length
# pulse2_us = 26  # pulse pi length

read_window = float(sys.argv[4])  # Readout window length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = read_window + 200  # TE
scan_spacing_us = float(sys.argv[5])  # TR
# number of points (DesiredReadoutWindowLength*4*freq)
samples_per_echo = read_window * 4 * cpmg_freq
echoes_per_scan = float(sys.argv[3])  # number of echos
init_adc_delay_compensation = float(
    sys.argv[12])  # acquisition shift microseconds
number_of_iteration = float(sys.argv[2])  # number of averaging
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
