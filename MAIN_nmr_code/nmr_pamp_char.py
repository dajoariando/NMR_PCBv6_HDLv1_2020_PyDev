'''
Created on May 04, 2020

This module characterizes the preamp gain and show the gain over frequency

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate, compute_gain_async, compute_gain_sync, compute_gain_fft_sync
from nmr_std_function.data_parser import parse_simple_info, find_Cpar_Cser_from_table, find_Vbias_Vvarac_from_table
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir
from nmr_std_function.time_func import time_meas

# load the config
from nmr_std_function.sys_configs import WMP_old_coil_1p7 as conf


def init( client_data_folder ):

    # enable remote debugging with SoC computing
    en_remote_dbg = 0

    # remote computing configuration. See the NMR class to see details of use
    en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

    # instantiate nmr object
    nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

    # system setup
    nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
    nmrObj.deassertAll()

    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                                   nmrObj.PSU_5V_ANA_N_EN_msk )

    nmrObj.assertControlSignal( 
                nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
    nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX2_H_msk | nmrObj.RX_FH_msk )

    # nmrObj.setPreampTuning( conf.vbias, conf.vvarac )

    nmrObj.setMatchingNetwork( 0, 0 )

    return nmrObj


def analyze( nmrObj , Vbias, Vvarac, freqSta, freqSto , freqSpa, freqSamp, fftpts, fftcmd, fftvalsub, continuous, en_fig ):

    fig_num = 1

    while True:

        # set the preamp tuning
        nmrObj.setPreampTuning( Vbias, Vvarac )

        # nmrObj.pamp_char_async ( freqSta, freqSto, freqSpa, freqSamp )
        nmrObj.pamp_char_sync ( freqSta, freqSto, freqSpa, fftpts, fftcmd, fftvalsub )

        if  nmrObj.en_remote_computing:  # copy remote files to local directory
            cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )

        meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
        # meas_folder[0] = "nmr_wobb_2018_06_25_12_44_48"

        if  nmrObj.en_remote_computing:  # copy remote folder to local directory
            cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
            exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, "rm -rf " + meas_folder[0], nmrObj.server_data_folder )  # delete the file in the server

        # maxS21, maxS21_freq, _ = compute_gain_async( nmrObj, data_folder, meas_folder[0], en_fig, fig_num )
        # maxS21, maxS21_freq, _ = compute_gain_sync( nmrObj, data_folder, meas_folder[0], en_fig, fig_num )
        maxS21, maxS21_freq, S21mV = compute_gain_fft_sync( nmrObj, nmrObj.data_folder, meas_folder[0], en_fig, fig_num )
        print( "maxS21_fft=%0.2fdBmV maxS21_freq=%0.2fMHz Vbias=%0.2fV Vvarac=%0.2fV" % ( 
             maxS21, maxS21_freq, Vbias, Vvarac ) )

        if ( not continuous ):
            break;

    return maxS21, maxS21_freq, S21mV


def exit( nmrObj ):
    nmrObj.deassertAll()
    nmrObj.exit()

'''
# comment the lines below when using nmr_pamp_char as a function in outside script
# measurement properties
client_data_folder = "D:\\TEMP"
en_fig = 1
tuning_freq = 1.7
freqSta = 1.5
freqSto = 3.0
freqSpa = 0.001
freqSamp = 25  # not being used for synchronized sampling. It's value will be the running freq * 4
fftpts = 1024
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
continuous = False

nmrObj = init( client_data_folder )

# find configuration
Vbias, Vvarac = find_Vbias_Vvarac_from_table ( nmrObj.client_path , tuning_freq, nmrObj.S21_table )

analyze ( nmrObj, Vbias, Vvarac, freqSta, freqSto, freqSpa, freqSamp, fftpts, fftcmd, fftvalsub, continuous, en_fig )
exit( nmrObj )
'''
