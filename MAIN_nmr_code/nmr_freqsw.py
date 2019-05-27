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
fig_num = 1
direct_read = 0   # perform direct read from SDRAM. use with caution above!

# instantiate nmr object
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk)
# nmrObj.setPreampTuning(-2.93, 3.7)  # for 2.43MHz BLACK
nmrObj.setPreampTuning(-2.93, -5)  # for 1.87MHz BLACK
# nmrObj.setMatchingNetwork(2700, 350)  # for 2.43MHz BLACK
# nmrObj.setMatchingNetwork(3180, 420)  # for 1.87MHz BLACK
nmrObj.setMatchingNetwork(255, 76)  # 4.05 MHz
nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)


pulse1_us = 2.9  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 200
scan_spacing_us = 400000
samples_per_echo = 512  # number of points
echoes_per_scan = 256  # number of echos
init_adc_delay_compensation = 6  # acquisition shift microseconds
number_of_iteration = 32  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

# sweep settings
cpmg_freq_sta = 3.9  # in MHz
cpmg_freq_sto = 4.0  # in MHz
cpmg_freq_ste = 10  # number of steps
cpmg_freq_sw = np.linspace(cpmg_freq_sta, cpmg_freq_sto, cpmg_freq_ste)

ainteg_tbl = np.zeros(cpmg_freq_ste)
for i in range(0, cpmg_freq_ste):
    cpmg_freq = cpmg_freq_sw[i]
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    datain = []  # set datain to 0 because the data will be read from file instead
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
        data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_scan_fig)
    ainteg_tbl[i] = a_integ
    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        line1, = ax.plot(cpmg_freq_sw[0:i + 1], ainteg_tbl[0:i + 1], 'r-')
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
