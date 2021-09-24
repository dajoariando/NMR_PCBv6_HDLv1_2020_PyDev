'''
Created on July 24th 2021

Running this module requires both SMAs for transmitter pulse to be disconnected from the sensor board.
This is important because even though the duplexer acts as high impedance during transmission, it's still generating a high enough voltage at the receiver, which
prevents the receiver from acquiring a small signal outside the attenuated Tx after the duplexer.

Create a signal loop excitation coil and connect it to the low power output SMA and place it close to the probe coil to create a weakly coupled coil.
 

@author: David Ariando
'''

from nmr_std_function.nmr_functions import compute_iterate, compute_gain_async, compute_gain_sync, compute_gain_fft_sync
from nmr_std_function.data_parser import parse_simple_info, find_Cpar_Cser_from_table, find_Vbias_Vvarac_from_table
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.ntwrk_functions import cp_rmt_file, cp_rmt_folder, exec_rmt_ssh_cmd_in_datadir
from nmr_std_function.time_func import time_meas


def init ( client_data_folder ):

    # enable remote debug option if working within the SoC
    en_remote_dbg = 0

    # remote computing configuration. See the NMR class to see details of use
    en_remote_computing = 1  # 1 when using remote PC to process the data, and 0 when using the remote SoC to process the data

    # instantiate nmr object
    nmrObj = tunable_nmr_system_2018( client_data_folder, en_remote_dbg, en_remote_computing )

    # system setup
    nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting

    nmrObj.deassertAll()

    nmrObj.assertControlSignal( nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                   nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                                   nmrObj.PSU_5V_ANA_N_EN_msk )

    nmrObj.assertControlSignal( 
                nmrObj.RX1_1L_msk | nmrObj.RX1_1H_msk | nmrObj.RX2_L_msk | nmrObj.RX2_H_msk | nmrObj.RX_SEL1_msk | nmrObj.RX_FL_msk | nmrObj.RX_FH_msk | nmrObj.PAMP_IN_SEL2_msk )
    nmrObj.deassertControlSignal( nmrObj.RX1_1H_msk | nmrObj.RX_FH_msk | nmrObj.RX_FH_msk )
    # nmrObj.deassertControlSignal( nmrObj.RX_FL_msk )

    nmrObj.setMatchingNetwork( 0, 0 )

    return nmrObj


def analyze( nmrObj, tuning_freq, sta_freq, sto_freq, spac_freq, samp_freq, fftpts, fftcmd, fftvalsub, continuous, en_fig ):

    timeObj = time_meas( False )
    fig_num = 1

    while True:

        Vbias, Vvarac = find_Vbias_Vvarac_from_table ( nmrObj.client_path , tuning_freq, nmrObj.S21_table )
        nmrObj.setPreampTuning( Vbias, Vvarac )
        Cpar, Cser = find_Cpar_Cser_from_table ( nmrObj.client_path , tuning_freq, nmrObj.S11_table )
        # nmrObj.setMatchingNetwork( Cpar, Cser )

        timeObj.setTimeSta()
        # nmrObj.pamp_char_async ( sta_freq, sto_freq, spac_freq, samp_freq )
        nmrObj.pamp_char_sync ( sta_freq, sto_freq, spac_freq, fftpts, fftcmd, fftvalsub )
        timeObj.setTimeSto()
        timeObj.reportTimeRel( "pamp_char_sync" )

        timeObj.setTimeSta()

        if  nmrObj.en_remote_computing:  # copy remote files to local directory
            cp_rmt_file( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, "current_folder.txt" )

        meas_folder = parse_simple_info( nmrObj.data_folder, 'current_folder.txt' )

        if  nmrObj.en_remote_computing:  # copy remote folder to local directory
            cp_rmt_folder( nmrObj.scp, nmrObj.server_data_folder, nmrObj.client_data_folder, meas_folder[0] )
            exec_rmt_ssh_cmd_in_datadir( nmrObj.ssh, "rm -rf " + meas_folder[0], nmrObj.server_data_folder )  # delete the file in the server

        # maxS21, maxS21_freq, _ = compute_gain_async( nmrObj, data_folder, meas_folder[0], en_fig, fig_num )
        # maxS21, maxS21_freq, _ = compute_gain_sync( nmrObj, nmrObj.data_folder, meas_folder[0], en_fig, fig_num )
        maxS21, maxS21_freq, _ = compute_gain_fft_sync( nmrObj, nmrObj.data_folder, meas_folder[0], en_fig, fig_num )
        # print( 'maxS21={0:0.2f} maxS21_freq={1:0.2f}'.format( maxS21, maxS21_freq ) )
        print( 'maxS21=%0.2f maxS21_freq=%0.2f Vbias=%0.2fV Vvarac=%0.2fV Cpar=%d Cser=%d' % ( maxS21, maxS21_freq, Vbias, Vvarac, Cpar, Cser ) )

        timeObj.setTimeSto()
        timeObj.reportTimeRel( "processing time" )

        if ( not continuous ):
            break


def exit( nmrObj ):
    nmrObj.deassertAll()
    nmrObj.exit()


client_data_folder = "D:\\TEMP"
en_fig = True
continuous = True
# measurement properties
tuning_freq = 1.7  # tune the matching network and preamp to this frequency
sta_freq = 1.4  # low bound frequency to be shown in the figure
sto_freq = 2.0  # up bound frequency to be shown in the figure
spac_freq = 0.001  # frequency resolution
samp_freq = 25  # only useful when the async method is used
fftpts = 512
fftcmd = fftpts / 4 * 3  # put nmrObj.NO_SAV_FFT, nmrObj.SAV_ALL_FFT, or any desired fft point number
fftvalsub = 9828  # adc data value subtractor before fed into the FFT core to remove DC components. Get the DC value by doing noise measurement
nmrObj = init( client_data_folder )
analyze ( nmrObj, tuning_freq, sta_freq, sto_freq, spac_freq, samp_freq, fftpts, fftcmd, fftvalsub, continuous, en_fig )
exit( nmrObj )
