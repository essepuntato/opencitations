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

from rdflib import Graph
from graphlib import GraphEntity, ProvEntity
from rdflib import ConjunctiveGraph
from storer import Storer
import os
from support import find_paths
from conf_spacin import dir_split_number, items_per_file


class ResourceFinder(object):

    def __init__(self, g_set=None, ts_url=None, base_dir=None, base_iri=None,
                 tmp_dir=None, context_map={}):
        self.g = Graph()
        self.base_dir = base_dir
        self.base_iri = base_iri
        self.storer = Storer(context_map=context_map)
        self.tmp_dir = tmp_dir
        self.name = "SPACIN " + self.__class__.__name__
        self.loaded = set()
        if g_set is not None:
            self.update_graph_set(g_set)
        if ts_url is None:
            self.ts = None
        else:
            self.ts = ConjunctiveGraph('SPARQLUpdateStore')
            self.ts.open((ts_url, ts_url))

    def add_prov_triples_in_filesystem(self, res_iri, prov_entity_type=None):
        if self.base_dir is not None and self.base_iri is not None:
            cur_file_path = find_paths(res_iri, self.base_dir, self.base_iri,
                                       dir_split_number, items_per_file)[1]
            if cur_file_path.endswith("index.json"):
                cur_path = cur_file_path.replace("index.json", "") + "prov"
            else:
                cur_path = cur_file_path[:-5] + os.sep + "prov"

            file_list = []
            if os.path.isdir(cur_path):
                for cur_dir, cur_subdir, cur_files in os.walk(cur_path):
                    for cur_file in cur_files:
                        if cur_file.endswith(".json") and \
                           (prov_entity_type is None or cur_file.startswith(prov_entity_type)):
                            file_list += [cur_dir + os.sep + cur_file]

            for file_path in file_list:
                if file_path not in self.loaded:
                    self.loaded.add(file_path)
                    cur_g = self.storer.load(file_path, tmp_dir=self.tmp_dir)
                    self.add_triples_in_graph(cur_g)

    def add_triples_in_graph(self, g):
        if g is not None:
            for s, p, o in g.triples((None, None, None)):
                self.g.add((s, p, o))

    def update_graph_set(self, g_set):
        for g in g_set.graphs():
            self.add_triples_in_graph(g)

    def retrieve(self, id_dict):
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                res = self.__id_with_type(id_string, id_type)
                if res is not None:
                    return res

    def retrieve_provenance_agent_from_name(self, string):
        query = """
            SELECT DISTINCT ?pa WHERE {
              ?pa a <%s> ;
                <%s> "%s"
            } LIMIT 1
        """ % (ProvEntity.prov_agent,
               GraphEntity.name, string)
        return self.__query(query)

    def retrieve_from_orcid(self, string):
        return self.__id_with_type(string, GraphEntity.orcid)

    def retrieve_citing_from_doi(self, string):
        return self.__id_with_type(
            string.lower(), GraphEntity.doi, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_pmid(self, string):
        return self.__id_with_type(
            string, GraphEntity.pmid, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_pmcid(self, string):
        return self.__id_with_type(
            string, GraphEntity.pmcid, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_url(self, string):
        return self.__id_with_type(
            string.lower(), GraphEntity.url, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_from_doi(self, string):
        return self.__id_with_type(string.lower(), GraphEntity.doi)

    def retrieve_from_pmid(self, string):
        return self.__id_with_type(string, GraphEntity.pmid)

    def retrieve_from_pmcid(self, string):
        return self.__id_with_type(string, GraphEntity.pmcid)

    def retrieve_from_url(self, string):
        return self.__id_with_type(string.lower(), GraphEntity.url)

    def retrieve_from_issn(self, string):
        return self.__id_with_type(string, GraphEntity.issn)

    def retrieve_from_isbn(self, string):
        return self.__id_with_type(string, GraphEntity.isbn)

    def retrieve_issue_from_journal(self, id_dict, issue_id, volume_id):
        if volume_id is None:
            return self.__retrieve_from_journal(id_dict, GraphEntity.journal_issue, issue_id)
        else:
            retrieved_volume = self.retrieve_volume_from_journal(id_dict, volume_id)
            if retrieved_volume is not None:
                query = """
                    SELECT DISTINCT ?br WHERE {
                        ?br a <%s> ;
                            <%s> <%s> ;
                            <%s> "%s"
                    } LIMIT 1
                """ % (GraphEntity.journal_issue,
                       GraphEntity.part_of, str(retrieved_volume),
                       GraphEntity.has_sequence_identifier, issue_id)
                return self.__query(query)

    def retrieve_volume_from_journal(self, id_dict, volume_id):
        return self.__retrieve_from_journal(id_dict, GraphEntity.journal_volume, volume_id)

    def retrieve_br_url(self, res, string):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.url)

    def retrieve_br_doi(self, res, string):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.doi)

    def retrieve_br_pmid(self, res, string):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmid)

    def retrieve_br_pmcid(self, res, string):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmcid)

    def retrieve_last_snapshot(self, prov_subj):
        query = """
            SELECT DISTINCT ?se WHERE {
                ?se <%s> <%s> .
                FILTER NOT EXISTS {?se <%s> ?ca }
            } LIMIT 1
        """ % (ProvEntity.specialization_of, str(prov_subj),
               ProvEntity.was_invalidated_by)
        return self.__query(query)

    def __retrieve_res_id_by_type(self, res, id_string, id_type):
        if id_string is not None:
            query = """
            SELECT DISTINCT ?id WHERE {
                <%s> <%s> ?id .
                ?id <%s> <%s> ;
                    <%s> "%s"
            }""" % (
                res, GraphEntity.has_identifier,
                GraphEntity.uses_identifier_scheme, id_type,
                GraphEntity.has_literal_value, id_string)
            return self.__query(query)

    def __retrieve_from_journal(self, id_dict, part_type, part_seq_id):
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                query = """
                SELECT DISTINCT ?res WHERE {
                    ?j <%s> ?id .
                    ?id
                        <%s> <%s> ;
                        <%s> "%s" .
                    ?res a <%s> ;
                        <%s>+ ?j ;
                        <%s> "%s"
                }""" % (
                    GraphEntity.has_identifier,
                    GraphEntity.uses_identifier_scheme, id_type,
                    GraphEntity.has_literal_value, id_string,
                    part_type,
                    GraphEntity.part_of,
                    GraphEntity.has_sequence_identifier, part_seq_id
                )

                return self.__query(query)

    def __id_with_type(self, id_string, id_type, extras=""):
        query = """
        SELECT DISTINCT ?res WHERE {
            ?res <%s> ?id .
            ?id
                <%s> <%s> ;
                <%s> "%s" .
                %s
        }""" % (
            GraphEntity.has_identifier,
            GraphEntity.uses_identifier_scheme, id_type,
            GraphEntity.has_literal_value, id_string, extras)

        return self.__query(query)

    def __query(self, query):
        if self.ts is not None:
            result = self.ts.query(query)
            for res, in result:
                return res

        # If nothing has been returned, check if there is something
        # in the current graph set
        result = self.g.query(query)
        for res, in result:
            return res

