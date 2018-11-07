'''
Created on Nov 06, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import pydevd


class tunable_nmr_system_2018:
    def __init__(self, data_folder):
        # Output control signal to FPGA via I2C
        self.PSU_15V_TX_P_EN_ofst = (0)
        self.PSU_15V_TX_N_EN_ofst = (1)
        self.AMP_HP_LT1210_EN_ofst = (2)
        self.PSU_5V_TX_N_EN_ofst = (3)
        self.PAMP_IN_SEL_TEST_ofst = (4)
        self.PAMP_IN_SEL_RX_ofst = (5)
        self.GPIO_GEN_PURP_1_ofst = (6)
        self.PSU_5V_ADC_EN_ofst = (7)
        self.RX_AMP_GAIN_2_ofst = (8)
        self.RX_AMP_GAIN_1_ofst = (9)
        self.RX_AMP_GAIN_4_ofst = (10)
        self.RX_AMP_GAIN_3_ofst = (11)
        self.RX_IN_SEL_1_ofst = (12)
        self.RX_IN_SEL_2_ofst = (13)
        self.PSU_5V_ANA_P_EN_ofst = (14)
        self.PSU_5V_ANA_N_EN_ofst = (15)
        # Output control signal mask to FPGA via I2C
        self.PSU_15V_TX_P_EN_msk = (1 << self.PSU_15V_TX_P_EN_ofst)
        self.PSU_15V_TX_N_EN_msk = (1 << self.PSU_15V_TX_N_EN_ofst)
        self.AMP_HP_LT1210_EN_msk = (1 << self.AMP_HP_LT1210_EN_ofst)
        self.PSU_5V_TX_N_EN_msk = (1 << self.PSU_5V_TX_N_EN_ofst)
        self.PAMP_IN_SEL_TEST_msk = (1 << self.PAMP_IN_SEL_TEST_ofst)
        self.PAMP_IN_SEL_RX_msk = (1 << self.PAMP_IN_SEL_RX_ofst)
        self.GPIO_GEN_PURP_1_msk = (1 << self.GPIO_GEN_PURP_1_ofst)
        self.PSU_5V_ADC_EN_msk = (1 << self.PSU_5V_ADC_EN_ofst)
        self.RX_AMP_GAIN_2_msk = (1 << self.RX_AMP_GAIN_2_ofst)
        self.RX_AMP_GAIN_1_msk = (1 << self.RX_AMP_GAIN_1_ofst)
        self.RX_AMP_GAIN_4_msk = (1 << self.RX_AMP_GAIN_4_ofst)
        self.RX_AMP_GAIN_3_msk = (1 << self.RX_AMP_GAIN_3_ofst)
        self.RX_IN_SEL_1_msk = (1 << self.RX_IN_SEL_1_ofst)
        self.RX_IN_SEL_2_msk = (1 << self.RX_IN_SEL_2_ofst)
        self.PSU_5V_ANA_P_EN_msk = (1 << self.PSU_5V_ANA_P_EN_ofst)
        self.PSU_5V_ANA_N_EN_msk = (1 << self.PSU_5V_ANA_N_EN_ofst)

        # variables
        self.data_folder = data_folder
        self.exec_folder = "/c_exec/"

        # directories
        self.work_dir = os.getcwd()
        os.chdir(self.data_folder)

    def turnOnRemoteDebug(self):
        # remote debugger setup
        from pydevd_file_utils import setup_client_server_paths
        server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
        client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
        PATH_TRANSLATION = [(client_path, server_path)]
        setup_client_server_paths(PATH_TRANSLATION)
        pydevd.settrace("dajo-compaqsff")

    def initNmrSystem(self):
        os.system(self.work_dir + "/c_exec/init")

    def turnOnPower(self):
        # Turn on power supply
        self.gnrl_cnt = self.PSU_15V_TX_P_EN_msk | self.PSU_15V_TX_N_EN_msk | self.PSU_5V_TX_N_EN_msk | self.PSU_5V_ADC_EN_msk | self.PSU_5V_ANA_P_EN_msk | self.PSU_5V_ANA_N_EN_msk
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str(self.gnrl_cnt)
        )

    def setPreampTuning(self):
        # set preamp tuning
        self.vbias = -3.35
        self.vvarac = -1.2
        os.system(
            self.work_dir + self.exec_folder + "preamp_tuning" + " " +
            str(self.vbias) + " " +
            str(self.vvarac)
        )

    def setMatchingNetwork(self):
        # Turn on matching network
        self.cshunt = 110
        self.cseries = 175
        os.system(
            self.work_dir + self.exec_folder + "i2c_mtch_ntwrk" + " " +
            str(self.cshunt) + " " +
            str(self.cseries)
        )

    def setSignalPath(self):
        # activate transmitter and stuffs
        self.gnrl_cnt = self.gnrl_cnt | self.AMP_HP_LT1210_EN_msk | self.PAMP_IN_SEL_RX_msk | self.RX_IN_SEL_1_msk
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str(self.gnrl_cnt)
        )

    def turnOffSystem(self):
        # Turn off matching network
        os.system(
            self.work_dir + self.exec_folder + "i2c_mtch_ntwrk" + " " +
            str(0) + " " +
            str(0)
        )
        # Disable all power and path
        os.system(
            self.work_dir + self.exec_folder + "i2c_gnrl" + " " +
            str(0)
        )

    def cpmgSequence(self, cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int):
        # execute cpmg sequence
        command = (self.work_dir + self.exec_folder + "cpmg_iterate" + " " +
                   str(cpmg_freq) + " " +
                   str(pulse1_us) + " " +
                   str(pulse2_us) + " " +
                   str(pulse1_dtcl) + " " +
                   str(pulse2_dtcl) + " " +
                   str(echo_spacing_us) + " " +
                   str(scan_spacing_us) + " " +
                   str(samples_per_echo) + " " +
                   str(echoes_per_scan) + " " +
                   str(init_adc_delay_compensation) + " " +
                   str(number_of_iteration) + " " +
                   str(ph_cycl_en) + " " +
                   str(pulse180_t1_int) + " " +
                   str(delay180_t1_int)
                   )
        os.system(command)  # execute command & ignore its console
