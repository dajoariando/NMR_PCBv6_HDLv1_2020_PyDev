'''
Created on Mar 30, 2018

@author: David Ariando
'''

#!/usr/bin/python

import os
import time
from nmr_std_function.nmr_class import tunable_nmr_system_2018
import pydevd

# variables
data_folder = "/root/NMR_DATA"
en_remote_dbg = 1

# nmr object declaration
nmrObj = tunable_nmr_system_2018(data_folder, en_remote_dbg)

# remote debug setup (NEW)
# if this one is being used, make sure that the directory is not changed inside
# the declaration of tunable_nmr_system_2018. Comment the line "os.chdir(self.data_folder)"
# inside tunable_nmr_system_2018 initialization script
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    PATH_TRANSLATION = [(nmrObj.client_path, nmrObj.server_path)]
    setup_client_server_paths(PATH_TRANSLATION)
    print("---server:%s---client:%s---" % (nmrObj.server_ip, nmrObj.client_ip))
    pydevd.settrace(nmrObj.client_ip, stdoutToServer=True, stderrToServer=True)

# remote debug setup (OLD)
# if this one is being used, make sure that the directory is not changed inside
# the declaration of tunable_nmr_system_2018. Comment the line "os.chdir(self.data_folder)"
# inside tunable_nmr_system_2018 initialization script
if en_remote_dbg:
    from pydevd_file_utils import setup_client_server_paths
    server_path = '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/'
    client_path = 'D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\129.22.143.88\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\'
    PATH_TRANSLATION = [('D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\129.22.143.88\\root\\nmr_pcb20_hdl10_2018\\MAIN_nmr_code\\',
                         '/root/nmr_pcb20_hdl10_2018/MAIN_nmr_code/')]
    pydevd.settrace("129.22.143.39")