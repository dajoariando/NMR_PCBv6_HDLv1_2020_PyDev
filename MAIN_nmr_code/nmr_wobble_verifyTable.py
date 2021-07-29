'''
    Created on July 29th 2020
    author: David Joseph Ariando
    this program takes data inside S11 table and plot it with the frequency in order to quickly verify if a table is working properly with the installed coil

'''

import nmr_wobble
import nmr_spt_fft
from nmr_std_function.data_parser import parse_simple_info, find_Cpar_Cser_from_table
import numpy as np
import matplotlib.pyplot as plt
import time

# measurement properties
client_data_folder = "D:\\TEMP"
en_fig = 0
freqSta = 1.5
freqSto = 2.3
freqSpa = 0.1
freqSamp = 25  # not used when using wobble_sync. Will be used when using wobble_async
fftpts = 1024
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
extSet = False  # use external executable to set the matching network Cpar and Cser
useRef = True  # use reference to eliminate background
fig_num = 5

nmrObj = nmr_wobble.init ( client_data_folder )

print( 'Generate reference.' )
S11_ref, _, _, _, _, _ = nmr_wobble.analyze( nmrObj, False, 0, 0, freqSta, freqSto, freqSpa, freqSamp , fftpts, fftcmd, fftvalsub, 0, 0 , en_fig )  # background is computed with no capacitor connected -> max reflection

freqList = np.arange ( freqSta, freqSto + freqSpa / 2, freqSpa )
S11_cmplx = np.zeros( len( freqList ), dtype=complex )
i = 0
for tuning_freq in freqList:
    Cpar, Cser = find_Cpar_Cser_from_table ( nmrObj.client_path , tuning_freq, nmrObj.S11_table )
    S11_cmplx[i] = nmr_spt_fft.analyze( nmrObj, extSet, Cpar, Cser, tuning_freq , fftpts, fftcmd, fftvalsub, en_fig )
    i = i + 1
    time.sleep( 1 )  # delay is important to make sure the folder name is different

plt.plot( freqList, 20 * np.log10( abs( np.divide( S11_cmplx , S11_ref ) ) ) )

nmr_wobble.exit( nmrObj )
