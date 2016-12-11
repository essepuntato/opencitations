#!/usr/bin/python
# -*- coding: utf-8 -*-
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

__author__ = 'essepuntato'

from conf_bee import *
from stopper import Stopper
import traceback
from datetime import datetime
from epmc_processor import EuropeanPubMedCentralProcessor
import os

start_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
exception_string = None
try:
    epmc = EuropeanPubMedCentralProcessor(
        stored_file, reference_dir, error_dir, pagination_file, Stopper(reference_dir), p_size=page_size)
    epmc.process(True)
except Exception as e:
    exception_string = str(e) + " " + traceback.format_exc().rstrip("\n+")

end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

if exception_string is not None:
    print exception_string
    if not os.path.exists(error_dir):
        os.makedirs(error_dir)
    with open(error_dir + end_time.replace(":", "-") + ".err", "w") as f:
        f.write(exception_string)

print "\nStarted at:\t%s\nEnded at:\t%s" % (start_time, end_time)