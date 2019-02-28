#!/bin/bash

for i in {1..500}
do
	echo -e "\t###run $i###" 
	python3 nmr_t2.py
done
