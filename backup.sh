#!/bin/bash

CUR_DIR="${pwd}"
BACKUP_DATE="$(date -I)"

# Gently stop all the processes
/home/essepuntato/OC/script/gently-stop.sh

# Wait until both BEE and SPACIN finish
while ps -ef | grep "[p]ython bee.py" > /dev/null || ps -ef | grep "[p]ython spacin.py" > /dev/null; do
    # If some of the processes is still active, wait for 60 seconds and check again
    sleep 60
done

cd /srv/oc

CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus' &"
eval $CMD
sleep 2
dar -c - -R corpus | nc -w 1 130.136.2.21 5000
sleep 3

CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-ref' &"
eval $CMD
sleep 2
dar -c - -R ref | nc -w 1 130.136.2.21 5000
sleep 3

CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-triplestore' &"
eval $CMD
sleep 2
dar -c - -R triplestore -X "log.txt" -X "nohup.out" | nc -w 1 130.136.2.21 5000

# Gently sun all the processes
/home/essepuntato/OC/script/gently-run.sh

cd $CUR_DIR