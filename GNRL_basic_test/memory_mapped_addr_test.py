#!/usr/bin/python

import pydevd
import mmap
import time

from pydevd_file_utils import setup_client_server_paths

PATH_TRANSLATION = [
    ('D:\\GDrive\\WORKSPACES\\Eclipse_Python_2018\\RemoteSystemsTempFiles\\DAJO-DE1SOC\\root\\Eclipse_Python_2018\\GNRL_basic_test\\',
     '/root/Eclipse_Python_2018/GNRL_basic_test/')
]

setup_client_server_paths(PATH_TRANSLATION)
pydevd.settrace("dajo-compaqsff")

h2f_axi_master_span = 0x40000000
h2f_axi_master_ofst = 0xC0000000
h2f_switch_addr_ofst = 0x4000000

with open("/dev/mem", "r+") as f:
    # memory-map the file, size 0 means whole file
    mem = mmap.mmap(f.fileno(), h2f_axi_master_span,
                    offset=h2f_axi_master_ofst)

    while 1:
        mem.seek(h2f_switch_addr_ofst)
        data = mem.read(4)  # read the data in byte format
        dataint = int.from_bytes(data, byteorder='little')
        time.sleep(0.5)
        print("current data = %d" % dataint)

    mem.close()  # close the map
