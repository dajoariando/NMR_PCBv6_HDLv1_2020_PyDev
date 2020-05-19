# 200518 compare nmr individual data of different decimation factor to see its effect in changing decimation factor.
# set the two folders that contains the file of the same name
# put the name into the "filename", e.g. dat_001

import matplotlib.pyplot as plt
from nmr_std_function import data_parser
import numpy as np

data_folder = 'Z:/NMR_DATA'
fold1 = '2020_05_18_23_23_49_cpmg'
fold2 = '2020_05_18_23_24_28_cpmg'

filename = 'dat_001'

# variables from NMR settings

# load acquisition setting 1
( param_list, value_list ) = data_parser.parse_info( 
    data_folder + '/' + fold1 + '/', 'acqu.par' )  # read file
dwellTime1 = data_parser.find_value( 
    'dwellTime', param_list, value_list )
dconvFact1 = data_parser.find_value( 
    'dconvFact', param_list, value_list )

# load acquisition setting 2
( param_list, value_list ) = data_parser.parse_info( 
    data_folder + '/' + fold2 + '/', 'acqu.par' )  # read file
dwellTime2 = data_parser.find_value( 
    'dwellTime', param_list, value_list )
dconvFact2 = data_parser.find_value( 
    'dconvFact', param_list, value_list )

# load data 1
file_path = ( data_folder + '/' + fold1 + '/' + filename )
dconv1 = np.array( data_parser.read_data( file_path ) )
xvect1 = np.arange( 0, dwellTime1 * len( dconv1 ), dwellTime1 )

# load data 2
file_path = ( data_folder + '/' + fold2 + '/' + filename )
dconv2 = np.array( data_parser.read_data( file_path ) )
xvect2 = np.arange( 0, dwellTime2 * len( dconv2 ), dwellTime2 )

# normalize data
dconv1 = dconv1 / dconvFact1
dconv2 = dconv2 / dconvFact2

# plot real data
plt.figure( 1 )
plt.title( 'real' )
plt.plot( xvect1[0:len( xvect1 ):2], dconv1[0:len( dconv1 ):2] , color = 'r', label = 'dconv:{:.0f}'.format( dconvFact1 ), linewidth = 0.1 )
plt.plot( xvect2[0:len( xvect2 ):2], dconv2[0:len( dconv2 ):2] , color = 'b' , label = 'dconv:{:.0f}'.format( dconvFact2 ), linewidth = 0.1 )
plt.legend()

# plot imag data
plt.figure( 2 )
plt.title( 'imag' )
plt.plot( xvect1[1:len( xvect1 ):2], dconv1[1:len( dconv1 ):2] , color = 'r', label = 'dconv:{:.0f}'.format( dconvFact1 ), linewidth = 0.1 )
plt.plot( xvect2[1:len( xvect2 ):2], dconv2[1:len( dconv2 ):2] , color = 'b' , label = 'dconv:{:.0f}'.format( dconvFact2 ) , linewidth = 0.1 )
plt.legend()

plt.show()
