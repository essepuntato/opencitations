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

# Backup of the OCC
dar -c - -R corpus | ssh 130.136.2.21 -l oc 'dar_xform -s 600M -w -n - /mnt/backup/oc/corpus_`date -I`'
dar -c - -R id-counter | ssh 130.136.2.21 -l oc 'dar_xform -s 600M -w -n - /mnt/backup/oc/id-counter_`date -I`'
dar -c - -R ref | ssh 130.136.2.21 -l oc 'dar_xform -s 600M -w -n - /mnt/backup/oc/ref_`date -I`'
dar -c - -R triplestore -X "log.txt" -X "nohup.out" | ssh 130.136.2.21 -l oc 'dar_xform -s 600M -w -n - /mnt/backup/oc/triplestore_`date -I`'

# Gently sun all the processes
/home/essepuntato/OC/script/gently-run.sh

cd $CUR_DIR