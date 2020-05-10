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
import pydevd
from datetime import datetime
import numpy as np
import shutil

# variables
data_folder = "/root/NMR_DATA"
en_fig = 1
en_remote_dbg = 0

# nmr object declaration
nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg )

# general measurement settings
samp_freq = 25  # sampling frequency
samples = 100000  # number of points
min_freq = 0.200
max_freq = 12.5

# get current time
now = datetime.now()
datename = now.strftime( "%y%m%d_%H%M%S_" )
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
    nstd, nmean = compute_stats ( min_freq, max_freq, data_folder, meas_folder[0], plotname, en_fig )  # real scan
    f.write( "std: %08.3f\tmean: %08.3f \t-> %s\n" % ( nstd, nmean, info ) )

    shutil.move ( data_folder + '/' + meas_folder[0], swfolder + '/' + info )  # move the data folder
    shutil.move ( swfolder + '/' + info + '/' + plotname, swfolder + '/' + plotname )  # move the data folder

    return fignum


# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

# turn off everything at the beginning
nmrObj.deassertAll()

f = open( datename + 'noise_std.txt', "w" )  # open text file
fignum = 0  # variable to store figure number

nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )
nmrObj.setPreampTuning( -2.7, -0.4 )  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork( 2381, 439 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 2381, 439 )
nmrObj.assertControlSignal( nmrObj.RX_SEL1_msk | nmrObj.PAMP_IN_SEL2_msk )

info = 'RXGAIN_01_01_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_04_01_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_10_01_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_01_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_04_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_10_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_01_01'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_01_04'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FH_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_01_01_10'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_04_04_04'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX2_H_msk | nmrObj.RX_FH_msk )
fignum = perform_noise_test ( info, fignum )

info = 'RXGAIN_10_10_10'
nmrObj.deassertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk )
fignum = perform_noise_test ( info, fignum )

# turn off everything
nmrObj.deassertAll()
f.close()  # close text file
