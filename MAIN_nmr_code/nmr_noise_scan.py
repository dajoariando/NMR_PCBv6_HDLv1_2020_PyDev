'''

    make sure to disable the noise test script in nmr_noise.py

'''

import nmr_noise
import numpy as np
from os import mkdir
from datetime import datetime
from nmr_std_function.data_parser import parse_simple_info
from shutil import move, copy

samp_freq = 25  # sampling frequency
samples = 100000  # number of points
min_freq = 3.8  # in MHz
max_freq = 4.7  # in MHz
# tuning_freq = 1.6  # hardware tuning frequency selector, using lookup table
meas_bw_kHz = 100  # downconversion filter bw
continuous = False  # continuous running at one frequency configuration
client_data_folder = "C:\\Users\\dave\\Documents\\NMR_DATA"
en_fig = True

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = client_data_folder + '\\' + datename + '_noise_scan'
mkdir( swfolder )

nmrObj = nmr_noise.init( swfolder )

freqList = np.arange ( 4.0, 4.5, 0.01 )
for tuning_freq in freqList:
    nmr_noise.analyze( nmrObj, samp_freq, samples, min_freq, max_freq, tuning_freq, meas_bw_kHz, continuous , en_fig )
    meas_folder = parse_simple_info( swfolder, 'current_folder.txt' )
    move( swfolder + '/' + meas_folder[0] , swfolder + '/noise_at_freq_%2.3f' % tuning_freq )  # move the folder
    copy( swfolder + ( '/noise_at_freq_%2.3f' % tuning_freq ) + '/noise_plot.png', swfolder + '/' + ( '/noise_at_freq_%2.3f.png' % tuning_freq ) )  # copy the figure into the main folder

nmr_noise.exit( nmrObj )
