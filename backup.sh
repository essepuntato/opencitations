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

BACKUP_DATE="$(date -I)"

# Gently stop all the processes
/home/essepuntato/OC/script/gently-stop.sh

# Wait until both BEE and SPACIN finish
while ps -ef | grep "[p]ython bee.py" > /dev/null || ps -ef | grep "[p]ython spacin.py" > /dev/null; do
    # If some of the processes is still active, wait for 60 seconds and check again
    sleep 60
done

# Get last statistics
/home/essepuntato/OC/statistics.sh

# Backup of the OCC

# ar
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ar' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/ar/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ar_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/ar/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# be
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_be' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/be/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_be_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/be/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# br
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_br' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/br/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_br_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/br/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# id
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_id' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/id/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_id_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/id/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# ra
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ra' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/ra/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_ra_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/ra/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# re
# backup data
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_re' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/re/ -X index.json -ar -P "^[0-9]+/[0-9]+$" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3
# backup provenance
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_re_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R /srv/oc/corpus/re/ -I "[a-z]*.json" | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# prov
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-corpus_prov' &"
eval $CMD
sleep 2
dar -Q -c - -R prov | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# references
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-ref' &"
eval $CMD
sleep 2
dar -Q -c - -R ref | nc -w 1 ocbackup.cs.unibo.it 5000
sleep 3

# triplestore
CMD="ssh ocbackup.cs.unibo.it -l oc -t -t 'nc -l -p 5000 | dar_xform -s 500M -w -n - /mnt/backup/oc/$BACKUP_DATE-triplestore' &"
eval $CMD
sleep 2
dar -Q -c - -R triplestore -X "log.txt" -X "nohup.out" | nc -w 1 ocbackup.cs.unibo.it 5000

# Gently run all the processes
/home/essepuntato/OC/script/gently-run.sh
