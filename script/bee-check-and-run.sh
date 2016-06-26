#!/bin/bash
myv=`ps -ef | grep "[p]ython bee.py"`

if [[ -z "$myv" ]]; then
    python bee.py &
    date >> bee_log.txt
fi