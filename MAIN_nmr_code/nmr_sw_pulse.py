'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time
import matplotlib.pyplot as plt
from scipy import signal
import pydevd
import numpy as np
from datetime import datetime

from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# variables
server_data_folder = "/root/NMR_DATA"
client_data_folder = "D:\\NMR_DATA"

en_scan_fig = 0
en_fig = 1
en_remote_dbg = 0
fig_num = 100
direct_read = 0  # perform direct read from SDRAM. use with caution above!
# remote computing configuration. See the NMR class to see details of use
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

if en_remote_computing:
    data_folder = client_data_folder
    en_remote_dbg = 0  # force remote debugging to be disabled
else:
    data_folder = server_data_folder

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

# load configuration
from nmr_std_function.sys_configs import UF_black_holder_brown_coil_PCB02 as conf

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
# nmrObj.turnOnPower()
nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setPreampTuning( conf.vbias, conf.vvarac )
nmrObj.setMatchingNetwork( conf.cpar, conf.cser )

nmrObj.assertControlSignal( 
        nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX_FH_msk ) # setting for UF
# nmrObj.deassertControlSignal( nmrObj.RX_FL_msk ) # setting for WMP

# cpmg settings
cpmg_freq = conf.Df_MHz
pulse1_dtcl = 0.5  # useless with current code
pulse2_dtcl = 0.5  # useless with current code
echo_spacing_us = conf.echo_spacing_us  # 200
scan_spacing_us = conf.scan_spacing_us
samples_per_echo = conf.samples_per_echo  # 3072
echoes_per_scan = conf.echoes_per_scan  # 20
init_adc_delay_compensation = conf.init_adc_delay_compensation  # acquisition shift microseconds.
number_of_iteration = 16  # number of averaging
ph_cycl_en = 1
pulse180_t1_int = 0
delay180_t1_int = 0
tx_sd_msk = 1  # 1 to shutdown tx opamp during reception, or 0 to keep it powered up during reception
en_dconv = 0  # enable downconversion in the fpga
dconv_fact = 4  # downconversion factor. minimum of 4.
echo_skip = 1  # echo skip factor. set to 1 for the ADC to capture all echoes
dconv_lpf_ord = conf.dconv_lpf_ord  # downconversion order
dconv_lpf_cutoff_kHz = conf.meas_bw_kHz  # downconversion lpf cutoff


# sweep settings
pulse_us_sta = 5.5  # in microsecond
pulse_us_sto = 6.5  # in microsecond
pulse_us_ste = (6-5)*10+1  # number of steps
pulse_us_sw = np.linspace( pulse_us_sta, pulse_us_sto, pulse_us_ste )

a_integ_table = np.zeros( pulse_us_ste )
for i in range( 0, pulse_us_ste ):
    print( '----------------------------------' )
    print( 'plength = ' + str( pulse_us_sw[i] ) + ' us' )

    pulse1_us = 2.8 # pulse pi/2 length
    pulse2_us = pulse_us_sw[i] # pulse pi length
    nmrObj.cpmgSequence( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration,
                        ph_cycl_en, pulse180_t1_int, delay180_t1_int , tx_sd_msk, en_dconv, dconv_fact, echo_skip )

    datain = []  # set datain to 0 because the data will be read from file instead

    # compute the generated data
    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )
    meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, "rm -rf " + meas_folder[0], nmrObj.server_data_folder  )  # delete the file in the server
    ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( 
        nmrObj, nmrObj.data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_scan_fig, dconv_lpf_ord, dconv_lpf_cutoff_kHz )
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
        fig.canvas.flush_events()

# turn off system
nmrObj.deassertControlSignal( 
    nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setPreampTuning( 0, 0 )
nmrObj.deassertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                             nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )

now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
if  en_remote_computing:
    fig.savefig( data_folder + "\\" + datename + '_pulsesw.pdf' )
else:
    fig.savefig( data_folder + "/" + datename + '_pulsesw.pdf' )

pass
pass
