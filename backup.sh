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
cd corpus

cd ar
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ar_$CUR_DIR'"
    eval $CMD
done
cd ..

cd be
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_be_$CUR_DIR'"
    eval $CMD
done
cd ..

cd br
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_br_$CUR_DIR'"
    eval $CMD
done
cd ..

cd id
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_id_$CUR_DIR'"
    eval $CMD
done
cd ..

cd ra
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ra_$CUR_DIR'"
    eval $CMD
done
cd ..

cd re
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="dar -c - -R $CUR_DIR | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_re_$CUR_DIR'"
    eval $CMD
done
cd ..

CMD="dar -c - -R prov | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_prov'"
eval $CMD

dar -c - -R id-counter | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/id-counter_`date -I`'
dar -c - -R ref | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/ref_`date -I`'
dar -c - -R triplestore -X "log.txt" -X "nohup.out" | ssh 130.136.2.21 -l oc 'dar_xform -s 500M -w -n - /mnt/backup/oc/triplestore_`date -I`'

# Gently sun all the processes
/home/essepuntato/OC/script/gently-run.sh

cd $CUR_DIR