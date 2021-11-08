# this requires python 3.7+, and it doesn't work in older python

from builtins import int
from ctypes.wintypes import INT
from dataclasses import dataclass


@dataclass
class board_config:
    Df_MHz: float
    vbias: float
    vvarac: float
    cpar: int
    cser: int
    meas_bw_kHz: float
    dconv_lpf_ord: int
    pulse1_us: float
    pulse2_us: float
    echo_spacing_us: float
    scan_spacing_us: float
    samples_per_echo: int
    echoes_per_scan: int
    init_adc_delay_compensation: float


WMP_old_coil_1p65 = board_config( 
    1.65,  # Df_MHz
    -2.1,  # vbias
    4.4,  # vvarac
    380,  # cpar
    179,  # cser
    50,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float
 )

WMP_old_coil_1p7 = board_config( 
    1.695,  # Df_MHz
    -1.9,  # vbias
    4.6,  # vvarac
    350,  # cpar
    185,  # cser
    50,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float
 )

WMP_new_coil = board_config( 
    1.76,  # Df_MHz
    -2.5,  # vbias
    4.4,  # vvarac
    100,  # cpar
    139,  # cser
    50,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float
 )

WMP_double_coil = board_config( 
    1.76,  # Df_MHz
    -2.5,  # vbias
    4.4,  # vvarac
    160,  # cpar
    150,  # cser
    50,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float
 )

UF_black_holder_brown_coil_PCB02 = board_config( 
    4.2 + ( 30 ) * 1e-3,  # Df_MHz
    -2.1,  # vbias
    -0.4,  # vvarac
    2140,  # cpar
    498,  # cser
    200,  # meas_bw_kHz
    2,  # filter order
    2.8,  # pulse 90 length
    5.9,  # pulse 180 length
    200,  # echo_spacing_us: float
    200000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float
 )

UF_black_holder_brown_coil_PCB04 = board_config( 
    4.2 + ( -46 + 38 + 9 ) * 1e-3,  # Df_MHz
    -2.25,  # vbias
    2.1,  # vvarac
    2410,  # cpar
    462,  # cser
    200,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1024,  # samples_per_echo: int
    1024,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float

 )

UF_black_holder_brown_coil_PCB04__DELETEME = board_config( 
    4.2 + ( -46 + 38 + 9 ) * 1e-3,  # Df_MHz
    -2.25,  # vbias
    2.1,  # vvarac
    2410,  # cpar
    462,  # cser
    200,  # meas_bw_kHz
    2,  # filter order
    12,  # pulse 90 length
    16,  # pulse 180 length
    200,  # echo_spacing_us: float
    500000,  # scan_spacing_us: float
    1000,  # samples_per_echo: int
    60,  # echoes_per_scan: int
    6  # init_adc_delay_compensation: float

 )
