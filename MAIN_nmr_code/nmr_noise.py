'''
Created on July 15th 2021

This module supports processing on the SoC/server (old method) and show the result on client via remote X window.
It also supports processing on the PC/client (new method) and show the result directly on client (much faster).

Set the correct settings in nmr_class for the ip addresses.

When en_remote_computing is 1, make sure to run the python code on the PC/client side.
When en_remote_computing is 0, make sure to run the python code on the SoCFPGA/server side.

This module calculates the general noise or in-bandwidth noise

@author: David Ariando
'''

#!/usr/bin/python

import os
from datetime import datetime
import pydevd
from scipy import signal
import matplotlib.pyplot as plt

from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col, find_Cpar_Cser_from_table, find_Vbias_Vvarac_from_table
from nmr_std_function.nmr_functions import compute_iterate, compute_stats, compute_in_bw_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# select the coil configuration
# from nmr_std_function.sys_configs import WMP_old_coil_1p7 as conf


def nmr_noise( samp_freq, samples, min_freq, max_freq, tuning_freq, meas_bw_kHz, continuous , client_data_folder ):

    # variables
    server_data_folder = "/root/NMR_DATA"
    # client_data_folder = "D:\\TEMP"
    S11_table = "genS11Table_SYS2.txt"  # filename for S11 tables
    S21_table = "genS21Table_SYS2.txt"
    en_fig = 1
    en_remote_dbg = 0
    en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

    if en_remote_computing:
        data_folder = client_data_folder
        en_remote_dbg = 0  # force remote debugging to be disabled
    else:
        data_folder = server_data_folder

    # nmr object declaration
    nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

    # measurement settings
    # samp_freq = 25  # sampling frequency
    # samples = 100000  # number of points
    # min_freq = 1.5  # in MHz
    # max_freq = 2.0  # in MHz
    # tuning_freq = 1.6  # hardware tuning frequency selector, using lookup table
    # meas_bw_kHz = 10  # downconversion filter bw

    # system setup
    nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                               nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                               nmrObj.PSU_5V_ANA_N_EN_msk )
    nmrObj.deassertControlSignal( 
        nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk )

    Cpar, Cser = find_Cpar_Cser_from_table ( nmrObj.client_path , tuning_freq, S11_table )
    Vbias, Vvarac = find_Vbias_Vvarac_from_table ( nmrObj.client_path , tuning_freq, S21_table )
    nmrObj.setPreampTuning( Vbias, Vvarac )  # try -2.7, -1.8 if fail
    nmrObj.setMatchingNetwork( Cpar, Cser )  # 4.25 MHz AFE
    # nmrObj.setMatchingNetwork( 0, 0 )

    nmrObj.assertControlSignal( 
        nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.RX_SEL1_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.PAMP_IN_SEL2_msk )
    # nmrObj.deassertControlSignal( nmrObj.RX_FH_msk | nmrObj.RX2_L_msk | nmrObj.RX_FH_msk )
    nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )
    # nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX2_H_msk | nmrObj.RX_FH_msk )

    while True:
        # time.sleep(0.5)

        nmrObj.noise( samp_freq, samples )

        if  en_remote_computing:  # copy remote files to local directory
            cp_rmt_file( nmrObj.scp, server_data_folder, client_data_folder, "current_folder.txt" )

        # process the data
        meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

        if  en_remote_computing:  # copy remote folder to local directory
            cp_rmt_folder( nmrObj.scp, server_data_folder, client_data_folder, meas_folder[0] )
            exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, "rm -rf " + meas_folder[0], nmrObj.server_data_folder )  # delete the file in the server

        # compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )
        compute_in_bw_noise( meas_bw_kHz, tuning_freq, min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )

        if ( not continuous ):
            break

    nmrObj.setMatchingNetwork( 0, 0 )
    nmrObj.setPreampTuning( 0, 0 )
    nmrObj.deassertAll()
    nmrObj.exit()


# uncomment this line to debug the nmr noise code locally here
samp_freq = 25  # sampling frequency
samples = 100000  # number of points
min_freq = 1.5  # in MHz
max_freq = 2.0  # in MHz
tuning_freq = 1.7  # hardware tuning frequency selector, using lookup table
meas_bw_kHz = 10  # downconversion filter bw
continuous = False  # continuous running at one frequency configuration
client_data_folder = "D:\\TEMP"
nmr_noise( samp_freq, samples, min_freq, max_freq, tuning_freq, meas_bw_kHz, continuous, client_data_folder )
