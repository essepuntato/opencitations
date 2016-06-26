#!/bin/bash
ps -ef | grep "[p]ython bee.py" | awk '{print $2}' | xargs kill