#!/bin/bash

CUR_DIR="${pwd}"

# Get the statistics of the corpus
cd /home/essepuntato/OC/script
nohup python statistics.py &

cd $CUR_DIR