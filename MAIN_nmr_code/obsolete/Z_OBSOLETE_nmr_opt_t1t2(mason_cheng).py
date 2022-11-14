
# New Sample
# T1T2 Optimization
# proposed by Mason & Cheng

#!/usr/bin/python

import os
import time
import numpy as np

from nmr_std_function.data_parser import parse_simple_info
from nmr_std_function.nmr_functions import compute_iterate
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.data_parser import parse_csv_float2col
from nmr_std_function.data_parser import parse_csv_float3col
from collections import deque
import matplotlib.pyplot as plt
from scipy import signal
import pydevd

# variables
data_folder = "/root/NMR_DATA"
# data_folder = "D:"
en_fig = 0
en_remote_dbg = 0


# remote debug setup
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\129.22.143.88\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [(client_path, server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    pydevd.settrace("dajo-compaqsff")

# system setup
nmrObj = tunable_nmr_system_2018(data_folder)

nmrObj.initNmrSystem()
nmrObj.turnOnPower()
nmrObj.setPreampTuning(-3.35, -1.4)
nmrObj.setMatchingNetwork(19, 66)
nmrObj.setSignalPath()

# optimization parameters
t2_opt_mult = 1

'''-----------Start T2 Optimization-------------------'''

while True:

    # cpmg settings
    cpmg_freq = 4.188  # 4.253 original
    pulse1_us = 2.5  # pulse pi/2 length
    pulse2_us = pulse1_us * 1.6  # pulse pi length
    pulse1_dtcl = 0.5  # useless with current code
    pulse2_dtcl = 0.5  # useless with current code
    echo_spacing_us = 100
    scan_spacing_us = 400000
    samples_per_echo = 64  # number of points
    echoes_per_scan = 5000  # number of echos
    init_adc_delay_compensation = 7  # acquisition shift microseconds
    number_of_iteration = 8  # number of averaging
    ph_cycl_en = 1
    pulse180_t1_int = 0
    delay180_t1_int = 0

    # do cpmg measurement
    nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                        echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
    # nmrObj.turnOffSystem()

    # do signal processing
    meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
    (a, _, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
        data_folder, meas_folder[0], 0, 0, 0, en_fig)

    # Average navg echoes
    navg = 100
    npts = int(np.floor(echoes_per_scan / navg))
    tmp1 = np.zeros(npts)
    tmp2 = np.zeros(npts)
    for j in range(0, npts):
        tmp1[j] = np.mean(np.real(a[j * navg:(j + 1) * navg - 1]))
        tmp2[j] = np.mean(t_echospace[j * navg:(j + 1) * navg - 1])
    echo_int = tmp1
    tvect_avg = tmp2

    # save t2 data to csv file to be processed
    f = open(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv', "w+")
    for i in range(len(tvect_avg)):
        f.write("%f," % (tvect_avg[i] * 1000))  # in milisecond
        f.write("%f\n" % (echo_int[i]))
    f.close()

    # process t2 data
    nmrObj.doLaplaceInversion(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv',
                              data_folder + '/' + meas_folder[0])
    tvect, data = parse_csv_float2col(
        data_folder + '/' + meas_folder[0], 't1heel_out.csv')

    # fitting data
    tvect1, data1, fit1 = parse_csv_float3col(
        data_folder + '/' + meas_folder[0], 't1heel_datafit.csv')
    plt.plot(tvect1, data1)
    plt.plot(tvect1, fit1)
    plt.show()

    # convert data to array
    tvectArray = np.array(tvect)
    dataArray = np.array(data)

    # null data after 2 s
    dataArray[tvectArray > 0.8] = 0

    # null data below echo_spacing
    dataArray[tvectArray < (echo_spacing_us / 1e6)] = 0

    i_peaks = signal.find_peaks_cwt(dataArray, np.arange(1, 10))

    '''
    a_peaks = np.zeros(len(i_peaks))
    for i in range(0, len(i_peaks)):
        a_peaks[i] = dataArray[i_peaks[i]]
    
    # find tvect in which the largest peak is found
    t2_opt = tvect[i_peaks[np.where(max(a_peaks))[0][0]]]  # in second
    '''

    t2_opt = tvectArray[max(i_peaks)]  # in second

    # adjust echoes_per_scan according to t2_opt
    echoes_per_scan = np.round((t2_opt * 1e6 * t2_opt_mult) / echo_spacing_us)

    t1_opt_echoes_per_scan = echoes_per_scan

    print('num of echoes: %d' % echoes_per_scan)
    print('t2Opt: %f' % t2_opt)
    print('t2OptMult: %f' % t2_opt_mult)
    plt.semilogx(tvect, dataArray)
    plt.show()

    # T1 Optimization
    # system setup
    '''
    --------T1 Optimization------------------------------------------------------------------
    '''
    #!/usr/bin/python

    import os
    import time
    import numpy as np
    import pydevd
    import matplotlib.pyplot as plt

    from nmr_std_function.data_parser import parse_simple_info
    from nmr_std_function.nmr_functions import compute_iterate
    from nmr_std_function.nmr_class import tunable_nmr_system_2018

    # variables
    data_folder = "/root/NMR_DATA"
    en_scan_fig = 0
    en_fig = 0
    en_remote_dbg = 0

    # remote debug setup
    if en_remote_dbg:
        from pydevd_file_utils import setup_client_server_paths
        server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
        client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
        PATH_TRANSLATION = [(client_path, server_path)]
        setup_client_server_paths(PATH_TRANSLATION)
        pydevd.settrace("dajo-compaqsff")

    # system setup
    '''
    
    nmrObj.initNmrSystem()
    
    nmrObj.setPreampTuning()
    nmrObj.setMatchingNetwork(19, 66)
    nmrObj.setSignalPath()
    
    nmrObj = tunable_nmr_system_2018(data_folder)
    nmrObj.turnOnPower()
    '''
    # cpmg settings
    cpmg_freq = 4.14
    pulse1_us = 2.5  # pulse pi/2 length
    pulse2_us = pulse1_us * 1.6  # pulse pi length
    pulse1_dtcl = 0.5  # useless with current code
    pulse2_dtcl = 0.5  # useless with current code
    echo_spacing_us = 100
    scan_spacing_us = t2_opt * 13 * 10.0 ** 6
    samples_per_echo = 64  # number of points
   # echoes_per_scan = 10000  # number of echos
    init_adc_delay_compensation = 10  # acquisition shift microseconds
    number_of_iteration = 4  # number of averaging
    ph_cycl_en = 1
    pulse180_t1_us = pulse2_us
    # sweep parameters
    logsw = 1  # logsw specifies logsweep, or otherwise linsweep
    delay180_sta = 100  # in microsecond
    delay180_sto = scan_spacing_us  # in microsecond
    delay180_ste = 10  # number of steps
    # reference parameters
    ref_number_of_iteration = 4  # number of averaging
    ref_twait_mult = 3  # wait time mult. from delay180_sto entered

    delay180_t1_sw, a0_table, a0_ref, asum_table, t1_opt = nmrObj.cpmgT1(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo, echoes_per_scan, init_adc_delay_compensation,
                                                                         number_of_iteration, ph_cycl_en, pulse180_t1_us, logsw, delay180_sta, delay180_sto, delay180_ste, ref_number_of_iteration, ref_twait_mult, data_folder, en_scan_fig, en_fig)

    pass

    '''
    -----------Continuous T2 Monitoring------------------------------------------------------------------
    '''

    print('t1Opt: %f' % t1_opt)

    t1t2 = t1_opt / t2_opt

    print('t1/t2: %f' % t1t2)

    counter = 0
    # iteration for T2
    while True:

        # cpmg settings
        en_fig = 0
        cpmg_freq = 4.188  # 4.253 original
        pulse1_us = 2.5  # pulse pi/2 length
        pulse2_us = pulse1_us * 1.6  # pulse pi length
        pulse1_dtcl = 0.5  # useless with current code
        pulse2_dtcl = 0.5  # useless with current code
        echo_spacing_us = 100
        scan_spacing_us = t1_opt * 10**6 * 1.6
        samples_per_echo = 64  # number of points
        echoes_per_scan = t1_opt_echoes_per_scan  # number of echos
        init_adc_delay_compensation = 7  # acquisition shift microseconds
        number_of_iteration = 8  # number of averaging
        ph_cycl_en = 1
        pulse180_t1_int = 0
        delay180_t1_int = 0

        # do cpmg measurement
        nmrObj.cpmgSequence(cpmg_freq, pulse1_us, pulse2_us, pulse1_dtcl, pulse2_dtcl, echo_spacing_us, scan_spacing_us, samples_per_echo,
                            echoes_per_scan, init_adc_delay_compensation, number_of_iteration, ph_cycl_en, pulse180_t1_int, delay180_t1_int)
        # nmrObj.turnOffSystem()

        # do signal processing
        meas_folder = parse_simple_info(data_folder, 'current_folder.txt')
        (a, _, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace) = compute_iterate(
            data_folder, meas_folder[0], 0, 0, 0, en_fig)

        # Average navg echoes
        navg = 100
        npts = int(np.floor(echoes_per_scan / navg))
        tmp1 = np.zeros(npts)
        tmp2 = np.zeros(npts)

        for j in range(0, npts):
            tmp1[j] = np.mean(np.real(a[j * navg:(j + 1) * navg - 1]))
            tmp2[j] = np.mean(t_echospace[j * navg:(j + 1) * navg - 1])
        echo_int = tmp1
        tvect_avg = tmp2

        EchoFirstHalf = np.sum(
            np.real(a[0:int(np.floor(len(np.real(a)) / 2)) - 1]))
        EchoSecondHalf = np.sum(
            np.real(a[int(np.floor(len(np.real(a)) / 2)):-1]))

        if counter == 0:
            queue_FirstHalf = deque([EchoFirstHalf, EchoFirstHalf])
            queue_SecondHalf = deque([EchoSecondHalf, EchoSecondHalf])
            std_FirstHalf = np.std(queue_FirstHalf)
            std_SecondHalf = np.std(queue_SecondHalf)
            mean_FirstHalf = np.mean(queue_FirstHalf)
            mean_SecondHalf = np.mean(queue_SecondHalf)
        elif counter > 0 and counter < 10:
            queue_FirstHalf.append(EchoFirstHalf)
            queue_SecondHalf.append(EchoSecondHalf)
            std_FirstHalf = np.std(queue_FirstHalf)
            std_SecondHalf = np.std(queue_SecondHalf)
            mean_FirstHalf = np.mean(queue_FirstHalf)
            mean_SecondHalf = np.mean(queue_SecondHalf)
        else:
            queue_FirstHalf.append(EchoFirstHalf)
            queue_FirstHalf.popleft()
            queue_SecondHalf.append(EchoSecondHalf)
            queue_SecondHalf.popleft()
            std_FirstHalf_tmp = np.std(queue_FirstHalf)
            std_SecondHalf_tmp = np.std(queue_SecondHalf)

            std_FirstHalf = np.std(queue_FirstHalf)
            std_SecondHalf = np.std(queue_SecondHalf)
            mean_FirstHalf = np.mean(queue_FirstHalf)
            mean_SecondHalf = np.mean(queue_SecondHalf)
            print('std_FirstHalf_tmp: %f' % std_FirstHalf)
            print('std_SecondHalf_tmp: %f' % std_SecondHalf)
            print('mean_FirstHalf_tmp: %f' % mean_FirstHalf)
            print('mean_SecondHalf_tmp: %f' % mean_SecondHalf)
            print('Mean-current: %f' % np.abs(mean_FirstHalf - EchoFirstHalf))
            # determine if the sample is switched, threshold 3* sigma
           # if std_FirstHalf * 3 < std_FirstHalf_tmp or std_SecondHalf * 3 <
           # std_SecondHalf_tmp:
            if std_FirstHalf * 3 < np.abs(mean_FirstHalf - EchoFirstHalf) or std_SecondHalf * 3 < np.abs(mean_SecondHalf - EchoSecondHalf):
                print('Sample swithed!')
                break

            else:
                std_FirstHalf = std_FirstHalf_tmp
                std_SecondHalf = std_SecondHalf_tmp

        counter = counter + 1
        print('Counter: %i' % counter)

        # under construction
        # save T1 and T2 data to csv file to be processed
        #f = open(data_folder + '/' + meas_folder[0] + '/' + 'T1T2.csv', "w+")
        # f.write("%f," % (T2))  # in milisecond
        #f.write("%f\n" % (T1_opt))
        # f.close()

    '''
    # save t2 data to csv file to be processed
    f = open(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv', "w+")
    for i in range(len(tvect_avg)):
        f.write("%f," % (tvect_avg[i] * 1000))  # in milisecond
        f.write("%f\n" % (echo_int[i]))
    f.close()
    
    
    # process t2 data
    print('Starting Laplace Inversion')
    nmrObj.doLaplaceInversion(data_folder + '/' + meas_folder[0] + '/' + 't2heel_in.csv',
                              data_folder + '/' + meas_folder[0])
    tvect, data = parse_csv_float2col(
        data_folder + '/' + meas_folder[0], 't1heel_out.csv')
    print('Laplace Inversion Done')
    # fitting data
    tvect1, data1, fit1 = parse_csv_float3col(
        data_folder + '/' + meas_folder[0], 't1heel_datafit.csv')
    
    
    print('Loading Fit Plot')
    plt.plot(tvect1, data1)
    plt.plot(tvect1, fit1)
    plt.show()
    print('Fit Plot Loaded')
    '''

    # question if want to contiune
    '''
    try:
        data = input("Sample switched. Press 'Y' to continue")
    except ValueError:
        print("Sorry. Didnt understand that.")
        continue

    if data == 'Y':
        print('Experiment Continue.')
    else:
        print('Experiment End.\n\n\n')
        break
    
    print('Done\n\n\n')
    '''
nmrObj.turnOffSystem()
