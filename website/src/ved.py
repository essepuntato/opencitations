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

import re
import web
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib import quote
from datetime import datetime
from citation import Citation


class VirtualEntityDirector(object):
    __extensions = (".rdf", ".ttl", ".json", ".html")
    __html = ("text/html",)
    __rdfxml = ("application/rdf+xml",)
    __turtle = ("text/turtle", "text/n3")
    __jsonld = ("application/ld+json", "application/json")

    __citation_local_url_re = "((0[1-9]+0)?[1-9][0-9]*)-((0[1-9]+0)?[1-9][0-9]*)"
    __identifier_local_url_re = "([a-z][a-z])-" + __citation_local_url_re

    def __init__(self, ldd, virtual_local_url, conf):
        self.ldd = ldd
        self.virtual_local_url = virtual_local_url
        self.virtual_baseurl = self.ldd.baseurl.replace(self.ldd.corpus_local_url, self.virtual_local_url)
        self.conf = conf
        self.virtual_entity_director = self.ldd.baseurl + "prov/pa/7"

    def redirect(self, url):
        if url.endswith(self.__extensions):
            return self.get_representation(url)
        else:
            content_type = web.ctx.env.get("HTTP_ACCEPT")
            if content_type:
                for accept_block in content_type.split(";")[::2]:
                    accept_types = accept_block.split(",")

                    if any(mime in accept_types for mime in self.__rdfxml):
                        raise web.seeother(self.virtual_local_url + url + ".rdf")
                    elif any(mime in accept_types for mime in self.__turtle):
                        raise web.seeother(self.virtual_local_url + url + ".ttl")
                    elif any(mime in accept_types for mime in self.__jsonld):
                        raise web.seeother(self.virtual_local_url + url + ".json")
                    else:  # HTML
                        raise web.seeother(self.virtual_local_url + url + ".html")

    def get_representation(self, url):
        if len(url) > 3:  # which means there is a local id specified
            ex_regex = "(\\%s)" % "|\\".join(self.__extensions)
            # dealing citations
            if re.match("^ci/%s%s$" % (self.__citation_local_url_re, ex_regex), url) is not None:
                return self.__handle_citation(url, ex_regex)
            # dealing virtual identifiers
            elif re.match("^id/%s%s$" % (self.__identifier_local_url_re, ex_regex), url) is not None:
                return self.__handle_identifier(url, ex_regex)

    def __execute_query(self, citing, cited):
        result = None

        try:
            i = iter(self.conf["ci"])
            while result is None:
                item = next(i)
                query, prefix, tp, use_it = item["query"], item["prefix"], item["tp"], item["use_it"]
                if use_it == "yes" and citing.startswith(prefix) and cited.startswith(prefix):
                    sparql = SPARQLWrapper(tp)
                    sparql_query = re.sub("\\[\\[CITED\\]\\]", re.sub("^" + prefix, "", cited),
                                          re.sub("\\[\\[CITING\\]\\]", re.sub("^" + prefix, "", citing), query))
                    sparql.setQuery(sparql_query)
                    sparql.setReturnFormat(JSON)
                    q_res = sparql.query().convert()["results"]["bindings"]
                    if len(q_res) > 0:
                        answer = q_res[0]
                        result = answer["citing"]["value"], answer["cited"]["value"], \
                                 answer["citing_year"]["value"] if "citing_year" in answer else None, \
                                 answer["cited_year"]["value"] if "cited_year" in answer else None, \
                                 tp + "?query=" + quote(sparql_query)

        except StopIteration:
            pass  # No nothing

        return result

    def __handle_citation(self, url, ex_regex):
        citing_entity_local_id = re.sub("^ci/%s%s$" % (self.__citation_local_url_re, ex_regex), "\\1", url)
        cited_entity_local_id = re.sub("^ci/%s%s$" % (self.__citation_local_url_re, ex_regex), "\\3", url)

        res = self.__execute_query(citing_entity_local_id, cited_entity_local_id)
        if res is not None:
            citing_url, cited_url, full_citing_pub_date, full_cited_pub_date, sparql_query_url = res
            citing_pub_date = full_citing_pub_date[:10]
            cited_pub_date = full_cited_pub_date[:10]

            citation = Citation(citing_entity_local_id, citing_url, citing_pub_date,
                                cited_entity_local_id, cited_url, cited_pub_date,
                                self.virtual_entity_director, sparql_query_url,
                                datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

            return self.ldd.get_representation(url, True, citation.get_citation_rdf(self.virtual_baseurl, False))

    def __handle_identifier(self, url, ex_regex):
        identified_entity_corpus_id = re.sub("^id/%s%s$" % (self.__identifier_local_url_re, ex_regex), "\\1/\\2-\\4",
                                             url)
        identified_entity_rdf = self.get_representation(identified_entity_corpus_id + ".rdf")
        if identified_entity_rdf is not None:
            citing_entity_local_id, cited_entity_local_id = identified_entity_corpus_id[3:].split("-")
            identifier = Citation(citing_entity_local_id, None, None,
                                  cited_entity_local_id, None, None,
                                  self.virtual_entity_director,
                                  self.virtual_baseurl + identified_entity_corpus_id,
                                  datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))

            return self.ldd.get_representation(url, True, identifier.get_oci_rdf(self.virtual_baseurl))

