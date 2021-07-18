# this requires python 3.7+, and it doesn't work in older python

from dataclasses import dataclass


@dataclass
class board_config:
    Df_MHz: float
    vbias: float
    vvarac: float
    cpar: int
    cser: int
    meas_bw_kHz: float


WMP_old_coil = board_config( 
    1.74,  # Df_MHz
    -2.1,  # vbias
    4.4,  # vvarac
    308,  # cpar
    175,  # cser
    50  # meas_bw_kHz
 )

WMP_old_coil_1p7 = board_config( 
    1.695,  # Df_MHz
    -1.9,  # vbias
    4.6,  # vvarac
    350,  # cpar
    185,  # cser
    50  # meas_bw_kHz
 )

WMP_new_coil = board_config( 
    1.76,  # Df_MHz
    -2.5,  # vbias
    4.4,  # vvarac
    100,  # cpar
    139,  # cser
    50  # meas_bw_kHz
 )

WMP_double_coil = board_config( 
    1.76,  # Df_MHz
    -2.5,  # vbias
    4.4,  # vvarac
    160,  # cpar
    150,  # cser
    50  # meas_bw_kHz
 )

