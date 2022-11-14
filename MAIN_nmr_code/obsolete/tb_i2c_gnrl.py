'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os

# variables
enable_remotedebug = 0

# remote debugger setup
if enable_remotedebug:
    import pydevd
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/Eclipse_Python_2018/nmr_pcb20_hdl10_2018/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\Eclipse_Python_2018\\nmr_pcb20_hdl10_2018\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("dajo-compaqsff")

work_dir = os.getcwd()

# Output control signal to FPGA via I2C
PSU_15V_TX_P_EN_ofst = (0)
PSU_15V_TX_N_EN_ofst = (1)
AMP_HP_LT1210_EN_ofst = (2)
PSU_5V_TX_N_EN_ofst = (3)
PAMP_IN_SEL_TEST_ofst = (4)
PAMP_IN_SEL_RX_ofst = (5)
GPIO_GEN_PURP_1_ofst = (6)
PSU_5V_ADC_EN_ofst = (7)
RX_AMP_GAIN_2_ofst = (8)
RX_AMP_GAIN_1_ofst = (9)
RX_AMP_GAIN_4_ofst = (10)
RX_AMP_GAIN_3_ofst = (11)
RX_IN_SEL_1_ofst = (12)
RX_IN_SEL_2_ofst = (13)
PSU_5V_ANA_P_EN_ofst = (14)
PSU_5V_ANA_N_EN_ofst = (15)

# Output control signal mask to FPGA via I2C
PSU_15V_TX_P_EN_msk = (1 << PSU_15V_TX_P_EN_ofst)
PSU_15V_TX_N_EN_msk = (1 << PSU_15V_TX_N_EN_ofst)
AMP_HP_LT1210_EN_msk = (1 << AMP_HP_LT1210_EN_ofst)
PSU_5V_TX_N_EN_msk = (1 << PSU_5V_TX_N_EN_ofst)
PAMP_IN_SEL_TEST_msk = (1 << PAMP_IN_SEL_TEST_ofst)
PAMP_IN_SEL_RX_msk = (1 << PAMP_IN_SEL_RX_ofst)
GPIO_GEN_PURP_1_msk = (1 << GPIO_GEN_PURP_1_ofst)
PSU_5V_ADC_EN_msk = (1 << PSU_5V_ADC_EN_ofst)
RX_AMP_GAIN_2_msk = (1 << RX_AMP_GAIN_2_ofst)
RX_AMP_GAIN_1_msk = (1 << RX_AMP_GAIN_1_ofst)
RX_AMP_GAIN_4_msk = (1 << RX_AMP_GAIN_4_ofst)
RX_AMP_GAIN_3_msk = (1 << RX_AMP_GAIN_3_ofst)
RX_IN_SEL_1_msk = (1 << RX_IN_SEL_1_ofst)
RX_IN_SEL_2_msk = (1 << RX_IN_SEL_2_ofst)
PSU_5V_ANA_P_EN_msk = (1 << PSU_5V_ANA_P_EN_ofst)
PSU_5V_ANA_N_EN_msk = (1 << PSU_5V_ANA_N_EN_ofst)

# Turn on power supply
gnrl_cnt = PSU_15V_TX_P_EN_msk | PSU_15V_TX_N_EN_msk | PSU_5V_TX_N_EN_msk | PSU_5V_ADC_EN_msk | PSU_5V_ANA_P_EN_msk | PSU_5V_ANA_N_EN_msk
os.system(
    work_dir + "/c_exec/i2c_gnrl" + " " +
    str(gnrl_cnt)
)

'''
# Turn off power supply
os.system(
    work_dir + "/c_exec/i2c_gnrl" + " " +
    str(0)
)
'''