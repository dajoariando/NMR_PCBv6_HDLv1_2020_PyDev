'''
Created on Apr 16, 2018

@author: David Ariando
'''

import hw_opt.mtch_ntwrk as mn
from hw_opt.mtch_ntwrk import conv_cInt_to_cReal
from hw_opt.mtch_ntwrk import comp_Z1
import numpy as np

L = 983e-9
RL = 0.1
CL = 10e-12

B1 = 0.1001
gamma = 42.577e6
f0 = B1 * gamma
f0 = 4.3e6

filename = './PARAM_mtch_ntwrk_caps_preamp_v2.csv'
cser, cpar = mn.read_PARAM_mtch_ntwrk_caps(filename)
Cp = conv_cInt_to_cReal(79, cpar)
print(Cp)
Z = comp_Z1(L, RL, CL, Cp, f0)
print('{0:0.3f}'.format(np.real(Z)))

Z, Cp_idx, Cs_idx = mn.Cp_opt(L, RL, CL, f0)
print('f0 = ', f0)
print('Z = ', Z)
print('Cp_idx = ', Cp_idx)
print('Cs_idx = ', Cs_idx)
pass

'''
filename = './PARAM_mtch_ntwrk_caps.csv'
cser, cpar = mn.read_PARAM_mtch_ntwrk_caps(filename)
c = mn.conv_cInt_to_cReal(100, cpar)
print(c)

cInt = mn.conv_cReal_to_cInt(c, cpar)
print(cInt)
'''
