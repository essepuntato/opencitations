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

import argparse
import os
import glob
import json
from reporter import Reporter

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        "find_prov_issues.py",
        description="This script allows one to identify the provenance item ids that have some issues.")
    arg_parser.add_argument("-i", "--input_dir", dest="i_dir", required=True,
                            help="The id directory where to look for issues.")
    arg_parser.add_argument("-o", "--output_file", dest="o_file", required=True,
                            help="The file where to write the results.")
    args = arg_parser.parse_args()
    
    rep = Reporter(True)
    rep.new_article()
    
    for cur_dir in glob.glob(args.i_dir + os.sep + "[0-9]*/[0-9]*/prov/"):
        se_file = cur_dir + os.sep + "se.json"
        
        with open(se_file) as f:
            cur_json = json.load(f)
            for item in cur_json["@graph"]:
                cur_graph = item["@graph"][0]
                generated = cur_graph["generated"]
                if isinstance(generated, list) and len(generated) > 1:
                    sen_string = cur_graph["iri"] + " [%s]" % str(len(generated))
                    if "datacite/hasIdentifier" in cur_graph["update_action"]:
                        sen_string += " [ID]"
                    if "cito/cites" in cur_graph["update_action"]:
                        sen_string += " [CIT]"
                    rep.add_sentence(sen_string)

    rep.write_file(args.o_file)
