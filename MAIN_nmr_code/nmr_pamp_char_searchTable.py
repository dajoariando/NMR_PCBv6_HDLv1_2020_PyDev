'''
    Created on July 30th 2020
    author: David Joseph Ariando

'''

import os
import time

from nmr_std_function.data_parser import parse_simple_info
from hw_opt.mtch_ntwrk import *
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir
import nmr_pamp_char

import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
# from faulthandler import disable

# measurement properties
client_data_folder = "D:\\TEMP"
en_fig = 1
freqSta = 1.2
freqSto = 3.0
freqSpa = 0.001
freqSamp = 25  # not being used for synchronized sampling. It's value will be the running freq * 4
fftpts = 1024
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
continuous = False

fig_num = 1
keepRawData = 1  # set this to keep the S11 raw data in text file

# acquisition settings (frequency to be shown in the table
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation

# frequency of interest for S11 to be optimized (range should be within frequencies in the acquisition settings
S21FreqSta = 1.3
S21FreqSto = 2.9

# sweep precision
vbiasPrec = 0.05  # change vbias by this value.
vvaracPrec = 0.05  # change vvarac by this value.
rigFact = 3  # keep searching up/down for rigFact amount of time before deciding the best tuning

# initial point options. either provide the L and R values, or provide with initial vvarac and vbias values
vbias_init = -2.6  # the bias voltage
vvarac_init = 3.8  # the varactor voltage

# global variable
exptnum = 0  # this number is automatically increased when runExpt() is called

# nmr object declaration
nmrObj = nmr_pamp_char.init( client_data_folder )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = nmrObj.data_folder + '/' + datename + '_genS21Table'
os.mkdir( swfolder )

# the initial value for vbias and vvarac
print( 'The seed voltage: vbias=%0.3fV vvarac=%0.3fV' % ( vbias_init, vvarac_init ) )

# define and initialize main table to store minimum S11 at the range of frequencies chosen
maxS21Table = np.zeros( ( len( freqSw ), 4 ), dtype=float )  # The columns are for frequency, max found value, and setting
maxS21Table[:, 0] = freqSw  # set column 1 to frequency
maxS21Table[:, 1] = -5000.00  # set column 2 to an undefined voltage value
maxS21Table[:, 2] = -100.00  # set column 3 to undefined setting of the vbias
maxS21Table[:, 3] = -100.00  # set column 4 to undefined setting of the vvarac


# function to update table
def updateTable( Table, newVal, setting1, setting2 ):
    for i in range( len( newVal ) ):
        if ( newVal[i] > Table[i, 1] ):
            Table[i, 1] = newVal[i]
            Table[i, 2] = setting1
            Table[i, 3] = setting2
    return Table


def runExpt( vbias, vvarac ):
    # useRef: use the pregenerated S11mV_ref as a reference to compute reflection. If this option is 0, then the compute_wobble will instead generated S11 in mV format instead of dB format

    # global variable
    global exptnum
    global maxS21Table

    exptnum = exptnum + 1

    maxS21dB, maxS21Freq, S21mV = nmr_pamp_char.analyze ( nmrObj, vbias, vvarac, freqSta, freqSto, freqSpa, freqSamp, fftpts, fftcmd, fftvalsub, continuous, en_fig )

    # update the table
    maxS21Table = updateTable( maxS21Table, 20 * np.log10( abs( S21mV ) ), vbias, vvarac )

    # move the measurement folder to the main folder
    meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )
    swfolder_ind = swfolder + '/' + str( 'vbias_%0.3f__vvarac_%0.3f' % ( vbias, vvarac ) )
    if en_fig:
        shutil.move( nmrObj.data_folder + '/' + meas_folder[0] + '/gainFFT.png', swfolder + '/' + str( 'plt%3d__vbias_%0.3f__vvarac_%0.3f.png' % ( exptnum, vbias, vvarac ) ) )  # move the figure

    if keepRawData:
        # write gain values to a file
        RawDataFile = open( swfolder + '/S21___vbias_%0.3f__vvarac_%0.3f.txt' % ( vbias, vvarac ), 'w' )
        RawDataFile.write( 'freq(MHz)\t max-voltage(mV)\n' )
        RawDataFile.close()
        with open( swfolder + '/S21___vbias_%0.3f__vvarac_%0.3f.txt' % ( vbias, vvarac ), 'a' ) as f:
            for ( a, b ) in zip ( freqSw, abs( S21mV ) ):
                f.write( '{:-8.3f},{:-8.3f}\n' .format( a, b ) )

        shutil.rmtree ( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder
    else:
        shutil.rmtree( nmrObj.data_folder + '/' + meas_folder[0] )  # remove the data folder

    return S21mV, maxS21Freq


def findMaxS21_atVvarac_rigorous( vvarac, vbias_iFirst , vbias_Prec, rigFact ):
    # rigFact: the factor for rigorous search. This means searching value up and down for rigFact amount of time to get the result

    global maxS21Table

    print( "\tStart findMaxS21_atVvarac()" )
    maxS21Freq, S21mV = runExpt( vbias_iFirst, vvarac )

    MaxS21mV = np.max( abs( S21mV ) )  # find the minimum S11 value
    vbias_ret = vbias_iFirst  # the vbias return value, update when less S11 value is found

    print( "\tDecrement vbias." )
    searchIncr = True  # set search increment to be true. It can be disabled when we find lower S11 by decrementing vbias_i when searching
    vbias_i = vbias_iFirst
    rigFact_i = rigFact  # reset the rigorous factor counter
    while( True ):  # find maximum S21 with decreasing vbias_i
        vbias_i = vbias_i - vbias_Prec
        if vbias_i < -5:
            break
        S21mVCurr, maxS21FreqCurr = runExpt( vbias_i, vvarac )
        MaxS21mVCurr = np.max( abs( S21mVCurr ) )
        if MaxS21mVCurr > MaxS21mV:  # find if current S21 is better than the previous one
            rigFact_i = rigFact  # reset the rigFact_i when a better S21 is found
            maxS21Freq = maxS21FreqCurr
            MaxS21mV = MaxS21mVCurr
            vbias_ret = vbias_i
            # searchIncr = False # no need to disable searchIncr in rigouros search
        else:
            rigFact_i = rigFact_i - 1
            if ( rigFact_i == 0 ):
                if ( not searchIncr ):
                    return maxS21Freq, vbias_ret
                else:
                    break

    print( "\tIncrement vbias." )
    vbias_i = vbias_iFirst
    rigFact_i = rigFact  # reset the rigorous factor counter
    while( searchIncr ):  # find maximum S21 with increasing vbias_i
        vbias_i = vbias_i + vbias_Prec
        if vbias_i > 5:  # stop if the vbias is more than max index of the table
            break
        S21mVCurr, maxS21FreqCurr = runExpt( vbias_i, vvarac )
        MaxS21mVCurr = np.max( abs( S21mVCurr ) )
        if MaxS21mVCurr > MaxS21mV:  # find if current S21 is better than the previous one
            rigFact_i = rigFact  # reset the rigFact_i when a better S21 is found
            maxS21Freq = maxS21FreqCurr
            MaxS21mV = MaxS21mVCurr
            vbias_ret = vbias_i
        else:
            rigFact_i = rigFact_i - 1
            if ( rigFact_i == 0 ):
                break

    return maxS21Freq, vbias_ret


# find initial seed, and update vbias_init if better vbias value is found for the corresponding vbias_init
S21maxFreq, vbias_init = findMaxS21_atVvarac_rigorous( vvarac_init, vbias_init , vbiasPrec, rigFact )

# search higher frequency from seed
vbias = vbias_init
vvarac = vvarac_init
S21minfreqRight = S21maxFreq
while( True ):
    print( 'Decrement vvarac. Find S21 maximum in higher frequency.' )
    if ( S21minfreqRight < S21FreqSto ):  # increase the frequency if the maximum S21 is still higher than freqSto
        vvarac = vvarac - vvaracPrec
        if vvarac < -5:  # stop if vvarac is 0 or below
            print( 'decrementing vvarac stops due to final vvarac value of -5V.' )
            break
        S21minfreqRight, vbias = findMaxS21_atVvarac_rigorous( vvarac, vbias , vbiasPrec, rigFact )
    else:
        print( 'decrementing vvarac stops due to maximum S21 in highest frequency of interest is found.' )
        break

# search lower frequency from seed
vvarac = vvarac_init
vbias = vbias_init
S21minfreqLeft = S21maxFreq
while ( True ):  # search lower frequency
    print( 'Increment vvarac. Find S11 minimum in lower frequency.' )
    if ( S21minfreqLeft > S21FreqSta ):  # decrease the frequency if the minimum S21 is still higher than freqSto
        vvarac = vvarac + vvaracPrec
        if vvarac > 5:  # stop if the vvarac is more than max index of the table
            print( 'incrementing vvarac stops due to final vvarac value of 5V ' )
            break
        S21minfreqLeft, vbias = findMaxS21_atVvarac_rigorous( vvarac, vbias, vbiasPrec, rigFact )
    else:
        print( 'incrementing vvarac stops due to minimum S11 in lowest frequency of interest is found.' )
        break

# write the optimum setting with the frequency and gain into the main file
Table = open( swfolder + '/genS21Table.txt', 'w' )
Table.write( 'search settings:\n' )
Table.write( '\tvvarac Precision = %0.3f V\n' % vvaracPrec )
Table.write( '\tvbias Precision = %0.3f V\n' % vbiasPrec )
Table.write( '\tAcq. Frequency Start = %0.3f MHz\n' % freqSta )
Table.write( '\tAcq. Frequency Stop = %0.3f MHz\n' % freqSto )
Table.write( '\tAcq. Frequency Spacing = %0.3f MHz\n' % freqSpa )
# Table.write( '\tAcq. Frequency Sampling = {:.1f} MHz\n'.format( freqSamp ) )
Table.write( '\tS21 Optimization Frequency Start = %0.3f MHz\n' % S21FreqSta )
Table.write( '\tS21 Optimization Frequency Stop = %0.3f MHz\n' % S21FreqSto )
Table.write( '\tvbias seed = %0.3f\n' % vbias_init )
Table.write( '\tvvarac seed = %0.3f\n' % vvarac_init )

Table.write( '\n' );
Table.write( 'freq(MHz)\t S21(dBmV)\t vbias(V)\t vvarac(V)\n' )
Table.close()
with open( swfolder + '/genS21Table.txt', 'a' ) as Table:
    for ( a, b , c, d ) in zip ( maxS21Table[:, 0], maxS21Table[:, 1], maxS21Table[:, 2], maxS21Table[:, 3] ):
        Table.write( '{:-7.4f},{:-7.4f},{:-0.3f},{:-0.3f}\n' .format( a, b, c, d ) )

# clean up
nmrObj.exit()

# plot the table figure and save file
plt.figure( 2 )
plt.plot( maxS21Table[:, 0], maxS21Table[:, 1] )
plt.title( 'Maximum Transmission' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'S21 (mV)' )
plt.savefig( swfolder + '/genS21Table.png' )
plt.show()
