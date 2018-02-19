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

from rdflib import Graph, RDF, RDFS, XSD, URIRef, Literal
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from datetime import datetime


class Citation(object):
    __cito_base = "http://purl.org/spar/cito/"
    __cites = URIRef(__cito_base + "cites")
    __citation = URIRef(__cito_base + "Citation")
    __has_citation_creation_date = URIRef(__cito_base + "hasCitationCreationDate")
    __has_citation_time_span = URIRef(__cito_base + "hasCitationTimeSpan")
    __has_citing_entity = URIRef(__cito_base + "hasCitingEntity")
    __has_cited_entity = URIRef(__cito_base + "hasCitedEntity")

    __datacite_base = "http://purl.org/spar/datacite/"
    __has_identifier = URIRef(__datacite_base + "hasIdentifier")
    __identifier = URIRef(__datacite_base + "Identifier")
    __uses_identifier_scheme = URIRef(__datacite_base + "usesIdentifierScheme")
    __oci = URIRef(__datacite_base + "oci")

    __literal_base = "http://www.essepuntato.it/2010/06/literalreification/"
    __has_literal_value = URIRef(__literal_base + "hasLiteralValue")

    __prism_base = "http://prismstandard.org/namespaces/basic/2.0/"
    __publication_date = URIRef(__prism_base + "publicationDate")

    __prov_base = "http://www.w3.org/ns/prov#"
    __was_attributed_to = URIRef(__prov_base + "wasAttributedTo")
    __had_primary_source = URIRef(__prov_base + "hadPrimarySource")
    __generated_at_time = URIRef(__prov_base + "generatedAtTime")

    def __init__(self,
                 citing_entity_local_id, citing_url, citing_pub_date,
                 cited_entity_local_id, cited_url, cited_pub_date,
                 prov_agent_url, source, prov_date):
        self.oci = citing_entity_local_id + "-" + cited_entity_local_id
        self.citing_url = citing_url
        self.cited_url = cited_url

        self.creation_date = None
        self.duration = None
        if self.contains_years(citing_pub_date):
            default_date = datetime(1970, 1, 1, 0, 0)
            self.creation_date = citing_pub_date[:10]
            citing_pub_datetime = parse(self.creation_date, default=default_date)

            if self.contains_years(cited_pub_date):
                cited_pub_datetime = parse(cited_pub_date[:10], default=default_date)
                print(citing_pub_datetime, cited_pub_datetime)
                delta = relativedelta(citing_pub_datetime, cited_pub_datetime)
                self.duration = self.get_duration(
                    delta,
                    self.contains_months(citing_pub_date) and self.contains_months(cited_pub_date),
                    self.contains_days(citing_pub_date) and self.contains_days(cited_pub_date))

        self.prov_agent_url = prov_agent_url
        self.source = source
        self.prov_date = prov_date

    def get_citation_rdf(self, baseurl, include_oci=True):
        citation_graph = Graph()

        citing_br = URIRef(self.citing_url)
        cited_br = URIRef(self.cited_url)

        citation_corpus_id = "ci/" + self.oci
        citation = URIRef(baseurl + citation_corpus_id)
        occ_citation_id = URIRef(baseurl + "id/ci-" + self.oci)
        citation_graph.add((citation, RDFS.label,
                            Literal("citation %s [%s]" % (self.oci, citation_corpus_id))))
        citation_graph.add((citation, RDF.type, self.__citation))
        citation_graph.add((citation, self.__has_citing_entity, citing_br))
        citation_graph.add((citation, self.__has_cited_entity, cited_br))
        citation_graph.add((citation, self.__has_identifier, occ_citation_id))

        if self.creation_date is not None:
            if Citation.contains_days(self.creation_date):
                xsd_type = XSD.date
            elif Citation.contains_months(self.creation_date):
                xsd_type = XSD.gYearMonth
            else:
                xsd_type = XSD.gYear
            print(self.creation_date)
            citation_graph.add((citation, self.__has_citation_creation_date,
                                Literal(self.creation_date, datatype=xsd_type)))
            if self.duration is not None:
                citation_graph.add((citation, self.__has_citation_time_span,
                                    Literal(self.duration, datatype=XSD.duration)))

        if include_oci:
            citation_graph += self.get_oci_rdf(baseurl)

        citation_graph.add((citation, self.__was_attributed_to, URIRef(self.prov_agent_url)))
        citation_graph.add((citation, self.__had_primary_source, URIRef(self.source)))
        citation_graph.add((citation, self.__generated_at_time, Literal(self.prov_date, datatype=XSD.dateTime)))

        return citation_graph

    def get_oci_rdf(self, baseurl):
        identifier_graph = Graph()
        identifier_local_id = "ci-" + self.oci
        identifier_corpus_id = "id/" + identifier_local_id
        identifier = URIRef(baseurl + identifier_corpus_id)
        identifier_graph.add((identifier, RDFS.label,
                              Literal("identifier %s [%s]" % (identifier_local_id, identifier_corpus_id))))
        identifier_graph.add((identifier, RDF.type, self.__identifier))
        identifier_graph.add((identifier, self.__uses_identifier_scheme, self.__oci))
        identifier_graph.add((identifier, self.__has_literal_value, Literal(self.oci)))

        identifier_graph.add((identifier, self.__was_attributed_to, URIRef(self.prov_agent_url)))
        identifier_graph.add((identifier, self.__had_primary_source, URIRef(self.source)))
        identifier_graph.add((identifier, self.__generated_at_time, Literal(self.prov_date, datatype=XSD.dateTime)))

        return identifier_graph

    def get_citation_csv(self, include_oci=True):
        pass

    def get_oci_csv(self):
        pass

    @staticmethod
    def contains_years(date):
        return date is not None and len(date) >= 4

    @staticmethod
    def contains_months(date):
        return date is not None and len(date) >= 7

    @staticmethod
    def contains_days(date):
        return date is not None and len(date) >= 10

    @staticmethod
    def get_duration(delta, consider_months, consider_days):
        result = ""
        if delta.years < 0:
            result += "-"
        result += "P"

        if delta.years != 0 or ((not consider_months or delta.months == 0) and (not consider_days or delta.days == 0)):
            result += "%sY" % abs(delta.years)

        if consider_months and delta.months != 0:
            result += "%sM" % abs(delta.months)

        if consider_days and delta.days != 0:
            result += "%sD" % abs(delta.days)

        return result


if __name__ == "__main__":
    pass  # TODO: test