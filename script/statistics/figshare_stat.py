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
import re
import os
import csv
import requests
import itertools
import json
import operator

figshare_api = "https://stats.figshare.com/timeline/"
figshare_granularity = ["month"]
figshare_counter = ["views", "downloads"]
figshare_item = ["article"]


def get_ids():
    ids = []
    r = requests.get("http://opencitations.net/download")
    for u in re.findall("doi\.org/10\.6084/m9\.figshare\.[0-9]+", r.text):
        ids += [re.sub("^.+\.([0-9]+)$", "\\1", u)]

    return ids


def initialize(json_r, granularity, counter, item, json_result, except_date):
    if item not in json_result:
        json_result[item] = {granularity: {}}

    for date in json_r:
        if date < except_date:
            if date not in json_result[item][granularity]:
                json_result[item][granularity][date] = {}
            if counter not in json_result[item][granularity][date]:
                json_result[item][granularity][date][counter] = 0

    return json_result


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("figshare_stat.py",
                                         description="This script call the Figshare API using all the ids "
                                                     "that are included in the download page of OpenCitations.")
    arg_parser.add_argument("-i", "--input", dest="input",
                            help="Use the specified JSON file for creating the CSV.")
    arg_parser.add_argument("-o", "--output", dest="output", required=True,
                            help="The directory where to store the Figshare statistics.")
    arg_parser.add_argument("-e", "--except_after", dest="except_after",
                            help="The date from which the data should not be considered (format yyyy-mm).")

    args = arg_parser.parse_args()

    out_dir = args.output + os.sep
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if args.except_after is None:
        except_date = "3000-01"
    else:
        except_date = args.except_after

    if args.input is not None:
        with open(args.input) as f:
            json_result = json.load(f)
    else:
        json_result = {}

        for id in get_ids():
            for granularity, counter, item in \
                    list(itertools.product(*[figshare_granularity, figshare_counter, figshare_item])):
                api_url = "%s%s/%s/%s/%s" % (figshare_api, granularity, counter, item, id)
                r = requests.get(api_url)

                print("Querying '%s'" % api_url)

                json_r = json.loads(r.text)["timeline"]

                if json_r is not None:
                    # Initialize the structure if it does not exist
                    json_result = initialize(json_r, granularity, counter, item, json_result, except_date)

                    # Update the values
                    for date in json_r:
                        if date < except_date:
                            json_result[item][granularity][date][counter] += json_r[date]

        with open(out_dir + "figshare_data.json", "w") as f:
            json.dump(json_result, f)

    # Create CSV
    for item in json_result:
        for granularity in json_result[item]:
            csv_file_path = "%sfigshare_%s_%s.csv" % (out_dir, item, granularity)
            all_rows = []

            for date in json_result[item][granularity]:
                cur_row = [date]
                for counter in figshare_counter:
                    cur_value = 0
                    if counter in json_result[item][granularity][date]:
                        cur_value = json_result[item][granularity][date][counter]
                    cur_row += [cur_value]
                all_rows += [cur_row]

            all_rows = sorted(all_rows, key=operator.itemgetter(0))
            all_rows.insert(0, [granularity] + figshare_counter)
            with open(csv_file_path, 'w') as f:
                w = csv.writer(f)
                w.writerows(all_rows)

    print "DONE"
