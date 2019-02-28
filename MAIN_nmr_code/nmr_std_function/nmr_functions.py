import math
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from nmr_std_function import data_parser
from nmr_std_function.signal_proc import down_conv
from nmr_std_function.data_parser import convert_to_prospa_data_t1
from nmr_std_function.signal_proc import nmr_fft


def compute_wobble(data_parent_folder, meas_folder, s11_min, en_fig, fig_num):
    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    freqSta = data_parser.find_value('freqSta', param_list, value_list)
    freqSto = data_parser.find_value('freqSto', param_list, value_list)
    freqSpa = data_parser.find_value('freqSpa', param_list, value_list)
    nSamples = data_parser.find_value('nSamples', param_list, value_list)
    freqSamp = data_parser.find_value('freqSamp', param_list, value_list)
    spect_bw = (freqSamp / nSamples) * 8

    file_name_prefix = 'wobbdata_'
    freqSw = np.arange(freqSta, freqSto, freqSpa)
    S11 = np.zeros(len(freqSw))
    for m in range(0, len(freqSw)):
        # for m in freqSw:
        file_path = (data_folder + file_name_prefix +
                     '{:4.3f}'.format(freqSw[m]))
        one_scan = np.array(data_parser.read_data(file_path))
        spectx, specty = nmr_fft(one_scan, freqSamp, 0)

        # FIND INDEX WHERE THE MAXIMUM SIGNAL IS PRESENT
        # PRECISE METHOD: find reflection at the desired frequency: creating precision problem where usually the signal shift a little bit from its desired frequency
        # ref_idx = abs(spectx - freqSw[m]) == min(abs(spectx - freqSw[m]))
        # BETTER METHOD: find reflection signal peak around the bandwidth
        ref_idx = (abs(spectx - freqSw[m]) <= spect_bw)

        S11[m] = max(specty[ref_idx])  # find reflection peak

    S11 = 20 * np.log10(S11 / max(S11))  # convert to dB scale
    S11_min10dB = (S11 <= s11_min)

    minS11 = min(S11)
    minS11_freq = freqSw[np.argmin(S11)]

    try:
        S11_fmin = min(freqSw[S11_min10dB])
        S11_fmax = max(freqSw[S11_min10dB])
    except:
        S11_fmin = 0
        S11_fmax = 0
        print('S11 requirement is not satisfied...')

    S11_bw = S11_fmax - S11_fmin

    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(1, 1, 1)
        line1, = ax.plot(freqSw, S11, 'r-')
        ax.set_ylim(-50, 0)
        ax.set_xlabel('Frequency [MHz]')
        ax.set_ylabel('S11 [dB]')
        ax.set_title("Reflection Measurement (S11) Parameter")
        ax.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()

        # old code, freeze after plotting
        # plt.figure(fig_num)
        # plt.plot(freqSw, S11)
        # plt.title("Reflection Measurement (S11) Parameter")
        # plt.xlabel('Frequency [MHz]')
        # plt.ylabel('S11 [dB]')
        # plt.grid()
        # plt.show()

    # print(S11_fmin, S11_fmax, S11_bw)
    return S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq


def compute_multiple(data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, direct_read, datain):

    # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # filename_prefix   : the name of data prefix
    # Df                : data frequency
    # Sf                : sample frequency
    # tE                : echo spacing
    # total_scan        : number_of_iteration
    # en_fig            : enable figure
    # en_ext_param      : enable external parameter for data signal processing
    # thetaref          : external parameter : rotation angle
    # echoref_avg        : external parameter : echo average reference
    # datain            : the data captured direct reading. data format: AC,averaged scans, phase-cycled
    # direct_read        : perform direct reading from SDRAM/FIFO

    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    # variables local to this function
    # the setting file for the measurement
    mtch_fltr_sta_idx = 0  # 0 is default or something referenced to SpE, e.g. SpE/4; the start index for match filtering is to neglect ringdown part from calculation
    # perform rotation to the data -> required for reference data for t1
    # measurement
    perform_rotation = 1
    # process individual raw data, otherwise it'll load a sum file generated
    # by C
    proc_indv_data = 0

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    SpE = int(data_parser.find_value(
        'nrPnts', param_list, value_list))
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    en_ph_cycle_proc = data_parser.find_value(
        'usePhaseCycle', param_list, value_list)
    # tE = data_parser.find_value('echoTimeRun', param_list, value_list)
    # Sf = data_parser.find_value(
    #    'adcFreq', param_list, value_list) * 1e6
    # Df = data_parser.find_value(
    #    'b1Freq', param_list, value_list) * 1e6
    # total_scan = int(data_parser.find_value(
    #    'nrIterations', param_list, value_list))

    # parse file and remove DC component
    if (direct_read):
        data = datain
    else:
        if (proc_indv_data):
            # read all datas and average it
            data = np.zeros(NoE * SpE)
            for m in range(1, total_scan + 1):
                file_path = (data_folder + file_name_prefix +
                             '{0:03d}'.format(m))
                # read the data from the file and store it in numpy array
                # format
                one_scan = np.array(data_parser.read_data(file_path))
                one_scan = (one_scan - np.mean(one_scan)) / \
                    total_scan  # remove DC component
                if (en_ph_cycle_proc):
                    if (m % 2):  # phase cycling every other scan
                        data = data - one_scan
                    else:
                        data = data + one_scan
                else:
                    data = data + one_scan
        else:
            # read sum data only
            file_path = (data_folder + 'asum')
            data = np.zeros(NoE * SpE)
            data = np.array(data_parser.read_data(file_path))
            data = (data - np.mean(data)) / \
                total_scan  # remove DC component

    if en_fig:  # plot the averaged scan
        echo_space = (1 / Sf) * np.linspace(1, SpE, SpE)  # in s
        plt.figure(1)
        for i in range(1, NoE + 1):
            plt.plot(((i - 1) * tE * 1e-6 + echo_space) * 1e3,
                     data[(i - 1) * SpE:i * SpE], linewidth=0.4)

    # filter the data
    data_filt = np.zeros((NoE, SpE), dtype=complex)
    for i in range(0, NoE):
        data_filt[i, :] = down_conv(data[i * SpE:(i + 1) * SpE], i, tE, Df, Sf)

    # scan rotation
    if en_ext_param:
        data_filt = data_filt * np.exp(-1j * thetaref)
        theta = math.atan2(np.sum(np.imag(data_filt)),
                           np.sum(np.real(data_filt)))
    else:
        theta = math.atan2(np.sum(np.imag(data_filt)),
                           np.sum(np.real(data_filt)))
        if perform_rotation:
            data_filt = data_filt * np.exp(-1j * theta)

    if en_fig:  # plot filtered data
        echo_space = (1 / Sf) * np.linspace(1, SpE, SpE)  # in s
        plt.figure(2)
        for i in range(0, NoE):
            plt.plot((i * tE * 1e-6 + echo_space) * 1e3,
                     np.real(data_filt[i, :]), 'b', linewidth=0.4)
            plt.plot((i * tE * 1e-6 + echo_space) * 1e3,
                     np.imag(data_filt[i, :]), 'r', linewidth=0.4)

    # find echo average, echo magnitude
    echo_avg = np.zeros(SpE, dtype=complex)
    for i in range(0, NoE):
        echo_avg += (data_filt[i, :] / NoE)

    if en_fig:  # plot echo shape
        plt.figure(3)
        tacq = (1 / Sf) * 1e6 * np.linspace(1, SpE, SpE)  # in uS
        plt.plot(tacq, np.abs(echo_avg), label='abs')
        plt.plot(tacq, np.real(echo_avg), label='real part')
        plt.plot(tacq, np.imag(echo_avg), label='imag part')
        plt.xlim(0, max(tacq))
        plt.title("Echo Shape")
        plt.xlabel('time(uS)')
        plt.ylabel('amplitude')
        plt.legend()

        # plot fft of the echosum
        plt.figure(4)
        zf = 8  # zero filling factor to get smooth curve
        ws = 2 * np.pi / (tacq[1] - tacq[0])  # in MHz
        wvect = np.linspace(-ws / 2, ws / 2, len(tacq) * zf)
        echo_zf = np.zeros(zf * len(echo_avg), dtype=complex)
        echo_zf[int((zf / 2) * len(echo_avg) - len(echo_avg) / 2)                : int((zf / 2) * len(echo_avg) + len(echo_avg) / 2)] = echo_avg
        spect = zf * (np.fft.fftshift(np.fft.fft(np.fft.ifftshift(echo_zf))))
        plt.plot(wvect / (2 * np.pi), np.real(spect),
                 label='real')
        plt.plot(wvect / (2 * np.pi), np.imag(spect),
                 label='imag')
        plt.xlim(4 / max(tacq) * -1, 4 / max(tacq) * 1)
        plt.title("fft of the echo-sum")
        plt.xlabel('offset frequency(MHz)')
        plt.ylabel('Echo amplitude (a.u.)')
        plt.legend()

    # matched filtering
    a = np.zeros(NoE, dtype=complex)
    for i in range(0, NoE):
        if en_ext_param:
            a[i] = np.mean(np.multiply(data_filt[i, mtch_fltr_sta_idx:SpE], np.conj(
                echoref_avg[mtch_fltr_sta_idx:SpE])))  # find amplitude with reference matched filtering
        else:
            a[i] = np.mean(np.multiply(data_filt[i, mtch_fltr_sta_idx:SpE], np.conj(
                echo_avg[mtch_fltr_sta_idx:SpE])))  # find amplitude with matched filtering

    a_integ = np.sum(np.real(a))

    t_echospace = tE / 1e6 * np.linspace(1, NoE, NoE)

    # def exp_func(x, a, b, c, d):
    #    return a * np.exp(-b * x) + c * np.exp(-d * x)
    def exp_func(x, a, b):
        return a * np.exp(-b * x)

    # average the first 5% of datas
    a_guess = np.mean(np.real(a[0:int(np.round(SpE / 20))]))
    #c_guess = a_guess
    # find min idx value where the value of (a_guess/exp) is larger than
    # real(a)
    # b_guess = np.where(np.real(a) == np.min(
    #    np.real(a[np.real(a) > a_guess / np.exp(1)])))[0][0] * tE / 1e6
    # this is dummy b_guess, use the one I made above this for smarter one
    # (but sometimes it doesn't work)
    b_guess = 10
    #d_guess = b_guess
    #guess = np.array([a_guess, b_guess, c_guess, d_guess])
    guess = np.array([a_guess, b_guess])

    try:
        popt, pocv = curve_fit(exp_func, t_echospace, np.real(a), guess)
        a0 = popt[0]
        T2 = 1 / popt[1]
        # Estimate SNR/echo/scan
        f = exp_func(t_echospace, *popt)  # curve fit
        noise = np.std(np.imag(a))
        res = np.std(np.real(a) - f)
        snr = a0 / (noise * math.sqrt(total_scan))

        if en_fig:
            # plot data
            plt.figure(5)
            plt.cla()
            # plot in milisecond
            plt.plot(t_echospace * 1e3, np.real(a), label="real")
            # plot in milisecond
            plt.plot(t_echospace * 1e3, np.imag(a), label="imag")

            # plot fitted line
            plt.figure(5)
            plt.plot(t_echospace * 1e3, f, label="fit")  # plot in milisecond
            plt.plot(t_echospace * 1e3, np.real(a) - f, label="residue")
            #plt.set(gca, 'FontSize', 12)
            plt.legend()
            plt.title('Filtered data')
            plt.xlabel('Time (mS)')
            plt.ylabel('Amplitude')

        if en_fig:
            plt.show()
    except:
        print('Problem in fitting. Set a0 and T2 output to 0\n')
        a0 = 0
        T2 = 0
        noise = 0
        res = 0
        snr = 0

    print('a0 = ' + '{0:.2f}'.format(a0))
    print('SNR/echo/scan = ' + '{0:.2f}'.format(snr))
    print('T2 = ' + '{0:.4f}'.format(T2 * 1e3) + ' msec')

    return (a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace)


def compute_iterate(data_parent_folder, meas_folder, en_ext_param, thetaref, echoref_avg, direct_read, datain, en_fig):

    data_folder = (data_parent_folder + '/' + meas_folder + '/')
    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    SpE = int(data_parser.find_value(
        'nrPnts', param_list, value_list))
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    en_ph_cycle_proc = data_parser.find_value(
        'usePhaseCycle', param_list, value_list)
    tE = data_parser.find_value('echoTimeRun', param_list, value_list)
    Sf = data_parser.find_value(
        'adcFreq', param_list, value_list) * 1e6
    Df = data_parser.find_value(
        'b1Freq', param_list, value_list) * 1e6
    total_scan = int(data_parser.find_value(
        'nrIterations', param_list, value_list))
    file_name_prefix = 'dat_'
    # en_ext_param = 0
    # thetaref = 0
    # echoref_avg = 0

    if (direct_read):
        (a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace) = compute_multiple(data_parent_folder, meas_folder, file_name_prefix,
                                                                                                          Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, direct_read, datain)
    else:
        (a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, t_echospace) = compute_multiple(data_parent_folder, meas_folder, file_name_prefix,
                                                                                                          Df, Sf, tE, total_scan, en_fig, en_ext_param, thetaref, echoref_avg, 0, datain)

    # print(snr, T2)
    return a, a_integ, a0, snr, T2, noise, res, theta, data_filt, echo_avg, Df, t_echospace


def compute_noise(data_parent_folder, meas_folder, en_fig):

    # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # en_fig            : enable figure

    file_name_prefix = 'dat_'
    data_folder = (data_parent_folder + '/' + meas_folder + '/')
    fig_num = 200

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    adcFreq = int(data_parser.find_value(
        'adcFreq', param_list, value_list))
    nrPnts = int(data_parser.find_value(
        'nrPnts', param_list, value_list))
    total_scan = int(data_parser.find_value(
        'nrIterations', param_list, value_list))

    # parse file and remove DC component
    data = np.zeros(nrPnts)
    for m in range(1, total_scan + 1):
        file_path = (data_folder + file_name_prefix + '{0:03d}'.format(m))
        # read the data from the file and store it in numpy array format
        one_scan = np.array(data_parser.read_data(file_path))
        # one_scan = (one_scan - np.mean(one_scan)) / \
        #   total_scan  # remove DC component
        data = data + one_scan

    spectx, specty = nmr_fft(one_scan, adcFreq, 0)
    if en_fig:
        plt.ion()
        fig = plt.figure(fig_num)
        fig.clf()
        ax = fig.add_subplot(2, 1, 1)
        line1, = ax.plot(spectx, specty, 'r-')
        # ax.set_ylim(-50, 0)
        ax.set_xlabel('Frequency [MHz]')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title("Noise spectrum")
        ax.grid()

        ax = fig.add_subplot(2, 1, 2)
        line1, = ax.plot(data, 'r-')
        ax.set_xlabel('Time')
        ax.set_ylabel('Amplitude [a.u.]')
        ax.set_title("Noise amplitude")
        ax.grid()

        fig.canvas.draw()
        fig.canvas.flush_events()


''' OBSOLETE
def compute_freqsw(data_parent_folder, meas_folder, T2bound, en_figure):
    # POTENTIAL PROBLEM : stop_parameter (frequency) is not included in the
    # process

    # # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # SpF                : sample per frequency
    # en_figure          : enable figure

    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, 'acqu.par')  # read file
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    total_scan = int(data_parser.find_value(
        'nrIterations', param_list, value_list))
    start_param = data_parser.find_value(
        'b1Freq_sta', param_list, value_list)
    stop_param = data_parser.find_value(
        'b1Freq_sto', param_list, value_list)
    spacing_param = data_parser.find_value(
        'b1Freq_spa', param_list, value_list)
    tE = data_parser.find_value(
        'echoTimeRun', param_list, value_list)

    sweep_param = np.arange(start_param, stop_param, spacing_param)
    a = np.zeros((len(sweep_param), NoE), dtype=complex)
    a_init = np.zeros(len(sweep_param))
    snr = np.zeros(len(sweep_param))
    T2 = np.zeros(len(sweep_param))
    noise = np.zeros(len(sweep_param))
    for m in range(0, len(sweep_param)):
        print('freq: ' + str(sweep_param[m]) + ' MHz')
        file_name_prefix = 'dat_' + '{0:06.3f}'.format(sweep_param[m]) + '_'
        (a[m, :], a_init[m], snr[m], T2[m], noise[m], _, _, _, _) = compute_multiple(data_parent_folder, meas_folder,
                                                                                     file_name_prefix, sweep_param[m] * 1e6, sweep_param[m] * 4 * 1e6, tE, total_scan, 0, 0, 0, 0)
        print('--------------------------------------')

    if en_figure:
        plt.figure(5)
        plt.plot(sweep_param, np.mean(np.real(a), axis=1))
        plt.title('Echo average with frequency')
        #set(gca, 'FontSize', 12)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Amplitude')

        plt.figure(6)
        plt.plot(sweep_param, a_init)
        plt.title('Initial amplitude with frequency')
        #set(gca, 'FontSize', 12)
        plt.xlabel('Frequency (MHz)')
        plt.ylabel('Amplitude')

        plt.show()

    validT2Idx = ((T2 > min(T2bound)) & (T2 < max(T2bound)))

    # find index of max a_init
    # opt_freq_idx = np.argwhere(a_init == max(a_init[validT2Idx]))[0][0]

    # find index of max snr
    opt_freq_idx = np.argwhere(snr == max(snr[validT2Idx]))[0][0]

    opt_freq = sweep_param[opt_freq_idx]
    # opt_freq = sweep_param[np.argmax(a_init)]
    return opt_freq


def compute_generalsw(data_parent_folder, meas_folder, analysis, en_fig):
    # this general sweep is to sweep variables without frequency change
    # nothing is change in compute_multiple loop below, so it's easier to
    # manage

    # POTENTIAL PROBLEM : stop_parameter (frequency) is not included in the
    # process

    # # variables to be input
    # data_parent_folder : the folder for all datas
    # meas_folder        : the specific folder for one measurement
    # SpF                : sample per frequency
    # en_fig          : enable figure

    data_folder = (data_parent_folder + '/' + meas_folder + '/')

    # this statement is not for technical purpose, but to easily manage
    # different kind of measurement with only one general sweep function :
    # the compute_generalsw. These parameters are generally for choosing
    # the correct setting file, parameter in the setting, axis name, and
    # verbose info
    if analysis == 't1_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'minTau'
        stop_param_name = 'maxTau'
        step_param_name = 'tauSteps'
        param_info = 'current delay 180 for t1 in us: '
        param_scaler = 1e-6
        param_unit = 's'
        figure_xlabel = 'delay 180 (s)'
    elif analysis == 'pulse1_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'pulse1_us_start'
        stop_param_name = 'pulse1_us_stop'
        step_param_name = 'pulse1_us_spacing'
        param_info = 'current pulse1_us : '
        param_scaler = 1
        param_unit = 'us'
        figure_xlabel = 'pulse1 length (us)'
    elif analysis == 'pulse2_sweep':
        file_info_name = 'acqu.par'
        start_param_name = 'pulse2_us_start'
        stop_param_name = 'pulse2_us_stop'
        step_param_name = 'pulse2_us_spacing'
        param_info = 'current pulse2_us : '
        param_scaler = 1
        param_unit = 'us'
        figure_xlabel = 'pulse2 length (us)'
    else:
        print('wrong analysis')

    # variables from NMR settings
    (param_list, value_list) = data_parser.parse_info(
        data_folder, file_info_name)  # read file
    tE = data_parser.find_value('echoTimeRun', param_list, value_list)
    NoE = int(data_parser.find_value(
        'nrEchoes', param_list, value_list))
    Df = data_parser.find_value('b1Freq', param_list, value_list) * 1e6
    Sf = data_parser.find_value('adcFreq', param_list, value_list) * 1e6
    start_param = data_parser.find_value(
        start_param_name, param_list, value_list) * 1e3
    stop_param = data_parser.find_value(
        stop_param_name, param_list, value_list) * 1e3
    nsteps = data_parser.find_value(
        step_param_name, param_list, value_list)
    logspaceyesno = int(data_parser.find_value(
        'logSpace', param_list, value_list))
    nrIterations = int(data_parser.find_value(
        'nrIterations', param_list, value_list))

    if logspaceyesno:
        sweep_param = np.logspace(
            np.log10(start_param), np.log10(stop_param), nsteps)
    else:
        sweep_param = np.linspace(start_param, stop_param, nsteps)

    # compute reference
    file_name_prefix = 'datref_'
    (aref, aref_init, snrref, T2ref, noiseref, resref, thetaref, data_filt_ref, echo_avg_ref) = compute_multiple(
        data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, nrIterations, False, 0, 0, 0)

    # compute data
    a = np.zeros((len(sweep_param), NoE), dtype=complex)
    a_init = np.zeros(len(sweep_param))
    snr = np.zeros(len(sweep_param))
    T2 = np.zeros(len(sweep_param))
    noise = np.zeros(len(sweep_param))
    for m in range(0, len(sweep_param)):
        print(param_info + str(sweep_param[m] * param_scaler) + param_unit)
        file_name_prefix = 'dat_' + '{0:5.3f}'.format(sweep_param[m]) + '_'
        (a[m, :], a_init[m], snr[m], T2[m], noise[m], _, _, _, _) = compute_multiple(
            data_parent_folder, meas_folder, file_name_prefix, Df, Sf, tE, nrIterations, False, 1, thetaref, echo_avg_ref)
        if analysis == 't1_sweep':
            # subtract the signal with the reference
            a[m, :] = aref - a[m, :]
            a_init[m] = aref_init - a_init[m]
        print('--------------------------------------')

    write_csv = True
    convert_to_prospa_data_t1(a, data_folder, write_csv)

    a_sum = np.zeros((len(sweep_param), 2), dtype=float)
    for i in range(0, len(sweep_param)):
        a_sum[i, 0] = sweep_param[i] / 1e6 * 1e3
        a_sum[i, 1] = np.real(np.sum(a[i]))
    with open(data_folder + 'data_t1heel.csv', 'w', newline='') as csvfile:
        filewriter = csv.writer(csvfile, delimiter=',')
        for i in range(0, len(sweep_param)):
            filewriter.writerow(a_sum[i, :])

    if en_fig:
        plt.figure(7)
        plt.plot(sweep_param * param_scaler, np.mean(np.real(a), axis=1))
        plt.title('Echo average')
        #set(gca, 'FontSize', 12)
        plt.xlabel(figure_xlabel)
        plt.ylabel('Amplitude')

        plt.figure(8)
        plt.plot(sweep_param * param_scaler, a_init)
        plt.title('Initial amplitude')
        #set(gca, 'FontSize', 12)
        plt.xlabel(figure_xlabel)
        plt.ylabel('Amplitude')

        plt.show()

    return snrref, noiseref, resref
'''
