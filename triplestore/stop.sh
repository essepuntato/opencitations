#!/bin/bash
ps -ef | grep "blazegraph.jar" | awk '{print $2}' | xargs kill