'''
Created on Apr 4, 2018

@author: David Ariando
'''

import numpy as np
import math
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt


def butter_lowpass( cutoff, fs, order ):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter( order, normal_cutoff, btype='low', analog=False )
    return b, a


def butter_lowpass_filter( data, cutoff, fs, order, en_figure ):
    b, a = butter_lowpass( cutoff, fs, order )

    if en_figure:
        w, h = freqz( b, a, worN=8000 )
        plt.figure( 10 )
        plt.plot( 0.5 * fs * w / np.pi, np.abs( h ), 'b' )
        plt.plot( cutoff, 0.5 * np.sqrt( 2 ), 'ko' )
        plt.axvline( cutoff, color='k' )
        plt.xlim( 0, 0.5 * fs )
        plt.title( "Lowpass Filter Frequency Response" )
        plt.xlabel( 'Frequency [Hz]' )
        plt.grid()
        pass

    y = lfilter( b, a, data )

    if en_figure:
        plt.figure( 11 )
        plt.plot( data, label='raw data' )
        plt.plot( y, label='filt data' )
        plt.legend()
        plt.show()

    return y


def down_conv( s, k, tE, Df, Sf ):

    # settings
    simp_dconv = False  # perform simplified downconversion for 4 phases signal

    # filter parameter
    filt_ord = 2
    filt_lpf_cutoff = 10e3  # in Hz

    T = 1 / Sf
    t = np.linspace( k * tE, k * tE + T * ( len( s ) - 1 ), len( s ) )

    # downconversion below Nyquist rate
    # Ds = abs(Df - Sf)
    # sReal = s * np.cos(2 * math.pi * Ds * t)
    # sImag = s * np.sin(2 * math.pi * Ds * t)

    if not simp_dconv:  # normal downconversion
        # downconversion at Nyquist rate or higher
        sReal = s * np.cos( 2 * math.pi * Df * t )
        sImag = s * np.sin( 2 * math.pi * Df * t )
    else:  # simulated downconversion happened in FPGA
         # echo is assumed to always start at phase 0. It is true if the pulse
         # length and delay length for pi and 2pi pulse is multiplication of 4
        sReal = np.zeros( len( s ), dtype=float )
        sImag = np.zeros( len( s ), dtype=float )
        for i in range( 0, len( s ) >> 2 ):
            sReal[i * 4 + 0] = s[i * 4 + 0] * 0
            sReal[i * 4 + 1] = s[i * 4 + 1] * 1
            sReal[i * 4 + 2] = s[i * 4 + 2] * 0
            sReal[i * 4 + 3] = s[i * 4 + 3] * -1
            sImag[i * 4 + 0] = s[i * 4 + 0] * 1
            sImag[i * 4 + 1] = s[i * 4 + 1] * 0
            sImag[i * 4 + 2] = s[i * 4 + 2] * -1
            sImag[i * 4 + 3] = s[i * 4 + 3] * 0

    r = butter_lowpass_filter( 
        sReal + 1j * sImag, filt_lpf_cutoff, Sf, filt_ord, False )

    return r


def nmr_fft( data, fs, en_fig ):
    spectx = np.linspace( -fs / 2, fs / 2, len( data ) )
    specty = np.fft.fftshift( np.fft.fft( data - np.mean( data ) ) )
    specty = np.divide( specty, len( data ) )  # normalize fft
    if en_fig:
        plt.figure
        plt.plot( spectx, specty, 'b' )
        plt.title( "FFT_data" )
        plt.xlabel( 'Frequency [MHz]' )
        plt.grid()
        plt.show()
    return spectx, specty
