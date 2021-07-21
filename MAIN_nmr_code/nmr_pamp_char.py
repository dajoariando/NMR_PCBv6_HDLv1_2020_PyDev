'''
Created on May 04, 2020

This module characterizes the preamp gain and show the gain over frequency

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate, compute_gain
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# load the config
from nmr_std_function.sys_configs import WMP_old_coil_1p7 as conf

# variables
server_data_folder = "/root/NMR_DATA"
client_data_folder = "D:\\TEMP"
# data_folder = "/root/NMR_DATA"
en_remote_dbg = 0
fig_num = 1
en_fig = 1

# remote computing configuration. See the NMR class to see details of use
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

if en_remote_computing:
    data_folder = client_data_folder
    en_remote_dbg = 0  # force remote debugging to be disabled
else:
    data_folder = server_data_folder

# measurement properties
sta_freq = 1.5
sto_freq = 2.2
spac_freq = 0.01
samp_freq = 25

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( server_data_folder, en_remote_dbg, en_remote_computing )

# work_dir = os.getcwd()
# os.chdir( data_folder )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

nmrObj.deassertAll()

nmrObj.assertControlSignal( nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setPreampTuning( conf.vbias, conf.vvarac )  # try -2.7, -1.8 if fail
nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setMatchingNetwork( 0, 0 )

while True:
    nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk |
                               nmrObj.RX_FL_msk )
    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                               nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                               nmrObj.PSU_5V_ANA_N_EN_msk )
    # time.sleep( 0.1 )

    nmrObj.pamp_char ( sta_freq, sto_freq, spac_freq, samp_freq )

    nmrObj.deassertAll()

    if  en_remote_computing:  # copy remote files to local directory
        cp_rmt_file( nmrObj, server_data_folder, client_data_folder, "current_folder.txt" )

    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    # meas_folder[0] = "nmr_wobb_2018_06_25_12_44_48"

    if  en_remote_computing:  # copy remote folder to local directory
        cp_rmt_folder( nmrObj, server_data_folder, client_data_folder, meas_folder[0] )
        exec_rmt_ssh_cmd_in_datadir( nmrObj, "rm -rf " + meas_folder[0] )  # delete the file in the server

    maxS21, maxS21_freq, _ = compute_gain( nmrObj, data_folder, meas_folder[0], en_fig, fig_num )
    print( 'maxS21={0:0.2f} maxS21_freq={1:0.2f}'.format( 
         maxS21, maxS21_freq ) )
