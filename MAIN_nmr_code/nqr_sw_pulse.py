'''
Created on Mar 30, 2018

@author: David Ariando
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
import numpy as np
from datetime import datetime

# variables
data_folder = "/root/NMR_DATA"
en_scan_fig = 0
en_fig = 1
en_remote_dbg = 0
fig_num = 100
direct_read = 0  # perform direct read from SDRAM. use with caution above!

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg )

# system setup
# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
# nmrObj.turnOnPower()
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setPreampTuning( -2.1, -2.4 )  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork( 1890, 298 )  # 4.25 MHz AFE
nmrObj.setMatchingNetwork( 1890, 298 )

nmrObj.assertControlSignal( 
    nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )

# cpmg settings
cpmg_freq = 4.642 + ( -9 ) * 1e-3
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = 200
scan_spacing_us = 1
samples_per_echo = 512  # number of points
echoes_per_scan = 1024  # number of echos
init_adc_delay_compensation = 6  # acquisition shift microseconds
number_of_iteration = 32  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0
tx_sd_msk = 1  # 1 to shutdown tx opamp during reception, or 0 to keep it powered up during reception
en_dconv = 1  # enable downconversion in the fpga
dconv_fact = 4  # downconversion factor. minimum of 4.

# sweep settings
pulse_us_sta = 5  # in microsecond
pulse_us_sto = 20  # in microsecond
pulse_us_ste = 15  # number of steps
pulse_us_sw = np.linspace( pulse_us_sta, pulse_us_sto, pulse_us_ste )

a_integ_table = np.zeros( pulse_us_ste )
for i in range( 0, pulse_us_ste ):
    print( '----------------------------------' )
    print( 'plength = ' + str( pulse_us_sw[i] ) + ' us' )

    pulse1_us = pulse_us_sw[i]  # pulse pi/2 length
    pulse2_us = pulse_us_sw[i]  # pulse pi length
    nmrObj.cpmgSequence( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration,
                        ph_cycl_en, pulse180_t1_int, delay180_t1_int , tx_sd_msk, en_dconv, dconv_fact )
    datain = []  # set datain to 0 because the data will be read from file instead
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_scan_fig )
    a_integ_table[i] = a_integ
    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )
        fig.clf()
        ax = fig.add_subplot( 1, 1, 1 )
        line1, = ax.plot( pulse_us_sw[0:i + 1], a_integ_table[0:i + 1], 'b-o' )
        # ax.set_ylim(-50, 0)
        # ax.set_xlabel('Frequency [MHz]')
        # ax.set_ylabel('S11 [dB]')
        # ax.set_title("Reflection Measurement (S11) Parameter")
        ax.grid()
        fig.canvas.draw()
        # fig.canvas.flush_events()

# turn off system
nmrObj.deassertControlSignal( 
    nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setPreampTuning( 0, 0 )
nmrObj.deassertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                             nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )

now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
fig.savefig( datename + '_pulsesw.pdf' )

pass
pass
