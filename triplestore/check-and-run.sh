#!/bin/bash
CUR_DIR="${pwd}"

cd /home/essepuntato/OC/triplestore
./run.sh
if [ "$?" = "0" ]; then
    date >> log.txt
fi

cd $CUR_DIR