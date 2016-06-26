#!/bin/bash
CUR_DIR="${pwd}"
cd /home/essepuntato/OC/script

myv=`ps -ef | grep "[p]ython bee.py"`

if [[ -z "$myv" ]]; then
    python bee.py &
    date >> bee_log.txt
fi

cd $CUR_DIR