'''
Created on July 15th 2021

This module supports processing on the SoC/server (old method) and show the result on client via remote X window.
It also supports processing on the PC/client (new method) and show the result directly on client (much faster).
When en_remote_computing is 1, make sure to run the python code on the PC/client side.
When en_remote_computing is 0, make sure to run the python code on the SoCFPGA/server side.

@author: David Ariando
'''

#!/usr/bin/python

import os
from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col
from nmr_std_function.nmr_functions import compute_iterate, compute_stats, compute_in_bw_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import matplotlib.pyplot as plt
from scipy import signal
import pydevd
from datetime import datetime
import meas_configs.wmp_pcb1 as conf
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder

# variables
server_data_folder = "/root/NMR_DATA"
client_data_folder = "D:\\TEMP"
en_fig = 1
en_remote_dbg = 0
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

if en_remote_computing:
    data_folder = client_data_folder
    en_remote_dbg = 0  # force remote debugging to be disabled
else:
    data_folder = server_data_folder

# nmr object declaration
nmrObj = tunable_nmr_system_2018( server_data_folder, en_remote_dbg, en_remote_computing )

# measurement settings
samp_freq = 25  # sampling frequency
samples = 40000  # number of points
min_freq = 1.5  # in MHz
max_freq = 2.0  # in MHz

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )
nmrObj.deassertControlSignal( 
    nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk )

nmrObj.setPreampTuning( conf.vbias, conf.vvarac )  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork( conf.cpar, conf.cser )  # 4.25 MHz AFE
# nmrObj.setMatchingNetwork( 0, 0 )

nmrObj.assertControlSignal( 
    nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.RX_SEL1_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.PAMP_IN_SEL2_msk )
# nmrObj.deassertControlSignal( nmrObj.RX_FH_msk | nmrObj.RX2_L_msk | nmrObj.RX_FH_msk )
nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )

while True:
    # time.sleep(0.5)

    nmrObj.noise( samp_freq, samples )

    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )

    # process the data
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )

    # compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )
    compute_in_bw_noise( conf.meas_bw_kHz, conf.Df_MHz, min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setPreampTuning( 0, 0 )
