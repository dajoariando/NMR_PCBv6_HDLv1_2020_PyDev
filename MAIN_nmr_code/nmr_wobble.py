'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os
import time

from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_functions import compute_wobble
from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_class import tunable_nmr_system_2018

# variables
data_parent_folder = "/root/NMR_DATA"
en_remote_dbg = 1
fig_num = 1
en_fig = 1

# measurement properties
sta_freq = 3
sto_freq = 5
spac_freq = 0.01
samp_freq = 25

# instantiate nmr object
nmrObj = tunable_nmr_system_2018(data_parent_folder, en_remote_dbg)

work_dir = os.getcwd()
os.chdir(data_parent_folder)

# system setup
nmrObj.initNmrSystem()  # necessary to set the GPIO initial setting
# nmrObj.turnOnPower()
nmrObj.assertControlSignal(nmrObj.PSU_5V_TX_N_EN_msk |
                           nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                           nmrObj.PSU_5V_ANA_N_EN_msk)


# nmrObj.setPreampTuning(-2.93, 3.7)  # for 2.43MHz BLACK
# nmrObj.setPreampTuning(-3.1, -4.2)  # for 1.87MHz BLACK
# nmrObj.setMatchingNetwork(2700, 350)  # for 2.43MHz BLACK
# nmrObj.setMatchingNetwork(3180, 420)  # for 1.87MHz BLACK
# nmrObj.setMatchingNetwork(255, 76)  # 4.05 MHz
# nmrObj.setMatchingNetwork(189, 74)  # 4.17 MHz KeA
# nmrObj.setPreampTuning(-2.9, -0)
# nmrObj.setMatchingNetwork(192, 74)  # 4.17 MHz AFE
nmrObj.setPreampTuning(-2.7, 0.3)
nmrObj.setMatchingNetwork(2390, 500)

while True:
    nmrObj.assertControlSignal(nmrObj.RX1_2L_msk | nmrObj.RX1_2H_msk | nmrObj.RX_SEL2_msk |
                               nmrObj.RX_FL_msk | nmrObj.RX_FH_msk)
    nmrObj.assertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                               nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                               nmrObj.PSU_5V_ANA_N_EN_msk)
    time.sleep(0.1)

    nmrObj.wobble(sta_freq, sto_freq, spac_freq, samp_freq)

    nmrObj.deassertControlSignal(nmrObj.RX1_2L_msk | nmrObj.RX1_2H_msk | nmrObj.RX_SEL2_msk |
                                 nmrObj.RX_FL_msk | nmrObj.RX_FH_msk)
    nmrObj.deassertControlSignal(nmrObj.PSU_15V_TX_P_EN_msk | nmrObj.PSU_15V_TX_N_EN_msk | nmrObj.PSU_5V_TX_N_EN_msk |
                                 nmrObj.PSU_5V_ADC_EN_msk | nmrObj.PSU_5V_ANA_P_EN_msk |
                                 nmrObj.PSU_5V_ANA_N_EN_msk)

    S11_min = -10
    meas_folder = parse_simple_info(data_parent_folder, 'current_folder.txt')
    # meas_folder[0] = "nmr_wobb_2018_06_25_12_44_48"

    S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = compute_wobble(
        data_parent_folder, meas_folder[0], S11_min, en_fig, fig_num)
    print('fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f} minS11={3:0.2f} minS11_freq={4:0.2f}'.format(
        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq))
