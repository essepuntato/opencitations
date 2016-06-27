#!/bin/bash
ps -ef | grep "[p]ython spacin.py" | awk '{print $2}' | xargs kill
exit 0