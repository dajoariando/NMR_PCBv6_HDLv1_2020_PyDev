'''
    Author: David Ariando
    Date: July 21st 2021
    This module creates a standardized measurement for measuring nmr signal for a magnetic field configuration
'''

from nmr_t2_auto import nmr_t2_auto
import numpy as np
from os import mkdir
from datetime import datetime
from nmr_std_function.data_parser import parse_simple_info
from shutil import move

# cpmg settings

pulse1_us = 15  # 75 for Cheng's coil. pulse pi/2 length.
pulse2_us = 1.6 * pulse1_us  # pulse pi length
echo_spacing_us = 500  # 200
scan_spacing_us = 100000
samples_per_echo = 1024  # 3072
echoes_per_scan = 128  # 20
init_adc_delay_compensation = 34  # acquisition shift microseconds.
ph_cycl_en = 1
dconv_lpf_ord = 2  # downconversion order
dconv_lpf_cutoff_Hz = 30e3  # downconversion lpf cutoff
client_data_folder = "D:\\TEMP"
cpmgFreqList = np.linspace( 1.61, 1.72, 12 )
iterList = ( 10, 100 )

# create name for new folder
now = datetime.now()
datename = now.strftime( "%Y_%m_%d_%H_%M_%S" )
swfolder = client_data_folder + '\\' + datename + '_t2std'
mkdir( swfolder )

# loop for standardized measurements
for number_of_iteration in iterList:
    for cpmg_freq in cpmgFreqList:
        nmr_t2_auto ( cpmg_freq, pulse1_us, pulse2_us, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, dconv_lpf_ord, dconv_lpf_cutoff_Hz, swfolder )
        meas_folder = parse_simple_info( swfolder, 'current_folder.txt' )
        move( swfolder + '/' + meas_folder[0] , swfolder + '/iter_%d__freq_%2.3f' % ( number_of_iteration, cpmg_freq ) )  # move the figure
