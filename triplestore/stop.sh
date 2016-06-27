#!/bin/bash
ps -ef | grep "[b]lazegraph.jar" | awk '{print $2}' | xargs kill
exit 0