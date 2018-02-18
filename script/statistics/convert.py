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

# This script converts the log file containing all the accesses to the OpenCitations
# resources into a CSV file for further processing

import csv
import argparse

field_names = ['TIME', 'REMOTE_ADDR', 'HTTP_USER_AGENT', 'HTTP_REFERER', 'HTTP_HOST', 'REQUEST_URI']


def convert(input_dash_files, output_csv_file):
    all_lines = set()
    final_file = []

    for input_dash_file in input_dash_files:
        print "Analyse '%s'" % input_dash_file
        with open(input_dash_file) as f:
            for line in f:
                try:
                    if line not in all_lines:
                        all_lines.add(line)
                        cur_tuple = {}
                        for i, item in enumerate(line.split(" # ")):
                            if i > 0:
                                cur_value = item.replace(field_names[i] + ": ", "")
                            else:
                                cur_value = item
                            cur_tuple[field_names[i]] = cur_value.strip()
                        final_file += [cur_tuple]
                except IndexError:
                    print "Error: " + line

    with open(output_csv_file, "w") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(final_file)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("convert.py",
                                         description="This script converts the file with the accesses "
                                                     "to the OpenCitations website resources into a "
                                                     "CSV document.")
    arg_parser.add_argument("-i", "--input", dest="input", nargs="+", required=True,
                            help="The file list with access logs.")
    arg_parser.add_argument("-o", "--output", dest="output", required=True,
                            help="The file where to store the CSV file.")

    args = arg_parser.parse_args()
    convert(args.input, args.output)
    print "DONE"
