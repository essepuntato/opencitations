#!/bin/bash

myv=`ps -ef | grep "[p]ython bee.py"`

if [[ -z "$myv" ]]; then
    python bee.py &
    exit 0
fi

exit 1