'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate, compute_wobble_sync
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# load configuration
from nmr_std_function.sys_configs import WMP_old_coil_1p7 as conf

# variables
server_data_folder = "/root/NMR_DATA"
client_data_folder = "D:\\TEMP"
en_remote_dbg = 0
fig_num = 1
en_fig = 1
meas_time = 1

# measurement properties
sta_freq = 1.5
sto_freq = 2.0
spac_freq = 0.004
samp_freq = 25

# remote computing configuration. See the NMR class to see details of use
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

if en_remote_computing:
    data_folder = client_data_folder
    en_remote_dbg = 0  # force remote debugging to be disabled
else:
    data_folder = server_data_folder

# nmr object declaration
nmrObj = tunable_nmr_system_2018( server_data_folder, en_remote_dbg, en_remote_computing )

# work_dir = os.getcwd()
# os.chdir( data_parent_folder )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

nmrObj.deassertAll()

nmrObj.assertControlSignal( nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setPreampTuning( conf.vbias, conf.vvarac )  # try -2.7, -1.8 if fail


def runExpt( cparVal, cserVal, S11mV_ref, useRef ):
    # useRef: use the pregenerated S11mV_ref as a reference to compute
    # reflection. If this option is 0, then the compute_wobble will instead
    # generated S11 in mV format instead of dB format

    if meas_time:
        start_time = time.time()

    # enable power and signal path
    nmrObj.assertControlSignal( 
        nmrObj.RX1_2L_msk | nmrObj.RX_SEL2_msk | nmrObj.RX_FL_msk )
    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                               nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )

    # change matching network values (twice because sometimes it doesnt' work
    # once due to transient
    nmrObj.setMatchingNetwork( cparVal, cserVal )
    nmrObj.setMatchingNetwork( cparVal, cserVal )

    # do measurement
    nmrObj.wobble( sta_freq, sto_freq, spac_freq, samp_freq )

    # disable all to save power
    nmrObj.deassertAll()

    if meas_time:
        elapsed_time = time.time() - start_time
        start_time = time.time()  # reset the start time
        print( "### time elapsed for running wobble exec: %.3f" % ( elapsed_time ) )

    # compute the generated data
    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )

    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj, "rm -rf " + meas_folder[0] )  # delete the file in the server

    S11dB, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = compute_wobble_sync( 
        nmrObj, data_folder, meas_folder[0], -10, S11mV_ref, useRef, en_fig, fig_num )
    print( '\t\tfmin={:0.3f} fmax={:0.3f} bw={:0.3f} minS11={:0.2f} minS11_freq={:0.3f} cparVal={:d} cserVal={:d}'.format( 
        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparVal, cserVal ) )

    if meas_time:
        elapsed_time = time.time() - start_time
        print( "### time elapsed for compute_wobble: %.3f" % ( elapsed_time ) )

    return S11dB, minS11_freq


# find reference
print( 'Generate reference.' )
# background is computed with no capacitor connected -> max reflection
S11mV_ref, minS11Freq_ref = runExpt( 0, 0, 0, 0 )

while True:
    runExpt( conf.cpar, conf.cser, S11mV_ref, 1 )
