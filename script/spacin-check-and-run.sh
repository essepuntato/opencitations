#!/bin/bash
myv=`ps -ef | grep "[p]ython spacin.py"`

if [[ -z "$myv" ]]; then
    python spacin.py &
    date >> spacin_log.txt
fi