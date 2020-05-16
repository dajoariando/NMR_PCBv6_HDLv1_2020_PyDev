'''
Created on Mar 30, 2018

@author: David Ariando

standard noise measurement of the AFE.
the standard samples is 1 million and it'll take sometime.

'''

#!/usr/bin/python

import os
import time

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_stats
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal
import shutil
import pydevd
from datetime import datetime
import numpy as np

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 0

# nmr object declaration
nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg )

# general measurement settings
samp_freq = 25  # sampling frequency
samples = 10000  # number of points
min_freq = 0.200
max_freq = 12.5

# get current time
now = datetime.now()
datename = now.strftime( "%y_%m_%d_%H_%M_%S" )
swfolder = data_folder + '/' + datename + '_noise_with_RXGain_sw'

fignum = 0


def perform_noise_test ( plotname , fignum ):

    fignum = fignum + 1

    info = str( fignum ).zfill( 2 ) + '___' + plotname
    plotname = info + '.png'

    # sample noise
    nmrObj.noise( samp_freq, samples )

    # process the data
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    nstd, nmean = compute_stats( min_freq, max_freq, data_folder, meas_folder[0], plotname, en_fig )  # real scan
    f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

    shutil.move ( data_folder + '/' + meas_folder[0], swfolder + '/' + info )  # move the data folder
    shutil.move ( swfolder + '/' + info + '/' + plotname, swfolder + '/' + plotname )  # move the data folder

    return fignum


# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

# get current time
now = datetime.now()
datename = now.strftime( "%y%m%d_%H%M%S_" )

# turn off everything at the beginning
nmrObj.deassertAll()

f = open( datename + 'noise_std.txt', "w" )  # open text file
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
nmrObj.assertControlSignal ( nmrObj.RX2_H_msk )
fignum = perform_noise_test ( info, fignum )

# enable the 1st rx path
info = 'en_1st_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX1_1H_msk )
fignum = perform_noise_test ( info, fignum )

# enable the pamp tuning
info = 'en_pamp_tuning'
nmrObj.setPreampTuning( -2.7, -0.4 )  # enable the preamp tuning
fignum = perform_noise_test ( info, fignum )

# enable the pamp input
info = 'en_pamp_input'
nmrObj.assertControlSignal ( nmrObj.PAMP_IN_SEL2_msk )
fignum = perform_noise_test ( info, fignum )

# enable the matching network
info = 'en_mtch_ntwrk'
nmrObj.setMatchingNetwork( 2381, 440 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 2381, 440 )  # 4.25 MHz AFE
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
