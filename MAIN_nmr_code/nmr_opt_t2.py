'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time
import numpy as np

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
from nmr_std_function.data_parser import parse_csv_float3col
import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# variables
data_folder = "/root/NMR_DATA"
# data_folder = "D:"
en_fig = 1
en_remote_dbg = 1

# remote debug setup
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\129.22.143.88\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
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

# optimization parameters
t2_opt_mult = 2.5

# cpmg settings
cpmg_freq = 4.188  # 4.253 original
pulse1_us = 2.5  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 300
scan_spacing_us = 4000000
samples_per_echo = 64  # number of points
echoes_per_scan = 1454  # number of echos
init_adc_delay_compensation = 7  # acquisition shift microseconds
number_of_iteration = 4  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

# do cpmg measurement
nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                    echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
nmrObj.turnOffSystem()

# do signal processing
meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
    data_folder, meas_folder[0], 0, 0, 0, en_fig)

# Average navg echoes
navg = 16
npts = int(np.floor(echoes_per_scan / navg))
tmp1 = np.zeros(npts)
tmp2 = np.zeros(npts)
for j in range(0, npts):
    tmp1[j] = np.mean(np.real(a[j * navg:(j + 1) * navg - 1]))
    tmp2[j] = np.mean(t_echospace[j * navg:(j + 1) * navg - 1])
echo_int = tmp1
tvect_avg = tmp2

# save t2 data to csv file to be processed
f = open(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv', "w+")
for i in range(len(tvect_avg)):
    f.write("%f," % (tvect_avg[i] * 1000))  # in milisecond
    f.write("%f\n" % (echo_int[i]))
f.close()

# process t2 data
nmrObj.doLaplaceInversion(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv',
                          data_folder + '/' + meas_folder[0])
tvect, data = parse_csv_float2col(
    data_folder + '/' + meas_folder[0], 't1heel_out.csv')

# fitting data
tvect1, data1, fit1 = parse_csv_float3col(
    data_folder + '/' + meas_folder[0], 't1heel_datafit.csv')
plt.plot(tvect1, data1)
plt.plot(tvect1, fit1)
plt.show()


# convert data to array
tvectArray = np.array(tvect)
dataArray = np.array(data)

# null data after 2 s
dataArray[tvectArray > 1.8] = 0

# null data below echo_spacing
dataArray[tvectArray < (echo_spacing_us / 1e6)] = 0

i_peaks = signal.find_peaks_cwt(dataArray, np.arange(1, 10))

'''
a_peaks = np.zeros(len(i_peaks))
for i in range(0, len(i_peaks)):
    a_peaks[i] = dataArray[i_peaks[i]]

# find tvect in which the largest peak is found
t2_opt = tvect[i_peaks[np.where(max(a_peaks))[0][0]]]  # in second
'''

t2_opt = tvectArray[max(i_peaks)]  # in second

# adjust echoes_per_scan according to t2_opt
echoes_per_scan = np.round((t2_opt * 1e6 * t2_opt_mult) / echo_spacing_us)

print('num of echoes: %d' % echoes_per_scan)


plt.semilogx(tvect, dataArray)
plt.show()
