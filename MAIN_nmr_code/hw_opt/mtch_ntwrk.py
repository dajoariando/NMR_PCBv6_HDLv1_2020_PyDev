import sys
sys.path.append( ".." )  # MAIN_nmr_code to path

import numpy as np
import csv
from nmr_std_function.nmr_functions import compute_wobble
from nmr_std_function.data_parser import parse_simple_info
import os
import csv
import math
import time
import shutil

from sympy import symbols, solveset, Eq, N, linsolve, nonlinsolve
import cmath


def comp_Z1( L, RL, CL, Cp, f0 ):
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return ( 1j * w0 * L + RL ) * ( 1 / ( 1j * w0 * Ct ) ) / ( 1j * w0 * L + RL + 1 / ( 1j * w0 * Ct ) )


def comp_Z2( Cs, f0 ):
    w0 = 2 * np.pi * f0
    return 1 / ( 1j * w0 * Cs )


def read_PARAM_mtch_ntwrk_caps( filename ):
    f = open( filename )
    csv_f = csv.reader( f )
    cser = []
    CpTbl = []
    for i in csv_f:
        if isFloat( i[0] ):
            cser.append( float( i[0] ) )
            CpTbl.append( float( i[1] ) )
    f.close()
    return cser, CpTbl


# convert discrete integer format of C to real C value
def conv_cInt_to_cReal( cInt, cTbl ):
    # cInt = c in integer format
    # cTbl = table for c

    cLen = 12  # switched capacitor length

    cReal = 0
    for ii in range( 0, cLen ):
        if cInt & ( 1 << ii ):
            cReal += cTbl[ii]

    return cReal


def conv_cReal_to_cInt( cReal, cTbl ):
    # cReal = c in real capacitance
    # cTbl = table for c

    # increase c from 0 to maximum and find its minimum difference
    # with cReal by trying to find minimum (cReal-c)
    # it is done by finding point where c value exceeds cReal

    cLen = 12  # switched capacitor length

    dC_old = 0
    for i in range( 1, 2 ** cLen ):
        csel = 0
        for ii in range( 0, cLen ):
            if i & ( 1 << ii ):
                csel += cTbl[ii]

        dC = cReal - csel
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


def Cp_opt( L, RL, CL, f0 ):

    cLen = 12  # switched capacitor length

    filename = './PARAM_NMR_AFE_v6.csv'
    cser, CpTbl = read_PARAM_mtch_ntwrk_caps( filename )

    Z1 = np.zeros( 2 ** cLen - 1, dtype = complex )  # ignore 0
    for i in range( 1, 2 ** cLen ):
        cpar_sel = 0
        for ii in range( 0, cLen ):
            if i & ( 1 << ii ):
                cpar_sel += CpTbl[ii]
        Z1[i - 1] = comp_Z1( L, RL, CL, cpar_sel, f0 )
    max_idx = np.argwhere( Z1 )[np.real( Z1 ) == max( 
        np.real( Z1 ) )]  # find max index
    # delete the values after max_index, effectively removing the 50 ohms
    # impedance matched at the other side (dominated by capacitance, instead
    # of coil)
    Z1[max_idx[0][0]:] = 0
    # subtract the real part of Z1 by 50 and find its absolute value
    Z1_absmin50 = np.abs( np.real( Z1 ) - 50 )
    # find Cp index with least reflection
    Cp_idx = np.argwhere( Z1_absmin50 == min( Z1_absmin50 ) )
    Cp_idx = Cp_idx[0][0]

    Z2 = np.zeros( 2 ** cLen - 1, dtype = complex )
    for i in range( 1, 2 ** cLen ):
        cser_sel = 0
        for ii in range( 0, cLen ):
            if i & ( 1 << ii ):
                cser_sel += cser[ii]
        Z2[i - 1] = comp_Z2( cser_sel, f0 )
    # imaginary amplitude
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


def compSimp ( x, y ):
    return x + 1j * y


def realZ ( L, RL, CL, Cp, f0 ):
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return RL / ( ( 1 - w0 ** 2 * L * Ct ) ** 2 + ( w0 * RL * Ct ) ** 2 )


def imagZ ( L, RL, CL, Cp, Cs, f0 ):
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return 1j * w0 * ( L - w0 ** 2 * L ** 2 * Cp - RL ** 2 * Cp ) / ( ( 1 - w0 ** 2 * L * Cp ) ** 2 + ( w0 * RL * Cp ) ** 2 ) + 1 / 1j * w0 * Cs


filename = './PARAM_NMR_AFE_v6.csv'
CsTbl, CpTbl = read_PARAM_mtch_ntwrk_caps( filename )

Cp = conv_cInt_to_cReal( 2381, CpTbl )
Cs = conv_cInt_to_cReal( 439, CsTbl )
f0 = 4.2e6

# comp_Z1( L, RL, CL, Cp, f0 )
# comp_Z2( Cs, f0 )


def addition( a, b ):
    return a + b


def subtract( a, b ):
    return a - b


x, y = symbols( 'x y' )
f = Eq( addition( x, y ), 50 )
g = Eq( subtract( x, y ), 10 )
ans = linsolve( [f, g], ( x, y ) )

L, RL = symbols( 'L RL' )
f = Eq( realZ ( L, RL, 0, Cp, f0 ), 50 )
g = Eq( imagZ ( L, RL, 0, Cp, Cs, f0 ), 0 )
ans = solveset( [f, g], ( L, RL ) )

pass
