'''
Created on Oct 30, 2018

@author: David Ariando
'''

import os

# variables
enable_remotedebug = 1
cshunt = 110
cseries = 185


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

# Turn on matching network
os.system(
    work_dir + "/c_exec/i2c_mtch_ntwrk" + " " +
    str(cshunt) + " " +
    str(cseries)
)

# Turn off matching network
os.system(
    work_dir + "/c_exec/i2c_mtch_ntwrk" + " " +
    str(0) + " " +
    str(0)
)