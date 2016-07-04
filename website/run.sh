#!/bin/bash

myv=`curl -s http://oc.cs.unibo.it`

if [[ -z "$myv" ]] || [[ $myv = "Traceback"*  ]]; then
    /etc/init.d/lighttpd stop
    sleep 2
    /etc/init.d/lighttpd start
    exit 0
fi

exit 1