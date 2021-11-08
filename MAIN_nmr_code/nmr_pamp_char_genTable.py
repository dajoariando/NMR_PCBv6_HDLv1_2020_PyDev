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
import nmr_pamp_char

# measurement properties
mode = 2 # IT HAS TO BE THE SAME AS IN nmr_pamp_char
client_data_folder = "D:\\NMR_DATA"
en_fig = True
continuous = False
freqSta = 1.8
freqSto = 5.5
freqSpa = 0.01
freqSamp = 25  # not being used for synchronized sampling. It's value will be the running freq * 4
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation

# fft parameters
fftpts = 512
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement

keepRawData = False  # setting to keep raw data

# instantiate nmr object
nmrObj = nmr_pamp_char.init( client_data_folder )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )

if nmrObj.en_remote_computing:
    swfolder = nmrObj.data_folder + '\\' + datename + '_genS21Table'
else:
    swfolder = nmrObj.data_folder + '/' + datename + '_genS21Table'
os.mkdir( swfolder )

vbiasSta = -2.6  # this value must be lower than vbiasSto
vbiasSto = 1
vbiasSpa = 10
vbiasSw = np.arange( vbiasSta, vbiasSto, vbiasSpa )

vvaracSta = -4.9  # this value must be lower than vvaracSto
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

# global variable
exptnum = 0

for i in range( len( vvaracSw ) ):
    for j in range( len( vbiasSw ) ):
        
        exptnum = exptnum + 1

        maxS21, maxS21_freq, S21mV = nmr_pamp_char.analyze ( nmrObj, vbiasSw[j], vvaracSw[i], freqSta, freqSto, freqSpa, freqSamp, fftpts, fftcmd, fftvalsub, continuous, en_fig )

        print( "" );

        maxGainTable = updateTable( maxGainTable, S21mV, vbiasSw[j], vvaracSw[i] )

        meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
        swfolder_ind = swfolder + '/' + str( 'vv_[{:03.3f}]__vb_[{:03.3f}]'.format( vvaracSw[i], vbiasSw[j] ) )
        # if ( en_fig ):
        #     shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/gainFFT.png', swfolder + '/' + str( 'plot_vv_[{:03.3f}]__vb_[{:03.3f}].png'.format( vvaracSw[i], vbiasSw[j] ) ) )  # move the figure
        if (mode == 0 or mode == 1):
            shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/gainFFT.png', swfolder + '/' + str( 'plt%3d__vbias_%0.3f__vvarac_%0.3f.png' % ( exptnum, vbiasSw[j], vvaracSw[i] ) ) )  # move the figure
        elif (mode == 2):
            shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/gain.png', swfolder + '/' + str( 'plt%3d__vbias_%0.3f__vvarac_%0.3f.png' % ( exptnum, vbiasSw[j], vvaracSw[i] ) ) )  # move the figure

        
        if keepRawData:
            # write gain values to a file
            with open( swfolder + '/gain_vv_[{:03.3f}]__vb_[{:03.3f}].txt'.format( vvaracSw[i], vbiasSw[j] ), 'w' ) as f:
                for ( a, b ) in zip ( freqSw, S21mV ):
                    f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

            shutil.move ( nmrObj.data_folder + '/' + meas_folder[0], swfolder_ind )  # move the data folder
        else:
            shutil.rmtree( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder

nmr_pamp_char.exit( nmrObj )

# write the optimum setting with the frequency and gain
Table = open( swfolder + '/genS21Table.txt', 'w' )
Table.write( 'settings:\n' )
Table.write( '\tvvarac: start={:03.3f} stop={:03.3f} spacing={:02.3f}\n'.format( vvaracSta, vvaracSto, vvaracSpa ) )
Table.write( '\tvbias: start={:03.3f} stop={:03.3f} spacing={:02.3f}\n'.format( vbiasSta, vbiasSto, vbiasSpa ) )
Table.write( '\n' );
Table.write( 'freq(MHz)\t peak-voltage(mV)\t vbias(V)\t vvarac(V)\n' )
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
