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

from datetime import datetime
import re
import os
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import XSD, RDF, RDFS
from support import create_literal, create_type
from graphlib import GraphSet
from storer import Storer
from reporter import Reporter


class DatasetHandler(object):
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    VOID = Namespace("http://rdfs.org/ns/void#")
    MTT = Namespace("https://w3id.org/spar/mediatype/text/")
    DBR = Namespace("http://dbpedia.org/resource/")

    dataset = DCAT.Dataset
    datafile = DCAT.Distribution

    title = DCTERMS.title
    description = DCTERMS.description
    issued = DCTERMS.issued
    modified = DCTERMS.modified
    keyword = DCAT.keyword
    subject = DCAT.theme
    landing_page = DCAT.landingPage
    subset = VOID.subset
    sparql_endpoint = VOID.sparqlEndpoint
    distribution = DCAT.distribution
    license = DCTERMS.license
    download_url = DCAT.downloadURL
    media_type = DCAT.mediaType
    byte_size = DCAT.byte_size
    label = RDFS.label
    a = RDF.type
    turtle = MTT.turtle
    bibliographic_database = DBR.Bibliographic_database
    open_access = DBR.Open_access
    scholary_communication = DBR.Scholarly_communication
    citations = DBR.Citation

    def __init__(self, tp_url_real, context_path, context_file_path,
                 base_iri, base_dir, info_dir, dataset_home, tmp_dir, triplestore_url=None):
        self.tp_url = triplestore_url
        self.base_iri = base_iri
        self.base_dir = base_dir
        self.info_dir = info_dir
        self.context_path = context_path
        self.dataset_home = URIRef(dataset_home)
        self.tmp_dir = tmp_dir
        self.tp_res = URIRef(tp_url_real)
        self.repok = Reporter(prefix="[DatasetHandler: INFO] ")
        self.reperr = Reporter(prefix="[DatasetHandler: ERROR] ")
        self.st = Storer(context_map={context_path: context_file_path},
                         repok=self.repok, reperr=self.reperr)
        self.st.set_preface_query(
            u"DELETE { ?res <%s> ?date } WHERE { ?res a <%s> ; <%s> ?date }" %
            (str(DatasetHandler.modified), str(DatasetHandler.dataset), str(DatasetHandler.modified)))

    # /START Create Literal
    def create_label(self, g, res, string):
        return create_literal(g, res, RDFS.label, string)

    def create_publication_date(self, g, res, string):
        return create_literal(g, res, self.issued, string, XSD.dateTime)

    def update_modification_date(self, g, res, string):
        g.remove((res, self.modified, None))
        return create_literal(g, res, self.modified, string, XSD.dateTime)

    def create_title(self, g, res, string):
        return create_literal(g, res, self.title, string)

    def create_description(self, g, res, string):
        return create_literal(g, res, self.description, string)

    def create_keyword(self, g, res, string):
        return create_literal(g, res, self.keyword, string)

    def create_byte_size(self, g, res, string):
        return create_literal(g, res, self.byte_size, string, XSD.decimal)
    # /END Create Literal

    # /START Create Complex Attributes
    def has_subject(self, g, res, obj):
        g.add((res, self.subject, obj))

    def has_landing_page(self, g, res, obj):
        g.add((res, self.landing_page, obj))

    def has_subset(self, g, res, obj):
        g.add((res, self.subset, obj))

    def has_sparql_endpoint(self, g, res, obj):
        g.add((res, self.sparql_endpoint, obj))

    def has_distribution(self, g, res, obj):
        g.add((res, self.distribution, obj))

    def has_license(self, g, res, obj):
        g.add((res, self.license, obj))

    def has_download_url(self, g, res, obj):
        g.add((res, self.download_url, obj))

    def has_media_type(self, g, res, obj):
        g.add((res, self.media_type, obj))
    # /END Create Complex Attributes

    # /START Types
    def dataset_type(self, g, res):
        create_type(g, res, self.dataset)

    def distribution_type(self, g, res):
        create_type(g, res, self.datafile)
    # /END Types

    def update_dataset_info(self, graph_set):
        cur_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        subgraphs_to_update = set()
        all_graphs = []

        for g in graph_set.graphs():
            cur_id = g.identifier
            if cur_id not in subgraphs_to_update:
                subgraphs_to_update.add(cur_id)
                cur_dataset_res = URIRef(cur_id)
                cur_dataset = self.get_dataset_graph(cur_dataset_res, cur_time)
                self.update_modification_date(cur_dataset, cur_dataset_res, cur_time)
                all_graphs += [cur_dataset]

        if subgraphs_to_update:
            cur_occ_res = URIRef(self.base_iri)
            cur_occ = self.get_dataset_graph(cur_occ_res, cur_time)
            self.update_modification_date(cur_occ, cur_occ_res, cur_time)

            for subgraph_id in subgraphs_to_update:
                self.has_subset(cur_occ, cur_occ_res, URIRef(subgraph_id))
            all_graphs += [cur_occ]

        if all_graphs:  # Store everything and upload to triplestore
            if self.tp_url is None:
                self.st.store_all(
                    self.base_dir, self.base_iri, self.context_path,
                    self.tmp_dir, all_graphs, True)
            else:
                self.st.upload_and_store(
                    self.base_dir, self.tp_url, self.base_iri, self.context_path,
                    self.tmp_dir, all_graphs, True)

    def get_dataset_graph(self, res, cur_time):
        dataset_path = self.get_metadata_path_from_resource(res)
        if os.path.exists(dataset_path):
            return list(self.st.load(dataset_path, tmp_dir=self.tmp_dir).contexts())[0]
        else:
            dataset_label = "OCC"
            dataset_title = "The OpenCitations Corpus"
            dataset_description = "The OpenCitations Corpus is an open repository of scholarly " \
                                  "citation data made available under a Creative Commons public " \
                                  "domain dedication, which provides in RDF accurate citation " \
                                  "information (bibliographic references) harvested from the " \
                                  "scholarly literature (described using the SPAR Ontologies) " \
                                  "that others may freely build upon, enhance and reuse for any " \
                                  "purpose, without restriction under copyright or database law."
            if re.search("/../$", str(res)) is not None:
                g = Graph(identifier=str(res))
                dataset_short_name = str(res)[-3:-1]
                dataset_name = GraphSet.labels[dataset_short_name]
                dataset_title += ": %s dataset" % dataset_name.title()
                dataset_description += " This sub-dataset contains all the '%s' resources." % \
                                       dataset_name
                dataset_label += " / %s" % dataset_short_name
                self.create_keyword(g, res, dataset_name)
            else:
                g = Graph()
                self.has_landing_page(g, res, self.dataset_home)
                self.has_sparql_endpoint(g, res, self.tp_res)
            self.dataset_type(g, res)
            self.create_label(g, res, dataset_label)
            self.create_title(g, res, dataset_title)
            self.create_description(g, res, dataset_description)
            self.create_publication_date(g, res, cur_time)
            self.create_keyword(g, res, "OCC")
            self.create_keyword(g, res, "OpenCitations")
            self.create_keyword(g, res, "OpenCitations Corpus")
            self.create_keyword(g, res, "SPAR Ontologies")
            self.create_keyword(g, res, "bibliographic references")
            self.create_keyword(g, res, "citations")
            self.has_subject(g, res, self.bibliographic_database)
            self.has_subject(g, res, self.scholary_communication)
            self.has_subject(g, res, self.open_access)
            self.has_subject(g, res, self.citations)

            return g

    def get_metadata_path_from_resource(self, dataset_res):
        return self.get_metadata_path_from_iri(str(dataset_res))

    def get_metadata_path_from_iri(self, dataset_iri):
        return re.sub("^%s" % self.base_iri, self.base_dir, dataset_iri) + "index.json"
