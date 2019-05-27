#!/usr/bin/python

import pydevd
import mmap
import time
import numpy as np
import matplotlib.pyplot as plt

from pydevd_file_utils import setup_client_server_paths

# ip addresses settings for the system
server_ip = '129.22.143.88'
client_ip = '129.22.143.39'
server_path = '/root/nmr_pcb20_hdl10_2018/GNRL_basic_test/'
# client path with samba
client_path = 'X:\\nmr_pcb20_hdl10_2018\\GNRL_basic_test\\'

from pydevd_file_utils import setup_client_server_paths
PATH_TRANSLATION = [(client_path, server_path)]
setup_client_server_paths(PATH_TRANSLATION)
print("---server:%s---client:%s---" %
      (server_ip, client_ip))
# pydevd.settrace(client_ip, stdoutToServer=True,
#                stderrToServer=True)

# static addresses of the FPGA
h2f_axi_master_span = 0x40000000
h2f_axi_master_ofst = 0xC0000000
h2f_lwaxi_master_span = 0x200000
h2f_lwaxi_master_ofst = 0xff200000

# axi defined addresses
h2f_switch_addr_ofst = 0x4000000
# lwaxi defined addresses
h2f_dconv_addr_ofst = 0x0448
h2f_dconv_csr_addr_ofst = 0x0480
h2f_dconvq_addr_ofst = 0x04c0
h2f_NoP_addr_ofst = 0x0010

h2f_dconvq_csr_addr_ofst = 0x04a0
h2f_dnosig_addr_ofst = 0x0430

# csr addressing
ALTERA_AVALON_FIFO_LEVEL_REG = 0
ALTERA_AVALON_FIFO_STATUS_REG = 1
ALTERA_AVALON_FIFO_EVENT_REG = 2
ALTERA_AVALON_FIFO_IENABLE_REG = 3
ALTERA_AVALON_FIFO_ALMOSTFULL_REG = 4
ALTERA_AVALON_FIFO_ALMOSTEMPTY_REG = 5

# read from memory
with open("/dev/mem", "r+") as f:
    # memory-map the file, size 0 means whole file
    mem = mmap.mmap(f.fileno(), h2f_lwaxi_master_span,
                    offset=h2f_lwaxi_master_ofst)

    i = 0
    # data_filt = np.zeros(256)
    while True:
        mem.seek(h2f_dconv_csr_addr_ofst + ALTERA_AVALON_FIFO_LEVEL_REG)
        datarem = mem.read(4)  # read the data in byte format
        dataremint = int.from_bytes(datarem, byteorder='little')
        # print("data remaining = %d" % dataremint)
        if(dataremint == 0):
            break

        mem.seek(h2f_dconv_addr_ofst)
        data = mem.read(4)  # read the data in byte format
        #data_filt[i] = int.from_bytes(data, byteorder='little', signed=True)
        print("current data = %d" % int.from_bytes(
            data, byteorder='little', signed=True))
        i = i + 1

    print(i)
    # plt.plot(data_filt)
    plt.show()
    mem.close()  # close the map
