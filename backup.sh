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
#cd corpus
#
#cd ar
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ar_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#cd be
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_be_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#cd br
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_br_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#cd id
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_id_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#cd ra
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ra_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#cd re
#for d in */ ; do
#    CUR_DIR=${d%?}
#    CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_re_$CUR_DIR' &"
#    eval $CMD
#    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
#done
#cd ..
#
#CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_prov' &"
#eval $CMD
#dar -c - -R prov | nc -w 1 130.136.2.21 5000
#
#cd ..

echo ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/"$BACKUP_DATE"-corpus' &
sleep 2
# dar -c - -R corpus | nc -w 1 130.136.2.21 5000
sleep 5

#CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-id-counter' &"
#eval $CMD
#sleep 2
#dar -c - -R id-counter | nc -w 1 130.136.2.21 5000
#sleep 5
#
#CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-ref' &"
#eval $CMD
#sleep 2
#dar -c - -R ref | nc -w 1 130.136.2.21 5000
#sleep 5
#
#CMD="ssh 130.136.2.21 -l oc 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-triplestore' &"
#eval $CMD
#sleep 2
#dar -c - -R triplestore -X "log.txt" -X "nohup.out" | nc -w 1 130.136.2.21 5000
#sleep 5

# Gently sun all the processes
/home/essepuntato/OC/script/gently-run.sh

cd $CUR_DIR