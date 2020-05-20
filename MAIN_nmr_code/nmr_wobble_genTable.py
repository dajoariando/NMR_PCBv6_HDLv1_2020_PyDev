'''
    Created on May 19th 2020
    author: David Joseph Ariando
    this program generates a table that contains minimum reflection values for
    different settings of cpar and cser of the matching network

'''

import os
import time
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_wobble
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
freqSta = 3
freqSto = 5
freqSpa = 0.01
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
swfolder = data_parent_folder + '/' + datename + '_genS11Table'
os.mkdir( swfolder )

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

nmrObj.deassertAll()

nmrObj.assertControlSignal( nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk )

cserSta = 1  # this value must be lower than cserSto
cserSto = 4096
cserSpa = 10
cserSw = np.arange( cserSta, cserSto, cserSpa )

cparSta = 1  # this value must be lower than cparSto
cparSto = 4096
cparSpa = 10
cparSw = np.arange( cparSta, cparSto, cparSpa )


def updateTable( Table, newVal, setting1, setting2 ):
    for i in range( len( newVal ) ):
        if ( newVal[i] < Table[i, 1] ):
            Table[i, 1] = newVal[i]
            Table[i, 2] = setting1
            Table[i, 3] = setting2
    return Table


minReflxTable = np.zeros( ( len( freqSw ), 4 ), dtype = float )  # The columns are for frequency, max found value, and setting
minReflxTable[:, 0] = freqSw  # set column 1 to frequency
minReflxTable[:, 1] = 5000  # set column 2 to an undefined voltage value
minReflxTable[:, 2] = -1  # set column 3 to undefined setting of the cpar
minReflxTable[:, 3] = -1  # set column 4 to undefined setting of the cser

for i in range( len( cparSw ) ):
    for j in range( len( cserSw ) ):
        nmrObj.assertControlSignal( nmrObj.RX1_2L_msk | nmrObj.RX_SEL2_msk | nmrObj.RX_FL_msk )
        nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk | nmrObj.PSU_5V_ANA_N_EN_msk )
        nmrObj.setMatchingNetwork( cparSw[i], cserSw[j] )
        nmrObj.setMatchingNetwork( cparSw[i], cserSw[j] )

        nmrObj.wobble( freqSta, freqSto, freqSpa, freqSamp )

        nmrObj.deassertAll()

        meas_folder = parse_simple_info( data_parent_folder, 'current_folder.txt' )

        S11_min = -10
        S11mV, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = compute_wobble( nmrObj, data_parent_folder, meas_folder[0], S11_min, en_fig, fig_num )
        print( 'fmin={:0.3f} fmax={:0.3f} bw={:0.3f} minS11={:0.2f} minS11_freq={:0.2f} cpar={:0.0f} cser={:0.0f}'.format( S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparSw[i], cserSw[j] ) )

        minReflxTable = updateTable( minReflxTable, S11mV, cparSw[i], cserSw[j] )

        swfolder_ind = swfolder + '/' + str( 'Cp_[{:03.0f}]__Cs_[{:03.0f}]'.format( cparSw[i], cserSw[j] ) )
        shutil.move( data_parent_folder + '/' + meas_folder[0] + '/wobble.png', swfolder + '/' + str( 'plot_Cp_[{:03.0f}]__Cs_[{:03.0f}].png'.format( cparSw[i], cserSw[j] ) ) )  # move the figure
        if keepRawData:
            # write gain values to a file
            with open( swfolder + '/S11_Cp_[{:03.0f}]__Cs_[{:03.0f}].txt'.format( cparSw[i], cserSw[j] ), 'w' ) as f:
                for ( a, b ) in zip ( freqSw, S11mV ):
                    f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

            shutil.move ( data_parent_folder + '/' + meas_folder[0], swfolder_ind )  # move the data folder
        else:
            shutil.rmtree( data_parent_folder + '/' + meas_folder[0], swfolder_ind )

# write the optimum setting with the frequency and gain
Table = open( swfolder + '/genS11Table.txt', 'w' )
Table.write( 'settings:\n' )
Table.write( '\tcpar: start={:.0f} stop={:.0f} spacing={:.0f}\n'.format( cparSta, cparSto, cparSpa ) )
Table.write( '\tcser: start={:.0f} stop={:.0f} spacing={:.0f}\n'.format( cserSta, cserSto, cserSpa ) )
Table.write( '\n' );
Table.write( 'freq(MHz)\t min-voltage(mV)\t Cpar(digit)\t Cser(digit)\n' )
Table.close()
with open( swfolder + '/genS11Table.txt', 'a' ) as Table:
    for ( a, b , c, d ) in zip ( minReflxTable[:, 0], minReflxTable[:, 1], minReflxTable[:, 2], minReflxTable[:, 3] ):
        Table.write( '{:-7.2f},{:-7.2f},{:-7.0f},{:-7.0f}\n' .format( a, b, c, d ) )

plt.figure( 2 )
plt.plot( minReflxTable[:, 0], minReflxTable[:, 1] )
plt.title( 'Minimum reflection' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'voltage (mV)' )
plt.savefig( swfolder + '/genS11Table.png' )
plt.show()
