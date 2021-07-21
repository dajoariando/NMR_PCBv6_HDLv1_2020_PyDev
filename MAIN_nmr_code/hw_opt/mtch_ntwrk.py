import sys
sys.path.append( ".." )  # MAIN_nmr_code to path

import numpy as np
import csv
from nmr_std_function.data_parser import parse_simple_info
import os
import csv
import math
import time
import shutil


def comp_Z1( L, RL, CL, Cp, f0 ):  # find impedance due to parallel LC (coil and Cpar)
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return ( 1j * w0 * L + RL ) * ( 1 / ( 1j * w0 * Ct ) ) / ( 1j * w0 * L + RL + 1 / ( 1j * w0 * Ct ) )


def comp_Z2( Cs, f0 ):  # find impedance due to Cs
    w0 = 2 * np.pi * f0
    return 1 / ( 1j * w0 * Cs )


def read_PARAM_mtch_ntwrk_caps( filename ):  # read table and store it in internal variables
    f = open( filename )
    csv_f = csv.reader( f )
    CsTbl = []
    CpTbl = []
    for i in csv_f:
        if isFloat( i[0] ):
            CsTbl.append( float( i[0] ) )
            CpTbl.append( float( i[1] ) )
    f.close()
    return CsTbl, CpTbl


# convert discrete integer format of C to real C value
def conv_cInt_to_cFarad( cInt, cTbl ):
    # cInt = c in integer format
    # cTbl = table for c

    cLen = len( cTbl )  # switched capacitor length

    cFarad = 0
    for ii in range( 0, cLen ):
        if cInt & ( 1 << ii ):
            cFarad += cTbl[ii]

    return cFarad


def incr_cFarad_by_at_least( incr, cInt, cTbl ):
    # this function increments cInt by at least incr value, and then checks if the resulting C value in Farad is actually
    # increments by at least incr. This is a fix to a problem of incrementing by 1 (or small value), doesn't actually increment
    # anything because the C value (in Farad) itself is not a perfect binary series, but sometimes less or more.

    incrVal = incr  # make it local variable
    while ( True ):
        if ( cInt + incrVal ) > ( 2 ** len( cTbl ) - 1 ):
            # if index overflow (more than the table provides), do not calculate conv_cInt_to_cFarad()
            # immediately break the loop return the current value
            break
        prevVal = conv_cInt_to_cFarad( cInt, cTbl )  # find the previous Cfarad value
        nextVal = conv_cInt_to_cFarad( cInt + incrVal, cTbl )  # find the next Cfarad value
        if ( nextVal >= prevVal ):  # if the next value is more than the previous one, break the loop
            break
        else:  # otherwise increment incrVal so that the next value is more than the previous value
            incrVal = incrVal + 1

    return cInt + incrVal


def decr_cFarad_by_at_least( decr, cInt, cTbl ):
    # this function decrements cInt by at least decr value, and then checks if the resulting C value in Farad is actually
    # decrements by at least decr. This is a fix to a problem of decrementing by 1 (or small value), doesn't actually decrement
    # anything because the C value (in Farad) itself is not a perfect binary series, but sometimes less or more.

    decrVal = decr  # make it local variable
    while ( True ):
        if ( cInt - decrVal ) <= 0:
            # if index underflow (less than the table provides), do not calculate conv_cInt_to_cFarad()
            # immediately break the loop and return the current value
            break
        prevVal = conv_cInt_to_cFarad( cInt, cTbl )
        nextVal = conv_cInt_to_cFarad( cInt - decrVal, cTbl )
        if ( nextVal <= prevVal ):
            break
        else:
            decrVal = decrVal + 1

    return cInt - decrVal


# find cInt values in integer for a desired capacitance values in farad
def conv_cFarad_to_cInt( cFarad, cTbl ):
    # cFarad = c in farad
    # cTbl = table for c

    # increase c from 0 to maximum and find its minimum difference
    # with cFarad by trying to find minimum (cFarad-c)
    # it is done by finding point where c value exceeds cFarad

    cLen = len( cTbl )  # switched capacitor length

    dC_old = 0
    for i in range( 1, 2 ** cLen ):
        csel = 0
        for ii in range( 0, cLen ):
            if i & ( 1 << ii ):
                csel += cTbl[ii]

        dC = cFarad - csel
        cInt = i
        if ( dC <= 0 ):  # stop when dC is bigger than dC old
            if abs( dC ) < dC_old:
                cInt = i
                break
            else:
                cInt = i - 1
                break
        dC_old = dC

    return cInt


def comp_Copt( L, RL, CL, f0 , CsTbl, CpTbl ):  # find index for Cp and Cs for a known coil parameters

    CpLen = len( CpTbl )  # switched capacitor length
    CsLen = len( CsTbl )  # switched capacitor length

    # read the table
    # filename = './PARAM_NMR_AFE_v6.csv'
    # CsTbl, CpTbl = read_PARAM_mtch_ntwrk_caps( filename )

    # generate Z1 table of all Cp values
    Z1 = np.zeros( 2 ** CpLen - 1, dtype=complex )  # ignore 0
    for i in range( 1, 2 ** CpLen ):
        cpar_sel = 0
        for ii in range( 0, CpLen ):
            if i & ( 1 << ii ):
                cpar_sel += CpTbl[ii]
        Z1[i - 1] = comp_Z1( L, RL, CL, cpar_sel, f0 )

    # find the resonance where Z1 is max, and then delete the part after maxval (capacitive part)
    # to keep only the inductive part
    max_idx = np.argwhere( Z1 )[np.real( Z1 ) == max( 
        np.real( Z1 ) )]  # find max index
    Z1[max_idx[0][0]:] = 0  # null all values after max index

    # subtract the real part of Z1 by 50 and find its absolute value
    Z1_absmin50 = np.abs( np.real( Z1 ) - 50 )

    # find Cp index with least reflection
    Cp_idx = np.argwhere( Z1_absmin50 == min( Z1_absmin50 ) )
    Cp_idx = Cp_idx[0][0]

    # generate Z2 table of all Cs values
    Z2 = np.zeros( 2 ** CsLen - 1, dtype=complex )
    for i in range( 1, 2 ** CsLen ):
        cser_sel = 0
        for ii in range( 0, CsLen ):
            if i & ( 1 << ii ):
                cser_sel += CsTbl[ii]
        Z2[i - 1] = comp_Z2( cser_sel, f0 )

    # find index where imag(Z1) + imag(Z2)
    Z_imag_amp = np.abs( np.imag( Z2 ) + np.imag( Z1[Cp_idx] ) )
    Cs_idx = np.argwhere( Z_imag_amp == min( Z_imag_amp ) )
    Cs_idx = Cs_idx[0][0]

    return Z1[Cp_idx] + Z2[Cs_idx], Cp_idx, Cs_idx


def isFloat( val ):
    try:
        float( val )
        return True
    except ValueError:
        return False


def realZ ( L, RL, CL, Cp, f0 ):  # compute the real-Z part of the matching network + coil
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return RL / ( ( 1 - w0 ** 2 * L * Ct ) ** 2 + ( w0 * RL * Ct ) ** 2 )


def imagZ ( L, RL, CL, Cp, Cs, f0 ):  # compute the imag-Z part of the matching network + coil
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return 1j * w0 * ( L - w0 ** 2 * L ** 2 * Cp - RL ** 2 * Cp ) / ( ( 1 - w0 ** 2 * L * Cp ) ** 2 + ( w0 * RL * Cp ) ** 2 ) + 1 / 1j * w0 * Cs
