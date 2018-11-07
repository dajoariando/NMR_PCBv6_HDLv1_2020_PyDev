import numpy as np
import csv
from nmr_std_function.nmr_functions import compute_wobble
from nmr_std_function.data_parser import parse_simple_info
import os
import csv
import math
import time
import shutil


def comp_Z1(L, RL, CL, Cp, f0):
    w0 = 2 * np.pi * f0
    Ct = CL + Cp
    return (1j * w0 * L + RL) * (1 / (1j * w0 * Ct)) / (1j * w0 * L + RL + 1 / (1j * w0 * Ct))


def comp_Z2(Cs, f0):
    w0 = 2 * np.pi * f0
    return 1 / (1j * w0 * Cs)


def read_PARAM_mtch_ntwrk_caps(filename):
    f = open(filename)
    csv_f = csv.reader(f)
    cser = []
    cpar = []
    for i in csv_f:
        if isFloat(i[0]):
            cser.append(float(i[0]))
            cpar.append(float(i[1]))
    f.close()
    return cser, cpar


# convert discrete integer format of C to real C value
def conv_cInt_to_cReal(cInt, cTbl):
    # cInt = c in integer format
    # cTbl = table for c

    cReal = 0
    for ii in range(0, 8):
        if cInt & (1 << ii):
            cReal += cTbl[ii]

    return cReal


def conv_cReal_to_cInt(cReal, cTbl):
    # cReal = c in real capacitance
    # cTbl = table for c

    # increase c from 0 to maximum and find its minimum difference
    # with cReal by trying to find minimum (cReal-c)
    # it is done by finding point where c value exceeds cReal

    dC_old = 0
    for i in range(1, 256):
        csel = 0
        for ii in range(0, 8):
            if i & (1 << ii):
                csel += cTbl[ii]

        dC = cReal - csel
        cInt = i
        if (dC <= 0):  # stop when dC is bigger than dC old
            if abs(dC) < dC_old:
                cInt = i
                break
            else:
                cInt = i - 1
                break
        dC_old = dC

    return cInt


def Cp_opt(L, RL, CL, f0):

    filename = './PARAM_mtch_ntwrk_caps_preamp_v2.csv'
    cser, cpar = read_PARAM_mtch_ntwrk_caps(filename)

    Z1 = np.zeros(255, dtype=complex)
    for i in range(1, 256):
        cpar_sel = 0
        for ii in range(0, 8):
            if i & (1 << ii):
                cpar_sel += cpar[ii]
        Z1[i - 1] = comp_Z1(L, RL, CL, cpar_sel, f0)
    max_idx = np.argwhere(Z1)[np.real(Z1) == max(
        np.real(Z1))]  # find max index
    # delete the values after max_index, effectively removing the 50 ohms
    # impedance matched at the other side (dominated by capacitance, instead
    # of coil)
    Z1[max_idx[0][0]:] = 0
    # subtract the real part of Z1 by 50 and find its absolute value
    Z1_absmin50 = np.abs(np.real(Z1) - 50)
    # find Cp index with least reflection
    Cp_idx = np.argwhere(Z1_absmin50 == min(Z1_absmin50))
    Cp_idx = Cp_idx[0][0]

    Z2 = np.zeros(255, dtype=complex)
    for i in range(1, 256):
        cser_sel = 0
        for ii in range(0, 8):
            if i & (1 << ii):
                cser_sel += cser[ii]
        Z2[i - 1] = comp_Z2(cser_sel, f0)
    # imaginary amplitude
    Z_imag_amp = np.abs(np.imag(Z2) + np.imag(Z1[Cp_idx]))
    Cs_idx = np.argwhere(Z_imag_amp == min(Z_imag_amp))
    Cs_idx = Cs_idx[0][0]

    return Z1[Cp_idx] + Z2[Cs_idx], Cp_idx, Cs_idx


def isFloat(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def wobb_meas(data_parent_folder, cparIdx, cserIdx, s11_obj, en_fig):
    startfreq = 3
    stopfreq = 5.5
    spacfreq = 0.02
    sampfreq = 25
    wobb_samples = int(sampfreq / spacfreq)
    command = ("./thesis_nmr_de1soc_hdl2.0_wobble" + " " +
               str(cparIdx) + " " +
               str(cserIdx) + " " +
               str(startfreq) + " " +
               str(stopfreq) + " " +
               str(spacfreq) + " " +
               str(sampfreq) + " " +
               str(wobb_samples))
    os.system(command + ' > /dev/null')
    meas_folder = parse_simple_info(
        data_parent_folder, 'current_folder.txt')
    S11_fmin, S11_fmax, S11_bw,  minS11, minS11_freq = compute_wobble(
        data_parent_folder, meas_folder[0], s11_obj, en_fig)
    #print('fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f}'.format(S11_fmin, S11_fmax, S11_bw))

    return S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq


def find_mtch_ntwrk(data_parent_folder, nmr_freq, s11_obj, cpar_sta, cser_sta, L, RL, CL, en_fig):

    # data_parent_folder : the data folder to be used for processing
    # nmr_freq : the NMR frequency to be tuned to
    # s11_obj : the objective reflection parameter
    # cpar_sta : starting cpar index
    # cser_sta : starting cser index
    # L : approximated coil inductance
    # RL : approximated coil parasitic resistance
    # CL : approximated coil parasitic capacitance

    # example data parent folder:
    # data_parent_folder = "D:/DELETEME"  # for testing in windows
    # data_parent_folder = "/root/nmr_fitting"  # for testing in linux

    # threshold for minS11
    minS11_thr = -20

    # read table
    filename = data_parent_folder + '/hw_opt/' + \
        'PARAM_mtch_ntwrk_caps_preamp_v1.csv'
    cserTbl, cparTbl = read_PARAM_mtch_ntwrk_caps(filename)

    # initial parameter
    cparIdx = cpar_sta
    cserIdx = cser_sta
    print('   START: fobj={0:.3f} cpar={1:d}({3:0.0f}pF) cser={2:d}({4:0.1f}pF)'.format(
        nmr_freq, cparIdx, cserIdx, conv_cInt_to_cReal(cparIdx, cparTbl) * 1e12, conv_cInt_to_cReal(cserIdx, cserTbl) * 1e12))

    # fixed parameters
    max_iter = 5

    for i in range(0, max_iter):

        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = wobb_meas(
            data_parent_folder, cparIdx, cserIdx, s11_obj, en_fig)
        print('      fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f} s11min={3:0.2f}dB s11min_freq={4:0.3f}MHz cpar={5:d}({7:0.0f}pF) cser={6:d}({8:0.1f}pF)'.format(
            S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparIdx, cserIdx, conv_cInt_to_cReal(cparIdx, cparTbl) * 1e12, conv_cInt_to_cReal(cserIdx, cserTbl) * 1e12))

        if (nmr_freq >= S11_fmin) & (nmr_freq <= S11_fmax):
            break  # already optimum condition
        else:
            # estimate new cpar from old cpar with (f1/f2)**2 = c2/c1
            f1 = minS11_freq
            f2 = nmr_freq
            cparOld = conv_cInt_to_cReal(cparIdx, cparTbl)
            cparNew = (f1 / f2)**2 * cparOld
            cparIdx = conv_cReal_to_cInt(cparNew, cparTbl)

            # compute Cser index from the previous measurement
            # Cser direction (1 means addition, and 0 means subtraction
            CserDir = 1
            Done = 0

            while (1):  # find minimum S11 by sweeping cser (at constant cpar)
                oldCserIdx = cserIdx
                if CserDir:
                    cserIdx = cserIdx + 3
                else:
                    cserIdx = cserIdx - 3

                old_S11_fmin = S11_fmin
                old_S11_fmax = S11_fmax
                old_S11_bw = S11_bw
                old_minS11 = minS11
                old_minS11_freq = minS11_freq
                S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq = wobb_meas(
                    data_parent_folder, cparIdx, cserIdx, s11_obj, 0)

                if (old_minS11 < minS11):
                    if CserDir:
                        CserDir = 0
                    else:
                        Done = 1
                    print('         fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f} s11min={3:0.2f}dB s11min_freq={4:0.3f}MHz cpar={5:d}({7:0.0f}pF) cser={6:d}({8:0.1f}pF)-FLUSHED'.format(
                        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparIdx, cserIdx, conv_cInt_to_cReal(cparIdx, cparTbl) * 1e12, conv_cInt_to_cReal(cserIdx, cserTbl) * 1e12))
                    S11_fmin = old_S11_fmin
                    S11_fmax = old_S11_fmax
                    S11_bw = old_S11_bw
                    minS11 = old_minS11
                    minS11_freq = old_minS11_freq
                    cserIdx = oldCserIdx
                else:
                    print('         fmin={0:0.3f} fmax={1:0.3f} bw={2:0.3f} s11min={3:0.2f}dB s11min_freq={4:0.3f}MHz cpar={5:d}({7:0.0f}pF) cser={6:d}({8:0.1f}pF)'.format(
                        S11_fmin, S11_fmax, S11_bw, minS11, minS11_freq, cparIdx, cserIdx, conv_cInt_to_cReal(cparIdx, cparTbl) * 1e12, conv_cInt_to_cReal(cserIdx, cserTbl) * 1e12))

                # check if the minS11 is less than minS11_thr
                # this is to ensure that the cser is approximately at the
                # optimum condition
                if (Done):
                    if (minS11_thr < minS11):
                        print('      warning: S11 of {0:0.2f}dB at {1:0.3f}MHz is not low enough: target S11 is {2:0.2f}dB'.format(
                            minS11, minS11_freq, minS11_thr))
                    else:
                        print('      S11 of {0:0.2f}dB at {1:0.3f}MHz satisfied the target S11 of {2:0.2f}dB'.format(
                            minS11, minS11_freq, minS11_thr))
                    break  # already optimum condition

            print('   fcurr={0:0.2f} fobj={1:0.2f} cpar={2:d}({4:0.0f}pF) cser={3:d}({5:0.1f}pF)'.
                  format(minS11_freq, nmr_freq, cparIdx, cserIdx, conv_cInt_to_cReal(cparIdx, cparTbl) * 1e12, conv_cInt_to_cReal(cserIdx, cserTbl) * 1e12))

    return cparIdx, cserIdx, S11_fmin, S11_fmax
