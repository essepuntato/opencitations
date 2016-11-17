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
        ca_file = cur_dir + os.sep + "ca.json"
        
        with open(se_file) as f, open(ca_file) as g:
            cur_se = json.load(f)
            cur_ca = json.load(g)
            for item in cur_se["@graph"]:
                generated = []
                se_generated_by = []
                se_invalidated_by = []
                
                for cur_graph in item["@graph"]:
                    cur_generated = cur_graph["generated"]
                    
                    if isinstance(cur_generated, list) and len(cur_generated) > 1:
                        generated += cur_generated
                        if "invalidated" in cur_graph:
                            cur_invalidated = cur_graph["invalidated"]
                            if isinstance(cur_invalidated, list):
                                generated += cur_invalidated
                            else:
                                generated += [cur_invalidated]
        
                        cur_generated_by = cur_graph["generated_by"]
                        
                        if isinstance(cur_generated_by, list):
                            se_generated_by += cur_generated_by
                        else:
                            se_generated_by += [cur_generated_by]
                        
                        if "invalidated_by" in cur_graph:
                            cur_invalidated_by = cur_graph["invalidated_by"]
                            if isinstance(cur_invalidated_by, list):
                                se_generated_by += cur_invalidated_by
                            else:
                                se_generated_by += [cur_invalidated_by]
                        
                generated = sorted(list(set(generated)))
                se_generated_by = sorted(list(set(se_generated_by)))
                sen_string = item["iri"] + "se/1" + ",[%s]," % str(len(generated))
                        
                for ca_item in cur_ca["@graph"]:
                    found = False
                    for cur_ca_graph in ca_item["@graph"]:
                        if cur_ca_graph["iri"] in se_generated_by:
                            found = True
                            all_descs = cur_ca_graph["description"]
                            descs = all_descs if isinstance(all_descs, list) else [all_descs]
                            for desc in descs:
                                if "citation data and new identifiers" in desc:
                                    sen_string += "[CIT+ID]"
                                elif "citation data" in desc:
                                    sen_string += "[CIT]"
                                elif "new identifiers" in desc:
                                    sen_string += "[ID]"
                    if found:
                        rep.add_sentence(sen_string)
                        break

    rep.write_file(args.o_file)
