#!/bin/bash
myv=`ps -ef | grep "[p]ython spacin.py"`

if [[ -z "$myv" ]]; then
    nohup python spacin.py &
    exit 0
fi

exit 1
