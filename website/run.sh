#!/bin/bash

myv=`curl -s http://oc.cs.unibo.it`

if [[ -z "$myv" ]] || [[ $myv = "Traceback"*  ]]; then
    ./stop.sh
    nohup python oc.py 80 &
    exit 0
fi

exit 1