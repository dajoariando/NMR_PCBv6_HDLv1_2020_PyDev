'''
    Created on May 19th 2020
    author: David Joseph Ariando
    this program generates a table that contains preamp frequency response
    characteristics with variable vvar and vbias. vbias sweep can be ignored
    if the optimum vbias is already tested

'''

import os
import time
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_gain
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt

# variables
data_parent_folder = "/root/NMR_DATA"
en_remote_dbg = 0
fig_num = 1
en_fig = 1

# measurement properties
freqSta = 2
freqSto = 8
freqSpa = 0.05
freqSamp = 25
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation

keepRawData = False  # setting to keep raw data

# instantiate nmr object
nmrObj = tunable_nmr_system_2018( data_parent_folder, en_remote_dbg )

work_dir = os.getcwd()
os.chdir( data_parent_folder )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = data_parent_folder + '/' + datename + '_genS21Table'
os.mkdir( swfolder )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

nmrObj.deassertAll()

nmrObj.assertControlSignal( nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

nmrObj.setMatchingNetwork( 0, 0 )
nmrObj.setMatchingNetwork( 0, 0 )

vbiasSta = -2.1  # this value must be lower than vbiasSto
vbiasSto = 0
vbiasSpa = 10
vbiasSw = np.arange( vbiasSta, vbiasSto, vbiasSpa )

vvaracSta = -5  # this value must be lower than vvaracSto
vvaracSto = 0
vvaracSpa = 0.1
vvaracSw = np.arange( vvaracSta, vvaracSto, vvaracSpa )


def updateTable( Table, newVal, setting1, setting2 ):
    for i in range( len( newVal ) ):
        if ( newVal[i] > Table[i, 1] ):
            Table[i, 1] = newVal[i]
            Table[i, 2] = setting1
            Table[i, 3] = setting2
    return Table


maxGainTable = np.zeros( ( len( freqSw ), 4 ), dtype = float )  # The columns are for frequency, max found value, and setting
maxGainTable[:, 0] = freqSw  # set column 1 to frequency
maxGainTable[:, 1] = -1  # set column 2 to an undefined voltage value
maxGainTable[:, 2] = -10  # set column 3 to undefined initial setting voltage of the varactor
maxGainTable[:, 3] = -10  # set column 4 to undefined initial setting voltage of the bias

for i in range( len( vvaracSw ) ):
    for j in range( len( vbiasSw ) ):
        nmrObj.assertControlSignal( nmrObj.RX1_1L_msk | nmrObj.RX2_L_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk )
        nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )
        nmrObj.setPreampTuning( vbiasSw[j], vvaracSw[i] )

        nmrObj.pamp_char ( freqSta, freqSto, freqSpa, freqSamp )

        nmrObj.deassertAll()

        meas_folder = parse_simple_info( data_parent_folder, 'current_folder.txt' )

        maxS21, maxS21_freq, S21mV = compute_gain( nmrObj, data_parent_folder, meas_folder[0], en_fig, fig_num )
        print( 'maxS21={:0.2f} maxS21_freq={:0.2f} vvarac={:0.1f} vbias={:0.1f}'.format( maxS21, maxS21_freq, vvaracSw[i], vbiasSw[j] ) )

        maxGainTable = updateTable( maxGainTable, S21mV, vvaracSw[i], vbiasSw[j] )

        swfolder_ind = swfolder + '/' + str( 'vv_[{:03.2f}]__vb_[{:03.2f}]'.format( vvaracSw[i], vbiasSw[j] ) )
        shutil.move( data_parent_folder + '/' + meas_folder[0] + '/gain.png', swfolder + '/' + str( 'plot_vv_[{:03.2f}]__vb_[{:03.2f}].png'.format( vvaracSw[i], vbiasSw[j] ) ) )  # move the figure
        if keepRawData:
            # write gain values to a file
            with open( swfolder + '/gain_vv_[{:03.2f}]__vb_[{:03.2f}].txt'.format( vvaracSw[i], vbiasSw[j] ), 'w' ) as f:
                for ( a, b ) in zip ( freqSw, S21mV ):
                    f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

            shutil.move ( data_parent_folder + '/' + meas_folder[0], swfolder_ind )  # move the data folder
        else:
            shutil.rmtree( data_parent_folder + '/' + meas_folder[0], swfolder_ind )

# write the optimum setting with the frequency and gain
Table = open( swfolder + '/genS21Table.txt', 'w' )
Table.write( 'settings:\n' )
Table.write( '\tvvarac: start={:03.1f} stop={:03.1f} spacing={:02.2f}\n'.format( vvaracSta, vvaracSto, vvaracSpa ) )
Table.write( '\tvbias: start={:03.1f} stop={:03.1f} spacing={:02.2f}\n'.format( vbiasSta, vbiasSto, vbiasSpa ) )
Table.write( '\n' );
Table.write( 'freq(MHz)\t peak-voltage(mV)\t vvarac(V)\t vbias(V)\n' )
Table.close()
with open( swfolder + '/genS21Table.txt', 'a' ) as Table:
    for ( a, b , c, d ) in zip ( maxGainTable[:, 0], maxGainTable[:, 1], maxGainTable[:, 2], maxGainTable[:, 3] ):
        Table.write( '{:-7.2f},{:-7.2f},{:-7.2f},{:-7.2f}\n' .format( a, b, c, d ) )

plt.figure( 2 )
plt.plot( maxGainTable[:, 0], maxGainTable[:, 1] )
plt.title( 'Max gain with optimized bias & varactor voltage' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'voltage (mV)' )
plt.savefig( swfolder + '/genS21Table.png' )
plt.show()
