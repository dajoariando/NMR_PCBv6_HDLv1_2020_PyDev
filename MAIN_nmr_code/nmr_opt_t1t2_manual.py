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

# variables
data_folder = "/root/NMR_DATA"
en_fig = 0
T2_mult = 1.6  # the experiment length optimization
max_fifo_data = 512 * 256

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)
# nmrObj.turnOnRemoteDebug()
nmrObj.initNmrSystem()
nmrObj.turnOnPower()
nmrObj.setPreampTuning()
nmrObj.setMatchingNetwork()
nmrObj.setSignalPath()

# cpmg settings
cpmg_freq = 4.268  # 4.253 original
pulse1_us = 5  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 1000
scan_spacing_us = 4000000
samples_per_echo = 512  # number of points
echoes_per_scan = 64  # number of echos
init_adc_delay_compensation = 10  # acquisition shift microseconds
number_of_iteration = 4  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

# measure initial T2
nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                    echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df) = compute_iterate(
    data_folder, meas_folder[0], en_fig)
print('T2 = ' + '{0:.4f}'.format(T2 * 1e6) + ' usec' +
      ', t_exp = ' + '{0:.4f}'.format(echoes_per_scan * echo_spacing_us) + ' usec')

while (T2 * 1e6) > (echoes_per_scan * echo_spacing_us):

    print('T2 = ' + '{0:.4f}'.format(T2 * 1e6) + ' usec' +
          ', t_exp = ' + '{0:.4f}'.format(echoes_per_scan * echo_spacing_us) + ' usec')

    echoes_per_scan = round(
        (T2 * 1e6) / echo_spacing_us * T2_mult)  # number of echos
    if echoes_per_scan > max_fifo_data / samples_per_echo:
        break

    # do NMR measurement
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df) = compute_iterate(
        data_folder, meas_folder[0], en_fig)

echoes_per_scan = round(
    (T2 * 1e6) / echo_spacing_us * T2_mult)  # number of echos
if echoes_per_scan > max_fifo_data / samples_per_echo:
    echoes_per_scan = max_fifo_data / samples_per_echo

print('Optimized number of echoes: ' + '{0:.4f}'.format(echoes_per_scan))
nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                    echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df) = compute_iterate(
    data_folder, meas_folder[0], 1)

nmrObj.turnOffSystem()
