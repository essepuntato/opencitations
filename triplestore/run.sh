#!/bin/bash
java -server -Xmx4g -Dbigdata.propertyFile=occ.properties -Djetty.port=3000 -Djetty.host=127.0.0.1 -jar blazegraph.jar &