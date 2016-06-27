#!/bin/bash

CUR_DIR="${pwd}"

cd /home/essepuntato/OC/script
./bee-run.sh
if [ "$?" = "0" ]; then
    date >> bee_log.txt
fi

cd $CUR_DIR