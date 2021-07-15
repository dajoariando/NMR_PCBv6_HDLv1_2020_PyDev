'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import time

a = time.time()

import os
from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col
from nmr_std_function.nmr_functions import compute_iterate, compute_stats, compute_in_bw_noise
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import matplotlib.pyplot as plt
from scipy import signal
import pydevd
from datetime import datetime
import meas_configs.wmp_pcb1 as conf

b = time.time()

# variables
data_folder = "/root/NMR_DATA"
en_fig = 0
en_remote_dbg = 0
compute_in_PC = 1 # do not compute in the SoC, but run the experiment once and compute in PC. Otherwise run the experiment continuously

# nmr object declaration
nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg )

# measurement settings
samp_freq = 25  # sampling frequency
samples = 40000  # number of points
min_freq = 1.5 # in MHz
max_freq = 2.0 # in MHz

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )
nmrObj.deassertControlSignal( 
    nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk )

nmrObj.setPreampTuning(conf.vbias, conf.vvarac)  # try -2.7, -1.8 if fail
# nmrObj.setMatchingNetwork( conf.cpar, conf.cser)  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 0,0)

nmrObj.assertControlSignal( 
    nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.RX_SEL1_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.PAMP_IN_SEL2_msk )
# nmrObj.deassertControlSignal( nmrObj.RX_FH_msk | nmrObj.RX2_L_msk | nmrObj.RX_FH_msk )
nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )


while True:

    # time.sleep(0.5)
    
    nmrObj.noise( samp_freq, samples )
    
    if compute_in_PC:
        
        c = time.time()
        print("loading lib time: %f" % (b-a))
        print("processing time: %f" % (c-b))
        quit()
    
    else:
        # process the data
        meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
        # compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )
        compute_in_bw_noise( conf.meas_bw_kHz, conf.Df_MHz, min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setPreampTuning( 0, 0 )
