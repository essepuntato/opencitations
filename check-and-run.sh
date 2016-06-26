#!/bin/bash

CUR_DIR="${pwd}"

# All the path specified is related to the original server where the website
# of the Open Citations project is actually installed.

# CHECK THE WEBSITE
cd /home/essepuntato/OC/website
./check-and-run.sh

# CHECK THE TRIPLESTORE
cd /srv/oc/triplestore
./check-and-run.sh

cd $CUR_DIR