#!/bin/bash
CUR_DIR="${pwd}"
cd /home/essepuntato/OC/script

myv=`ps -ef | grep "[p]ython spacin.py"`

if [[ -z "$myv" ]]; then
    python spacin.py &
    date >> spacin_log.txt
fi

cd $CUR_DIR