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
en_remote_dbg = 0
fig_num = 100
direct_read = 0   # perform direct read from SDRAM. use with caution above!

# instantiate nmr object
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
# nmrObj.turnOnPower()
nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk)
# nmrObj.setPreampTuning(-2.93, 3.7)  # for 2.43MHz BLACK
nmrObj.setPreampTuning(-3.1, -4.2)  # for 1.87MHz BLACK
# nmrObj.setMatchingNetwork(2700, 350)  # for 2.43MHz BLACK
# nmrObj.setMatchingNetwork(3180, 420)  # for 1.87MHz BLACK
# nmrObj.setMatchingNetwork(255, 76)  # 4.05 MHz
# nmrObj.setMatchingNetwork(189, 74)  # 4.17 MHz KeA
nmrObj.setMatchingNetwork(192, 74)  # 4.17 MHz AFE
# nmrObj.setSignalPath()
# for normal path
nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)
# for reflection path or broadband board
# nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
#                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_2_msk)

# cpmg settings
cpmg_freq = 4.16
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 200
scan_spacing_us = 50000
samples_per_echo = 1024  # number of points
echoes_per_scan = 128  # number of echos
init_adc_delay_compensation = 6  # acquisition shift microseconds
number_of_iteration = 16  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

# sweep settings
pulse1_us_sta = 0.1  # in microsecond
pulse1_us_sto = 3.0  # in microsecond
pulse1_us_ste = 30  # number of steps
pulse1_us_sw = np.linspace(pulse1_us_sta, pulse1_us_sto, pulse1_us_ste)

a_integ_table = np.zeros(pulse1_us_ste)
for i in range(0, pulse1_us_ste):
    pulse1_us = pulse1_us_sw[i]  # pulse pi/2 length
    pulse2_us = pulse1_us * 1.6  # pulse pi length
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    datain = []  # set datain to 0 because the data will be read from file instead
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
        data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_scan_fig)
    a_integ_table[i] = a_integ
    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        line1, = ax.plot(pulse1_us_sw[0:i + 1], a_integ_table[0:i + 1], 'r-')
        # ax.set_ylim(-50, 0)
        # ax.set_xlabel('Frequency [MHz]')
        # ax.set_ylabel('S11 [dB]')
        # ax.set_title("Reflection Measurement (S11) Parameter")
        ax.grid()
        fig.canvas.draw()
        # fig.canvas.flush_events()

# turn off system
nmrObj.deassertControlSignal(
    nmrObj.AMP_HP_LT1210_EN_msk | nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)
nmrObj.setMatchingNetwork(0, 0)
nmrObj.setPreampTuning(0, 0)
nmrObj.deassertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                             nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk)
pass
