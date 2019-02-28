#!/bin/bash

for i in {1..200}
do
	echo -e "\t###run $i###" 
	python3 WMP_nmr_t2_meas_Test.py
done
