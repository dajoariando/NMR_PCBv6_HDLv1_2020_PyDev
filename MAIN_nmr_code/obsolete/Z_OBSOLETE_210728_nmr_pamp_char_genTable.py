'''
    Created on May 19th 2020
    author: David Joseph Ariando
    this program generates a table that contains an optimum setting for the preamp vbias
    and preamp varactor voltage by sweeping of vbias and vvarac

'''

import os
import time
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt

from nmr_std_function.nmr_functions import compute_iterate, compute_gain_sync, compute_gain_fft_sync
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir

# variables
client_data_folder = "D:\\TEMP"
en_remote_dbg = 0
fig_num = 1
en_fig = 1
# remote computing configuration. See the NMR class to see details of use
en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

# measurement properties
freqSta = 1.5
freqSto = 2.2
freqSpa = 0.002
freqSamp = 25
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation

# fft parameters
fftpts = 128
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement

keepRawData = False  # setting to keep raw data

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )

if en_remote_computing:
    swfolder = nmrObj.data_folder + '\\' + datename + '_genS21Table'
else:
    swfolder = nmrObj.data_folder + '/' + datename + '_genS21Table'
os.mkdir( swfolder )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

nmrObj.deassertAll()

nmrObj.assertControlSignal( nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setMatchingNetwork( 0, 0 )

vbiasSta = -2.6  # this value must be lower than vbiasSto
vbiasSto = 0
vbiasSpa = 10
vbiasSw = np.arange( vbiasSta, vbiasSto, vbiasSpa )

vvaracSta = 3.0  # this value must be lower than vvaracSto
vvaracSto = 4.9
vvaracSpa = 0.01
vvaracSw = np.arange( vvaracSta, vvaracSto, vvaracSpa )


def updateTable( Table, newVal, setting1, setting2 ):
    for i in range( len( newVal ) ):
        if ( newVal[i] > Table[i, 1] ):
            Table[i, 1] = newVal[i]
            Table[i, 2] = setting1
            Table[i, 3] = setting2
    return Table


maxGainTable = np.zeros( ( len( freqSw ), 4 ), dtype=float )  # The columns are for frequency, max found value, and setting
maxGainTable[:, 0] = freqSw  # set column 1 to frequency
maxGainTable[:, 1] = -1  # set column 2 to an undefined voltage value
maxGainTable[:, 2] = -10  # set column 3 to undefined initial setting voltage of the varactor
maxGainTable[:, 3] = -10  # set column 4 to undefined initial setting voltage of the bias

nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )
nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk )

for i in range( len( vvaracSw ) ):
    for j in range( len( vbiasSw ) ):

        nmrObj.setPreampTuning( vbiasSw[j], vvaracSw[i] )

        nmrObj.pamp_char_sync ( freqSta, freqSto, freqSpa, fftpts, fftcmd, fftvalsub )

        # compute the generated data
        if  en_remote_computing:  # copy remote files to local directory
            cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )
        meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )

        if  en_remote_computing:  # copy remote folder to local directory
            cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
            exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, nmrObj.server_data_folder, "rm -rf " + meas_folder[0] )  # delete the file in the server

        # maxS21, maxS21_freq, S21mV = compute_gain( nmrObj, data_folder, meas_folder[0], en_fig, fig_num )
        maxS21, maxS21_freq, S21mV = compute_gain_fft_sync( nmrObj, nmrObj.data_folder, meas_folder[0], en_fig, fig_num )
        print( 'maxS21={:0.3f} maxS21_freq={:0.3f} vvarac={:0.3f} vbias={:0.3f}'.format( maxS21, maxS21_freq, vvaracSw[i], vbiasSw[j] ) )

        maxGainTable = updateTable( maxGainTable, S21mV, vvaracSw[i], vbiasSw[j] )

        swfolder_ind = swfolder + '/' + str( 'vv_[{:03.3f}]__vb_[{:03.3f}]'.format( vvaracSw[i], vbiasSw[j] ) )
        shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/gainFFT.png', swfolder + '/' + str( 'plot_vv_[{:03.3f}]__vb_[{:03.3f}].png'.format( vvaracSw[i], vbiasSw[j] ) ) )  # move the figure
        if keepRawData:
            # write gain values to a file
            with open( swfolder + '/gain_vv_[{:03.3f}]__vb_[{:03.3f}].txt'.format( vvaracSw[i], vbiasSw[j] ), 'w' ) as f:
                for ( a, b ) in zip ( freqSw, S21mV ):
                    f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

            shutil.move ( nmrObj.data_folder + '/' + meas_folder[0], swfolder_ind )  # move the data folder
        else:
            shutil.rmtree( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder

nmrObj.deassertAll()

# write the optimum setting with the frequency and gain
Table = open( swfolder + '/genS21Table.txt', 'w' )
Table.write( 'settings:\n' )
Table.write( '\tvvarac: start={:03.3f} stop={:03.3f} spacing={:02.3f}\n'.format( vvaracSta, vvaracSto, vvaracSpa ) )
Table.write( '\tvbias: start={:03.3f} stop={:03.3f} spacing={:02.3f}\n'.format( vbiasSta, vbiasSto, vbiasSpa ) )
Table.write( '\n' );
Table.write( 'freq(MHz)\t peak-voltage(mV)\t vvarac(V)\t vbias(V)\n' )
Table.close()
with open( swfolder + '/genS21Table.txt', 'a' ) as Table:
    for ( a, b , c, d ) in zip ( maxGainTable[:, 0], maxGainTable[:, 1], maxGainTable[:, 2], maxGainTable[:, 3] ):
        Table.write( '{:-7.4f},{:-7.4f},{:-7.3f},{:-7.3f}\n' .format( a, b, c, d ) )

plt.figure( 2 )
plt.plot( maxGainTable[:, 0], maxGainTable[:, 1] )
plt.title( 'Max gain with optimized bias & varactor voltage' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'voltage (mV)' )
plt.savefig( swfolder + '/genS21Table.png' )
plt.show()
