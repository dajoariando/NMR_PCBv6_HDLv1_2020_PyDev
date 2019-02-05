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
import numpy as np

# variables
data_folder = "/root/NMR_DATA"
en_scan_fig = 0
en_fig = 1
en_remote_dbg = 1
fig_num = 100

# remote debug setup
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'C:\\AcquisitionSW\\python_code\\RemoteSystemsTempFiles\\192.168.2.101\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("192.168.2.1")

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)
nmrObj.initNmrSystem()
nmrObj.turnOnPower()
nmrObj.setPreampTuning(-3.35, -1.4)
# nmrObj.setMatchingNetwork(14, 95)
nmrObj.setMatchingNetwork(0, 0)
nmrObj.setSignalPath()

# cpmg settings
cpmg_freq = 1.788
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 200
scan_spacing_us = 100000
samples_per_echo = 512  # number of points
echoes_per_scan = 256  # number of echos
init_adc_delay_compensation = 17  # acquisition shift microseconds
number_of_iteration = 64  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

# sweep settings
pulse1_us_sta = 8  # in microsecond
pulse1_us_sto = 20  # in microsecond
pulse1_us_ste = 40  # number of steps
pulse1_us_sw = np.linspace(pulse1_us_sta, pulse1_us_sto, pulse1_us_ste)

a0_table = np.zeros(pulse1_us_ste)
for i in range(0, pulse1_us_ste):
    pulse1_us = 8  # pulse pi/2 length
    pulse2_us = pulse1_us_sw[i]  # pulse pi length
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
        data_folder, meas_folder[0], 0, 0, 0, en_scan_fig)
    a0_table[i] = a0
    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        line1, = ax.plot(pulse1_us_sw[0:i + 1], a0_table[0:i + 1], 'r-')
        # ax.set_ylim(-50, 0)
        # ax.set_xlabel('Frequency [MHz]')
        # ax.set_ylabel('S11 [dB]')
        # ax.set_title("Reflection Measurement (S11) Parameter")
        ax.grid()
        fig.canvas.draw()
        # fig.canvas.flush_events()

nmrObj.turnOffSystem()
pass
