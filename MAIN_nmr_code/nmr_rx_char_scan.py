'''
Created on July 24th 2021

This module takes input frequency and sweep nmr_rx_char() with different tuning frequency.

Running this module requires both SMAs for transmitter pulse to be disconnected from the sensor board.
This is important because even though the duplexer acts as high impedance during transmission, it's still generating a high enough voltage at the receiver, which
prevents the receiver from acquiring a small signal outside the attenuated Tx after the duplexer.

Create a signal loop excitation coil and connect it to the low power output SMA and place it close to the probe coil to create a weakly coupled coil.
 

@author: David Ariando
'''

import nmr_rx_char
import numpy as np
from os import mkdir
from datetime import datetime
from nmr_std_function.data_parser import parse_simple_info
from shutil import move, copy

client_data_folder = "D:\\TEMP"
en_fig = 1
continuous = 0

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = client_data_folder + '\\' + datename + '_rx_char_scan'
mkdir( swfolder )

nmrObj = nmr_rx_char.init( swfolder )

# measurement properties
# tuning_freq = 1.8  # tune the matching network and preamp to this frequency
sta_freq = 1.8  # low bound frequency to be shown in the figure
sto_freq = 2.1  # up bound frequency to be shown in the figure
spac_freq = 0.001  # frequency resolution
samp_freq = 25  # only useful when the async method is used
fftpts = 512
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number. For the C function tx_acq_sync, fftcmd is always fftpts/4*3 in order to recover the signal at 1/4 of the ADC freq.
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement

freqList = np.arange ( 1.9, 2.0, 0.001 )
for tuning_freq in freqList:
    nmr_rx_char.analyze( nmrObj, tuning_freq, sta_freq, sto_freq, spac_freq, samp_freq, fftpts, fftcmd, fftvalsub, continuous, en_fig )
    meas_folder = parse_simple_info( swfolder, 'current_folder.txt' )
    move( swfolder + '/' + meas_folder[0] , swfolder + '/rx_char_at_freq_%2.3f' % tuning_freq )  # move the folder
    # copy( swfolder + ( '/rx_char_at_freq_%2.3f' % tuning_freq ) + '/gain.png', swfolder + '/' + ( '/rx_char_at_freq_%2.3f.png' % tuning_freq ) )  # copy the figure into the main folder
    copy( swfolder + ( '/rx_char_at_freq_%2.3f' % tuning_freq ) + '/gainFFT.png', swfolder + '/' + ( '/FFT_rx_char_at_%2.3f_MHz.png' % tuning_freq ) )  # copy the figure into the main folder

nmr_rx_char.exit( nmrObj )
