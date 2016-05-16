#!/bin/bash
myv=`curl -s http://localhost:3000/blazegraph/sparql?query=SELECT%20%3Fs%20%7B%3Fs%20%3Fp%20%3Fo%7D%20LIMIT%201`

if [ -z "$myv" ] || [[ $myv != *"results"* ]];
then
    stop.sh
    run.sh
    date >> log.txt
fi