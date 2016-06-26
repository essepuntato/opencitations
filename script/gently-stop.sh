#!/bin/bash
python stopper.py -t /srv/oc/ref/todo --add
# This will stop both the SPACIN and BEE processes gently,
# when they finish their last (current) iteration