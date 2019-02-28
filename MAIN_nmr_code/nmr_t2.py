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
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# settings
data_folder = "/root/NMR_DATA"  # the nmr data folder
en_fig = 0  # enable figure
en_remote_dbg = 0  # enable remote debugging. Enable debug server first!
direct_read = 0   # perform direct read from SDRAM. use with caution above!
meas_time = 1  # measure time

if (meas_time):
    start_time = time.time()

# remote debug setup
server_ip = '129.22.143.88'
client_ip = '129.22.143.39'
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    # client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\' + \
    # server_ip + '\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\' # client
    # path with remote system
    client_path = 'X:\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'  # client path with samba
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace(client_ip)

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
# for normal path
nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)
# for reflection path or broadband board
# nmrObj.assertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
#                           nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_2_msk)

# cpmg settings
cpmg_freq = 0.5  # 4.253 original 4.188
pulse1_us = 8  # pulse pi/2 length
pulse2_us = pulse1_us * 1.6  # pulse pi length
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 220
scan_spacing_us = 100000
samples_per_echo = 128  # number of points
echoes_per_scan = 300  # number of echos
init_adc_delay_compensation = 10  # acquisition shift microseconds
number_of_iteration = 4  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0

if (direct_read):
    datain = nmrObj.cpmgSequenceDirectRead(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                                           echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en,
                                           pulse180_t1_int, delay180_t1_int)
else:
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration,
                        ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    datain = []  # set datain to 0 because the data will be read from file instead

# turn off system
# nmrObj.turnOffSystem()
# for normal path
nmrObj.deassertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
                             nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_1_msk)
# for reflection path or broadband board
# nmrObj.deassertControlSignal(nmrObj.AMP_HP_LT1210_EN_msk |
# nmrObj.PAMP_IN_SEL_RX_msk | nmrObj.RX_IN_SEL_2_msk)

nmrObj.setMatchingNetwork(0, 0)
nmrObj.setPreampTuning(0, 0)
nmrObj.deassertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                             nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk)

meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
(a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
    data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_fig)

if (meas_time):
    elapsed_time = time.time() - start_time
    print("time elapsed: %.3f" % (elapsed_time))
