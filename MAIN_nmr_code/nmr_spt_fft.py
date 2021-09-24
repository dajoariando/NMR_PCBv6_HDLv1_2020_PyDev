'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_spfft
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir
from nmr_std_function.time_func import time_meas

# load configuration
# from nmr_std_function.sys_configs import WMP_old_coil_1p7 as conf


def init ( client_data_folder ):

    # enable remote debugging with SoC computing
    en_remote_dbg = 0

    # remote computing configuration. See the NMR class to see details of use
    en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

    # nmr object declaration
    nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

    # system setup
    nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
    nmrObj.deassertAll()

    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )

    # enable power and signal path
    nmrObj.assertControlSignal( 
            nmrObj.RX1_2L_msk | nmrObj.RX_SEL2_msk | nmrObj.RX_FL_msk )

    # nmrObj.setPreampTuning( conf.vbias, conf.vvarac )  # try -2.7, -1.8 if fail

    return nmrObj


def analyze( nmrObj, extSet, cparVal, cserVal, freq , fftpts, fftcmd, ftvalsub, en_fig ):

    fig_num = 1

    if ( not extSet ):  # if extSet is used, matching network should be programmed from external source (e.g. C executable), otherwise set the value from here
        nmrObj.setMatchingNetwork( cparVal, cserVal )
        # nmrObj.setMatchingNetwork( cparVal, cserVal )

    # do measurement
    nmrObj.spt_fft( freq , fftpts, fftcmd, ftvalsub )

    # compute the generated data
    if  nmrObj.en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )
    meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
    if  nmrObj.en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, nmrObj.server_data_folder, "rm -rf " + meas_folder[0] )  # delete the file in the server
    S11_cmplx = compute_spfft( nmrObj, nmrObj.data_folder, meas_folder[0], en_fig, fig_num )

    return S11_cmplx


def exit( nmrObj ):
    nmrObj.deassertAll()
    nmrObj.exit()

'''
# measurement properties
client_data_folder = "D:\\TEMP"
en_fig = 1
freq = 1.8
freqSamp = 25  # not used when using wobble_sync. Will be used when using wobble_async
fftpts = 1024
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
extSet = False  # use external executable to set the matching network Cpar and Cser
useRef = True  # use reference to eliminate background

nmrObj = init ( client_data_folder )

print( 'Generate reference.' )
S11, S11_ph = analyze( nmrObj, False, 166, 175, freq, fftpts, fftcmd, fftvalsub , en_fig )  # background is computed with no capacitor connected -> max reflection

exit( nmrObj )
'''
