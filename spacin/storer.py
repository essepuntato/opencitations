#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

from SPARQLWrapper import SPARQLWrapper
from reporter import Reporter
import re
import os
from rdflib import Graph
import shutil


class Storer(object):

    def __init__(self, graph_set=None, repok=None, reperr=None):
        if graph_set is None:
            self.g = []
        else:
            self.g = graph_set.graphs()
        if repok is None:
            self.repok = Reporter()
        else:
            self.repok = repok
        if reperr is None:
            self.reperr = Reporter()
        else:
            self.reperr = reperr

    def upload_and_store(self, base_dir, triplestore_url, base_iri, context_path, tmp_dir=None):
        self.repok.new_article()
        self.reperr.new_article()

        self.repok.add_sentence("[Storer: INFO] Starting the process")

        for idx, cur_g in enumerate(self.g):
            self.upload(cur_g, triplestore_url, idx)
            self.store(cur_g, base_dir, base_iri, context_path, tmp_dir)

    def upload(self, cur_g, triplestore_url, idx=0):
        self.repok.new_article()
        self.reperr.new_article()

        cur_g_iri = str(cur_g.identifier)
        try:
            tp = SPARQLWrapper(triplestore_url)
            tp.setMethod('POST')
            tp.setQuery("INSERT DATA { GRAPH <%s> { %s } }" %
                        (cur_g_iri,
                         cur_g.serialize(format="nt")))
            tp.query()

            self.repok.add_sentence(
                "[Storer: INFO] "
                "Triplestore updated with %s more RDF statements (graph '%s') contained "
                "in the graph number '%s'." %
                (len(cur_g), cur_g_iri, str(idx + 1)))

            return True

        except Exception as e:
            self.reperr.add_sentence("[Storer: ERROR 1] "
                                     "Graph number '%s' was not loaded into the "
                                     "triplestore due to communication problems: %s" %
                                     (str(idx + 1), str(e)))

            return False

    def store(self, cur_g, base_dir, base_iri, context_path, tmp_dir=None):
        self.repok.new_article()
        self.reperr.new_article()

        if len(cur_g) > 0:
            cur_subject = set(cur_g.subjects(None, None)).pop()

            cur_dir_path = base_dir + re.sub("^%s(.+)/[0-9]+$" % base_iri, "\\1", str(cur_subject))
            if not os.path.exists(cur_dir_path):
                os.makedirs(cur_dir_path)

            cur_file_path = cur_dir_path + os.sep + \
                            re.sub("^.+/([0-9]+)$", "\\1", str(cur_subject)) + ".json"

            # Merging the data
            if os.path.exists(cur_file_path):
                cur_g = self.load(cur_file_path, cur_g, tmp_dir)

            cur_g.serialize(cur_file_path, format="json-ld", indent=4, context=context_path)

            self.repok.add_sentence("[Storer: INFO] File '%s' added." % cur_file_path)

    def load(self, rdf_file_path, cur_graph=None, tmp_dir=None):
        current_graph = cur_graph

        if os.path.isfile(rdf_file_path):
            try:
                current_graph = Storer.__load_graph(rdf_file_path, current_graph)
            except IOError:
                if tmp_dir is not None:
                    current_file_path = tmp_dir + os.sep + "tmp_rdf_file.rdf"
                    shutil.copyfile(rdf_file_path, current_file_path)
                    try:
                        current_graph = Storer.__load_graph(current_file_path, current_graph)
                    except IOError:
                        self.reperr.add_sentence("[Storer: ERROR 2] "
                                                 "It was impossible to handle the format used for "
                                                 "storing the file (stored in the temporary path) '%s'"
                                                 % current_file_path)
                    os.remove(current_file_path)
                else:
                    self.reperr.add_sentence("[Storer: ERROR 3] "
                                             "It was impossible to handle the format used for "
                                             "storing the file '%s'"
                                             "It was impossible to try to load the file from the "
                                             "temporary path since that has not been specified in "
                                             "advance" % rdf_file_path)
        else:
            self.reperr.add_sentence("[Storer: ERROR 4] "
                                     "The file specified ('%s') doesn't exist."
                                     % rdf_file_path)

        return current_graph

    @staticmethod
    def __load_graph(file_path, cur_graph=None):
        formats = ["json-ld", "rdfxml", "turtle", "trig"]

        if cur_graph is None:
            current_graph = Graph()
        else:
            current_graph = cur_graph

        for cur_format in formats:
            try:
                current_graph.load(file_path, format=cur_format)
                return current_graph
            except Exception:
                pass  # Try another format

        raise IOError("1", "It was impossible to handle the format used for storing the file '%s'" %
                      file_path)