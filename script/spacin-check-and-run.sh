#!/bin/bash

CUR_DIR="${pwd}"

cd /home/essepuntato/OC/script
./spacin-run.sh
if [ "$?" = "0" ]; then
    date >> spacin_log.txt
fi

cd $CUR_DIR