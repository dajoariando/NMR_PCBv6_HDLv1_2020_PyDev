'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time
import numpy as np
import pydevd
import matplotlib.pyplot as plt

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018

# variables
data_folder = "/root/NMR_DATA"
en_scan_fig = 0
en_fig = 1
en_remote_dbg = 0

# remote debug setup
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("dajo-compaqsff")

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)
nmrObj.initNmrSystem()
nmrObj.turnOnPower()
nmrObj.setPreampTuning()
nmrObj.setMatchingNetwork(19, 66)
nmrObj.setSignalPath()

# cpmg settings
cpmg_freq = 4.188
pulse1_us = 2.5  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 120
scan_spacing_us = 400000
samples_per_echo = 1024  # number of points
echoes_per_scan = 64  # number of echos
init_adc_delay_compensation = 10  # acquisition shift microseconds
number_of_iteration = 4  # number of averaging
ph_cycl_en = 1
pulse180_t1_us = pulse2_us
# sweep parameters
logsw = 1  # logsw specifies logsweep, or otherwise linsweep
delay180_sta = 100  # in microsecond
delay180_sto = 400000  # in microsecond
delay180_ste = 20  # number of steps
# reference parameters
ref_number_of_iteration = 20  # number of averaging
ref_twait_mult = 3  # wait time mult. from delay180_sto entered

nmrObj.cpmgT1(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation,
              number_of_iteration, ph_cycl_en, pulse180_t1_us, logsw, delay180_sta, delay180_sto, delay180_ste, ref_number_of_iteration, ref_twait_mult, data_folder, en_scan_fig, en_fig)

nmrObj.turnOffSystem()
pass
