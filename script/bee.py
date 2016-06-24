#!/usr/bin/python
# -*- coding: utf-8 -*-
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
        stored_file, reference_dir, error_dir, pagination_file, Stopper(reference_dir))
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