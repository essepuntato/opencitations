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
from conf_spacin import temp_dir_for_rdf_loading
from reporter import Reporter


class Checker(object):
    def __init__(self, input_dir, output_dir=None, tmp_dir=None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.tmp_dir = tmp_dir
        self.storer = Storer()
        self.name = self.__class__.__name__
        self.repok = Reporter(prefix="[%s - INFO] " % self.name)
        self.repok.new_article()
        self.reper = Reporter(prefix="[%s - ERROR] " % self.name)
        self.reper.new_article()

    def process(self):
        for cur_dir, cur_subdir, cur_files in os.walk(self.input_dir):
            for cur_file in cur_files:
                self.repok.new_article()
                self.reper.new_article()
                cur_rdf_path = cur_dir + os.sep + cur_file
                try:
                    self.repok.add_sentence("Processing '%s'" % cur_rdf_path)
                    g = self.storer.load(cur_rdf_path, tmp_dir=self.tmp_dir)
                    if self.output_dir is None:
                        self.repok.add_sentence("The RDF graph has been converted in TRIG as follows:\n%s"
                                                % g.serialize(format="trig"))
                    else:
                        if not os.path.exists(self.output_dir):
                            os.makedirs(self.output_dir)
                        output_file = self.output_dir + os.sep + "converted_" + cur_file + ".ttl"
                        self.repok.add_sentence("The RDF graph has been stored in %s"
                                                % (output_file, g.serialize(output_file, format="trig")))
                except Exception:
                    self.reper.add_sentence("The file '%s' doesn't contain RDF statements", False)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        "checker.py", description="This script allows one to convert any RDF file contained in "
                                  "the input directory into TRIG format.")
    arg_parser.add_argument("-i", "--input-dir", dest="input_dir", required=True,
                            help="The directory containing the RDF documents to check.")
    arg_parser.add_argument("-o", "--output-dir", dest="output_dir",
                            help="The directory containing the converted RDF documents.")
    args = arg_parser.parse_args()

    checker = Checker(args.input_dir, args.output_dir, temp_dir_for_rdf_loading)
    checker.process()
