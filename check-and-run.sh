#!/bin/bash

CUR_DIR="${pwd}"

# CHECK THE WEBSITE
# The path specified is related to the original server where the website
# of the Open Citations project is actually installed.
cd /home/essepuntato/OC/website
./check-and-run.sh

cd $CUR_DIR