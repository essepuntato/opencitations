#!/bin/bash
ps -ef | grep "[p]ython oc.py" | awk '{print $2}' | xargs kill
exit 0