'''
Created on Mar 30, 2018

@author: David Ariando

in progress:
*** direct_read, a setting to read data directly from SDRAM using Python is implemented using the same CPMG_iterate C-function (with the loop handled by Python instead of C).
It is a slower operation than using C to write to SDCard directly. It might be due to every iteration will
generate acqu.par separately in separate folder. Or MAYBE [less likely] writing to SDRAM via DMA is slower than writing directly
to a text file. Or MAYBE because every iteration runs CPMG_iterate with 1-iteration, the C program is called
number_of_iteration times. Also the computation of SNR/echo/scan is wrong in compute_iterate due to having
only 1 as a number_of_iteration in acqu.par. It seems to be no point of using Python if C still needs to be called.
So many problems yet not having better speed. It might be better to write everything in Python instead.
'''

#!/usr/bin/python

import os
import time
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import calcP90
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
from nmr_std_function import data_parser
import matplotlib.pyplot as plt
from scipy import signal
import pydevd
import numpy as np


# settings
data_folder = "/root/NMR_DATA"  # the nmr data folder
en_fig = 1  # enable figure
en_remote_dbg = 0  # enable remote debugging. Enable debug server first!
direct_read = 0   # perform direct read from SDRAM. use with caution above!
meas_time = 1  # measure time
process_data = 0  # process data within the SoC

# cpmg settings
cpmg_freq = 6  # *4 for the real ADC frequency
pulse1_us = 0  # 75 for Cheng's coil. pulse pi/2 length.
pulse2_us = 1.6 * pulse1_us  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 300  # cheng' coil : 750
scan_spacing_us = 1000000
samples_per_echo = 1024  # number of points
echoes_per_scan = 1  # number of echos
# put to 10 for broadband board and 6 for tunable board
init_adc_delay_compensation = 6  # acquisition shift microseconds.
number_of_iteration = 1  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0


if (meas_time):
    start_time = time.time()

# instantiate nmr object
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk)

nmrObj.assertControlSignal(
    nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk)

while True:
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration,
                        ph_cycl_en, pulse180_t1_int, delay180_t1_int)

    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    data_fold = (data_folder + '/' + meas_folder[0] + '/')
    file_path = (data_fold + 'asum')

    (param_list, value_list) = data_parser.parse_info(
        data_fold, 'acqu.par')  # read file

    SpE = int(data_parser.find_value(
        'nrPnts', param_list, value_list))
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    data = np.zeros(NoE * SpE)
    data = np.array(data_parser.read_data(file_path))

    ppval = np.max(data) - np.min(data)
    print("peak-to-peak : %d" % ppval)
    # print("rms : %f" % ppval / (2 * np.sqrt(2)))

    plt.ion()
    fig = plt.figure(1)
    fig.clf()
    plt.plot(data)
    fig.canvas.draw()


# turn off system
nmrObj.deassertControlSignal(
    nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk)

nmrObj.deassertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                             nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk)


if (meas_time):
    elapsed_time = time.time() - start_time
    print("time elapsed: %.3f" % (elapsed_time))
