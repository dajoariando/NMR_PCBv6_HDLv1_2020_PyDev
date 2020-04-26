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
en_remote_dbg = 1
fcpmg_to_fsys_mult = 16
fig_num = 1

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
nmrObj.setMatchingNetwork()
nmrObj.setSignalPath()

# cpmg settings
cpmg_freq = 4.238  # 4.253 original
pulse1_us = 5  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 150
scan_spacing_us = 400000
samples_per_echo = 512  # number of points
echoes_per_scan = 64  # number of echos
init_adc_delay_compensation = 10  # acquisition shift microseconds
number_of_iteration = 10  # number of averaging
ph_cycl_en = 1
pulse180_t1_us = pulse2_us
# delay180_t1_int = 0
# sweep parameters
logsw = 1  # logsw specifies logsweep, or otherwise linsweep
delay180_sta = 100  # in microsecond
delay180_sto = 200000  # in microsecond
delay180_ste = 20  # number of steps
# reference parameters
ref_number_of_iteration = 20  # number of averaging

# compute period for the system clock (which is multiplication of the cpmg
# freq)
t_sys = (1 / cpmg_freq) / fcpmg_to_fsys_mult

# compute pulse180_t1 in integer values
pulse180_t1_int = np.round((pulse180_t1_us / t_sys) /
                           fcpmg_to_fsys_mult) * fcpmg_to_fsys_mult

# process delay
if logsw:
    delay180_t1_sw = np.logspace(
        np.log10(delay180_sta), np.log10(delay180_sto), delay180_ste)
else:
    delay180_t1_sw = np.linspace(delay180_sta, delay180_sto, delay180_ste)
# make delay to be multiplication of 16
delay180_t1_sw_int = np.round((delay180_t1_sw / t_sys) /
                              fcpmg_to_fsys_mult) * fcpmg_to_fsys_mult

# compute the reference
# do cpmg scan
nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                    echoes_per_scan, init_adc_delay_compensation, ref_number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_sw_int[delay180_ste - 1])
# process the data
meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a_ref, a0_ref, snr_ref, T2_ref, noise_ref, res_ref, theta_ref, data_filt_ref, echo_avg_ref, Df, _) = compute_iterate(
    data_folder, meas_folder[0], 0, 0, 0, en_scan_fig)

# make the loop
snr_table = np.zeros(delay180_ste)
a0_table = np.zeros(delay180_ste)
for i in range(0, delay180_ste):
    # do cpmg scan
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_sw_int[i])
    # process the data
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, _) = compute_iterate(
        data_folder, meas_folder[0], 1, theta_ref, echo_avg_ref, en_scan_fig)
    # interscan data store
    snr_table[i] = snr
    a0_table[i] = a0

    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        line1, = ax.plot(delay180_t1_sw[0:i + 1], a0_table[0:i + 1], 'r-')
        # ax.set_ylim(-50, 0)
        # ax.set_xlabel('Frequency [MHz]')
        # ax.set_ylabel('S11 [dB]')
        # ax.set_title("Reflection Measurement (S11) Parameter")
        ax.grid()
        fig.canvas.draw()
        # fig.canvas.flush_events()


nmrObj.turnOffSystem()
pass
