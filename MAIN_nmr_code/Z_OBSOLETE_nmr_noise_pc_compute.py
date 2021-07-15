'''
Created on July 14, 2021

This script uses nmr_noise.py parameters

@author: David Ariando
'''

#!/usr/bin/python

import paramiko
from scp import SCPClient
from nmr_std_function.nmr_class import tunable_nmr_system_2018
from nmr_std_function.nmr_functions import compute_stats, compute_in_bw_noise
from nmr_std_function.data_parser import parse_simple_info
import meas_configs.wmp_pcb1 as conf


# nmr object declaration
data_folder = "D:\\TEMP"
en_remote_dbg = 0
en_fig = 1
en_remote_computing = 1
nmrObj = tunable_nmr_system_2018( data_folder, en_remote_dbg)

# measurement settings
min_freq = 1.5 # in MHz
max_freq = 2.0 # in MHz

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

while (1):
    
    ssh.connect(hostname= nmrObj.server_ip , username='root', password='dave', look_for_keys=False)
    scp = SCPClient(ssh.get_transport())
    
    stdin, stdout, stderr = ssh.exec_command('cd ' + nmrObj.server_path + " && python3 nmr_noise.py")
    stdout.channel.recv_exit_status()          # Blocking call

    
    scp.get("/root/NMR_DATA/current_folder.txt",data_folder+"\\current_folder.txt")
    
    meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
    scp.get("/root/NMR_DATA/"+meas_folder[0],data_folder, recursive=True)
    
    scp.close()
    
    # compute_stats( min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )    
    compute_in_bw_noise( conf.meas_bw_kHz, conf.Df_MHz, min_freq, max_freq, data_folder, meas_folder[0], 'noise_plot.png', en_fig )
    
    ssh.close()
