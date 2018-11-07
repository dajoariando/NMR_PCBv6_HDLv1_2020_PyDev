'''
Created on Mar 30, 2018

@author: David Ariando
'''

import nmr_std_function.data_parser as nmr_info

data_folder = "D:/NMR_EECS397_PCBv3_2017/DATAS/nmr_2018_03_07_19_32_23/"
file_name = "CPMG_iterate_settings.txt"
(param_list, value_list) = nmr_info.parse_info(
    data_folder, file_name)

# echo_spacing = value_list[[i for i, elem in enumerate(param_list) if 'echo_spacing_us' in elem][0]]

echo_spacing = nmr_info.find_value('echo_spacing_us', param_list, value_list)

print(echo_spacing)
