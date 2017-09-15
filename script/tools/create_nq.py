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
import re
import shutil
import json
from reporter import Reporter
from rdflib import ConjunctiveGraph

def load(cur_graph, rdf_file_path, tmp_dir=None):
    if os.path.isfile(rdf_file_path):
        try:
            cur_graph = __load_graph(cur_graph, rdf_file_path)
        except IOError:
            if tmp_dir is not None:
                current_file_path = tmp_dir + os.sep + "tmp_rdf_file_create_nq.rdf"
                shutil.copyfile(rdf_file_path, current_file_path)
                try:
                    cur_graph = __load_graph(cur_graph, current_file_path)
                except IOError as e:
                    reperr.add_sentence("It was impossible to handle the format used for "
                                        "storing the file (stored in the temporary path) '%s'. "
                                        "Additional details: %s"
                                        % (current_file_path, str(e)))
                os.remove(current_file_path)
            else:
                reperr.add_sentence("It was impossible to try to load the file from the "
                                    "temporary path '%s' since that has not been specified in "
                                    "advance" % rdf_file_path)
    else:
        reperr.add_sentence("The file specified ('%s') doesn't exist."
                            % rdf_file_path)

    return cur_graph


def __load_graph(current_graph, file_path):
    errors = ""

    try:
        with open(file_path) as f:
            json_ld_file = json.load(f)
            if isinstance(json_ld_file, dict):
                json_ld_file = [json_ld_file]

            for json_ld_resource in json_ld_file:
                # Trick to force the use of a pre-loaded context if the format
                # specified is JSON-LD
                cur_context = json_ld_resource["@context"]
                json_ld_resource["@context"] = context_json

                current_graph.parse(data=json.dumps(json_ld_resource), format="json-ld")

            return current_graph
    except Exception as e:
        errors = " | " + str(e)  # Try another format

    raise IOError("It was impossible to handle the format used for storing the file '%s'%s" %
                  (file_path, errors))


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("create_nq.py",
                                         description="This script create an nt file given a directory containing json-ld files.")
    arg_parser.add_argument("-i", "--input", dest="input", required=True,
                            help="The directory containing the json-ld data.")
    arg_parser.add_argument("-o", "--output", dest="output", required=True,
                            help="The output file.")
    arg_parser.add_argument("-t", "--tmp_dir", dest="tmp_dir",
                            help="The directory for easing the RDF loading.")
    arg_parser.add_argument("-c", "--context", dest="context", required=True,
                            help="The JSON-LD context to use.")

    args = arg_parser.parse_args()

    with open(args.context) as f:
        context_json = json.load(f)

    repok = Reporter(True, prefix="[create_nq.py: INFO] ")
    reperr = Reporter(True, prefix="[create_nq.py: ERROR] ")
    repok.new_article()
    reperr.new_article()

    for cur_dir, cur_subdir, cur_files in os.walk(args.input):
        with open(args.output, 'a') as f:
            for cur_file in cur_files:
                if cur_file.endswith(".json"):
                    cur_g = ConjunctiveGraph()
                    cur_g = load(cur_g, cur_dir + os.sep + cur_file, args.tmp_dir)
                    nt_strings = cur_g.serialize(format="nquads")
                    f.write(nt_strings)

    repok.add_sentence("Done.")
    if not reperr.is_empty():
        reperr.write_file("create_nq.rep.%s.err.txt" % (
            re.sub("_+", "_", re.sub("[\.%s/]" % os.sep, "_", args.input))))
