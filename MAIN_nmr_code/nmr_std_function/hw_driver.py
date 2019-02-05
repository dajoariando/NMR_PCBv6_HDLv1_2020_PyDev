import numpy as np
import mmap


class fpga_de1soc:
    def __init__(self):
        # hardware addresses
        self.h2f_axi_master_span = 0x40000000
        self.h2f_axi_master_ofst = 0xC0000000
        self.h2f_switch_addr_ofst = 0x4000000
        self.h2f_sdram_addr_ofst = 0x00000000

    def readSDRAM(self, Points):
        data_width = 2  # in bytes
        data = np.zeros(Points)

        with open("/dev/mem", "r+") as f:
            # memory-map the file, size 0 means whole file
            mem = mmap.mmap(f.fileno(), self.h2f_axi_master_span,
                            offset=self.h2f_axi_master_ofst)
            for i in range(0, Points):
                # one data is 2 bytes: increment address by 2
                mem.seek(self.h2f_sdram_addr_ofst + i * 2)
                dataread = mem.read(2)
                data[i] = int.from_bytes(dataread, byteorder='little')
                # print("current data = %d" % data[i])
            mem.close()  # close the map

        return data
