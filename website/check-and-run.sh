#!/bin/bash
myv=`curl -s http://oc.cs.unibo.it`

if [[ -z "$myv" ]] || [[ $myv = "Traceback"*  ]]; then
    ./stop.sh
    ./run.sh
    date >> log.txt
fi