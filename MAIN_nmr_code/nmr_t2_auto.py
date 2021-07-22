'''
Created on Mar 30, 2018

@author: David Ariando

in progress:
*** direct_read, a setting to read data directly from SDRAM using Python is implemented using the same CPMG_iterate C-function (with the loop handled by Python instead of C).
It is a slower operation than using C to write to SDCard directly. It might be due to every iteration will
generate acqu.par separately in separate folder. Or MAYBE [less likely] writing to SDRAM via DMA is slower than writing directly
to a text file. Or MAYBE because every iteration runs CPMG_iterate with 1-iteration, the C program is called
number_of_iteration times. Also the computation of SNR/echo/scan is wrong in compute_iterate due to having
only 1 as a number_of_iteration in acqu.par. It seems to be no point of using Python if C still needs to be called.
So many problems yet not having better speed. It might be better to write everything in Python instead.

Cheng 07/2020 Option to change matching network and preamp values automatically
'''

#!/usr/bin/python

import time

import pydevd
from scipy import signal
import os

import matplotlib.pyplot as plt
from nmr_std_function.data_parser import parse_simple_info, parse_csv_float2col, find_Cpar_Cser_from_table, find_Vbias_Vvarac_from_table
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir


def nmr_t2_auto ( cpmg_freq, pulse1_us, pulse2_us, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, dconv_lpf_ord, dconv_lpf_cutoff_Hz, client_data_folder ):
    meas_time = 1  # measure time
    if ( meas_time ):
        start_time = time.time()

    if ( meas_time ):
        elapsed_time = time.time() - start_time
        print( "load library time: %.3f" % ( elapsed_time ) )
        start_time = time.time()

    # variables
    server_data_folder = "/root/NMR_DATA"
    # client_data_folder = "D:\\TEMP"
    S11_table = "genS11Table.txt"  # filename for S11 tables
    S21_table = "genS21Table.txt"
    en_fig = 0  # enable figure
    en_remote_dbg = 0  # enable remote debugging. Enable debug server first!
    direct_read = 0  # perform direct read from SDRAM. use with caution above!
    process_data = 1  # process data within the SoC
    # remote computing configuration. See the NMR class to see details of use
    en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data
    if en_remote_computing:
        data_folder = client_data_folder
        en_remote_dbg = 0  # force remote debugging to be disabled
    else:
        data_folder = server_data_folder

    # cpmg settings. Many are now configurable outside the function
    # cpmg_freq = 1.67
    # pulse1_us = 15  # 75 for Cheng's coil. pulse pi/2 length.
    # pulse2_us = 1.6 * pulse1_us  # pulse pi length
    pulse1_dtcl = 0.5  # useless with current code
    pulse2_dtcl = 0.5  # useless with current code
    # echo_spacing_us = 500  # 200
    # scan_spacing_us = 100000
    # samples_per_echo = 1024  # 3072
    # echoes_per_scan = 128  # 20
    # put to 10 for broadband board and 6 for tunable board
    # init_adc_delay_compensation = 34  # acquisition shift microseconds.
    # number_of_iteration = 10  # number of averaging
    # ph_cycl_en = 1
    pulse180_t1_int = 0
    delay180_t1_int = 0
    tx_sd_msk = 1  # 1 to shutdown tx opamp during reception, or 0 to keep it powered up during reception
    en_dconv = 0  # enable downconversion in the fpga
    dconv_fact = 4  # downconversion factor. minimum of 4.
    echo_skip = 1  # echo skip factor. set to 1 for the ADC to capture all echoes
    # dconv_lpf_ord = 2  # downconversion order
    # dconv_lpf_cutoff_Hz = 30e3  # downconversion lpf cutoff

    # instantiate nmr object
    nmrObj = tunable_nmr_system_2018( server_data_folder, en_remote_dbg, en_remote_computing )

    # system setup
    nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting. Also fix the
    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                               nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                               nmrObj.PSU_5V_ANA_N_EN_msk )
    # nmrObj.deassertControlSignal(
    #    nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk)

    Vbias, Vvarac = find_Vbias_Vvarac_from_table ( nmrObj.client_path , cpmg_freq, S21_table )
    nmrObj.setPreampTuning( Vbias, Vvarac )
    Cpar, Cser = find_Cpar_Cser_from_table ( nmrObj.client_path , cpmg_freq, S11_table )
    nmrObj.setMatchingNetwork( Cpar, Cser )
    nmrObj.setMatchingNetwork( Cpar, Cser )

    nmrObj.assertControlSignal( 
            nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
    # nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX_FH_msk )
    nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )

    if ( meas_time ):
        elapsed_time = time.time() - start_time
        print( "set parameter time: %.3f" % ( elapsed_time ) )
        start_time = time.time()

    if ( direct_read ):
        datain = nmrObj.cpmgSequenceDirectRead( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                                               echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en,
                                               pulse180_t1_int, delay180_t1_int, tx_sd_msk )
    else:
        nmrObj.cpmgSequence( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                            echoes_per_scan, init_adc_delay_compensation, number_of_iteration,
                            ph_cycl_en, pulse180_t1_int, delay180_t1_int, tx_sd_msk, en_dconv, dconv_fact, echo_skip )
        datain = []  # set datain to 0 because the data will be read from file instead

    if ( meas_time ):
        elapsed_time = time.time() - start_time
        print( "cpmgSequence acquisition time: %.3f" % ( elapsed_time ) )
        start_time = time.time()

    nmrObj.deassertControlSignal( 
            nmrObj.RX1_1H_msk | nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )

    nmrObj.setMatchingNetwork( 0, 0 )
    nmrObj.setPreampTuning( 0, 0 )
    nmrObj.deassertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                 nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )

    if ( process_data ):

        # compute the generated data
        if  en_remote_computing:  # copy remote files to local directory
            cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )
        meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

        if  en_remote_computing:  # copy remote folder to local directory
            cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )
            exec_rmt_ssh_cmd_in_datadir( nmrObj, "rm -rf " + meas_folder[0] )  # delete the file in the server
        ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace ) = compute_iterate( nmrObj,
            data_folder, meas_folder[0], 0, 0, 0, direct_read, datain, en_fig , dconv_lpf_ord, dconv_lpf_cutoff_Hz )

    if ( meas_time ):
        elapsed_time = time.time() - start_time
        print( "data processing time: %.3f" % ( elapsed_time ) )
        start_time = time.time()

'''
# cpmg settings
cpmg_freq = 1.67
pulse1_us = 15  # 75 for Cheng's coil. pulse pi/2 length.
pulse2_us = 1.6 * pulse1_us  # pulse pi length
echo_spacing_us = 500  # 200
scan_spacing_us = 100000
samples_per_echo = 1024  # 3072
echoes_per_scan = 128  # 20
init_adc_delay_compensation = 34  # acquisition shift microseconds.
number_of_iteration = 100  # number of averaging
ph_cycl_en = 1
dconv_lpf_ord = 2  # downconversion order
dconv_lpf_cutoff_Hz = 30e3  # downconversion lpf cutoff
client_data_folder = "D:\\TEMP"
nmr_t2_auto ( cpmg_freq, pulse1_us, pulse2_us, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, dconv_lpf_ord, dconv_lpf_cutoff_Hz, client_data_folder )
'''
