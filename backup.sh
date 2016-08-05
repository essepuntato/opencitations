#!/bin/bash
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.


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
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ar_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

cd be
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_be_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

cd br
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_br_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

cd id
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_id_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

cd ra
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ra_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

cd re
for d in */ ; do
    CUR_DIR=${d%?}
    CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_re_$CUR_DIR' &"
    eval $CMD
    sleep 2
    dar -c - -R $CUR_DIR | nc -w 1 130.136.2.21 5000
    sleep 3
done
cd ..

CMD="ssh 130.136.2.21 -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_prov' &"
eval $CMD
sleep 2
dar -c - -R prov | nc -w 1 130.136.2.21 5000
sleep 3

cd ..

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