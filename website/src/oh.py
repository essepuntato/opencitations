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

from xml.sax import SAXParseException
import web
import rdflib
import os
import re
import shutil


class OntologyHandler(object):
    __extensions = (".rdf", ".ttl", ".json", ".html")
    __rdfxml = ("application/rdf+xml",)
    __turtle = ("text/turtle", "text/n3")
    __jsonld = ("application/ld+json", "application/json")

    def __init__(self, baseurl, doc_basepath, ontomap, tmp_dir):
        self.baseurl = baseurl
        self.doc_basepath = doc_basepath
        self.ontomap = ontomap
        self.tmp_dir = tmp_dir

    def log(self):
        if self.logger is not None:
            self.logger.mes()

    def get_render(self):
        return self.render

    def redirect(self, url):
        if url.endswith(self.__extensions):
            return self.get_representation(url)
        else:
            content_type = web.ctx.env.get("HTTP_ACCEPT")
            if content_type:
                for accept_block in content_type.split(";")[::2]:
                    accept_types = accept_block.split(",")

                    if any(mime in accept_types for mime in self.__rdfxml):
                        raise web.seeother(url + ".rdf")
                    elif any(mime in accept_types for mime in self.__turtle):
                        raise web.seeother(url + ".ttl")
                    elif any(mime in accept_types for mime in self.__jsonld):
                        raise web.seeother(url + ".json")
                    else:  # HTML
                        raise web.seeother(url + ".html")

    def get_representation(self, url):
        # URL = [base]/[acronym]
        ontology_acronym = re.sub("^%s/?(.+)\..+$" % (self.baseurl), "\\1", url)
        if ontology_acronym is not None:
            if url.endswith(".html"):
                doc_file = self.doc_basepath + os.sep + ontology_acronym + ".html"
                if os.path.exists(doc_file):
                    with open(doc_file) as f:
                        return f.read()
            elif ontology_acronym in self.ontomap:
                ontology_url = self.ontomap[ontology_acronym]
                cur_graph = self.load_graph(ontology_url)
                if len(cur_graph):
                    if url.endswith(".rdf"):
                        return cur_graph.serialize(format="xml")
                    elif url.endswith(".ttl"):
                        return cur_graph.serialize(format="turtle")
                    elif url.endswith(".json"):
                        return cur_graph.serialize(format="json-ld")

    def load_graph(self, ontology_url):
        current_graph = rdflib.Graph()

        try:
            current_graph.load(ontology_url)
        except IOError:
            current_file_path = self.tmp_dir + os.sep + "tmp_rdf_file.rdf"
            shutil.copyfile(ontology_url, current_file_path)
            try:
                current_graph.load(current_file_path)
                os.remove(current_file_path)
            except Exception as e:
                os.remove(current_file_path)
                raise e
        except Exception as e:
            raise e

        return current_graph