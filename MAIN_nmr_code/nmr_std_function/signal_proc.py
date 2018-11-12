'''
Created on Apr 4, 2018

@author: David Ariando
'''

import numpy as np
import math
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt


def butter_lowpass(cutoff, fs, order):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order, en_figure):
    b, a = butter_lowpass(cutoff, fs, order)

    if en_figure:
        w, h = freqz(b, a, worN=8000)
        plt.figure(10)
        plt.plot(0.5 * fs * w / np.pi, np.abs(h), 'b')
        plt.plot(cutoff, 0.5 * np.sqrt(2), 'ko')
        plt.axvline(cutoff, color='k')
        plt.xlim(0, 0.5 * fs)
        plt.title("Lowpass Filter Frequency Response")
        plt.xlabel('Frequency [Hz]')
        plt.grid()
        pass

    y = lfilter(b, a, data)

    if en_figure:
        plt.figure(11)
        plt.plot(data, label='raw data')
        plt.plot(y, label='filt data')
        plt.legend()
        plt.show()

    return y


def down_conv(s, k, tE, Df, Sf):

    T = 1 / Sf
    t = np.linspace(k * tE, k * tE + T * (len(s) - 1), len(s))

    # compute the signal frequency: only for ADC freq below Nyquist rate
    # Ds = abs(Df - Sf)

    #sReal = s * np.cos(2 * math.pi * Ds * t)
    sReal = s * np.cos(2 * math.pi * Df * t)
    #sImag = s * np.sin(2 * math.pi * Ds * t)
    sImag = s * np.sin(2 * math.pi * Df * t)

    r = butter_lowpass_filter(sReal + 1j * sImag, 3e5, Sf, 2, False)

    return r


def nmr_fft(data, fs, en_fig):
    spectx = np.linspace(-fs / 2, fs / 2, len(data))
    specty = abs(np.fft.fftshift(np.fft.fft(data - np.mean(data))))
    if en_fig:
        plt.figure
        plt.plot(spectx, specty, 'b')
        plt.title("FFT_data")
        plt.xlabel('Frequency [MHz]')
        plt.grid()
        plt.show()
    return spectx, specty
