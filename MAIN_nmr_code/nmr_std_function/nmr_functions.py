import csv
import math
import os

import matplotlib
from scipy.optimize import curve_fit

import matplotlib.pyplot as plt
from nmr_std_function import data_parser
from nmr_std_function.data_parser import convert_to_prospa_data_t1
from nmr_std_function.signal_proc import down_conv, nmr_fft, butter_lowpass_filter
import numpy as np


def compute_spfft( nmrObj, data_parent_folder, meas_folder, en_fig, fig_num ):

    # compute_spfft computes data from a single fft hardware capture

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freq = data_parser.find_value( 'freq', param_list, value_list )
    fftPts = data_parser.find_value( 'fftPts', param_list, value_list )
    fftSaveAllData = data_parser.find_value( 'fftSaveAllData', param_list, value_list )
    fftSaveOnePts = data_parser.find_value( 'fftSaveOnePts', param_list, value_list )

    if ( fftSaveOnePts ):
        fftPtIdx = data_parser.find_value( 'fftPtIdx', param_list, value_list )

    if ( fftSaveAllData ):
        file_name_prefix = 'tx_acq_'

        S11 = np.zeros( len( freqSw ) )
        S11_ph = np.zeros( len( freqSw ) )

        freqSamp = freq * 4  # defined by the C programming, (*4) is a fix number
        spect_bw = freq / fftPts * 2  # this is the frequency spacing between adjacent FFT point. Spect_bw is set so that only one point in searching will be found and it will be the closest frequency of interest

        # for m in freqSw:
        file_path = ( data_folder + file_name_prefix +
                     '{:4.3f}'.format( freq ) )

        # read the data
        one_scan_real = np.array( data_parser.read_data( 
                file_path + "_Re" ) )  # use ascii representation
        os.remove( file_path + "_Re" )  # delete the file after use

        one_scan_imag = np.array( data_parser.read_data( 
                file_path + "_Im" ) )  # use ascii representation
        os.remove( file_path + "_Im" )  # delete the file after use

        # find voltage at the input of ADC in mV
        one_scan_real = one_scan_real * nmrObj.uvoltPerDigit / 1e3 / fftPts
        one_scan_imag = one_scan_imag * nmrObj.uvoltPerDigit / 1e3 / fftPts

        # find the fft output
        # spectx, specty = nmr_fft( one_scan, freqSamp, 0 )
        specty = one_scan_real + np.multiply( 1j, one_scan_imag )
        spectx = np.linspace( -freqSamp / 2, freqSamp / 2, int( fftPts ) )

        # find the index of the excitation frequency
        ref_idx = ( abs( spectx - freq ) <= ( spect_bw ) )

        # compute amplitude at the frequency of interest
        S11 = abs( specty[np.where( ref_idx == True )[0][0] + 1] )  # +1 factor is to correct the shifted index by one when generating fft x-axis
        S11_ph = np.angle( specty[np.where( ref_idx == True )[0][0] + 1], deg = True )

    elif fftSaveOnePts:
        S11_ReIm = np.array( data_parser.read_data( data_folder + "spfft.txt" ) ) / fftPts
        S11_cmplx = S11_ReIm[0] + np.multiply( 1j, S11_ReIm[1] )
        S11 = abs( S11_cmplx )
        S11_ph = np.angle( S11_cmplx, deg = True )

    return S11_cmplx


def compute_wobble_fft_sync( nmrObj, data_parent_folder, meas_folder, s11_min, S11mV_ref, useRef, en_fig, fig_num ):

    # compute_wobble_sync uses 1 clock domain for the sampling clock and the excitation clock, just as it is in synchronized CPMG sequence. The sampling clock is 4x the excitation clock , and the system clock is 4x the sampling clock. The phase in compute_wobble_sync is usable.

    # S11mV_ref is the reference s11 corresponds to maximum reflection (can be made by totally untuning matching network, e.g. disconnecting all caps in matching network)
    # useRef uses the S11mV_ref as reference, otherwise it will use the max
    # signal available in the data

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )
    fftPts = data_parser.find_value( 'fftPts', param_list, value_list )
    fftSaveAllData = data_parser.find_value( 'fftSaveAllData', param_list, value_list )
    fftSaveOnePts = data_parser.find_value( 'fftSaveOnePts', param_list, value_list )

    if ( fftSaveOnePts ):
        fftPtIdx = data_parser.find_value( 'fftPtIdx', param_list, value_list )

    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )

    if ( fftSaveAllData ):
        file_name_prefix = 'tx_acq_'

        S11dB = np.zeros( len( freqSw ) )
        S11mV_ph = np.zeros( len( freqSw ) )
        S11mV_cpx = np.zeros( len( freqSw ), dtype = complex )
        for m in range( 0, len( freqSw ) ):
            freqSamp = freqSw[m] * 4  # defined by the C programming, (*4) is a fix number
            spect_bw = freqSw[m] / fftPts * 2  # this is the frequency spacing between adjacent FFT point. Spect_bw is set so that only one point in searching will be found and it will be the closest frequency of interest

            # for m in freqSw:
            file_path = ( data_folder + file_name_prefix +
                         '{:4.3f}'.format( freqSw[m] ) )

            # read the data
            one_scan_real = np.array( data_parser.read_data( 
                    file_path + "_Re" ) )  # use ascii representation
            os.remove( file_path + "_Re" )  # delete the file after use

            one_scan_imag = np.array( data_parser.read_data( 
                    file_path + "_Im" ) )  # use ascii representation
            os.remove( file_path + "_Im" )  # delete the file after use

            # find voltage at the input of ADC in mV
            one_scan_real = one_scan_real * nmrObj.uvoltPerDigit / 1e3 / fftPts
            one_scan_imag = one_scan_imag * nmrObj.uvoltPerDigit / 1e3 / fftPts

            # find the fft output
            # spectx, specty = nmr_fft( one_scan, freqSamp, 0 )
            specty = one_scan_real + np.multiply( 1j, one_scan_imag )
            spectx = np.linspace( -freqSamp / 2, freqSamp / 2, int( fftPts ) )

            # find the index of the excitation frequency
            ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw ) )

            # compute amplitude at the frequency of interest
            S11mV_cpx[m] = specty[np.where( ref_idx == True )[0][0] + 1]

    elif fftSaveOnePts:
        S11mV_re = np.array( data_parser.read_data( data_folder + "S21_fftReal.txt" ) ) * nmrObj.uvoltPerDigit / 1e3 / fftPts
        S11mV_im = np.array( data_parser.read_data( data_folder + "S21_fftImag.txt" ) ) * nmrObj.uvoltPerDigit / 1e3 / fftPts
        S11mV_cpx = S11mV_re + np.multiply( 1j, S11mV_im )

    if useRef:  # if reference is present
        S11 = S11mV_cpx / S11mV_ref
        S11dB = 20 * np.log10( abs( S11 ) )  # convert to dB scale
        S11ph = np.angle( S11, deg = True )
    else:  # if reference is not present
        S11 = S11mV_cpx
        S11dB = 20 * np.log10( abs( S11mV_cpx ) / max( abs( S11mV_cpx ) ) )  # convert to dB scale
        S11ph = np.angle( S11mV_cpx, deg = True )

    S11_min10dB = ( S11dB <= s11_min )

    minS11 = min( S11dB )
    minS11_freq = freqSw[np.argmin( S11dB )]

    try:
        S11_fmin = min( freqSw[S11_min10dB] )
        S11_fmax = max( freqSw[S11_min10dB] )
    except:
        S11_fmin = 0
        S11_fmax = 0
        # print( 'S11 requirement is not satisfied...' )

    S11_bw = S11_fmax - S11_fmin

    # compute impedance
    if useRef:
        # S11 = np.multiply( S11dB , np.exp( 1j * ( S11ph * 2 * np.pi / 360 ) ) )
        Z11 = ( 1 + S11 ) / ( 1 - S11 )

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num, figsize = [12, 7] )
        fig.clf()
        ax = fig.add_subplot( 221 )
        line1, = ax.plot( freqSw, S11dB, 'b-', marker = '.', linewidth = 1, markersize = 6 )
        ax.set_ylim( -60, 10 )
        ax.set_ylabel( 'S11dB [dB]' )
        ax.set_title( "Reflection Measurement (S11dB) Parameter" )
        ax.grid()

        bx = fig.add_subplot( 223 )
        bx.plot( freqSw, S11ph, 'r-' , marker = '.', linewidth = 1, markersize = 6 )
        bx.set_xlabel( 'Frequency [MHz]' )
        bx.set_ylabel( 'Phase (deg)' )
        # bx.set_title( 'incorrect phase due to non-correlated transmit and sampling' )
        bx.grid()

        if useRef:
            cx = fig.add_subplot ( 222 )
            cx.plot( freqSw, np.real( Z11 ), 'b', marker = '.', linewidth = 1, markersize = 6 )
            cx.set_ylim( -200, 200 )
            cx.set_ylabel ( 'Re(Z11/Zs)' )
            cx.set_title( "Normalized Impedance (Z11/Zs)" )
            cx.grid()

            dx = fig.add_subplot ( 224 )
            dx.plot( freqSw, np.imag( Z11 ), 'r', marker = '.', linewidth = 1, markersize = 6 )
            dx.set_ylim( -200, 200 )
            dx.set_ylabel ( 'Im(Z11/Zs)' )
            # dx.set_title( "Imaginary Impedance" )
            dx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'wobble.png' )

    # write S11dB to a file
    with open( data_folder + 'S11dB.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S11dB, S11ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    # print(S11_fmin, S11_fmax, S11_bw)
    if useRef:
        return S11, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq
    else:
        return S11, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq


def compute_wobble_sync( nmrObj, data_parent_folder, meas_folder, s11_min, S11mV_ref, useRef, en_fig, fig_num ):

    # compute_wobble_sync uses 1 clock domain for the sampling clock and the excitation clock, just as it is in synchronized CPMG sequence. The sampling clock is 4x the excitation clock , and the system clock is 4x the sampling clock. The phase in compute_wobble_sync is usable.

    # S11mV_ref is the reference s11 corresponds to maximum reflection (can be made by totally untuning matching network, e.g. disconnecting all caps in matching network)
    # useRef uses the S11mV_ref as reference, otherwise it will use the max
    # signal available in the data

    # settings
    # put 1 if the data file uses binary representation, otherwise it is in
    # ascii format. Find the setting in the C programming file
    binary_OR_ascii = 0  # manual setting: put the same setting from the C programming

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )

    file_name_prefix = 'tx_acq_'
    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )
    S11mV = np.zeros( len( freqSw ) )
    S11_ph = np.zeros( len( freqSw ) )
    for m in range( 0, len( freqSw ) ):
        freqSamp = freqSw[m] * 4
        spect_bw = ( freqSamp / nSamples ) * 1  # determining the RBW

        # for m in freqSw:
        file_path = ( data_folder + file_name_prefix +
                     '{:4.3f}'.format( freqSw[m] )+'_ReIm' )

        if binary_OR_ascii:
            # one_scan = data_parser.read_hex_int16(file_path)  # use binary
            # representation
            one_scan = data_parser.read_hex_int32( 
                file_path )  # use binary representation for 32-bit file
        else:
            one_scan = np.array( data_parser.read_data( 
                file_path ) )  # use ascii representation

        os.remove( file_path )  # delete the file after use

        # find voltage at the input of ADC in mV
        one_scan = one_scan * nmrObj.uvoltPerDigit / 1e3

        spectx, specty = nmr_fft( one_scan, freqSamp, 0 )

        # plt.figure( 12345 )
        # plt.plot( spectx, abs( specty ) )
        # plt.figure( 23451 )
        # plt.plot( spectx, np.angle( specty, deg=True ) )

        # FIND INDEX WHERE THE MAXIMUM SIGNAL IS PRESENT
        # PRECISE METHOD: find reflection at the desired frequency: creating precision problem where usually the signal shift a little bit from its desired frequency
        # ref_idx = abs(spectx - freqSw[m]) == min(abs(spectx - freqSw[m]))
        # BETTER METHOD: find reflection signal peak around the bandwidth
        ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw / 2 ) )

        # S11mV[m] = max( abs( specty[ref_idx] ) )  # find reflection peak
        # compute the mean of amplitude inside RBW
        # S11mV[m] = np.mean( abs( specty[ref_idx] ) )
        # S11_ph[m] = np.mean( np.angle( specty[ref_idx], deg=True ) )
        S11mV[m] = abs( specty[np.where( ref_idx == True )[0][0] + 1] )  # +1 factor is to correct the shifted index by one when generating fft x-axis
        S11_ph[m] = np.angle( specty[np.where( ref_idx == True )[0][0] + 1], deg = True )

    if useRef:  # if reference is present
        S11 = np.divide( S11mV, S11mV_ref )
        S11dB = 20 * np.log10( S11 )  # convert to dB scale
    else:  # if reference is not present
        S11 = S11mV / max( S11mV )
        S11dB = 20 * np.log10( S11 )  # convert to dB scale

    S11_min10dB = ( S11dB <= s11_min )

    minS11 = min( S11dB )
    minS11_freq = freqSw[np.argmin( S11dB )]

    try:
        S11_fmin = min( freqSw[S11_min10dB] )
        S11_fmax = max( freqSw[S11_min10dB] )
    except:
        S11_fmin = 0
        S11_fmax = 0
        print( 'S11 requirement is not satisfied...' )

    S11_bw = S11_fmax - S11_fmin

    # compute impedance
    if useRef:
        S11_cmplx = np.multiply( np.divide( S11mV, S11mV_ref ), np.exp( 1j * ( S11_ph * 2 * np.pi / 360 ) ) )
        Z11 = ( 1 + S11_cmplx ) / ( 1 - S11_cmplx )
    '''
        # interpolate to find the frequency where Re(Z11/Zs) is 1, or load impedance is approx. 50 Ohms
        Z11_maxidx = np.max( abs( np.real( Z11 ) ) ) == np.real( Z11 )
        Z11_maxidx = np.where( Z11_maxidx == True )[0][0]  # find index of resonance (max impedance)
        Z11_a = np.sign( np.real( Z11[0:Z11_maxidx] ) - 1 )  # find minimum point where Re(Z11/Zs)-1=0
        Z11_signidx = np.where( Z11_a == 1 )[0][0]
        den = ( freqSw[Z11_signidx] - freqSw[Z11_signidx - 1] )
        num = np.real( Z11[Z11_signidx] ) - np.real( Z11[Z11_signidx - 1] )
        freq0 = freqSw[Z11_signidx] - ( np.real( Z11[Z11_signidx] ) - 1 ) * den / num  # compute frequency where Z11/Zs = 1
        print( "freq0 : %f MHz" % freq0 )
        # find the value of Z11_imag at the frequency above
        num = np.imag( Z11[Z11_signidx] ) - np.imag( Z11[Z11_signidx - 1] )
        Z11_imag0 = num / den * ( freq0 - freqSw[Z11_signidx] ) + np.imag( Z11[Z11_signidx] )
        print( "Z11_imag0 : %f" % Z11_imag0 )

    else:
    '''
    freq0 = 0
    Z11_imag0 = 0

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num, figsize = [12, 7] )
        fig.clf()
        ax = fig.add_subplot( 221 )
        line1, = ax.plot( freqSw, S11dB, 'b-', marker = '.', linewidth = 1, markersize = 6 )
        ax.set_ylim( -35, 10 )
        ax.set_ylabel( 'S11 [dB]' )
        ax.set_title( "Reflection Measurement (S11) Parameter" )
        ax.grid()

        bx = fig.add_subplot( 223 )
        bx.plot( freqSw, S11_ph, 'r-' , marker = '.', linewidth = 1, markersize = 6 )
        bx.set_xlabel( 'Frequency [MHz]' )
        bx.set_ylabel( 'Phase (deg)' )
        # bx.set_title( 'incorrect phase due to non-correlated transmit and sampling' )
        bx.grid()

        if useRef:
            cx = fig.add_subplot ( 222 )
            cx.plot( freqSw, np.real( Z11 ), 'b', marker = '.', linewidth = 1, markersize = 6 )
            cx.set_ylim( -2, 2 )
            cx.set_ylabel ( 'Re(Z11/Zs)' )
            cx.set_title( "Normalized Impedance (Z11/Zs)" )
            cx.grid()

            dx = fig.add_subplot ( 224 )
            dx.plot( freqSw, np.imag( Z11 ), 'r', marker = '.', linewidth = 1, markersize = 6 )
            dx.set_ylim( -2, 2 )
            dx.set_ylabel ( 'Im(Z11/Zs)' )
            # dx.set_title( "Imaginary Impedance" )
            dx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'wobble.png' )

    # write S11mV to a file
    with open( data_folder + 'S11mV.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S11dB, S11_ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    # print(S11_fmin, S11_fmax, S11_bw)
    if useRef:
        return S11, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, freq0, Z11_imag0
    else:
        return S11mV, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, freq0, Z11_imag0


def compute_wobble_async( nmrObj, data_parent_folder, meas_folder, s11_min, S11mV_ref, useRef, en_fig, fig_num ):

    # compute_wobble_async uses 2 independent clocks, i.e. for the sampling clock and the excitation clock. The phase in compute_wobble_async is not usable.

    # S11mV_ref is the reference s11 corresponds to maximum reflection (can be made by totally untuning matching network, e.g. disconnecting all caps in matching network)
    # useRef uses the S11mV_ref as reference, otherwise it will use the max
    # signal available in the data

    # settings
    # put 1 if the data file uses binary representation, otherwise it is in
    # ascii format. Find the setting in the C programming file
    binary_OR_ascii = 1  # manual setting: put the same setting from the C programming
    
    en_indv_fig = 0 # enable individual figure for the measurement

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )
    freqSamp = data_parser.find_value( 'freqSamp', param_list, value_list )
    spect_bw = ( freqSamp / nSamples ) * 4  # determining the RBW

    file_name_prefix = 'tx_acq_'
    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )
    S11mV = np.zeros( len( freqSw ) )
    S11_ph = np.zeros( len( freqSw ) )
    for m in range( 0, len( freqSw ) ):
        # for m in freqSw:
        file_path = ( data_folder + file_name_prefix +
                     '{:4.3f}'.format( freqSw[m] ) )

        if binary_OR_ascii:
            # one_scan = data_parser.read_hex_int16(file_path)  # use binary
            # representation
            one_scan = data_parser.read_hex_int32( 
                file_path )  # use binary representation for 32-bit file
        else:
            one_scan = np.array( data_parser.read_data( 
                file_path ) )  # use ascii representation

        os.remove( file_path )  # delete the file after use

        # find voltage at the input of ADC in mV
        one_scan = one_scan * nmrObj.uvoltPerDigit / 1e3
        
        if en_indv_fig:
            plt.ion()
            fig = plt.figure( 10 )
            fig.clf()
            plt.plot( one_scan, 'r-' )
            # ax.set_ylabel( 'S11 [dB]' )
            # ax.set_title( "Reflection Measurement (S11) Parameter" )
            plt.grid()
    
            fig.canvas.draw()
            fig.canvas.flush_events()
    

        spectx, specty = nmr_fft( one_scan, freqSamp, 0 )
        
        if en_indv_fig:
            plt.ion()
            fig = plt.figure( 11 )
            # fig.clf()
            plt.plot( spectx,abs(specty) )
            # ax.set_ylabel( 'S11 [dB]' )
            # ax.set_title( "Reflection Measurement (S11) Parameter" )
            plt.grid()
    
            fig.canvas.draw()
            fig.canvas.flush_events()

        # FIND INDEX WHERE THE MAXIMUM SIGNAL IS PRESENT
        # PRECISE METHOD: find reflection at the desired frequency: creating precision problem where usually the signal shift a little bit from its desired frequency
        # ref_idx = abs(spectx - freqSw[m]) == min(abs(spectx - freqSw[m]))
        # BETTER METHOD: find reflection signal peak around the bandwidth
        ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw / 2 ) )

        # S11mV[m] = max( abs( specty[ref_idx] ) )  # find reflection peak
        # compute the mean of amplitude inside RBW
        S11mV[m] = np.mean( abs( specty[ref_idx] ) )
        S11_ph[m] = np.mean( np.angle( specty[ref_idx] ) ) * ( 360 / ( 2 * np.pi ) )

    if useRef:  # if reference is present
        S11 = np.divide( S11mV, S11mV_ref )
        S11dB = 20 * np.log10( S11 )  # convert to dB scale
    else:  # if reference is not present
        S11 = S11mV / max( S11mV )
        S11dB = 20 * np.log10( S11 )  # convert to dB scale

    S11_min10dB = ( S11dB <= s11_min )

    minS11 = min( S11dB )
    minS11_freq = freqSw[np.argmin( S11dB )]

    try:
        S11_fmin = min( freqSw[S11_min10dB] )
        S11_fmax = max( freqSw[S11_min10dB] )
    except:
        S11_fmin = 0
        S11_fmax = 0
        print( 'S11 requirement is not satisfied...' )

    S11_bw = S11_fmax - S11_fmin

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )
        fig.clf()
        ax = fig.add_subplot( 211 )
        line1, = ax.plot( freqSw, S11dB, 'r-' )
        ax.set_ylim( -60, 10 )
        ax.set_ylabel( 'S11 [dB]' )
        ax.set_title( "Reflection Measurement (S11) Parameter" )
        ax.grid()

        bx = fig.add_subplot( 212 )
        bx.plot( freqSw, S11_ph, 'r-' )
        bx.set_xlabel( 'Frequency [MHz]' )
        bx.set_ylabel( 'Phase (deg)' )
        bx.set_title( 
            'incorrect phase due to non-correlated transmit and sampling' )
        bx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'wobble.png' )

    # write S11mV to a file
    with open( data_folder + 'S11mV.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S11dB, S11_ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    # print(S11_fmin, S11_fmax, S11_bw)
    if useRef:
        return S11, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq
    else:
        return S11mV, S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq


def compute_gain_sync( nmrObj, data_parent_folder, meas_folder, en_fig, fig_num ):
    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    # settings
    # put 1 if the data file uses binary representation, otherwise it is in
    # ascii format. Find the setting in the C programming file
    binary_OR_ascii = 1  # manual setting: put the same setting from the C programming

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )
    # freqSamp = data_parser.find_value( 'freqSamp', param_list, value_list )
    # spect_bw = ( freqSamp / nSamples ) * 4  # determining the RBW

    file_name_prefix = 'tx_acq_'
    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )
    S21 = np.zeros( len( freqSw ) )
    S21_ph = np.zeros( len( freqSw ) )
    for m in range( 0, len( freqSw ) ):
        freqSamp = freqSw[m] * 4  # defined by the C programming, (*4) is a fix number
        spect_bw = ( freqSamp / nSamples ) * 1  # determining the RBW

        # for m in freqSw:
        file_path = ( data_folder + file_name_prefix +
                     '{:4.3f}'.format( freqSw[m] ) )

        if binary_OR_ascii:
            # one_scan = data_parser.read_hex_int16(file_path)  # use binary
            # representation
            one_scan = data_parser.read_hex_int32( 
                file_path )  # use binary representation for 32-bit file
        else:
            one_scan = np.array( data_parser.read_data( 
                file_path ) )  # use ascii representation

        os.remove( file_path )  # delete the file after use

        '''
        plt.ion()
        fig = plt.figure( 64 )
        fig.clf()
        ax = fig.add_subplot( 111 )
        ax.plot( one_scan )
        fig.canvas.draw()
        fig.canvas.flush_events()
        '''

        # find voltage at the input of ADC in mV
        one_scan = one_scan * nmrObj.uvoltPerDigit / 1e3

        spectx, specty = nmr_fft( one_scan, freqSamp, 0 )

        # plt.figure( 12345 )
        # plt.clf()
        # plt.plot( abs( specty ) )
        # plt.show()

        # FIND INDEX WHERE THE MAXIMUM SIGNAL IS PRESENT
        # PRECISE METHOD: find reflection at the desired frequency: creating precision problem where usually the signal shift a little bit from its desired frequency
        # ref_idx = abs(spectx - freqSw[m]) == min(abs(spectx - freqSw[m]))
        # BETTER METHOD: find reflection signal peak around the bandwidth
        # divide 2 is due to +/- half-BW around the interested frequency
        ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw / 2 ) )

        # compute amplitude at the frequency of interest
        S21[m] = abs( specty[np.where( ref_idx == True )[0][0] + 1] )  # +1 factor is to correct the shifted index by one when generating fft x-axis
        S21_ph[m] = np.angle( specty[np.where( ref_idx == True )[0][0] + 1], deg = True )

    S21dB = 20 * np.log10( S21 )  # convert to dBmV scale

    maxS21 = max( S21dB )
    maxS21_freq = freqSw[np.argmax( S21dB )]
    maxS21_ph = S21_ph[np.argmax( S21dB )]
    S21_in_bw_range = ( S21dB >= ( maxS21 - 3 ) )
    S21_in_bw_idx = np.where( S21_in_bw_range == True )
    S21_lo_bound = freqSw[np.min( S21_in_bw_idx )]
    S21_hi_bound = freqSw[np.max( S21_in_bw_idx )]
    S21_lo_phase = S21_ph[np.min( S21_in_bw_idx )]
    S21_hi_phase = S21_ph[np.max( S21_in_bw_idx )]

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )
        fig.clf()
        ax = fig.add_subplot( 211 )
        line1, = ax.plot( freqSw, S21dB, 'r-' )
        ax.set_ylim( -30, 80 )
        ax.set_ylabel( 'S21 [dBmV]' )
        ax.set_title( "S21: %0.1f dBmV @%0.3f MHz, BW=%0.0f kHz, ph=%0.0f$\degree$" % ( maxS21, maxS21_freq, ( S21_hi_bound - S21_lo_bound ) * 1e3 , maxS21_ph ) )
        ax.grid()

        bx = fig.add_subplot( 212 )
        bx.plot( freqSw, S21_ph, 'r-' )
        bx.set_xlabel( 'Frequency [MHz]' )
        bx.set_ylabel( 'Phase (deg)' )
        bx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'gain.png' )

    # write gain values to a file
    with open( data_folder + 'S21.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S21dB, S21_ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    return maxS21, maxS21_freq, S21


def compute_gain_fft_sync( nmrObj, data_parent_folder, meas_folder, en_fig, fig_num ):
    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )
    fftPts = data_parser.find_value( 'fftPts', param_list, value_list )
    fftSaveAllData = data_parser.find_value( 'fftSaveAllData', param_list, value_list )
    fftSaveOnePts = data_parser.find_value( 'fftSaveOnePts', param_list, value_list )

    if ( fftSaveOnePts ):
        fftPtIdx = data_parser.find_value( 'fftPtIdx', param_list, value_list )

    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )

    if ( fftSaveAllData ):
        file_name_prefix = 'tx_acq_'

        S21 = np.zeros( len( freqSw ) )
        S21_ph = np.zeros( len( freqSw ) )
        for m in range( 0, len( freqSw ) ):
            freqSamp = freqSw[m] * 4  # defined by the C programming, (*4) is a fix number
            spect_bw = freqSw[m] / fftPts * 2  # this is the frequency spacing between adjacent FFT point. Spect_bw is set so that only one point in searching will be found and it will be the closest frequency of interest

            # for m in freqSw:
            file_path = ( data_folder + file_name_prefix +
                         '{:4.3f}'.format( freqSw[m] ) )

            # read the data
            one_scan_real = np.array( data_parser.read_data( 
                    file_path + "_Re" ) )  # use ascii representation
            os.remove( file_path + "_Re" )  # delete the file after use

            one_scan_imag = np.array( data_parser.read_data( 
                    file_path + "_Im" ) )  # use ascii representation
            os.remove( file_path + "_Im" )  # delete the file after use

            # find voltage at the input of ADC in mV
            one_scan_real = one_scan_real * nmrObj.uvoltPerDigit / 1e3 / fftPts
            one_scan_imag = one_scan_imag * nmrObj.uvoltPerDigit / 1e3 / fftPts

            # find the fft output
            # spectx, specty = nmr_fft( one_scan, freqSamp, 0 )
            specty = one_scan_real + np.multiply( 1j, one_scan_imag )
            spectx = np.linspace( -freqSamp / 2, freqSamp / 2, int( fftPts ) )

            # find the index of the excitation frequency
            ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw ) )

            # compute amplitude at the frequency of interest
            S21[m] = abs( specty[np.where( ref_idx == True )[0][0] + 1] )  # +1 factor is to correct the shifted index by one when generating fft x-axis
            S21_ph[m] = np.angle( specty[np.where( ref_idx == True )[0][0] + 1], deg = True )

    elif fftSaveOnePts:
        S21_re = np.array( data_parser.read_data( data_folder + "S21_fftReal.txt" ) ) / fftPts
        S21_im = np.array( data_parser.read_data( data_folder + "S21_fftImag.txt" ) ) / fftPts
        S21_cmplx = S21_re + np.multiply( 1j, S21_im )
        S21 = abs( S21_cmplx )
        S21_ph = np.angle( S21_cmplx, deg = True )

    S21dB = 20 * np.log10( S21 )  # convert to dBmV scale

    maxS21dB = max( S21dB )
    maxS21_freq = freqSw[np.argmax( S21dB )]
    maxS21_ph = S21_ph[np.argmax( S21dB )]
    S21_in_bw_range = ( S21dB >= ( maxS21dB - 3 ) )
    S21_in_bw_idx = np.where( S21_in_bw_range == True )
    S21_lo_bound = freqSw[np.min( S21_in_bw_idx )]
    S21_hi_bound = freqSw[np.max( S21_in_bw_idx )]
    S21_lo_phase = S21_ph[np.min( S21_in_bw_idx )]
    S21_hi_phase = S21_ph[np.max( S21_in_bw_idx )]

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )
        fig.clf()
        ax = fig.add_subplot( 211 )
        line1, = ax.plot( freqSw, S21dB, 'r-' )
        ax.set_ylim( -30, 80 )
        ax.set_ylabel( 'S21 [dBmV]' )
        ax.set_title( "S21: %0.1f dBmV @%0.3f MHz, BW=%0.0f kHz, ph=%0.0f$\degree$" % ( maxS21dB, maxS21_freq, ( S21_hi_bound - S21_lo_bound ) * 1e3 , maxS21_ph ) )
        ax.grid()

        bx = fig.add_subplot( 212 )
        bx.plot( freqSw, S21_ph, 'r-' )
        bx.set_xlabel( 'Frequency [MHz]' )
        bx.set_ylabel( 'Phase (deg)' )
        bx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'gainFFT.png' )

    # write gain values to a file
    with open( data_folder + 'S21.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S21dB, S21_ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    return maxS21dB, maxS21_freq, S21


def compute_gain_async( nmrObj, data_parent_folder, meas_folder, en_fig, fig_num ):
    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    # settings
    # put 1 if the data file uses binary representation, otherwise it is in
    # ascii format. Find the setting in the C programming file
    binary_OR_ascii = 1  # manual setting: put the same setting from the C programming

    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    freqSta = data_parser.find_value( 'freqSta', param_list, value_list )
    freqSto = data_parser.find_value( 'freqSto', param_list, value_list )
    freqSpa = data_parser.find_value( 'freqSpa', param_list, value_list )
    nSamples = data_parser.find_value( 'nSamples', param_list, value_list )
    freqSamp = data_parser.find_value( 'freqSamp', param_list, value_list )
    spect_bw = ( freqSamp / nSamples ) * 4  # determining the RBW

    file_name_prefix = 'tx_acq_'
    # plus freqSpa/2 is to include the endpoint (just like what the C does)
    freqSw = np.arange( freqSta, freqSto + ( freqSpa / 2 ), freqSpa )
    S21 = np.zeros( len( freqSw ) )
    S21_ph = np.zeros( len( freqSw ) )
    for m in range( 0, len( freqSw ) ):
        # for m in freqSw:
        file_path = ( data_folder + file_name_prefix +
                     '{:4.3f}'.format( freqSw[m] ) )

        if binary_OR_ascii:
            # one_scan = data_parser.read_hex_int16(file_path)  # use binary
            # representation
            one_scan = data_parser.read_hex_int32( 
                file_path )  # use binary representation for 32-bit file
        else:
            one_scan = np.array( data_parser.read_data( 
                file_path ) )  # use ascii representation

        os.remove( file_path )  # delete the file after use

        '''
        plt.ion()
        fig = plt.figure( 64 )
        fig.clf()
        ax = fig.add_subplot( 111 )
        ax.plot( one_scan )
        fig.canvas.draw()
        fig.canvas.flush_events()
        '''

        # find voltage at the input of ADC in mV
        one_scan = one_scan * nmrObj.uvoltPerDigit / 1e3

        spectx, specty = nmr_fft( one_scan, freqSamp, 0 )

        # FIND INDEX WHERE THE MAXIMUM SIGNAL IS PRESENT
        # PRECISE METHOD: find reflection at the desired frequency: creating precision problem where usually the signal shift a little bit from its desired frequency
        # ref_idx = abs(spectx - freqSw[m]) == min(abs(spectx - freqSw[m]))
        # BETTER METHOD: find reflection signal peak around the bandwidth
        # divide 2 is due to +/- half-BW around the interested frequency
        ref_idx = ( abs( spectx - freqSw[m] ) <= ( spect_bw / 2 ) )

        # compute the mean of amplitude inside RBW
        S21[m] = np.mean( abs( specty[ref_idx] ) )
        # compute the angle mean. Currently it is not useful because the phase
        # is not preserved in the sequence
        S21_ph[m] = np.mean( np.angle( specty[ref_idx] ) ) * ( 360 / ( 2 * np.pi ) )

    S21dB = 20 * np.log10( S21 )  # convert to dBmV scale

    maxS21 = max( S21dB )
    maxS21_freq = freqSw[np.argmax( S21dB )]

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )
        fig.clf()
        ax = fig.add_subplot( 111 )
        line1, = ax.plot( freqSw, S21dB, 'r-' )
        ax.set_ylim( -30, 80 )
        ax.set_ylabel( 'S21 [dBmV]' )
        ax.set_title( "Transmission Measurement (S21) Parameter" )
        ax.grid()

        # bx = fig.add_subplot( 212 )
        # bx.plot( freqSw, S21_ph, 'r-' )
        # bx.set_xlabel( 'Frequency [MHz]' )
        # bx.set_ylabel( 'Phase (deg)' )
        # bx.set_title( 'incorrect phase due to non-correlated transmit and sampling' )
        # bx.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        plt.savefig( data_folder + 'gain.png' )

    # write gain values to a file
    with open( data_folder + 'S21.txt', 'w' ) as f:
        for ( a, b, c ) in zip( freqSw, S21dB, S21_ph ):
            f.write( '{:-8.3f},{:-8.3f},{:-7.1f}\n' .format( a, b, c ) )

    return maxS21, maxS21_freq, S21


def compute_multiple( nmrObj, data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, direct_read, datain, dconv_lpf_ord, dconv_lpf_cutoff_kHz ):

    # variables to be input
    # nmrObj            : the hardware definition
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # filename_prefix   : the name of data prefix
    # Df                : data frequency
    # Sf                : sample frequency
    # tE                : echo spacing
    # total_scan        : number_of_iteration
    # en_fig            : enable figure
    # en_ext_param      : enable external parameter for data signal processing
    # thetaref          : external parameter : rotation angle
    # echoref_avg        : external parameter : echo average reference
    # datain            : the data captured direct reading. data format: AC,averaged scans, phase-cycled
    # direct_read        : perform direct reading from SDRAM/FIFO

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )

    # variables local to this function
    # the setting file for the measurement
    mtch_fltr_sta_idx = 0  # 0 is default or something referenced to SpE, e.g. SpE/4; the start index for match filtering is to neglect ringdown part from calculation
    # perform rotation to the data -> required for reference data for t1
    # measurement
    perform_rotation = 1
    # process individual raw data, otherwise it'll load a sum file generated
    # by C
    proc_indv_data = 0
    # put 1 if the data file uses binary representation, otherwise it is in
    # ascii format
    binary_OR_ascii = 0
    ignore_echoes = 2  # ignore initial echoes #

    # simulate decimation in software (DO NOT use this for normal operation,
    # only for debugging purpose)
    sim_dec = 0
    sim_dec_fact = 32

    compute_figure = True  # compute the figure and save the figure to file. To show it in runtime, enable the en_fig

    # variables from NMR settings
    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    SpE = int( data_parser.find_value( 'nrPnts', param_list, value_list ) )
    NoE = int( data_parser.find_value( 'nrEchoes', param_list, value_list ) )
    en_ph_cycle_proc = data_parser.find_value( 
        'usePhaseCycle', param_list, value_list )
    # tE = data_parser.find_value('echoTimeRun', param_list, value_list)
    # Sf = data_parser.find_value(
    #    'adcFreq', param_list, value_list) * 1e6
    # Df = data_parser.find_value(
    #    'b1Freq', param_list, value_list) * 1e6
    # total_scan = int(data_parser.find_value(
    #    'nrIterations', param_list, value_list))
    fpga_dconv = data_parser.find_value( 'fpgaDconv', param_list, value_list )
    dconv_fact = data_parser.find_value( 'dconvFact', param_list, value_list )
    echo_skip = data_parser.find_value( 'echoSkipHw', param_list, value_list )

    # account for skipped echoes
    NoE = int( NoE / echo_skip )
    tE = tE * echo_skip

    # compensate for dconv_fact if fpga dconv is used
    if fpga_dconv:
        SpE = int( SpE / dconv_fact )
        Sf = Sf / dconv_fact

    # ignore echoes
    if ignore_echoes:
        NoE = NoE - ignore_echoes

    # time domain for plot
    tacq = ( 1 / Sf ) * 1e6 * np.linspace( 1, SpE, SpE )  # in uS
    t_echospace = tE / 1e6 * np.linspace( 1, NoE, NoE )  # in uS

    if fpga_dconv:  # use fpga dconv
        # load IQ data
        file_path = ( data_folder + 'dconv' )

        if binary_OR_ascii:
            dconv = data_parser.read_hex_float( 
                file_path )  # use binary representation
        else:
            dconv = np.array( data_parser.read_data( file_path )
                             )  # use ascii representation

        if ignore_echoes:
            dconv = dconv[ignore_echoes * 2 * SpE:len( dconv )]

        # normalize the data
        # normalize with decimation factor (due to sum in the fpga)
        dconv = dconv / dconv_fact
        dconv = dconv / nmrObj.fir_gain  # normalize with the FIR gain in the fpga
        # convert to voltage unit at the probe
        dconv = dconv / nmrObj.totGain * nmrObj.uvoltPerDigit
        # scale all the data to magnitude of sin(45). The FPGA uses unity
        # magnitude (instead of sin45,135,225,315) to simplify downconversion
        # operation
        dconv = dconv * nmrObj.dconv_gain

        # combined IQ
        data_filt = np.zeros( ( NoE, SpE ), dtype = complex )
        for i in range( 0, NoE ):
            data_filt[i, :] = \
                dconv[i * ( 2 * SpE ):( i + 1 ) * ( 2 * SpE ):2] + 1j * \
                dconv[i * ( 2 * SpE ) + 1:( i + 1 ) * ( 2 * SpE ):2]

        if compute_figure:  # plot the averaged scan
            echo_space = ( 1 / Sf ) * np.linspace( 1, SpE, SpE )  # in s
            plt.figure( 1 )
            plt.clf()
            for i in range( 0, NoE ):
                plt.plot( ( ( i - 1 ) * tE * 1e-6 + echo_space ) * 1e3,
                         np.real( data_filt[i, :] ), linewidth = 0.4, color = 'b' )
                plt.plot( ( ( i - 1 ) * tE * 1e-6 + echo_space ) * 1e3,
                         np.imag( data_filt[i, :] ), linewidth = 0.4, color = 'r' )
            plt.title( "Averaged raw data (downconverted)" )
            plt.xlabel( 'time(ms)' )
            plt.ylabel( 'probe voltage (uV)' )
            plt.savefig( data_folder + '.png' )

        # raw average data
        echo_rawavg = np.mean( data_filt, axis = 0 )

        if compute_figure:  # plot echo rawavg
            plt.figure( 6 )
            plt.clf()
            plt.plot( tacq, np.real( echo_rawavg ), label = 'real' )
            plt.plot( tacq, np.imag( echo_rawavg ), label = 'imag' )
            plt.plot( tacq, np.abs( echo_rawavg ), label = 'abs' )
            plt.xlim( 0, max( tacq ) )
            plt.title( "Echo Average before rotation (down-converted)" )
            plt.xlabel( 'time(uS)' )
            plt.ylabel( 'probe voltage (uV)' )
            plt.legend()
            plt.savefig( data_folder + 'fig_echo_avg_dconv.png' )

        # simulate additional decimation (not needed for normal operqtion). For
        # debugging purpose
        if ( sim_dec ):
            SpE = int( SpE / sim_dec_fact )
            Sf = Sf / sim_dec_fact
            data_filt_dec = np.zeros( ( NoE, SpE ), dtype = complex )
            for i in range( 0, SpE ):
                data_filt_dec[:, i] = np.mean( 
                    data_filt[:, i * sim_dec_fact:( i + 1 ) * sim_dec_fact], axis = 1 )
            data_filt = np.zeros( ( NoE, SpE ), dtype = complex )
            data_filt = data_filt_dec
            tacq = ( 1 / Sf ) * 1e6 * np.linspace( 1, SpE, SpE )  # in uS

    else:
        # do down conversion locally
        if ( direct_read ):
            data = datain
        else:
            if ( proc_indv_data ):
                # read all datas and average it
                data = np.zeros( NoE * SpE )
                for m in range( 1, total_scan + 1 ):
                    file_path = ( data_folder + file_name_prefix +
                                 '{0:03d}'.format( m ) )
                    # read the data from the file and store it in numpy array
                    # format
                    one_scan = np.array( data_parser.read_data( file_path ) )
                    one_scan = ( one_scan - np.mean( one_scan ) ) / \
                        total_scan  # remove DC component
                    if ( en_ph_cycle_proc ):
                        if ( m % 2 ):  # phase cycling every other scan
                            data = data - one_scan
                        else:
                            data = data + one_scan
                    else:
                        data = data + one_scan
            else:
                # read sum data only
                file_path = ( data_folder + 'asum' )
                data = np.zeros( NoE * SpE )

                if binary_OR_ascii:
                    data = data_parser.read_hex_float( 
                        file_path )  # use binary representation
                else:
                    # use ascii representation
                    data = np.array( data_parser.read_data( file_path ) )

                dataraw = data
                data = ( data - np.mean( data ) )

        # ignore echoes
        if ignore_echoes:
            data = data[ignore_echoes * SpE:len( data )]

        # compute the probe voltage before gain stage
        data = data / nmrObj.totGain * nmrObj.uvoltPerDigit

        if compute_figure:  # plot the averaged scan
            echo_space = ( 1 / Sf ) * np.linspace( 1, SpE, SpE )  # in s
            plt.figure( 1 )
            plt.clf()
            for i in range( 1, NoE + 1 ):
                # plt.plot(((i - 1) * tE * 1e-6 + echo_space) * 1e3, data[(i - 1) * SpE:i * SpE], linewidth=0.4)
                plt.plot( ( ( i - 1 ) * tE * 1e-6 + echo_space ) * 1e3,
                         dataraw[( i - 1 ) * SpE:i * SpE], linewidth = 0.4 )
            plt.title( "Averaged raw data" )
            plt.xlabel( 'time(ms)' )
            plt.ylabel( 'probe voltage (uV)' )
            plt.savefig( data_folder + '.png' )

        # raw average data
        echo_rawavg = np.zeros( SpE, dtype = float )
        for i in range( 0, NoE ):
            echo_rawavg += ( data[i * SpE:( i + 1 ) * SpE] / NoE )

        if compute_figure:  # plot echo rawavg
            plt.figure( 6 )
            plt.clf()
            plt.plot( tacq, echo_rawavg, label = 'echo rawavg' )
            plt.xlim( 0, max( tacq ) )
            plt.title( "Echo Average (raw)" )
            plt.xlabel( 'time(uS)' )
            plt.ylabel( 'probe voltage (uV)' )
            plt.legend()
            plt.savefig( data_folder + 'fig_echo_avg.png' )

        # filter the data
        data_filt = np.zeros( ( NoE, SpE ), dtype = complex )
        for i in range( 0, NoE ):
            data_filt[i, :] = down_conv( 
                data[i * SpE:( i + 1 ) * SpE], i, tE, Df, Sf, dconv_lpf_ord, dconv_lpf_cutoff_kHz * 1e3 )

        # simulate additional decimation (not needed for normal operqtion). For
        # debugging purpose
        if ( sim_dec ):
            SpE = int( SpE / sim_dec_fact )
            Sf = Sf / sim_dec_fact
            data_filt_dec = np.zeros( ( NoE, SpE ), dtype = complex )
            for i in range( 0, SpE ):
                data_filt_dec[:, i] = np.sum( 
                    data_filt[:, i * sim_dec_fact:( i + 1 ) * sim_dec_fact], axis = 1 )
            data_filt = np.zeros( ( NoE, SpE ), dtype = complex )
            data_filt = data_filt_dec
            tacq = ( 1 / Sf ) * 1e6 * np.linspace( 1, SpE, SpE )  # in uS

    # scan rotation
    if en_ext_param:
        data_filt = data_filt * np.exp( -1j * thetaref )
        theta = math.atan2( np.sum( np.imag( data_filt ) ),
                           np.sum( np.real( data_filt ) ) )
    else:
        theta = math.atan2( np.sum( np.imag( data_filt ) ),
                           np.sum( np.real( data_filt ) ) )
        if perform_rotation:
            data_filt = data_filt * np.exp( -1j * theta )

    if compute_figure:  # plot filtered data
        echo_space = ( 1 / Sf ) * np.linspace( 1, SpE, SpE )  # in s
        plt.figure( 2 )
        plt.clf()

        data_parser.write_text_append( data_folder, "fig_filt_data.txt", "settings: NoE: %d, SpE: %d, tE: %0.2f, fs: %0.2f. Format: re(echo1), im(echo1), re(echo2), im(echo2), ... " % ( NoE, SpE, tE, Sf ) )

        for i in range( 0, NoE ):
            plt.plot( ( i * tE * 1e-6 + echo_space ) * 1e3,
                     np.real( data_filt[i, :] ), 'b', linewidth = 0.4 )
            plt.plot( ( i * tE * 1e-6 + echo_space ) * 1e3,
                     np.imag( data_filt[i, :] ), 'r', linewidth = 0.4 )

        for i in range ( 0, NoE ):
            data_parser.write_text_append_row( data_folder, "fig_filt_data.txt", np.real( data_filt[i, :] ) )
            data_parser.write_text_append_row( data_folder, "fig_filt_data.txt", np.imag( data_filt[i, :] ) )

        plt.legend()
        plt.title( 'Filtered data' )
        plt.xlabel( 'Time (mS)' )
        plt.ylabel( 'probe voltage (uV)' )
        plt.savefig( data_folder + 'fig_filt_data.png' )

    # find echo average, echo magnitude
    echo_avg = np.zeros( SpE, dtype = complex )
    for i in range( 0, NoE ):
        echo_avg += ( data_filt[i, :] / NoE )

    if compute_figure:  # plot echo shape
        plt.figure( 3 )
        plt.clf()
        plt.plot( tacq, np.abs( echo_avg ), label = 'abs' )
        plt.plot( tacq, np.real( echo_avg ), label = 'real part' )
        plt.plot( tacq, np.imag( echo_avg ), label = 'imag part' )
        plt.xlim( 0, max( tacq ) )
        plt.title( "Echo Shape" )
        plt.xlabel( 'time(uS)' )
        plt.ylabel( 'probe voltage (uV)' )
        plt.legend()
        plt.savefig( data_folder + 'fig_echo_shape.png' )
        data_parser.write_text_append( data_folder, "fig_echo_shape.txt", "format: abs, real, imag, time_us" )
        data_parser.write_text_append_row( data_folder, "fig_echo_shape.txt", np.abs( echo_avg ) )
        data_parser.write_text_append_row( data_folder, "fig_echo_shape.txt", np.real( echo_avg ) )
        data_parser.write_text_append_row( data_folder, "fig_echo_shape.txt", np.imag( echo_avg ) )
        data_parser.write_text_append_row( data_folder, "fig_echo_shape.txt", tacq )

        # plot fft of the echosum
        plt.figure( 4 )
        plt.clf()
        zf = 100  # zero filling factor to get smooth curve
        ws = 2 * np.pi / ( tacq[1] - tacq[0] )  # in MHz
        wvect = np.linspace( -ws / 2, ws / 2, len( tacq ) * zf )
        echo_zf = np.zeros( zf * len( echo_avg ), dtype = complex )
        echo_zf[int( ( zf / 2 ) * len( echo_avg ) - len( echo_avg ) / 2 ): int( ( zf / 2 ) * len( echo_avg ) + len( echo_avg ) / 2 )] = echo_avg
        spect = zf * ( np.fft.fftshift( np.fft.fft( np.fft.ifftshift( echo_zf ) ) ) )
        spect = spect / len( spect )  # normalize the spectrum
        plt.plot( wvect / ( 2 * np.pi ), np.real( spect ),
                 label = 'real' )
        plt.plot( wvect / ( 2 * np.pi ), np.imag( spect ),
                 label = 'imag' )
        plt.xlim( 10 / max( tacq ) * -1, 10 / max( tacq ) * 1 )
        plt.title( "FFT of the echo-sum. " + "Peak:real@{:0.2f}kHz,abs@{:0.2f}kHz".format( wvect[np.abs( np.real( spect ) ) == max( 
            np.abs( np.real( spect ) ) )][0] / ( 2 * np.pi ) * 1e3, wvect[np.abs( spect ) == max( np.abs( spect ) )][0] / ( 2 * np.pi ) * 1e3 ) )
        plt.xlabel( 'offset frequency(MHz)' )
        plt.ylabel( 'Echo amplitude (a.u.)' )
        plt.legend()
        plt.savefig( data_folder + 'fig_echo_A.png' )
        data_parser.write_text_append( data_folder, "fig_echo_A.txt", "format: real, imag, freq_MHz" )
        data_parser.write_text_append_row( data_folder, "fig_echo_A.txt", np.real( spect ) )
        data_parser.write_text_append_row( data_folder, "fig_echo_A.txt", np.imag( spect ) )
        data_parser.write_text_append_row( data_folder, "fig_echo_A.txt", wvect / ( 2 * np.pi ) )

    # matched filtering
    a = np.zeros( NoE, dtype = complex )
    for i in range( 0, NoE ):
        if en_ext_param:
            a[i] = np.mean( np.multiply( data_filt[i, mtch_fltr_sta_idx:SpE], np.conj( 
                echoref_avg[mtch_fltr_sta_idx:SpE] ) ) )  # find amplitude with reference matched filtering
        else:
            a[i] = np.mean( np.multiply( data_filt[i, mtch_fltr_sta_idx:SpE], np.conj( 
                echo_avg[mtch_fltr_sta_idx:SpE] ) ) )  # find amplitude with matched filtering

    a_integ = np.sum( np.real( a ) )

    # def exp_func(x, a, b, c, d):
    #    return a * np.exp(-b * x) + c * np.exp(-d * x)
    def exp_func( x, a, b ):
        return a * np.exp( -b * x )

    # average the first 5% of datas
    a_guess = np.mean( np.real( a[0:int( np.round( SpE / 20 ) )] ) )
    # c_guess = a_guess
    # find min idx value where the value of (a_guess/exp) is larger than
    # real(a)
    # b_guess = np.where(np.real(a) == np.min(
    #    np.real(a[np.real(a) > a_guess / np.exp(1)])))[0][0] * tE / 1e6
    # this is dummy b_guess, use the one I made above this for smarter one
    # (but sometimes it doesn't work)
    b_guess = 0.01
    # d_guess = b_guess
    # guess = np.array([a_guess, b_guess, c_guess, d_guess])
    guess = np.array( [a_guess, b_guess] )

    try:  # try fitting data
        popt, pocv = curve_fit( exp_func, t_echospace, np.real( a ), guess )

        # obtain fitting parameter
        a0 = popt[0]
        T2 = 1 / popt[1]

        # Estimate SNR/echo/scan
        f = exp_func( t_echospace, *popt )  # curve fit
        noise = np.std( np.imag( a ) )
        res = np.std( np.real( a ) - f )
        snr_imag = a0 / ( noise * math.sqrt( total_scan ) )
        snr_res = a0 / ( res * math.sqrt( total_scan ) )
        snr = snr_imag

        # plot fitted line
        plt.figure( 5 )
        plt.clf()
        plt.cla()
        plt.plot( t_echospace * 1e3, f, label = "fit" )  # plot in milisecond
        plt.plot( t_echospace * 1e3, np.real( a ) - f, label = "residue" )

    except:
        print( 'Problem in fitting. Set a0 and T2 output to 0\n' )
        a0 = 0
        T2 = 0
        noise = 0
        res = 0
        snr = 0

    if compute_figure:
        # plot data
        plt.figure( 5 )
        # plot in milisecond
        plt.plot( t_echospace * 1e3, np.real( a ), label = "real" )
        # plot in milisecond
        plt.plot( t_echospace * 1e3, np.imag( a ), label = "imag" )

        # plt.set(gca, 'FontSize', 12)
        plt.legend()
        plt.title( 'Matched filtered data. SNRim:{:03.2f} SNRres:{:03.2f}.\na:{:0.3f} n_im:{:0.4f} n_res:{:0.4f} T2:{:0.2f}msec'.format( 
            snr, snr_res, a0, ( noise * math.sqrt( total_scan ) ), ( res * math.sqrt( total_scan ) ), T2 * 1e3 ) )
        plt.xlabel( 'Time (mS)' )
        plt.ylabel( 'probe voltage (uV)' )
        plt.savefig( data_folder + 'fig_matched_filt_data.png' )

        data_parser.write_text_append( data_folder, "fig_matched_filt_data.txt", "output params: noise std: %0.5f, res std: %0.5f, snr_imag: %0.3f, snr_res: %0.3f, a0: %0.3f, T2: %0.3f ms. Format: a_real, a_imag, fit, time(s) " % ( noise, res, snr_imag, snr_res, a0, T2 * 1e3 ) )
        data_parser.write_text_append_row( data_folder, "fig_matched_filt_data.txt", np.real( a ) )
        data_parser.write_text_append_row( data_folder, "fig_matched_filt_data.txt", np.imag( a ) )
        data_parser.write_text_append_row( data_folder, "fig_matched_filt_data.txt", f )
        data_parser.write_text_append_row( data_folder, "fig_matched_filt_data.txt", t_echospace )

    if en_fig and compute_figure:
        plt.show()

    print( 'a0 = ' + '{0:.2f}'.format( a0 ) )
    print( 'SNR/echo/scan = ' +
          'imag:{0:.2f}, res:{1:.2f}'.format( snr, snr_res ) )
    print( 'T2 = ' + '{0:.4f}'.format( T2 * 1e3 ) + ' msec' )

    return ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace )


def compute_iterate( nmrObj, data_parent_folder, meas_folder, en_ext_param, thetaref, echoref_avg, direct_read, datain, en_fig, dconv_lpf_ord, dconv_lpf_cutoff_kHz ):

    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )
    # variables from NMR settings
    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    SpE = int( data_parser.find_value( 
        'nrPnts', param_list, value_list ) )
    NoE = int( data_parser.find_value( 
        'nrEchoes', param_list, value_list ) )
    en_ph_cycle_proc = data_parser.find_value( 
        'usePhaseCycle', param_list, value_list )
    tE = data_parser.find_value( 'echoTimeRun', param_list, value_list )
    Sf = data_parser.find_value( 
        'adcFreq', param_list, value_list ) * 1e6
    Df = data_parser.find_value( 
        'b1Freq', param_list, value_list ) * 1e6
    total_scan = int( data_parser.find_value( 
        'nrIterations', param_list, value_list ) )
    file_name_prefix = 'dat_'
    # en_ext_param = 0
    # thetaref = 0
    # echoref_avg = 0

    if ( direct_read ):
        ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace ) = compute_multiple( nmrObj, data_parent_folder, meas_folder, file_name_prefix,
                                                                                                          Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, direct_read, datain, dconv_lpf_ord, dconv_lpf_cutoff_kHz )
    else:
        ( a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace ) = compute_multiple( nmrObj, data_parent_folder, meas_folder, file_name_prefix,
                                                                                                          Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, 0, datain, dconv_lpf_ord, dconv_lpf_cutoff_kHz )

    # print(snr, T2)
    return a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace


def compute_stats( minfreq, maxfreq, data_parent_folder, meas_folder, plotname, en_fig ):

    # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # en_fig            : enable figure

    # compute settings
    process_sum_data = 1  # otherwise process raw data

    file_name_prefix = 'dat_'
    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )
    fig_num = 200

    # variables from NMR settings
    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    adcFreq = data_parser.find_value( 
        'adcFreq', param_list, value_list )
    nrPnts = int( data_parser.find_value( 
        'nrPnts', param_list, value_list ) )
    total_scan = int( data_parser.find_value( 
        'nrIterations', param_list, value_list ) )

    # parse file and remove DC component
    nmean = 0
    if process_sum_data:
        file_path = ( data_folder + 'asum' )
        one_scan_raw = np.array( data_parser.read_data( file_path ) )
        nmean = np.mean( one_scan_raw )
        one_scan = ( one_scan_raw - nmean ) / total_scan

    else:
        for m in range( 1, total_scan + 1 ):
            file_path = ( data_folder + file_name_prefix + '{0:03d}'.format( m ) )
            # read the data from the file and store it in numpy array format
            one_scan_raw = np.array( data_parser.read_data( file_path ) )
            nmean = np.mean( one_scan_raw )
            one_scan = ( one_scan_raw - nmean ) / \
                total_scan  # remove DC component

    # compute fft
    spectx, specty = nmr_fft( one_scan, adcFreq, 0 )
    specty = abs( specty )
    fft_range = [i for i, value in enumerate( spectx ) if ( 
        value >= minfreq and value <= maxfreq )]  # limit fft display

    # compute std
    nstd = np.std( one_scan )

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )

        # maximize window
        plot_backend = matplotlib.get_backend()
        mng = plt.get_current_fig_manager()
        if plot_backend == 'TkAgg':
            # mng.resize(*mng.window.maxsize())
            mng.resize( 800, 600 )
        elif plot_backend == 'wxAgg':
            mng.frame.Maximize( True )
        elif plot_backend == 'Qt4Agg':
            mng.window.showMaximized()

        fig.clf()
        ax = fig.add_subplot( 311 )

        line1, = ax.plot( spectx[fft_range], specty[fft_range], 'b-' )
        # ax.set_ylim(-50, 0)
        ax.set_xlabel( 'Frequency (MHz)' )
        ax.set_ylabel( 'Amplitude (a.u.)' )
        ax.set_title( "Spectrum" )
        ax.grid()

        ax = fig.add_subplot( 312 )
        x_time = np.linspace( 1, len( one_scan_raw ), len( one_scan_raw ) )
        x_time = np.multiply( x_time, ( 1 / adcFreq ) )  # in us
        x_time = np.multiply( x_time, 1e-3 )  # in ms
        line1, = ax.plot( x_time, one_scan_raw, 'b-' )
        ax.set_xlabel( 'Time(ms)' )
        ax.set_ylabel( 'Amplitude (a.u.)' )
        ax.set_title( "Amplitude. std=%0.2f. mean=%0.2f." % ( nstd, nmean ) )
        ax.grid()

        # plot histogram
        n_bins = 200
        ax = fig.add_subplot( 313 )
        n, bins, patches = ax.hist( one_scan, bins = n_bins )
        ax.set_title( "Histogram" )

        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()

        # fig = plt.gcf() # obtain handle
        plt.savefig( data_folder + plotname )

    # standard deviation of signal
    print( '\t\t: rms= ' + '{0:.4f}'.format( nstd ) +
          ' mean= {0:.4f}'.format( nmean ) )
    return nstd, nmean


def compute_in_bw_noise( bw_kHz, Df_MHz, minfreq, maxfreq, data_parent_folder, meas_folder, plotname, en_fig ):

    # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # en_fig            : enable figure

    # compute settings
    process_sum_data = 1  # otherwise process raw data

    file_name_prefix = 'dat_'
    data_folder = ( data_parent_folder + '/' + meas_folder + '/' )
    fig_num = 200

    # variables from NMR settings
    ( param_list, value_list ) = data_parser.parse_info( 
        data_folder, 'acqu.par' )  # read file
    adcFreq = data_parser.find_value( 
        'adcFreq', param_list, value_list )
    nrPnts = int( data_parser.find_value( 
        'nrPnts', param_list, value_list ) )
    total_scan = int( data_parser.find_value( 
        'nrIterations', param_list, value_list ) )

    # parse file and remove DC component
    nmean = 0
    if process_sum_data:
        file_path = ( data_folder + 'asum' )
        one_scan_raw = np.array( data_parser.read_data( file_path ) )
        nmean = np.mean( one_scan_raw )
        one_scan = ( one_scan_raw - nmean ) / total_scan

    else:
        for m in range( 1, total_scan + 1 ):
            file_path = ( data_folder + file_name_prefix + '{0:03d}'.format( m ) )
            # read the data from the file and store it in numpy array format
            one_scan_raw = np.array( data_parser.read_data( file_path ) )
            nmean = np.mean( one_scan_raw )
            one_scan = ( one_scan_raw - nmean ) / \
                total_scan  # remove DC component

    # compute in-bandwidth noise
    Sf = adcFreq * 1e6
    # filter parameter
    filt_ord = 2
    filt_lpf_cutoff = bw_kHz * 1e3  # in Hz

    T = 1 / Sf
    t = np.linspace( 0, T * ( len( one_scan ) - 1 ), len( one_scan ) )

    # down-conversion
    sReal = one_scan * np.cos( 2 * math.pi * Df_MHz * 1e6 * t )
    sImag = one_scan * np.sin( 2 * math.pi * Df_MHz * 1e6 * t )

    # filter
    r = butter_lowpass_filter( 
        sReal + 1j * sImag, filt_lpf_cutoff, Sf, filt_ord, False )

    # upconversion
    one_scan = np.real( r ) * np.cos( 2 * math.pi * Df_MHz * 1e6 * t ) + np.imag( r ) * np.sin( 2 * math.pi * Df_MHz * 1e6 * t )  # r * np.exp(1j* 2 * math.pi *  1.742*1e6 * t)
    one_scan = np.real( one_scan )

    # filter profile
    filt_prfl = np.random.randn( len( one_scan ) )  # generate ones
    filt_prfl_ori = filt_prfl  # noise data with no filter process
    sfiltReal = filt_prfl * np.cos( 2 * math.pi * Df_MHz * 1e6 * t )  # real downconversion
    sfiltImag = filt_prfl * np.sin( 2 * math.pi * Df_MHz * 1e6 * t )  # imag downconversion
    filt_out = butter_lowpass_filter( 
        sfiltReal + 1j * sfiltImag, filt_lpf_cutoff, Sf, filt_ord, False )  # filter
    filt_prfl = np.real( filt_out ) * np.cos( 2 * math.pi * Df_MHz * 1e6 * t ) + np.imag( filt_out ) * np.sin( 2 * math.pi * Df_MHz * 1e6 * t )  # upconversion
    filt_prfl = np.real( filt_prfl )

    # compute fft
    spectx, specty = nmr_fft( one_scan, adcFreq, 0 )
    specty = abs( specty )
    fft_range = [i for i, value in enumerate( spectx ) if ( 
        value >= minfreq and value <= maxfreq )]  # limit fft display

    # compute fft for the filter profile
    filtspectx, filtspecty = nmr_fft( filt_prfl, adcFreq, 0 )
    filtspecty = abs( filtspecty )
    filtorispecx, filtorispecty = nmr_fft( filt_prfl_ori, adcFreq, 0 )  # noise data with no filter process
    filtorispecty = abs( filtorispecty )

    # compute std
    nstd = np.std( one_scan )

    if en_fig:
        plt.ion()
        fig = plt.figure( fig_num )

        # maximize window
        plot_backend = matplotlib.get_backend()
        mng = plt.get_current_fig_manager()
        if plot_backend == 'TkAgg':
            # mng.resize(*mng.window.maxsize())
            mng.resize( 1000, 600 )
        elif plot_backend == 'wxAgg':
            mng.frame.Maximize( True )
        elif plot_backend == 'Qt4Agg':
            mng.window.showMaximized()

        fig.clf()
        ax = fig.add_subplot( 311 )

        filtnorm = sum( specty[fft_range] ) / sum( filtspecty[fft_range] )

        line1, = ax.plot( spectx[fft_range], specty[fft_range], 'b-', label = 'data', linewidth = 0.5 )
        line2, = ax.plot( filtspectx[fft_range], filtspecty[fft_range] * filtnorm, 'r.', markersize = 0.8, label = 'synth. noise' )  # amplitude is normalized with the max value of specty
        # line3, = ax.plot(filtorispecx[fft_range], filtorispecty[fft_range]*(filtnorm/2), 'y.', markersize=2.0, label='synth. noise unfiltered') # amplitude is normalized with the max value of specty

        # ax.set_ylim(-50, 0)
        ax.set_xlabel( 'Frequency (MHz)' )
        ax.set_ylabel( 'Amplitude (a.u.)' )
        ax.set_title( "Spectrum" )
        ax.grid()
        ax.legend()
        #plt.ylim( [-0.2, 5] )

        # plot time domain data
        ax = fig.add_subplot( 312 )
        x_time = np.linspace( 1, len( one_scan_raw ), len( one_scan_raw ) )
        x_time = np.multiply( x_time, ( 1 / adcFreq ) )  # in us
        x_time = np.multiply( x_time, 1e-3 )  # in ms
        line1, = ax.plot( x_time, one_scan, 'b-' , linewidth = 0.5 )
        ax.set_xlabel( 'Time(ms)' )
        ax.set_ylabel( 'Amplitude (a.u.)' )
        ax.set_title( "Amplitude. std=%0.2f. mean=%0.2f." % ( nstd, nmean ) )
        ax.grid()
        #plt.ylim( [-100, 100] )

        # plot histogram
        n_bins = 200
        ax = fig.add_subplot( 313 )
        n, bins, patches = ax.hist( one_scan, bins = n_bins )
        ax.set_title( "Histogram" )
        plt.ylim( [0, 2000] )

        plt.tight_layout()
        fig.canvas.draw()
        fig.canvas.flush_events()

        # fig = plt.gcf() # obtain handle
        plt.savefig( data_folder + plotname )

    # standard deviation of signal
    print( '\t\t: rms= ' + '{0:.4f}'.format( nstd ) +
          ' mean= {0:.4f}'.format( nmean ) )
    return nstd, nmean


def calcP90( Vpp, rs, L, f, numTurns, coilLength, coilFactor ):

    # estimates the 90 degree pulse length based on voltage output at the coil
    # Vpp: measured voltage at the coil
    # rs: series resitance of coil
    # L: inductance of coil
    # f: Larmor frequency in Hz
    # numTurns: Number of turns in coil
    # coilLength: Length of coil in m
    # coilFactor: obtained by measurement compensation with KeA, will be coil geometry
    # dependant

    import math
    import numpy as np

    gamma = 42.58e6  # MHz/Tesla
    u = 4 * np.pi * 10 ** -7
    Q = 2 * np.pi * f * L / rs
    Vrms = Vpp / ( 2 * math.sqrt( 2 ) )
    Irms = Vrms / ( math.sqrt( Q ** 2 + 1 ** 2 ) * rs )

    # extra factor due to finite coil length (geometry)
    B1 = u * ( numTurns / ( 2 * coilLength ) ) * Irms / coilFactor
    P90 = ( 1 / ( gamma * B1 ) ) * ( 90 / 360 )
    Pwatt = ( Irms ** 2 ) * rs

    return P90, Pwatt

''' OBSOLETE
def compute_freqsw(data_parent_folder, meas_folder, T2bound, en_figure):
    # POTENTIAL PROBLEM : stop_parameter (frequency) is not included in the
    # process

    # # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # SpF                : sample per frequency
    # en_figure          : enable figure

    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    total_scan = int(data_parser.find_value(
        'nrIterations', param_list, value_list))
    start_param = data_parser.find_value(
        'b1Freq_sta', param_list, value_list)
    stop_param = data_parser.find_value(
        'b1Freq_sto', param_list, value_list)
    spacing_param = data_parser.find_value(
        'b1Freq_spa', param_list, value_list)
    tE = data_parser.find_value(
        'echoTimeRun', param_list, value_list)

    sweep_param = np.arange(start_param, stop_param, spacing_param)
    a = np.zeros((len(sweep_param), NoE), dtype=complex)
    a_init = np.zeros(len(sweep_param))
    snr = np.zeros(len(sweep_param))
    T2 = np.zeros(len(sweep_param))
    noise = np.zeros(len(sweep_param))
    for m in range(0, len(sweep_param)):
        print('freq: ' + str(sweep_param[m]) + ' MHz')
        file_name_prefix = 'dat_' + '{0:06.3f}'.format(sweep_param[m]) + '_'
        (a[m, :], a_init[m], snr[m], T2[m], noise[m], _, _, _, _) = compute_multiple(data_parent_folder, meas_folder,
                                                                                     file_name_prefix, sweep_param[m] * 1e6, sweep_param[m] * 4 * 1e6, tE, total_scan, 0, 0, 0, 0)
        print('--------------------------------------')

    if en_figure:
        plt.figure(5)
        plt.plot(sweep_param, np.mean(np.real(a), axis=1))
        plt.title('Echo average with frequency')
        #set(gca, 'FontSize', 12)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Amplitude')

        plt.figure(6)
        plt.plot(sweep_param, a_init)
        plt.title('Initial amplitude with frequency')
        #set(gca, 'FontSize', 12)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Amplitude')

        plt.show()

    validT2Idx = ((T2 > min(T2bound)) & (T2 < max(T2bound)))

    # find index of max a_init
    # opt_freq_idx = np.argwhere(a_init == max(a_init[validT2Idx]))[0][0]

    # find index of max snr
    opt_freq_idx = np.argwhere(snr == max(snr[validT2Idx]))[0][0]

    opt_freq = sweep_param[opt_freq_idx]
    # opt_freq = sweep_param[np.argmax(a_init)]
    return opt_freq


def compute_generalsw(data_parent_folder, meas_folder, analysis, en_fig):
    # this general sweep is to sweep variables without frequency change
    # nothing is change in compute_multiple loop below, so it's easier to
    # manage

    # POTENTIAL PROBLEM : stop_parameter (frequency) is not included in the
    # process

    # # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # SpF                : sample per frequency
    # en_fig          : enable figure

    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    # this statement is not for technical purpose, but to easily manage
    # different kind of measurement with only one general sweep function :
    # the compute_generalsw. These parameters are generally for choosing
    # the correct setting file, parameter in the setting, axis name, and
    # verbose info
    if analysis == 't1_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'minTau'
        stop_param_name = 'maxTau'
        step_param_name = 'tauSteps'
        param_info = 'current delay 180 for t1 in us: '
        param_scaler = 1e-6
        param_unit = 's'
        figure_xlabel = 'delay 180 (s)'
    elif analysis == 'pulse1_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'pulse1_us_start'
        stop_param_name = 'pulse1_us_stop'
        step_param_name = 'pulse1_us_spacing'
        param_info = 'current pulse1_us : '
        param_scaler = 1
        param_unit = 'us'
        figure_xlabel = 'pulse1 length (us)'
    elif analysis == 'pulse2_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'pulse2_us_start'
        stop_param_name = 'pulse2_us_stop'
        step_param_name = 'pulse2_us_spacing'
        param_info = 'current pulse2_us : '
        param_scaler = 1
        param_unit = 'us'
        figure_xlabel = 'pulse2 length (us)'
    else:
        print('wrong analysis')

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, file_info_name)  # read file
    tE = data_parser.find_value('echoTimeRun', param_list, value_list)
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    Df = data_parser.find_value('b1Freq', param_list, value_list) * 1e6
    Sf = data_parser.find_value('adcFreq', param_list, value_list) * 1e6
    start_param = data_parser.find_value(
        start_param_name, param_list, value_list) * 1e3
    stop_param = data_parser.find_value(
        stop_param_name, param_list, value_list) * 1e3
    nsteps = data_parser.find_value(
        step_param_name, param_list, value_list)
    logspaceyesno = int(data_parser.find_value(
        'logSpace', param_list, value_list))
    nrIterations = int(data_parser.find_value(
        'nrIterations', param_list, value_list))

    if logspaceyesno:
        sweep_param = np.logspace(
            np.log10(start_param), np.log10(stop_param), nsteps)
    else:
        sweep_param = np.linspace(start_param, stop_param, nsteps)

    # compute reference
    file_name_prefix = 'datref_'
    (aref, aref_init, snrref, T2ref, noiseref, resref, thetaref, data_filt_ref, echo_avg_ref) = compute_multiple(
        data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, nrIterations, False, 0, 0, 0)

    # compute data
    a = np.zeros((len(sweep_param), NoE), dtype=complex)
    a_init = np.zeros(len(sweep_param))
    snr = np.zeros(len(sweep_param))
    T2 = np.zeros(len(sweep_param))
    noise = np.zeros(len(sweep_param))
    for m in range(0, len(sweep_param)):
        print(param_info + str(sweep_param[m] * param_scaler) + param_unit)
        file_name_prefix = 'dat_' + '{0:5.3f}'.format(sweep_param[m]) + '_'
        (a[m, :], a_init[m], snr[m], T2[m], noise[m], _, _, _, _) = compute_multiple(
            data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, nrIterations, False, 1, thetaref, echo_avg_ref)
        if analysis == 't1_sweep':
            # subtract the signal with the reference
            a[m, :] = aref - a[m, :]
            a_init[m] = aref_init - a_init[m]
        print('--------------------------------------')

    write_csv = True
    convert_to_prospa_data_t1(a, data_folder, write_csv)

    a_sum = np.zeros((len(sweep_param), 2), dtype=float)
    for i in range(0, len(sweep_param)):
        a_sum[i, 0] = sweep_param[i] / 1e6 * 1e3
        a_sum[i, 1] = np.real(np.sum(a[i]))
    with open(data_folder + 'data_t1heel.csv', 'w', newline='') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        for i in range(0, len(sweep_param)):
            filewriter.writerow(a_sum[i, :])

    if en_fig:
        plt.figure(7)
        plt.plot(sweep_param * param_scaler, np.mean(np.real(a), axis=1))
        plt.title('Echo average')
        #set(gca, 'FontSize', 12)
        plt.xlabel(figure_xlabel)
        plt.ylabel('Amplitude')

        plt.figure(8)
        plt.plot(sweep_param * param_scaler, a_init)
        plt.title('Initial amplitude')
        #set(gca, 'FontSize', 12)
        plt.xlabel(figure_xlabel)
        plt.ylabel('Amplitude')

        plt.show()

    return snrref, noiseref, resref
'''
