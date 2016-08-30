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

# Gently stop all the processes
/home/essepuntato/OC/script/gently-stop.sh

# Wait until the statistics, backup, BEE and SPACIN finish
while ps -ef | grep "[p]ython statistics.py" > /dev/null || ps -ef | grep "[b]ackup.sh" > /dev/null || ps -ef | grep "[p]ython bee.py" > /dev/null || ps -ef | grep "[p]ython spacin.py" > /dev/null; do
    # If some of the processes is still active, wait for 60 seconds and check again
    sleep 60
done

# Stop and run again the triplestore
cd /srv/oc/triplestore
./stop.sh
sleep 2
./check-and-run.sh

# Gently run all the processes
/home/essepuntato/OC/script/gently-run.sh

cd $CUR_DIR