'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate, compute_wobble_sync, compute_wobble_async, compute_wobble_fft_sync
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


def runExpt( nmrObj, extSet, cparVal, cserVal, sta_freq, sto_freq, spac_freq, samp_freq , fftpts, fftcmd, ftvalsub, S11mV_ref, useRef , en_fig ):
    # useRef: use the pregenerated S11mV_ref as a reference to compute
    # reflection. If this option is 0, then the compute_wobble will instead
    # generated S11 in mV format instead of dB format

    fig_num = 1

    # change matching network values (twice because sometimes it doesnt' work
    # once due to transient
    if ( not extSet ):  # if extSet is used, matching network should be programmed from external source (e.g. C executable), otherwise set the value from here
        nmrObj.setMatchingNetwork( cparVal, cserVal )
        # nmrObj.setMatchingNetwork( cparVal, cserVal )

    timeObj = time_meas( True )
    timeObj.setTimeSta()
    # do measurement
    nmrObj.wobble_sync( sta_freq, sto_freq, spac_freq , fftpts, fftcmd, ftvalsub )
    # nmrObj.wobble_async( sta_freq, sto_freq, spac_freq, samp_freq )
    timeObj.setTimeSto()
    timeObj.reportTimeRel( "wobble_sync" )

    # disable all to save power
    # nmrObj.deassertAll()

    timeObj.setTimeSta()
    # compute the generated data
    if  nmrObj.en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )
    meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
    if  nmrObj.en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, nmrObj.server_data_folder, "rm -rf " + meas_folder[0] )  # delete the file in the server
    timeObj.setTimeSto()
    timeObj.reportTimeRel( "transfer_data" )

    timeObj.setTimeSta()
    S11dB, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, freq0, Z11_imag0 = compute_wobble_fft_sync( nmrObj, nmrObj.data_folder, meas_folder[0], -10, S11mV_ref, useRef, en_fig, fig_num )
    # S11dB, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, freq0, Z11_imag0 = compute_wobble_sync( nmrObj, nmrObj.data_folder, meas_folder[0], -10, S11mV_ref, useRef, en_fig, fig_num )
    # S11dB, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = compute_wobble_async( nmrObj, nmrObj.data_folder, meas_folder[0], -10, S11mV_ref, useRef, en_fig, fig_num )

    print( '\t\tfmin={:0.3f} fmax={:0.3f} bw={:0.3f} minS11={:0.2f} minS11_freq={:0.3f} cparVal={:d} cserVal={:d}'.format( 
        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparVal, cserVal ) )

    timeObj.setTimeSto()
    timeObj.reportTimeRel( "data processing" )

    return S11dB, minS11_freq


def exit( nmrObj ):
    nmrObj.deassertAll()
    nmrObj.exit()

'''
client_data_folder = "D:\\TEMP"
en_fig = 1
# measurement properties
sta_freq = 1.8
sto_freq = 2.2
spac_freq = 0.001
samp_freq = 25  # not used when using wobble_sync. Will be used when using wobble_async
fftpts = 1024
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
extSet = False  # use external executable to set the matching network Cpar and Cser
useRef = True  # use reference to eliminate background

nmrObj = init ( client_data_folder )

print( 'Generate reference.' )
S11mV_ref, minS11Freq_ref = runExpt( nmrObj, False, 0, 0, sta_freq, sto_freq, spac_freq, samp_freq , fftpts, fftcmd, fftvalsub, 0, 0 , en_fig )  # background is computed with no capacitor connected -> max reflection

while True:
    runExpt( nmrObj, extSet, 320, 177, sta_freq, sto_freq, spac_freq, samp_freq , fftpts, fftcmd, fftvalsub, S11mV_ref, useRef , en_fig )

exit( nmrObj )
'''
