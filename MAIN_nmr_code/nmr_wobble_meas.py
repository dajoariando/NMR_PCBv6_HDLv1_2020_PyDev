'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_wobble
from nmr_std_function.data_parser import parse_simple_info

# variables
data_parent_folder = "/root/NMR_DATA"
enable_remotedebug = 0
fig_num = 1

# remote debugger setup
if enable_remotedebug:
    import pydevd
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("dajo-compaqsff")

work_dir = os.getcwd()
os.chdir(data_parent_folder)

en_fig = 1

# init system
os.system(work_dir + '/c_exec/init')

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

# activate transmitter and stuffs
gnrl_cnt = gnrl_cnt | RX_IN_SEL_2_msk
os.system(
    work_dir + "/c_exec/i2c_gnrl" + " " +
    str(gnrl_cnt)
)

# Turn on matching network
cshunt = 19
cseries = 66
os.system(
    work_dir + "/c_exec/i2c_mtch_ntwrk" + " " +
    str(cshunt) + " " +
    str(cseries)
)

while True:
    gnrl_cnt = gnrl_cnt | AMP_HP_LT1210_EN_msk | PSU_15V_TX_P_EN_msk | PSU_15V_TX_N_EN_msk
    os.system(
        work_dir + "/c_exec/i2c_gnrl" + " " +
        str(gnrl_cnt)
    )

    startfreq = 4
    stopfreq = 4.5
    spacfreq = 0.05
    sampfreq = 25
    os.system(
        work_dir + "/c_exec/wobble" + " " +
        str(startfreq) + " " +
        str(stopfreq) + " " +
        str(spacfreq) + " " +
        str(sampfreq)
    )

    gnrl_cnt = gnrl_cnt & (
        ~(AMP_HP_LT1210_EN_msk | PSU_15V_TX_P_EN_msk | PSU_15V_TX_N_EN_msk))
    os.system(
        work_dir + "/c_exec/i2c_gnrl" + " " +
        str(gnrl_cnt)
    )

    S11_min = -10
    meas_folder = parse_simple_info(data_parent_folder, 'current_folder.txt')
    # meas_folder[0] = "nmr_wobb_2018_06_25_12_44_48"

    S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = compute_wobble(
        data_parent_folder, meas_folder[0], S11_min, en_fig, fig_num)
    print('fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f} minS11={3:0.2f} minS11_freq={4:0.2f}'.format(
        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq))

    time.sleep(1)
