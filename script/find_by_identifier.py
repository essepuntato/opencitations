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
from storer import Storer
from conf_spacin import *
from graphlib import GraphEntity
import json
import io


def merge(similar_file_paths, final_result):
    found = None
    for i, l in enumerate(final_result):
        for path in similar_file_paths:
            if path in l:
                found = i
                break
        if found is not None:
            break

    if found is None:
        final_result += [similar_file_paths]
    else:
        final_result[found] = list(set(similar_file_paths).union(final_result[found]))

    return final_result

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        "find_by_identifier.py",
        description="This script allows one to identify the files in a given directory "
                    "containing RDF documents that seem to be identical according to the "
                    "identifier of the entity they describe.")
    arg_parser.add_argument("-i", "--input_dir", dest="i_dir", required=True,
                            help="The directory where to look for duplicates.")
    arg_parser.add_argument("-o", "--output_file", dest="o_file",
                            help="The file where to write the results.")
    arg_parser.add_argument("--recursive", dest="rec", default=False, action="store_true",
                            help="The process will consider also the subdir recursively.")
    args = arg_parser.parse_args()

    id_doc = {}

    s = Storer(context_map={context_path: context_file_path})

    all_files = []
    if args.rec:
        for cur_dir, cur_subdir, cur_files in os.walk(args.i_dir):
            for cur_file in cur_files:
                if cur_file.endswith(".json"):
                    all_files += [cur_dir + os.sep + cur_file]
    else:
        for cur_file in os.listdir(args.i_dir):
            if cur_file.endswith(".json"):
                all_files += [args.i_dir + os.sep + cur_file]

    for rdf_path in all_files:
        cur_g = s.load(rdf_path, tmp_dir=temp_dir_for_rdf_loading)
        try:
            for o in cur_g.objects(None, GraphEntity.has_identifier):
                o_local_path = str(o).replace(base_iri, base_dir) + ".json"
                id_g = s.load(o_local_path, tmp_dir=temp_dir_for_rdf_loading)
                for v in id_g.objects(None, GraphEntity.has_literal_value):
                    if v not in id_doc:
                        id_doc[v] = []
                    id_doc[v] += [rdf_path]
        except:
            pass  # Do nothing

    result = []
    for id_lit in id_doc:
        cur_list = id_doc[id_lit]
        if len(cur_list) > 1:
            result = merge(cur_list, result)

    for doc_set in result:
        print "Similar documents:"
        for doc_item in doc_set:
            print "\t%s" % doc_item

    if args.o_file is not None:
        with io.open(args.o_file, "w", encoding="utf-8") as f:
            json.dump(result, f)
