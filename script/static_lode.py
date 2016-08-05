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

import os
import requests
import codecs
import argparse
import re


class StaticLODE(object):
    def __init__(self, doc_dir, onto_map, lang="en", imported_url=None,
                 lode_url="http://eelst.cs.unibo.it/apps/LODE", repl=None):
        self.doc_dir = doc_dir
        self.lode_url = lode_url + "/extract?owlapi=true&lang=%s&url=" % lang
        self.imported_basepath = lode_url
        self.imported_url = imported_url
        self.onto_map = onto_map
        self.repl = repl

    def create_documentation(self):
        for acronym in self.onto_map:
            print "Prepare the documentation of '%s'" % acronym
            ontology_url = self.onto_map[acronym]
            print self.lode_url + ontology_url
            cur_doc = requests.get(self.lode_url + ontology_url).text
            if self.imported_url is not None:
                cur_doc = cur_doc.replace(self.imported_basepath, self.imported_url)
            if self.repl is not None:
                orig_repl = self.repl.split("->")
                cur_doc = re.sub(orig_repl[0], orig_repl[1], cur_doc)
            cur_doc = re.sub("<dl><dt>Other visualisation:</dt><dd>"
                             "<a href=\"[^\"]+\">Ontology source</a></dd></dl>", "", cur_doc)
            if not os.path.exists(self.doc_dir):
                os.makedirs(self.doc_dir)
            with codecs.open(self.doc_dir + os.sep + acronym + ".html", mode="w", encoding="utf-8") as f:
                f.write(cur_doc)
                print "\t ... done!"

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("static_lode.py")
    arg_parser.add_argument("-pu", "--prefix-url", dest="prefurl", required=True,
                            help="The prefix followed by a ':' plus the URL of the ontology to convert.")
    arg_parser.add_argument("-o", "--output-dir", dest="output_dir", required=True,
                            help="The directory where to store the documentation files created.")
    arg_parser.add_argument("-s", "--source-material-url", dest="source_material_url",
                            help="The directory that contains all the LODE related files for "
                                 "presentation on the browser.")
    arg_parser.add_argument("-l", "--lode-url", dest="lode_url",
                            default="http://eelst.cs.unibo.it/apps/LODE",
                            help="The URL where LODE is available.")
    arg_parser.add_argument("-lang", "--language", dest="language", default="en",
                            help="The ISO code of the language used to retrieve the documentation "
                                 "(default: 'en?).")
    arg_parser.add_argument("-repl", "--string-replace", dest="string_replace",
                            help="A 'source->replace' regular expression for replacement of strings.")
    args = arg_parser.parse_args()

    all_ontologies_url = {}
    split_input = args.prefurl.split(":", 1)
    all_ontologies_url.update({split_input[0]: split_input[1]})

    sl = StaticLODE(args.output_dir, all_ontologies_url, args.language,
                    args.source_material_url, args.lode_url, args.string_replace)

    sl.create_documentation()

    # How to call it for a specific ontology:
    # python static_lode.py -pu fabio:http://purl.org/spar/fabio -o spar/ontology_documentations -s /static/lode
