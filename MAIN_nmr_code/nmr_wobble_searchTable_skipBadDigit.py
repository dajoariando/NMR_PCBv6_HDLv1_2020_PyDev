'''
    Created on May 22th 2020
    author: David Joseph Ariando
    this program generates a table that contains minimum reflection values for
    different settings of cpar and cser of the matching network.

    It works by finding a seed value for cpar and cser, and then sweeping cpar
    up or down (according to cparPrec) to obtain the minimum S11 by changing cser values.
    cser seed is decremented by cserPrec and if it results in worse S11, cser is instead
    incremented afterwards from its original value. On the other hand, if decrementing
    cser results in better S11, cser doesn't need to be incremented.

    This function doesn't try to find minimum S11 at a specific frequency, but instead
    changing cpar value to increase/decrease frequency, and then find the minimum possible
    S11 by changing cser, doesn't matter what the final frequency is. Every measurement
    updates the minReflxTable if there's a frequency point that results in has a lower
    lower S11 value compare to the already saved S11 value in the table. Therefore,
    every measurement is considered to make it into the table when it's running.

    First set the acquisition settings, that sets the start, stop, spacing, and sampling
    frequency. Then set the range of frequency of interest: S11FreqSta and S11FreqSto.
    Then set the sweeping precision (in digit) of the Cser and Cpar. Then set the
    initial point by either providing the coil properties (l_init, r_init, and c_init)
    and set lrSeed to 1 to indicate that coil properties is used. Otherwise, set lrSeed
    to 0 and set ccSeed to 1 to indicate that initial cpar and cser is known, and also
    set the cpar_init and cser_init. It is better to set correct cpar_init and cser_init
    by manually changing it and measure using nmr_wobble and set it anywhere inside the
    S11FreqSta and S11FreqSto range of frequency. If it's outside, then the search
    function will take a long time to get into the right value, or it won't show
    search correctly.

'''

import os
import time
from nmr_std_function.nmr_functions import compute_iterate, compute_wobble_sync, compute_wobble_async
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from hw_opt.mtch_ntwrk import *
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir
import nmr_wobble

import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
from faulthandler import disable

# measurement properties
client_data_folder = "D:\\TEMP"
en_fig = 1
freqSta = 1.2
freqSto = 3.0
freqSpa = 0.001
freqSamp = 25  # not used when using wobble_sync. Will be used when using wobble_async
fftpts = 512
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
extSet = False  # use external executable to set the matching network Cpar and Cser
useRef = True  # use reference to eliminate background

fig_num = 1
keepRawData = 1  # set this to keep the S11 raw data in text file
tblMtchNtwrk = 'hw_opt/PARAM_NMR_AFE_v6.csv'  # table for the capacitance matching network capacitance values

# acquisition settings (frequency to be shown in the table
freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )  # plus half is to remove error from floating point number operation

# frequency of interest for S11 to be optimized (range should be within frequencies in the acquisition settings
S11FreqSta = 1.3
S11FreqSto = 2.9

# sweep precision
cparPrec = 2  # change cpar by this value.
cserPrec = 1  # change cser by this value.
rigFact = 10  # keep searching up/down for rigFact amount of time before deciding the best S11

# initial point options. either provide the L and R values, or provide with initial cpar and cser values
lrSeed = 0  # put this to 1 if inductance of the coil is available
ccSeed = 1  # put this to 1 if the capacitances value are available as a seed. lrSeed will take precedence over this
initDataOpt = lrSeed  # use lrSeed if L-R is known or ccSeed if cpar-cser is known and set the values below
if lrSeed:  # if lrSeed is used, set these parameters below
    l_init = 1e-6  # coil inductance
    r_init = 0.1  # coil resistance
    c_init = 0.0  # coil parasitic capacitance
else:
    if ccSeed:  # if ccSeed is used, set these parameters below
        cpar_init = 282  # the parallel capacitance
        cser_init = 199  # the series capacitance. This value is not necessary what's reported on the final table

# search settings
# searchMode = findAbsMin
# if searchMode == findMinMin:  # find the minimum allowable S11 and then stop
S11_min = -10  # the minimum allowable S11 value to be reported as adequate to stop search in findMinMin
#    printf( 'search mode is findMinMin. Search stops when S11 of {:0.2f}dB is found.'.format( S11_min ) )
# elif searchMode == findAbsMin:  # find the absolute minimum given the frequency range
#    printf( 'search mode is findAbsMin.' )

# global variable
exptnum = 0  # this number is automatically increased when runExpt() is called

# nmr object declaration
nmrObj = nmr_wobble.init ( client_data_folder )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = nmrObj.data_folder + '/' + datename + '_genS11Table'
os.mkdir( swfolder )

# find the initial cpar and cser values
CsTbl, CpTbl = read_PARAM_mtch_ntwrk_caps( nmrObj.client_path + tblMtchNtwrk )
if lrSeed:  # if coil parameters are available
    # seeds for cpar and cser are computed via L,R, and frequency
    print( 'The coil parameters are known: {:0.2f}uH {:0.0f}mOhm {:0.1f}pF'.format( l_init * 1e6, r_init * 1e3, c_init * 1e12 ) )
    f_init = ( S11FreqSto - S11FreqSta ) / 2  # set the center frequency
    _, cpar_init, cs_init = comp_Copt( l_init, r_init, c_init, f_init , CsTbl, CpTbl )
else:
    if ccSeed:  # if capacitance seed values for matching network are available
        # seeds for cpar and cser are already given
        print( 'The seed capacitance are known: cpar={:d}({:0.1f}pF) cser={:d}({:0.1f}pF)'.format( cpar_init, conv_cInt_to_cFarad( cpar_init, CpTbl ) * 1e12, cser_init , conv_cInt_to_cFarad( cser_init, CsTbl ) * 1e12 ) )

# define and initialize main table to store minimum S11 at the range of frequencies chosen
minReflxTable = np.zeros( ( len( freqSw ), 4 ), dtype=float )  # The columns are for frequency, max found value, and setting
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


def findMinS11_atCparVal( cpar, cser_iFirst , cser_Prec, s11mV_ref ):
    global minReflxTable

    print( "\tStart findMinS11_atCparVal()" )
    S11cx, minS11Freq = runExpt( cpar, cser_iFirst , s11mV_ref , 'True' )

    MinS11mV = np.min( abs( S11cx ) )  # find the minimum S11 value
    cser_ret = cser_iFirst  # the cser return value, update when less S11 value is found

    print( "\tDecrement cser." )
    searchIncr = True  # set search increment to be true. It can be disabled when we find lower S11 by decrementing cser_i when searching
    cser_i = cser_iFirst
    while( True ):  # find minimum S11 with decreasing cser_i
        cser_i = decr_cFarad_by_at_least( cser_Prec, cser_i, CsTbl )  # decrement cser_i by at least cser_Prec
        if cser_i <= 0:
            break
        S11cxCurr, minS11FreqCurr = runExpt( cpar, cser_i , s11mV_ref, 'True' )
        MinS11mVCurr = np.min( abs( S11cxCurr ) )
        if MinS11mVCurr < MinS11mV:  # find if current S11 is better than the previous one
            minS11Freq = minS11FreqCurr
            MinS11mV = MinS11mVCurr
            cser_ret = cser_i
            searchIncr = False
        else:
            if ( not searchIncr ):
                return minS11Freq, cser_ret
            else:
                break

    print( "\tIncrement cser." )
    cser_i = cser_iFirst
    while( searchIncr ):  # find minimum S11 with increasing cser_i
        cser_i = incr_cFarad_by_at_least( cser_Prec, cser_i, CsTbl )  # decrement cser_i by at least cser_Prec
        if cser_i > 2 ** len( CsTbl ) - 1:  # stop if the cser is more than max index of the table
            break
        S11cxCurr, minS11FreqCurr = runExpt( cpar, cser_i, s11mV_ref, 'True' )
        MinS11mVCurr = np.min( abs( S11cxCurr ) )
        if MinS11mVCurr < MinS11mV:  # find if current S11 is better than the previous one
            minS11Freq = minS11FreqCurr
            MinS11mV = MinS11mVCurr
            cser_ret = cser_i
        else:
            break

    return minS11Freq, cser_ret


def findMinS11_atCparVal_rigorous( cpar, cser_iFirst , cser_Prec, rigFact, s11mV_ref ):
    # rigFact: the factor for rigorous search. This means searching value up and down for rigFact amount of time to get the result

    cserBadDigit = ( 1 << 6 )  # variable for the bad digit

    global minReflxTable

    print( "\tStart findMinS11_atCparVal()" )
    S11cx, minS11Freq = runExpt( cpar, cser_iFirst , s11mV_ref , 'True' )

    MinS11mV = np.min( abs( S11cx ) )  # find the minimum S11 value
    cser_ret = cser_iFirst  # the cser return value, update when less S11 value is found

    print( "\tDecrement cser." )
    searchIncr = True  # set search increment to be true. It can be disabled when we find lower S11 by decrementing cser_i when searching
    cser_i = cser_iFirst
    rigFact_i = rigFact  # reset the rigorous factor counter
    while( True ):  # find minimum S11 with decreasing cser_i
        cser_i = cser_i - cser_Prec
        if ( cser_i & cserBadDigit ):
            cser_i = cser_i & ( ~cserBadDigit ) | ( cserBadDigit - 1 )
        if cser_i <= 0:
            break
        S11cxCurr, minS11FreqCurr = runExpt( cpar, cser_i , s11mV_ref, 'True' )
        MinS11mVCurr = np.min( abs( S11cxCurr ) )
        if MinS11mVCurr < MinS11mV:  # find if current S11 is better than the previous one
            rigFact_i = rigFact  # reset the rigFact_i when a better S11 is found
            minS11Freq = minS11FreqCurr
            MinS11mV = MinS11mVCurr
            cser_ret = cser_i
            # searchIncr = False # no need to disable searchIncr in rigouros search
        else:
            rigFact_i = rigFact_i - 1
            if ( rigFact_i == 0 ):
                if ( not searchIncr ):
                    return minS11Freq, cser_ret
                else:
                    break

    print( "\tIncrement cser." )
    cser_i = cser_iFirst
    rigFact_i = rigFact  # reset the rigorous factor counter
    while( searchIncr ):  # find minimum S11 with increasing cser_i
        cser_i = cser_i + cser_Prec
        if ( cser_i & cserBadDigit ):
            cser_i = ( cser_i & ( ~( ( cserBadDigit ) - 1 ) ) ) + cserBadDigit
        if cser_i > 2 ** len( CsTbl ) - 1:  # stop if the cser is more than max index of the table
            break
        S11cxCurr, minS11FreqCurr = runExpt( cpar, cser_i, s11mV_ref, 'True' )
        MinS11mVCurr = np.min( abs( S11cxCurr ) )
        if MinS11mVCurr < MinS11mV:  # find if current S11 is better than the previous one
            rigFact_i = rigFact  # reset the rigFact_i when a better S11 is found
            minS11Freq = minS11FreqCurr
            MinS11mV = MinS11mVCurr
            cser_ret = cser_i
        else:
            rigFact_i = rigFact_i - 1
            if ( rigFact_i == 0 ):
                break

    return minS11Freq, cser_ret


# find reference
print( 'Generate reference.' )
S11mV_ref, minS11Freq_ref = runExpt( 0, 0, 0, 0 )  # background is computed with no capacitor connected -> max reflection

# find initial seed, and update cser_init if better cser value is found for the corresponding cpar_init
# S11minFreq, cser_init = findMinS11_atCparVal( cpar_init, cser_init , cserPrec, S11mV_ref )
S11minFreq, cser_init = findMinS11_atCparVal_rigorous( cpar_init, cser_init , cserPrec, rigFact, S11mV_ref )

# search higher frequency from seed
cpar = cpar_init
cser = cser_init
S11minfreqRight = S11minFreq
while( True ):
    print( 'Decrement cpar. Find S11 minimum in higher frequency.' )
    if ( S11minfreqRight < S11FreqSto ):  # increase the frequency if the minimum S11 is still smaller than freqSto
        cpar = cpar - cparPrec
        if cpar <= 0:  # stop if cpar is 0 or below
            print( 'decrementing cpar stops due to final cpar value <= 0.' )
            break
        # S11minfreqRight, cser = findMinS11_atCparVal( cpar, cser , cserPrec, S11mV_ref )
        S11minfreqRight, cser = findMinS11_atCparVal_rigorous( cpar, cser , cserPrec, rigFact, S11mV_ref )
    else:
        print( 'decrementing cpar stops due to minimum S11 in highest frequency of interest is found.' )
        break

# search lower frequency from seed
cpar = cpar_init
cser = cser_init
S11minfreqLeft = S11minFreq
while ( True ):  # search lower frequency
    print( 'Increment cpar. Find S11 minimum in lower frequency.' )
    if ( S11minfreqLeft > S11FreqSta ):  # decrease the frequency if the minimum S11 is still higher than freqSto
        cpar = cpar + cparPrec
        if cpar > 2 ** len( CpTbl ) - 1:  # stop if the cpar is more than max index of the table
            print( 'incrementing cpar stops due to final cpar value {:d} > {:d}'.format( cpar, 2 ** len( CpTbl ) - 1 ) )
            break
        # S11minfreqLeft, cser = findMinS11_atCparVal( cpar, cser, cserPrec, S11mV_ref )
        S11minfreqLeft, cser = findMinS11_atCparVal_rigorous( cpar, cser, cserPrec, rigFact, S11mV_ref )
    else:
        print( 'incrementing cpar stops due to minimum S11 in lowest frequency of interest is found.' )
        break

# write the optimum setting with the frequency and gain into the main file
Table = open( swfolder + '/genS11Table.txt', 'w' )
Table.write( 'search settings:\n' )
Table.write( '\tCpar Precision = {:d}\n'.format( cparPrec ) )
Table.write( '\tCser Precision = {:d}\n'.format( cserPrec ) )
Table.write( '\tAcq. Frequency Start = {:.3f} MHz\n'.format( freqSta ) )
Table.write( '\tAcq. Frequency Stop = {:.3f} MHz\n'.format( freqSto ) )
Table.write( '\tAcq. Frequency Spacing = {:.3f} MHz\n'.format( freqSpa ) )
# Table.write( '\tAcq. Frequency Sampling = {:.1f} MHz\n'.format( freqSamp ) )
Table.write( '\tS11 Optimization Frequency Start = {:.2f} MHz\n'.format( S11FreqSta ) )
Table.write( '\tS11 Optimization Frequency Stop = {:.2f} MHz\n'.format( S11FreqSto ) )
if lrSeed:
    l_init = 1e-6  # coil inductance
    r_init = 0.1  # coil resistance
    c_init = 0.0  # coil parasitic capacitance
    Table.write( '\tCoil inductance = {:.3f} uH\n'.format( l_init * 1e6 ) )
    Table.write( '\tCoil resistance = {:.1f} MHz\n'.format( r_init * 1e3 ) )
    Table.write( '\tCoil capacitance = {:.3f} pF\n'.format( c_init * 1e12 ) )
    Table.write( '\tderived Cpar = {:d} ({:.1f} pF)\n'.format( cpar_init , conv_cInt_to_cFarad( cpar_init, CpTbl ) * 1e12 ) )
    Table.write( '\tderived Cser = {:d} ({:.1f} pF)\n'.format( cser_init , conv_cInt_to_cFarad( cser_init, CsTbl ) * 1e12 ) )
else:
    if ccSeed:  # if ccSeed is used, set these parameters below
        Table.write( '\tCpar seed = {:d} ({:.1f} pF)\n'.format( cpar_init , conv_cInt_to_cFarad( cpar_init, CpTbl ) * 1e12 ) )
        Table.write( '\tCser seed = {:d} ({:.1f} pF)\n'.format( cser_init , conv_cInt_to_cFarad( cser_init, CsTbl ) * 1e12 ) )

Table.write( '\n' );
Table.write( 'freq(MHz)\t S11(dB)\t Cpar(digit)\t Cser(digit)\n' )
Table.close()
with open( swfolder + '/genS11Table.txt', 'a' ) as Table:
    for ( a, b , c, d ) in zip ( minReflxTable[:, 0], minReflxTable[:, 1], minReflxTable[:, 2], minReflxTable[:, 3] ):
        Table.write( '{:-7.4f},{:-7.4f},{:-7.0f},{:-7.0f}\n' .format( a, b, c, d ) )

# clean up
nmrObj.deassertAll()
nmrObj.exit()

# plot the table figure and save file
plt.figure( 2 )
plt.plot( minReflxTable[:, 0], minReflxTable[:, 1] )
plt.title( 'Minimum reflection' )
plt.xlabel( 'freq (MHz)' )
plt.ylabel( 'S11 (dB)' )
plt.savefig( swfolder + '/genS11Table.png' )
plt.show()
