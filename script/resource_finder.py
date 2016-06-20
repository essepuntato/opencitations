#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

from rdflib import Graph
from graphlib import GraphEntity, ProvEntity
from rdflib import ConjunctiveGraph


class ResourceFinder(object):

    def __init__(self, g_set=None, ts_url=None):
        self.g = Graph()
        self.name = "SPACIN " + self.__class__.__name__
        if g_set is not None:
            self.update_graph_set(g_set)
        if ts_url is None:
            self.ts = None
        else:
            self.ts = ConjunctiveGraph('SPARQLUpdateStore')
            self.ts.open((ts_url, ts_url))

    def update_graph_set(self, g_set):
        for g in g_set.graphs():
            for s, p, o in g.triples((None, None, None)):
                self.g.add((s, p, o))

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

    def retrieve_citing_from_pmid(self, string):
        return self.__id_with_type(
            string, GraphEntity.pmcid, "?res <%s> ?cited" % GraphEntity.cites)

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

    def retrieve_issue_from_journal(self, id_dict, issue_id):
        return self.__retrieve_from_journal(id_dict, GraphEntity.journal_issue, issue_id)

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

