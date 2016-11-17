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
import rdflib
import shutil
import json
from reporter import Reporter
from rdflib import Graph, ConjunctiveGraph, URIRef, Literal
from rdflib.namespace import RDF, Namespace, RDFS
import csv
from support import find_local_line_id
from datetime import datetime
import glob
import collections

context_path = "https://w3id.org/oc/corpus/context.json"
repok = Reporter(True, prefix="[fix_prov.py: INFO] ")
reperr = Reporter(True, prefix="[fix_prov.py: ERROR] ")
repok.new_article()
reperr.new_article()
context_json = {}
PROV = Namespace("http://www.w3.org/ns/prov#")
OCO = Namespace("https://w3id.org/oc/ontology/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CITO = Namespace("http://purl.org/spar/cito/")
DATACITE = Namespace("http://purl.org/spar/datacite/")
FRBR = Namespace("http://purl.org/vocab/frbr/core#")
LITERAL = Namespace("http://www.essepuntato.it/2010/06/literalreification/")


def load(file_p, tmp_dir=None):
    errors = ""
    current_graph = ConjunctiveGraph()

    if tmp_dir is not None:
        file_path = tmp_dir + os.sep + "tmp_rdf_file.rdf"
        shutil.copyfile(file_p, file_path)
    else:
        file_path = file_p

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

    if tmp_dir is not None:
        os.remove(file_path)

    raise IOError("[1]", "It was impossible to handle the format used for storing the file '%s'%s" %
                  (file_path, errors))

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("create_id_counter.py",
                                         description="This script create the id-counter prov dir "
                                                     "starting from the provenance data.")
    arg_parser.add_argument("-i", "--input_dir", dest="input", required=True,
                            help="The corpus base dir.")
    arg_parser.add_argument("-o", "--out_dir", dest="output", required=True,
                            help="The directory where to store the new id-counter.")
    arg_parser.add_argument("-c", "--context", dest="context", required=True,
                            help="The JSON-LD context to use.")
    arg_parser.add_argument("-t", "--tmp_dir", dest="tmp_dir",
                            help="The directory for easing the RDF loading.")
    
    args = arg_parser.parse_args()
    
    repok.new_article()
    reperr.new_article()
    
    with open(args.context) as f:
        context_json = json.load(f)
    
        for prov_dir in glob.glob(args.input + os.sep + "[a-z]*/[0-9]*/[0-9]*/prov/"):
            cur_se_path = prov_dir + os.sep + "se.json"
            cur_cr_path = prov_dir + os.sep + "cr.json"
            cur_ca_path = prov_dir + os.sep + "ca.json"
            
            final_dir = prov_dir.replace(args.input, args.output + os.sep)
            if not os.path.exists(final_dir):
                os.makedirs(final_dir)
            
            for cur_file in [cur_se_path, cur_ca_path, cur_cr_path]:
                cur_result = {}
                cur_g = load(cur_file, args.tmp_dir)
                final_file = cur_file[:-5].replace(args.input, args.output + os.sep) + ".txt"
                
                for res_g in cur_g.contexts():
                    cur_iri = res_g.identifier.replace("/prov/", "")
                    res_line = find_local_line_id(cur_iri, 1000)
                    cur_result[res_line] = len(set(res_g.subjects()))
            
                ordered_result = collections.OrderedDict(sorted(cur_result.items()))
                all_lines = []
                for line_number in ordered_result:
                    value = ordered_result.get(line_number)
                    line_len = len(all_lines)
                    zero_line_number = line_number - 1
                    for i in range(line_number):
                        if i >= line_len:
                            all_lines += ["\n"]
                        if i == zero_line_number:
                            all_lines[i] = str(value) + "\n"

                with open(final_file, "wb") as g:
                    g.writelines(all_lines)
                
    if not reperr.is_empty():
        reperr.write_file("create_id_counter%s_.rep.err.txt" %
                          datetime.now().strftime('%Y_%m_%dT%H_%M_%S'))