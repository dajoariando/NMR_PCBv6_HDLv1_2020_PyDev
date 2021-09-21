'''
Created on Nov 06, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import pydevd
import numpy as np
import matplotlib.pyplot as plt
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.data_parser import parse_csv_float2col
from scipy import signal
from datetime import datetime
import shutil
from nmr_std_function.data_parser import write_text_append
from nmr_std_function.hw_driver import fpga_de1soc
# from email.errors import ObsoleteHeaderDefect
from nmr_std_function.ntwrk_functions import exec_rmt_ssh_cmd_in_datadir, init_ntwrk, exit_ntwrk


class tunable_nmr_system_2018:

    def __init__( self, client_data_folder, en_remote_dbg, en_remote_computing ):

        # chip offset declaration (look at the KiCAD for the designated
        # chip name)
        self.i2c_U21_ofst = 0
        self.i2c_U71_ofst = 16
        self.spi_pamp_U32 = 32

        # Output control signal to FPGA via I2C addr:0x40
        self.RX_FL_ofst = ( 0 + self.i2c_U21_ofst )
        self.RX_FH_ofst = ( 1 + self.i2c_U21_ofst )
        self.RX_SEL2_ofst = ( 2 + self.i2c_U21_ofst )
        self.RX_SEL1_ofst = ( 3 + self.i2c_U21_ofst )
        self.RX3_L_ofst = ( 4 + self.i2c_U21_ofst )
        self.RX3_H_ofst = ( 5 + self.i2c_U21_ofst )
        self.RX1_2L_ofst = ( 6 + self.i2c_U21_ofst )
        self.RX1_2H_ofst = ( 7 + self.i2c_U21_ofst )
        # self.___(8 + self.i2c_U21_ofst)
        # self.___(9 + self.i2c_U21_ofst)
        # self.___(10 + self.i2c_U21_ofst)
        # self.PAMP_RDY_ofst = (11 + self.i2c_U21_ofst)
        self.RX1_1H_ofst = ( 12 + self.i2c_U21_ofst )
        self.RX1_1L_ofst = ( 13 + self.i2c_U21_ofst )
        self.RX2_H_ofst = ( 14 + self.i2c_U21_ofst )
        self.RX2_L_ofst = ( 15 + self.i2c_U21_ofst )

        self.RX_FL_msk = ( 1 << self.RX_FL_ofst )
        self.RX_FH_msk = ( 1 << self.RX_FH_ofst )
        self.RX_SEL2_msk = ( 1 << self.RX_SEL2_ofst )
        self.RX_SEL1_msk = ( 1 << self.RX_SEL1_ofst )
        self.RX3_L_msk = ( 1 << self.RX3_L_ofst )
        self.RX3_H_msk = ( 1 << self.RX3_H_ofst )
        self.RX1_2L_msk = ( 1 << self.RX1_2L_ofst )
        self.RX1_2H_msk = ( 1 << self.RX1_2H_ofst )
        # self.___(8)
        # self.___(9)
        # self.___(10)
        # self.PAMP_RDY_msk = (1 << self.PAMP_RDY_ofst)
        self.RX1_1H_msk = ( 1 << self.RX1_1H_ofst )
        self.RX1_1L_msk = ( 1 << self.RX1_1L_ofst )
        self.RX2_H_msk = ( 1 << self.RX2_H_ofst )
        self.RX2_L_msk = ( 1 << self.RX2_L_ofst )

        # Output control signal to FPGA via I2C addr:0x41
        # self.___(0 + self.i2c_U71_ofst)
        # self.___(1 + self.i2c_U71_ofst)
        # self.___(2 + self.i2c_U71_ofst)
        # self.___(3 + self.i2c_U71_ofst)
        # self.___(4 + self.i2c_U71_ofst)
        # self.___(5 + self.i2c_U71_ofst)
        self.DUP_STAT_ofst = ( 6 + self.i2c_U71_ofst )
        self.QSW_STAT_ofst = ( 7 + self.i2c_U71_ofst )
        self.PSU_5V_ADC_EN_ofst = ( 8 + self.i2c_U71_ofst )
        self.PSU_5V_ANA_N_EN_ofst = ( 9 + self.i2c_U71_ofst )
        self.PSU_5V_ANA_P_EN_ofst = ( 10 + self.i2c_U71_ofst )
        self.MTCH_NTWRK_RST_ofst = ( 11 + self.i2c_U71_ofst )
        self.PSU_15V_TX_P_EN_ofst = ( 12 + self.i2c_U71_ofst )
        self.PSU_15V_TX_N_EN_ofst = ( 13 + self.i2c_U71_ofst )
        self.PSU_5V_TX_N_EN_ofst = ( 14 + self.i2c_U71_ofst )
        # self.___(15 + self.i2c_U71_ofst)
        # self.___(0 + 16)
        # self.___(1 + 16)
        # self.___(2 + 16)
        # self.___(3 + 16)
        # self.___(4 + 16)
        # self.___(5 + 16)
        self.DUP_STAT_msk = ( 1 << self.DUP_STAT_ofst )
        self.QSW_STAT_msk = ( 1 << self.QSW_STAT_ofst )
        self.PSU_5V_ADC_EN_msk = ( 1 << self.PSU_5V_ADC_EN_ofst )
        self.PSU_5V_ANA_N_EN_msk = ( 1 << self.PSU_5V_ANA_N_EN_ofst )
        self.PSU_5V_ANA_P_EN_msk = ( 1 << self.PSU_5V_ANA_P_EN_ofst )
        self.MTCH_NTWRK_RST_msk = ( 1 << self.MTCH_NTWRK_RST_ofst )
        self.PSU_15V_TX_P_EN_msk = ( 1 << self.PSU_15V_TX_P_EN_ofst )
        self.PSU_15V_TX_N_EN_msk = ( 1 << self.PSU_15V_TX_N_EN_ofst )
        self.PSU_5V_TX_N_EN_msk = ( 1 << self.PSU_5V_TX_N_EN_ofst )
        # self.___(15 + 16)

        # definition for spi pamp input control
        self.PAMP_IN_SEL1_ofst = ( 2 + self.spi_pamp_U32 )
        self.PAMP_IN_SEL2_ofst = ( 3 + self.spi_pamp_U32 )
        self.PAMP_IN_SEL1_msk = ( 1 << self.PAMP_IN_SEL1_ofst )
        self.PAMP_IN_SEL2_msk = ( 1 << self.PAMP_IN_SEL2_ofst )

        # definition for FFT hardware measurement
        self.SAV_ALL_FFT = -1
        self.NO_SAV_FFT = 0

        # General control defaults for the FPGA
        self.gnrl_cnt = 0

        # Numeric conversion of the hardware
        self.pamp_gain_dB = 60  # preamp gain
        self.rx_gain_dB = 20  # rx amp gain
        self.totGain = 10 ** ( ( self.pamp_gain_dB + self.rx_gain_dB ) / 20 )
        self.uvoltPerDigit = 3.2 * ( 10 ** 6 ) / 16384  # ADC conversion, in microvolt
        self.fir_gain = 21513  # downconversion FIR filter gain (sum of all coefficients)
        self.dconv_gain = 0.707106781  # downconversion gain factor due to sine(45,135,225,315) multiplication

        # ip addresses settings for the system
        self.server_ip = '192.168.137.168'  # '129.22.143.88'
        self.client_ip = '192.168.137.1'  # '129.22.143.39'
        self.server_path = '/root/NMR_PCBv6_HDLv1_2020_PyDev/MAIN_nmr_code/'
        # client path with samba
        self.client_path = 'Y:\\NMR_PCBv6_HDLv1_2020_PyDev\\MAIN_nmr_code\\'
        self.ssh_usr = 'root'
        self.ssh_passwd = 'dave'
        # data folder
        self.server_data_folder = "/root/NMR_DATA"
        self.client_data_folder = client_data_folder
        self.exec_folder = "/c_exec/"

        # configuration table to be loaded
        self.S11_table = "genS11Table.txt"  # filename for S11 tables
        self.S21_table = "genS21Table.txt"

        if en_remote_computing:
            self.data_folder = self.client_data_folder
            en_remote_dbg = 0  # force remote debugging to be disabled
        else:
            self.data_folder = self.server_data_folder

        if en_remote_dbg:
            from pydevd_file_utils import setup_client_server_paths
            PATH_TRANSLATION = [( self.client_path, self.server_path )]
            setup_client_server_paths( PATH_TRANSLATION )
            print( "---server:%s---client:%s---" %
                  ( self.server_ip, self.client_ip ) )
            pydevd.settrace( self.client_ip, stdoutToServer=True,
                            stderrToServer=True )

        # This variable supports processing on the SoC/server (old method) and show the result on client via remote X window.
        # It also supports processing on the PC/client (new method) and show the result directly on client (much faster).
        # When en_remote_computing is 1, make sure to run the python code on the PC/client side.
        # When en_remote_computing is 0, make sure to run the python code on the SoCFPGA/server side.
        self.en_remote_computing = en_remote_computing

        if not en_remote_computing:
            # directories
            self.work_dir = os.getcwd()
            # only do this after remote debug initialization
            os.chdir( self.data_folder )
        else:
            self.ssh, self.scp = init_ntwrk ( self.server_ip, self.ssh_usr, self.ssh_passwd )

    def exit( self ):
        exit_ntwrk ( self.ssh, self.scp )

    def turnOnRemoteDebug( self ):
        # CANNOT RUN FROM HERE, YOU HAVE TO COPY THE CONTENT OF THIS FOLDER TO THE EXECUTABLE WHERE YOU RUN THE CODE AND RUN IT FROM THERE
        # THIS IS KEPT FOR CLEAN DOCUMENTATION PURPOSES
        # from pydevd_file_utils import setup_client_server_paths
        # server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
        # client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
        # PATH_TRANSLATION = [(client_path, server_path)]
        # setup_client_server_paths(PATH_TRANSLATION)
        # pydevd.settrace("dajo-compaqsff")
        from pydevd_file_utils import setup_client_server_paths
        PATH_TRANSLATION = [( self.client_path, self.server_path )]
        setup_client_server_paths( PATH_TRANSLATION )
        print( "---server:%s---client:%s---" %
              ( self.server_ip, self.client_ip ) )
        pydevd.settrace( self.client_ip, stdoutToServer=True,
                        stderrToServer=True )

    def initNmrSystem( self ):
        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/init"
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( self.work_dir + "/c_exec/init" )

    def setPreampTuning( self, vbias, vvarac ):
        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/preamp_tuning" + " " + str( vbias ) + " " + str( vvarac )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            # set preamp tuning
            os.system( 
                self.work_dir + self.exec_folder + "preamp_tuning" + " " +
                str( vbias ) + " " +
                str( vvarac )
            )

    def setMatchingNetwork( self, cpar, cser ):
        self.assertControlSignal( self.MTCH_NTWRK_RST_msk )

        # Turn on matching network
        # self.cshunt = cpar
        # self.cseries = cser
        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/i2c_mtch_ntwrk" + " " + str( cpar ) + " " + str( cser )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( 
                self.work_dir + self.exec_folder + "i2c_mtch_ntwrk" + " " +
                str( cpar ) + " " +
                str( cser )
            )

    def assertControlSignal( self, cnt_in ):
        self.gnrl_cnt = self.gnrl_cnt | cnt_in

        self.gnrl_cnt0 = ( self.gnrl_cnt >> self.i2c_U21_ofst ) & 0xffff
        self.gnrl_cnt1 = ( self.gnrl_cnt >> self.i2c_U71_ofst ) & 0xffff
        self.gnrl_cnt2 = ( self.gnrl_cnt >> self.spi_pamp_U32 ) & 0xff

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/i2c_gnrl" + " " + str( self.gnrl_cnt0 ) + " " + str( self.gnrl_cnt1 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
            ssh_cmd = self.server_path + "c_exec/spi_pamp_input" + " " + str( self.gnrl_cnt2 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( 
                self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
                str( self.gnrl_cnt0 ) + " " +
                str( self.gnrl_cnt1 )
            )
            os.system( self.work_dir + self.exec_folder + "spi_pamp_input" + " " +
                      str( self.gnrl_cnt2 )
                      )

    def deassertControlSignal( self, cnt_in ):
        self.gnrl_cnt = self.gnrl_cnt & ( ~cnt_in )
        self.gnrl_cnt0 = self.gnrl_cnt & 0xffff
        self.gnrl_cnt1 = ( self.gnrl_cnt >> 16 ) & 0xffff
        self.gnrl_cnt2 = ( self.gnrl_cnt >> self.spi_pamp_U32 ) & 0xff

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/i2c_gnrl" + " " + str( self.gnrl_cnt0 ) + " " + str( self.gnrl_cnt1 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
            ssh_cmd = self.server_path + "c_exec/spi_pamp_input" + " " + str( self.gnrl_cnt2 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( 
                self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
                str( self.gnrl_cnt0 ) + " " +
                str( self.gnrl_cnt1 )
            )
            os.system( self.work_dir + self.exec_folder + "spi_pamp_input" + " " +
                      str( self.gnrl_cnt2 )
                      )

    def deassertAll ( self ):
        self.gnrl_cnt = 0

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/i2c_gnrl" + " " + str( 0 ) + " " + str( 0 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
            ssh_cmd = self.server_path + "c_exec/spi_pamp_input" + " " + str( 0 )
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( 
                    self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
                    str( 0 ) + " " +
                    str( 0 )
                )
            os.system( self.work_dir + self.exec_folder + "spi_pamp_input" + " " +
                    str( 0 )
                )

    def doLaplaceInversion( self, filename, outpath ):
        # laplace inversion computatation
        if self.en_remote_computing:
            ssh_cmd = self.server_path + "nmr_sig_proc" + " " + filename + " " + outpath
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os.system( 
                self.work_dir + self.exec_folder + "nmr_sig_proc" + " " +
                filename + " " +
                outpath
            )

    def cpmgSequence( self, cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int , tx_sd_msk, en_dconv , dconv_fact, echo_skip ):
        # execute cpmg sequence
        if ( en_dconv ):
            exec_name = "cpmg_iterate_dconv"
        else:
            exec_name = "cpmg_iterate_raw"

        command = ( exec_name + " " +
                   str( cpmg_freq ) + " " +
                   str( pulse1_us ) + " " +
                   str( pulse2_us ) + " " +
                   str( pulse1_dtcl ) + " " +
                   str( pulse2_dtcl ) + " " +
                   str( echo_spacing_us ) + " " +
                   str( scan_spacing_us ) + " " +
                   str( samples_per_echo ) + " " +
                   str( echoes_per_scan ) + " " +
                   str( init_adc_delay_compensation ) + " " +
                   str( number_of_iteration ) + " " +
                   str( ph_cycl_en ) + " " +
                   str( pulse180_t1_int ) + " " +
                   str( delay180_t1_int ) + " " +
                   str( tx_sd_msk ) + " " +
                   str( dconv_fact ) + " " +
                   str( echo_skip )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def cpmgSequenceDirectRead( self, cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int ):

        if self.en_remote_computing:

            print( "ERROR! cpmgSequenceDirectRead is not supported by remote data processing!" )

        else:

            data = np.zeros( samples_per_echo * echoes_per_scan )

            for i in range( 0, number_of_iteration ):
                # execute cpmg sequence
                command = ( self.work_dir + self.exec_folder + "cpmg_iterate_direct" + " " +
                           str( cpmg_freq ) + " " +
                           str( pulse1_us ) + " " +
                           str( pulse2_us ) + " " +
                           str( pulse1_dtcl ) + " " +
                           str( pulse2_dtcl ) + " " +
                           str( echo_spacing_us ) + " " +
                           str( scan_spacing_us ) + " " +
                           str( samples_per_echo ) + " " +
                           str( echoes_per_scan ) + " " +
                           str( init_adc_delay_compensation ) + " " +
                           str( 1 ) + " " +
                           str( ph_cycl_en ) + " " +
                           str( pulse180_t1_int ) + " " +
                           str( delay180_t1_int )
                           )
                os.system( command )  # execute command & ignore its console

                # read the data from SDRAM
                fpgaObj = fpga_de1soc()
                # get data averaged by number of iteration
                one_scan = fpgaObj.readSDRAM( samples_per_echo *
                                             echoes_per_scan )
                if ( ph_cycl_en ):
                    if ( i % 2 ):  # phase cycling every other scan
                        data = data - np.divide( one_scan, number_of_iteration )
                    else:
                        data = data + np.divide( one_scan, number_of_iteration )
                else:
                    data = data + np.divide( one_scan, number_of_iteration )

            return data

    def fid( self, cpmg_freq, pulse2_us, pulse2_dtcl, scan_spacing_us, samples_per_echo, number_of_iteration, tx_opa_sd ):
        # execute cpmg sequence
        command = ( "fid" + " " +
                   str( cpmg_freq ) + " " +
                   str( pulse2_us ) + " " +
                   str( pulse2_dtcl ) + " " +
                   str( scan_spacing_us ) + " " +
                   str( samples_per_echo ) + " " +
                   str( number_of_iteration ) + " " +
                   str( tx_opa_sd )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + +command )
            os.system( os_command )  # execute command & ignore its console

    def noise( self, samp_freq, samples ):
        scan_spacing_us = 100000
        number_of_iteration = 1
        # execute noise sequence

        command = ( "noise" + " " +
                   str( samp_freq ) + " " +
                   str( scan_spacing_us ) + " " +
                   str( samples ) + " " +
                   str( number_of_iteration )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def wobble_async( self, sta_freq, sto_freq, spac_freq, samp_freq ):
        # execute cpmg sequence
        command = ( "wobble_async" + " " +
                   str( sta_freq ) + " " +
                   str( sto_freq ) + " " +
                   str( spac_freq ) + " " +
                   str( samp_freq )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def wobble_sync( self, sta_freq, sto_freq, spac_freq, fftpts, fftcmd, fftvalsub ):
        # execute cpmg sequence
        command = ( "wobble_sync" + " " +
                   str( sta_freq ) + " " +
                   str( sto_freq ) + " " +
                   str( spac_freq ) + " " +
                   str( fftpts ) + " " +
                   str( fftcmd ) + " " +
                   str( fftvalsub )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def spt_fft( self, freq, fftpts, fftcmd, fftvalsub ):
        # execute cpmg sequence
        command = ( "spt_fft" + " " +
                   str( freq ) + " " +
                   str( fftpts ) + " " +
                   str( fftcmd ) + " " +
                   str( fftvalsub )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def pamp_char_async( self, sta_freq, sto_freq, spac_freq, samp_freq ):
        # execute cpmg sequence
        command = ( "pamp_char_async" + " " +
                   str( sta_freq ) + " " +
                   str( sto_freq ) + " " +
                   str( spac_freq ) + " " +
                   str( samp_freq )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def pamp_char_sync( self, sta_freq, sto_freq, spac_freq, fftpts, fftcmd, fftvalsub ):
        # execute cpmg sequence
        command = ( "pamp_char_sync" + " " +
                   str( sta_freq ) + " " +
                   str( sto_freq ) + " " +
                   str( spac_freq ) + " " +
                   str( fftpts ) + " " +
                   str( fftcmd ) + " " +
                   str( fftvalsub )
                   )

        if self.en_remote_computing:
            ssh_cmd = self.server_path + "c_exec/" + command
            exec_rmt_ssh_cmd_in_datadir( self.ssh, ssh_cmd, self.server_data_folder )
        else:
            os_command = ( self.work_dir + self.exec_folder + command )
            os.system( os_command )  # execute command & ignore its console

    def cpmgT1( self, cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_us, logsw, delay180_sta, delay180_sto, delay180_ste, ref_number_of_iteration, ref_twait_mult, data_folder, en_scan_fig, en_fig ):

        if self.en_remote_computing:

            print( "ERROR! cpmgT1 is not supported by remote data processing!" )

        else:

            # create t1 measurement folder
            t1_meas_folder = datetime.now().strftime( '%Y_%m_%d_%H_%M_%S' ) + '_t1_meas'
            os.mkdir( t1_meas_folder )
            t1_meas_hist = 't1_meas_hist.txt'  # the history file name for t1 measurement

            self.fig_num = 1
            self.fcpmg_to_fsys_mult = 16  # system_frequency/cpmg_frequency,set by fpga
            self.t1_opt_mult = 1.6

            # compute period for the system clock (which is multiplication of the cpmg
            # freq)
            t_sys = ( 1 / cpmg_freq ) / self.fcpmg_to_fsys_mult

            # compute pulse180_t1 in integer values and round it to
            # fcpmg_to_fsys_mult multiplication
            pulse180_t1_int = np.round( 
                ( pulse180_t1_us / t_sys ) / self.fcpmg_to_fsys_mult ) * self.fcpmg_to_fsys_mult

            # process delay
            if logsw:
                delay180_t1_sw = np.logspace( 
                    np.log10( delay180_sta ), np.log10( delay180_sto ), delay180_ste )
            else:
                delay180_t1_sw = np.linspace( 
                    delay180_sta, delay180_sto, delay180_ste )
            # make delay to be multiplication of fcpmg_to_fsys_mult
            delay180_t1_sw_int = np.round( ( delay180_t1_sw / t_sys ) /
                                          self.fcpmg_to_fsys_mult ) * self.fcpmg_to_fsys_mult

            # compute the reference and do cpmg
            ref_twait = ref_twait_mult * delay180_t1_sw_int[delay180_ste - 1]
            ref_twait_int = np.round( 
                ( ref_twait ) / self.fcpmg_to_fsys_mult ) * self.fcpmg_to_fsys_mult
            self.cpmgSequence( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                              echoes_per_scan, init_adc_delay_compensation, ref_number_of_iteration, ph_cycl_en, pulse180_t1_int, ref_twait_int )
            # process the data
            meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
            ( a_ref, _, a0_ref, snr_ref, T2_ref, noise_ref, res_ref, theta_ref, data_filt_ref, echo_avg_ref, Df, _ ) = compute_iterate( 
                data_folder, meas_folder[0], 0, 0, 0, en_scan_fig )

            # move the folder to t1 measurement folder and write history
            shutil.move( meas_folder[0], t1_meas_folder )
            write_text_append( t1_meas_folder, t1_meas_hist, meas_folder[0] )

            # make the loop
            a0_table = np.zeros( delay180_ste )  # normal format
            a0_table_decay = np.zeros( delay180_ste )  # decay format
            asum_table = np.zeros( delay180_ste )  # normal format
            asum_table_decay = np.zeros( delay180_ste )  # decay format
            for i in range( 0, delay180_ste ):
                delay180_t1_int = delay180_t1_sw_int[i]

                # do cpmg scan
                self.cpmgSequence( cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                                  echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int )
                # process the data (note that a0 and T2 is based on single
                # exponential fit)
                meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
                ( a, _, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, _ ) = compute_iterate( 
                    data_folder, meas_folder[0], 1, theta_ref, echo_avg_ref, en_scan_fig )

                # move the folder to t1 measurement folder and write history
                shutil.move( meas_folder[0], t1_meas_folder )
                write_text_append( t1_meas_folder, t1_meas_hist, meas_folder[0] )

                # interscan data store
                a0_table[i] = a0
                a0_table_decay[i] = a0_ref - a0
                asum_table[i] = np.mean( np.real( a ) )
                asum_table_decay[i] = np.mean( np.real( a_ref ) ) - np.mean( np.real( a ) )

                if en_fig:
                    print( 'Loading Figure' )
                    plt.ion()
                    fig = plt.figure( self.fig_num )
                    fig.clf()

                    ax = fig.add_subplot( 3, 1, 1 )
                    if logsw:
                        line1, = ax.semilogx( 
                            delay180_t1_sw[0:i + 1] / 1000, asum_table[0:i + 1], 'r-' )
                    else:
                        line1, = ax.plot( 
                            delay180_t1_sw[0:i + 1] / 1000, asum_table[0:i + 1], 'r-' )

                    # ax.set_xlim(-50, 0)
                    # ax.set_ylim(-50, 0)
                    ax.set_ylabel( 'Initial amplitude [a.u.]' )
                    ax.set_title( "T1 inversion recovery" )
                    ax.grid()

                    ax = fig.add_subplot( 3, 1, 2 )
                    if logsw:
                        line1, = ax.semilogx( 
                            delay180_t1_sw[0:i + 1] / 1000, asum_table_decay[0:i + 1], 'r-' )
                    else:
                        line1, = ax.plot( 
                            delay180_t1_sw[0:i + 1] / 1000, asum_table_decay[0:i + 1], 'r-' )
                    # ax.set_xlim(-50, 0)
                    # ax.set_ylim(-50, 0)
                    # ax.set_xlabel('Wait time [ms]')
                    ax.set_ylabel( 'Initial amplitude [a.u.]' )
                    ax.grid()

                    ax = fig.add_subplot( 3, 1, 3 )
                    ax.set_ylabel( 'Amplitude [a.u.]' )
                    ax.set_xlabel( 'Wait time [ms]' )
                    ax.grid()

                    fig.canvas.draw()
                    fig.canvas.flush_events()
                    print( 'Figure Loaded' )
            # save t1 data to csv file to be processed
            f = open( t1_meas_folder + '/' + 't1heel_in.csv', "w+" )
            for i in range( 0, delay180_ste ):
                f.write( "%f," % ( delay180_t1_sw[i] / 1000 ) )  # in milisecond
                f.write( "%f\n" % ( a0_table_decay[i] ) )
            f.close()

            # process t1 data
            self.doLaplaceInversion( t1_meas_folder + '/' + 't1heel_in.csv',
                                    t1_meas_folder )
            tvect, data = parse_csv_float2col( 
                t1_meas_folder, 't1heel_out.csv' )

            i_peaks = signal.find_peaks_cwt( data, np.arange( 1, 10 ) )

            t1_opt = tvect[max( i_peaks )]
            '''
            a_peaks = np.zeros(len(i_peaks))
            for i in range(0, len(i_peaks)):
                a_peaks[i] = data[i_peaks[i]]
    
            # find tvect in which the largest peak is found
            t1_opt = tvect[i_peaks[np.where(max(a_peaks))[0][0]]]  # in second
            '''

            if en_fig:
                ax = fig.add_subplot( 3, 1, 3 )
                if logsw:
                    line1, = ax.semilogx( np.multiply( tvect, 1000 ), data, 'r-' )
                else:
                    line1, = ax.plot( np.multiply( tvect, 1000 ), data, 'r-' )
                ax.set_ylabel( 'Amplitude [a.u.]' )
                ax.set_xlabel( 'Wait time [ms]' )
                ax.grid()
                fig.canvas.draw()

            # copy the measurement history script
            shutil.copy( 'measurement_history_matlab_script.txt', t1_meas_folder )

            return delay180_t1_sw, a0_table, a0_ref, asum_table, t1_opt, t1_meas_folder

''' OBSOLETE
    def setSignalPath( self ):  # ONLY VALID FOR v4.0 and below
        # activate transmitter and stuffs
        self.gnrl_cnt = self.gnrl_cnt | self.AMP_HP_LT1210_EN_msk | self.PAMP_IN_SEL_RX_msk | self.RX_IN_SEL_1_msk
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str( self.gnrl_cnt )
        )

    def turnOnPower( self ):  # ONLY VALID FOR v4.0 and below
        # Turn on power supply
        self.gnrl_cnt = self.PSU_15V_TX_P_EN_msk | self.PSU_15V_TX_N_EN_msk | self.PSU_5V_TX_N_EN_msk | self.PSU_5V_ADC_EN_msk | self.PSU_5V_ANA_P_EN_msk | self.PSU_5V_ANA_N_EN_msk
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str( self.gnrl_cnt )
        )

    def turnOffSystem( self ):  # ONLY VALID FOR v4.0 and below
        # Turn off matching network
        os.system(
            self.work_dir + self.exec_folder + "i2c_mtch_ntwrk" + " " +
            str( 0 ) + " " +
            str( 0 )
        )
        # Disable all power and path
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str( 0 )
        )
'''
