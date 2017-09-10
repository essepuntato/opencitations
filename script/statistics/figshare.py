#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Silvio Peroni <essepuntato@gmail.com>
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

# This script unpacks all the DAR files related to a monthly OpenCitations Corpus dump
# and recreates the Corpus file system

import argparse
import zipfile
import re
import os
import subprocess
import glob
import requests
import itertools
import json

figshare_api = "https://stats.figshare.com/timeline/"
figshare_granularity = ["month"]
figshare_counter = ["view", "downloads", "shares"]
figshare_item = ["article"]


def get_ids():
    ids = []
    r = requests.get("http://opencitations.net/download")
    for u in re.findall("doi\.org/10\.6084/m9\.figshare\.[0-9]+", r.text):
        ids += [re.sub("^.+\.([0-9]+)$", "\\1", u)]

    return ids


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("unpack.py",
                                         description="This script unpack all the DAR files related to a monthly "
                                                     "OpenCitations Corpus dump (stored in ZIP files) and "
                                                     "recreates the Corpus file system")
    arg_parser.add_argument("-i", "--input", dest="input",
                            help="The directory containing all the ZIP files to unpack.")
    arg_parser.add_argument("-o", "--output", dest="output",
                            help="The directory where to store the Corpus data. If no "
                                 "directory is specified, the script use the one specified "
                                 "as input.")

    args = arg_parser.parse_args()

    json_result = {}

    for id in get_ids():
        for granularity, counter, item in \
                list(itertools.product(*[figshare_granularity, figshare_counter, figshare_item])):
            api_url = "%s%s/%s/%s/%s" % (figshare_api, granularity, counter, item, id)
            r = requests.get(api_url)
            json_r = json.load(r.text)["timeline"]
            if id not in json_result:
                pass # initialize the json with all the values in figshare_granularity, figshare_counter, and figshare_item

    # Calculate what we need (i.e. accesses views and etc. by month)


    print "\n\nDONE"
