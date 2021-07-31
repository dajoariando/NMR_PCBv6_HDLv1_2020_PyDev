'''
Created on Mar 30, 2018

@author: David Ariando

standard noise measurement of the AFE.
the standard samples is 1 million and it'll take sometime.

'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col
from nmr_std_function.nmr_functions import compute_stats, compute_in_bw_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import matplotlib.pyplot as plt
from scipy import signal
import shutil
import pydevd
from datetime import datetime
import numpy as np
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# select the coil configuration
from nmr_std_function.sys_configs import WMP_old_coil as conf

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

# general measurement settings
samp_freq = 25  # sampling frequency
samples = 500000  # number of points
min_freq = 1.8  # 0.200
max_freq = 2.2  # 12.5

# get current time
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = data_folder + '/' + datename + '_noise_std'

fignum = 0


def perform_noise_test ( plotname , fignum ):

    fignum = fignum + 1

    info = str( fignum ).zfill( 2 ) + '___' + plotname
    plotname = info + '.png'

    # sample noise
    nmrObj.noise( samp_freq, samples )

    # process the data
    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj, "rm -rf " + meas_folder[0] )  # delete the file in the server
    # nstd, nmean = compute_stats( min_freq, max_freq, data_folder, meas_folder[0], plotname, en_fig )  # real scan
    nstd, nmean = compute_in_bw_noise( conf.meas_bw_kHz, conf.Df_MHz, min_freq, max_freq, data_folder, meas_folder[0], plotname, en_fig )
    f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

    shutil.move ( data_folder + '/' + meas_folder[0], swfolder + '/' + info )  # move the data folder
    shutil.move ( swfolder + '/' + info + '/' + plotname, swfolder + '/' + plotname )  # move the data folder

    return fignum


# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

# get current time
# now = datetime.now()
# datename = now.strftime( "%y%m%d_%H%M%S_" )

# turn off everything at the beginning
nmrObj.deassertAll()

if en_remote_computing:
    f = open( data_folder + '\\' + datename + '_noise_std.txt', "w" )  # open text file
else:
    f = open( swfolder + '/' + 'noise_std.txt', "w" )  # open text file
fignum = 0  # variable to store figure number

# enable the minimum power supply necessary for the ADC
info = 'en_adc_power'
nmrObj.assertControlSignal ( nmrObj.PSU_5V_ADC_EN_msk )
# fignum = perform_noise_test ( info, fignum )

# enable the first RX path power supply
info = 'en_rx_power'
nmrObj.assertControlSignal ( nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )
# fignum = perform_noise_test ( info, fignum )

# enable the final rx path
info = 'en_final_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX_FH_msk )
fignum = perform_noise_test ( info, fignum )

# enable the rx selector
info = 'en_rx_sel_path'
nmrObj.assertControlSignal ( nmrObj.RX_SEL1_msk )
fignum = perform_noise_test ( info, fignum )

# enable the 2nd rx path
info = 'en_2nd_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX2_H_msk | nmrObj.RX2_L_msk )
fignum = perform_noise_test ( info, fignum )

# enable the 1st rx path
info = 'en_1st_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk )
fignum = perform_noise_test ( info, fignum )

# enable the pamp tuning
info = 'en_pamp_tuning'
nmrObj.setPreampTuning( conf.vbias, conf.vvarac )  # enable the preamp tuning
fignum = perform_noise_test ( info, fignum )

# enable the pamp input
info = 'en_pamp_input'
nmrObj.assertControlSignal ( nmrObj.PAMP_IN_SEL2_msk )
fignum = perform_noise_test ( info, fignum )

# enable the matching network
info = 'en_mtch_ntwrk'
nmrObj.setMatchingNetwork( conf.cpar, conf.cser )
nmrObj.setMatchingNetwork( conf.cpar, conf.cser )
fignum = perform_noise_test ( info, fignum )

# enable the tx power
info = 'en_tx_power'
nmrObj.assertControlSignal ( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk )
fignum = perform_noise_test ( info, fignum )

# disable the matching network
info = 'dis_mtch_ntwrk'
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
fignum = perform_noise_test ( info, fignum )

# disable the preamp input
info = 'dis_pamp_input'
nmrObj.deassertControlSignal ( nmrObj.PAMP_IN_SEL2_msk )
fignum = perform_noise_test ( info, fignum )

# disable the pamp tuning
info = 'dis_pamp_tuning'
nmrObj.setPreampTuning( 0, 0 )  # enable the preamp tuning
fignum = perform_noise_test ( info, fignum )

# turn off everything
nmrObj.deassertControlSignal( 
    nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk |
    nmrObj.PSU_5V_TX_N_EN_msk |
    nmrObj.PSU_5V_ADC_EN_msk |
    nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk
    )
nmrObj.deassertControlSignal( 
    nmrObj.RX_FL_msk | nmrObj.RX_FH_msk |
    nmrObj.RX_SEL1_msk | nmrObj.RX_SEL2_msk |
    nmrObj.RX2_L_msk | nmrObj.RX2_H_msk |
    nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk |
    nmrObj.PAMP_IN_SEL1_msk | nmrObj.PAMP_IN_SEL2_msk |
    nmrObj.RX3_L_msk | nmrObj.RX3_H_msk |
    nmrObj.RX1_2L_msk | nmrObj.RX1_2H_msk
    )
f.close()  # close text file
