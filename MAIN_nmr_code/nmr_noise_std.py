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
from nmr_std_function.nmr_functions import compute_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
import matplotlib.pyplot as plt
from scipy import signal
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
samp_freq = 16  # sampling frequency
samples = 100000  # number of points
min_freq = 0.200
max_freq = 12.5


def perform_noise_test ( plotname ):
    en = True
    if ( en ):
        # sample noise
        nmrObj.noise( samp_freq, samples )

        # process the data
        meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
        # compute_noise(min_freq, max_freq, data_folder, meas_folder[0], plotname, 0)  # dummy scan
        nstd, nmean = compute_noise( min_freq, max_freq, data_folder, meas_folder[0], plotname, en_fig )  # real scan
    else:  # dummy scan
        nstd = 0
        nmean = 0
    return nstd, nmean


# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

# get current time
now = datetime.now()
datename = now.strftime( "%y%d%m_%H%M%S_" )

# turn off everything at the beginning
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

f = open( datename + 'noise_std.txt', "w" )  # open text file
fignum = 0  # variable to store figure number

# enable the minimum power supply necessary for the ADC
fignum = fignum + 1
info = 'en_adc_power'
nmrObj.assertControlSignal ( nmrObj.PSU_5V_ADC_EN_msk )
# nstd, nmean = perform_noise_test (str(fignum).zfill(2) + '_' + info + '.png')
# f.write("std: %08.3f\tmean: %08.3f \t-> %s\n" % (nstd, nmean, info))

# enable the first RX path power supply
fignum = fignum + 1
info = 'en_rx_power'
nmrObj.assertControlSignal ( nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )
# nstd, nmean = perform_noise_test (str(fignum).zfill(2) + '_' + info + '.png')
# f.write("std: %08.3f\tmean: %08.3f \t-> %s\n" % (nstd, nmean, info))

# enable the final rx path
fignum = fignum + 1
info = 'en_final_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the rx selector
fignum = fignum + 1
info = 'en_rx_sel_path'
nmrObj.assertControlSignal ( nmrObj.RX_SEL1_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the 2nd rx path
fignum = fignum + 1
info = 'en_2nd_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX2_L_msk | nmrObj.RX2_H_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the 1st rx path
fignum = fignum + 1
info = 'en_1st_rx_path'
nmrObj.assertControlSignal ( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the pamp tuning
fignum = fignum + 1
info = 'en_pamp_tuning'
nmrObj.setPreampTuning( -2.7, 0.3 )  # enable the preamp tuning
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the pamp input
fignum = fignum + 1
info = 'en_pamp_input'
nmrObj.assertControlSignal ( nmrObj.PAMP_IN_SEL2_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the matching network
fignum = fignum + 1
info = 'en_mtch_ntwrk'
nmrObj.setMatchingNetwork( 2381, 440 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 2381, 440 )  # 4.25 MHz AFE
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# enable the tx power
fignum = fignum + 1
info = 'en_tx_power'
nmrObj.assertControlSignal ( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# disable the matching network
fignum = fignum + 1
info = 'dis_mtch_ntwrk'
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 0, 0 )  # 4.25 MHz AFE
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# disable the preamp input
fignum = fignum + 1
info = 'dis_pamp_input'
nmrObj.deassertControlSignal ( nmrObj.PAMP_IN_SEL2_msk )
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

# disable the pamp tuning
fignum = fignum + 1
info = 'dis_pamp_tuning'
nmrObj.setPreampTuning( 0, 0 )  # enable the preamp tuning
nstd, nmean = perform_noise_test ( str( fignum ).zfill( 2 ) + '_' + info + '.png' )
f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

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
