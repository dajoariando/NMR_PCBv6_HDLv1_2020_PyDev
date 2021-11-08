'''
    Created on May 19th 2020
    author: David Joseph Ariando
    this program generates a table that contains minimum reflection values for
    different settings of cpar and cser of the matching network.


'''

import os
import time
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_wobble_sync, compute_wobble_async
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
import nmr_wobble

# variables
client_data_folder = "D:\\NMR_DATA"
nmrObj = nmr_wobble.init ( client_data_folder ) # nmr object declaration
en_remote_dbg = 0
fig_num = 1
en_fig = 1  # enable figure for every measurement
keepRawData = False  # set this to keep the S11 raw data in text file
tblMtchNtwrk = 'hw_opt/PARAM_NMR_AFE_v6.csv'  # table for the capacitance matching network capacitance values
freqSta = 5
freqSto = 10
freqSpa = 0.01
freqSamp = 25
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation
fftpts = 512
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9546  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
extSet = False  # use external executable to set the matching network Cpar and Cser
useRef = True  # use reference to eliminate background

# measurement settings
S11_min = -10  # the minimum allowable S11 value to be reported as adequate

# capacitance sweep
cserSta = 1  # cser start value. this value must be lower than cserSto
cserSto = 4095  # cser stop value
cserSpa = 2  # cser spacing value

cparSta = 1  # cpar start value. this value must be lower than cparSto
cparSto = 10  # cpar stop value
cparSpa = 1  # cpar spacing value

# save working directory
# work_dir = os.getcwd()
# os.chdir( data_parent_folder )

# global variable
exptnum = 0  # this number is automatically increased when runExpt() is called

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = nmrObj.data_folder + '/' + datename + '_genS11Table'
os.mkdir( swfolder )

# define and initialize table
minReflxTable = np.zeros( ( len( freqSw ), 4 ), dtype = float )  # The columns are for frequency, max found value, and setting
minReflxTable[:, 0] = freqSw  # set column 1 to frequency
minReflxTable[:, 1] = 5000  # set column 2 to an undefined voltage value
minReflxTable[:, 2] = -1  # set column 3 to undefined setting of the cpar
minReflxTable[:, 3] = -1  # set column 4 to undefined setting of the cser

# function to update table
def updateTable( Table, newVal, setting1, setting2 ):
    for i in range( len( newVal ) ):
        if ( newVal[i] < Table[i, 1] ):
            Table[i, 1] = newVal[i]
            Table[i, 2] = setting1
            Table[i, 3] = setting2
    return Table

def runExpt( cparVal, cserVal, S11mV_ref, useRef ):
    # useRef: use the pregenerated S11mV_ref as a reference to compute reflection. If this option is 0, then the compute_wobble will instead generated S11 in mV format instead of dB format

    # global variable
    global exptnum
    global minReflxTable

    exptnum = exptnum + 1

    S11, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = nmr_wobble.analyze( nmrObj, extSet, cparVal, cserVal, freqSta, freqSto, freqSpa, freqSamp , fftpts, fftcmd, fftvalsub, S11mV_ref, useRef , en_fig )

    # update the table
    minReflxTable = updateTable( minReflxTable, 20 * np.log10( abs( S11 ) ), cparVal, cserVal )

    # move the measurement folder to the main folder
    meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
    swfolder_ind = swfolder + '/' + str( 'Cp_[{:d}]__Cs_[{:d}]'.format( cparVal, cserVal ) )
    if en_fig:
        shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/wobble.png', swfolder + '/' + str( 'plt{:03d}_Cp_[{:d}]__Cs_[{:d}].png'.format( exptnum, cparVal, cserVal ) ) )  # move the figure

    if keepRawData:
        # write gain values to a file
        RawDataFile = open( swfolder + '/S11_Cp_[{:d}]__Cs_[{:d}].txt'.format( cparVal, cserVal ), 'w' )
        RawDataFile.write( 'freq(MHz)\t min-voltage(mV)\n' )
        RawDataFile.close()
        with open( swfolder + '/S11_Cp_[{:d}]__Cs_[{:d}].txt'.format( cparVal, cserVal ), 'a' ) as f:
            for ( a, b ) in zip ( freqSw, abs( S11 ) ):
                f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

        shutil.rmtree ( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder
        
    else:
        shutil.rmtree( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder

    return S11, minS11_freq

# generate reference
S11mV_ref, minS11Freq_ref = runExpt( 0, 0, 0, 0 )  # background is computed with no capacitor connected -> max reflection

# generate sweep values
cserSw = np.arange( cserSta, cserSto, cserSpa )
cparSw = np.arange( cparSta, cparSto, cparSpa )

for i in range( len( cparSw ) ):
    for j in range( len( cserSw ) ):
        S11cxCurr, minS11FreqCurr = runExpt( cparSw[i], cserSw[j], S11mV_ref, 'True' )

# write the optimum setting with the frequency and gain into the main file
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

# plot the table figure and save file
plt.figure( 2 )
plt.plot( minReflxTable[:, 0], minReflxTable[:, 1] )
plt.title( 'Minimum reflection' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'voltage (mV)' )
plt.savefig( swfolder + '/genS11Table.png' )
plt.show()
