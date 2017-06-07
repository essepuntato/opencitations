#!/bin/bash
myv=`timeout 30s curl -s http://localhost:3000/blazegraph/sparql?query=SELECT%20%3Fs%20%7B%3Fs%20%3Fp%20%3Fo%7D%20LIMIT%201`

if [ -z "$myv" ] || [[ $myv != *"results"* ]];
then
    ./stop.sh
    sleep 2
    nohup java -server -Xmx8G -Dbigdata.propertyFile=occ.properties -Djetty.port=3000 -Djetty.host=127.0.0.1 -jar blazegraph.jar &
    exit 0
fi

exit 1