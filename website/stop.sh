#!/bin/bash
ps -ef | grep "python oc.py" | awk '{print $2}' | xargs kill