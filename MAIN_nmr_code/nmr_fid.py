'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col, parse_csv_float4col, find_Cpar_Cser_from_table, find_Vbias_Vvarac_from_table
from nmr_std_function.nmr_functions import compute_iterate, compute_stats
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# variables
server_data_folder = "/root/NMR_DATA"
client_data_folder = "D:\\TEMP"
S11_table = "genS11Table.txt"  # filename for S11 tables
S21_table = "genS21Table_10k.txt"
en_fig = 1
en_remote_dbg = 0
# remote computing configuration. See the NMR class to see details of use
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data
if en_remote_computing:
    data_folder = client_data_folder
    en_remote_dbg = 0  # force remote debugging to be disabled
else:
    data_folder = server_data_folder

# cpmg settings
cpmg_freq = 1.7  # 4.253 original 4.188
pulse2_us = 10  # pulse pi length
pulse2_dtcl = 0.5  # useless with current code
scan_spacing_us = 100
samples_per_echo = 10000  # number of points
number_of_iteration = 1  # number of averaging
tx_opa_sd = 1  # put 1 to shutdown tx opamp during reception or 0 to keep it on
min_freq = 1
max_freq = cpmg_freq * 2

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( server_data_folder, en_remote_dbg, en_remote_computing )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

Cpar, Cser = find_Cpar_Cser_from_table ( nmrObj.client_path , cpmg_freq, S11_table )
Vbias, Vvarac = find_Vbias_Vvarac_from_table ( nmrObj.client_path , cpmg_freq, S21_table )
nmrObj.setPreampTuning( Vbias, Vvarac )
nmrObj.setMatchingNetwork( Cpar, Cser )
nmrObj.setMatchingNetwork( Cpar, Cser )

nmrObj.assertControlSignal( 
        nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
# nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )

while True:
    nmrObj.fid( cpmg_freq, pulse2_us, pulse2_dtcl,
               scan_spacing_us, samples_per_echo, number_of_iteration, tx_opa_sd )

    # compute the generated data
    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj, "rm -rf " + meas_folder[0] )  # delete the file in the server
    compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'fid_plot.png', en_fig )

nmrObj.deassertAll()
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 0, 0 )

