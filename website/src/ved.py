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
import rdflib
import web
from rdflib.namespace import RDF, RDFS, XSD


class VirtualEntityDirector(object):
    __extensions = (".rdf", ".ttl", ".json", ".html")
    __html = ("text/html",)
    __rdfxml = ("application/rdf+xml",)
    __turtle = ("text/turtle", "text/n3")
    __jsonld = ("application/ld+json", "application/json")

    __cito_base = "http://purl.org/spar/cito/"
    __cites = rdflib.URIRef(__cito_base + "cites")
    __citation = rdflib.URIRef(__cito_base + "Citation")
    __has_citation_time_span = rdflib.URIRef(__cito_base + "hasCitationTimeSpan")
    __has_citing_entity = rdflib.URIRef(__cito_base + "hasCitingEntity")
    __has_cited_entity = rdflib.URIRef(__cito_base + "hasCitedEntity")

    __datacite_base = "http://purl.org/spar/datacite/"
    __has_identifier = rdflib.URIRef(__datacite_base + "hasIdentifier")
    __identifier = rdflib.URIRef(__datacite_base + "Identifier")
    __uses_identifier_scheme = rdflib.URIRef(__datacite_base + "usesIdentifierScheme")
    __oci = rdflib.URIRef(__datacite_base + "oci")

    __literal_base = "http://www.essepuntato.it/2010/06/literalreification/"
    __has_literal_value = rdflib.URIRef(__literal_base + "hasLiteralValue")

    __fabio_base = "http://purl.org/spar/fabio/"
    __has_publication_year = rdflib.URIRef(__fabio_base + "hasPublicationYear")

    def __init__(self, ldd, virtual_local_url):
        self.ldd = ldd
        self.virtual_local_url = virtual_local_url
        self.virtual_baseurl = self.ldd.baseurl.replace(self.ldd.corpus_local_url, self.virtual_local_url)

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
            if re.match("^ci/([a-z]+-)?[0-9]+-([a-z]+-)?[0-9]+%s$" % ex_regex, url) is not None:  # dealing citations
                return self.__handle_citation(url, ex_regex)
            elif re.match("^id/[a-z][a-z]-([a-z-0-9]+)%s$" % ex_regex, url) is not None:  # dealing virtual identifiers
                return self.__handle_identifier(url, ex_regex)

    def __handle_citation(self, url, ex_regex):
        citing_entity_local_id = re.sub("^ci/(([a-z]+-)?[0-9]+)-.+%s$" % ex_regex, "\\1", url)
        citing_entity_corpus_id = "br/" + citing_entity_local_id
        citing_br_rdf = self.ldd.get_representation(citing_entity_corpus_id + ".rdf", True)
        if citing_br_rdf is not None:
            citing_br_g = rdflib.Graph()
            citing_br_g.parse(data=citing_br_rdf, format="xml")
            cited_entity_local_id = re.sub("^ci/([a-z]+-)?[0-9]+-(([a-z]+-)?[0-9]+)%s$" % ex_regex, "\\2", url)
            cited_entity_corpus_id = "br/" + cited_entity_local_id

            citing_br = rdflib.URIRef(self.ldd.baseurl + citing_entity_corpus_id)
            cited_br = rdflib.URIRef(self.ldd.baseurl + cited_entity_corpus_id)
            if len(list(citing_br_g.triples((citing_br, self.__cites, cited_br)))):
                citation_graph = rdflib.Graph()
                citation_local_id = citing_entity_local_id + "-" + cited_entity_local_id
                citation_corpus_id = "ci/" + citation_local_id
                citation = rdflib.URIRef(self.virtual_baseurl + citation_corpus_id)
                occ_citation_id = rdflib.URIRef(self.virtual_baseurl + "id/" + citation_corpus_id.replace("/", "-"))
                citation_graph.add((citation, RDFS.label,
                                    rdflib.Literal("citation %s [%s]" % (citation_local_id, citation_corpus_id))))
                citation_graph.add((citation, RDF.type, self.__citation))
                citation_graph.add((citation, self.__has_citing_entity, citing_br))
                citation_graph.add((citation, self.__has_cited_entity, cited_br))
                citation_graph.add((citation, self.__has_identifier, occ_citation_id))

                citing_pub_year = list(citing_br_g.objects(citing_br, self.__has_publication_year))
                if citing_pub_year:
                    cited_br_rdf = self.ldd.get_representation(cited_entity_corpus_id + ".rdf", True)
                    cited_br_g = rdflib.Graph()
                    cited_br_g.parse(data=cited_br_rdf, format="xml")

                    cited_pub_year = list(cited_br_g.objects(cited_br, self.__has_publication_year))
                    if cited_pub_year:
                        citation_graph.add((
                            citation, self.__has_citation_time_span,
                            rdflib.Literal(
                                int(citing_pub_year[0][:4]) - int(cited_pub_year[0][:4]), datatype=XSD.integer)))

                return self.ldd.get_representation(url, True, citation_graph)

    def __handle_identifier(self, url, ex_regex):
        identified_entity_corpus_id = re.sub("^id/([a-z][a-z])-([a-z-0-9]+)%s$" % ex_regex, "\\1/\\2", url)
        identified_entity_rdf = self.get_representation(identified_entity_corpus_id + ".rdf")
        if identified_entity_rdf is not None:
            identifier_graph = rdflib.Graph()
            identifier_local_id = identified_entity_corpus_id.replace("/", "-")
            identifier_corpus_id = "id/" + identifier_local_id
            identifier = rdflib.URIRef(self.virtual_baseurl + identifier_corpus_id)
            identifier_graph.add((identifier, RDFS.label,
                                  rdflib.Literal("identifier %s [%s]" % (identifier_local_id, identifier_corpus_id))))
            identifier_graph.add((identifier, RDF.type, self.__identifier))
            if identified_entity_corpus_id.startswith("ci/"):  # OCI for citations
                identifier_graph.add((identifier, self.__uses_identifier_scheme, self.__oci))
                identifier_graph.add((identifier, self.__has_literal_value,
                                      rdflib.Literal(identified_entity_corpus_id[3:])))

            return self.ldd.get_representation(url, True, identifier_graph)
