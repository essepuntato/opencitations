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

from xml.sax import SAXParseException

__author__ = 'essepuntato'
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD, RDFS
from reporter import Reporter
import re
import os
from datetime import datetime
from support import is_string_empty, create_literal, create_type, get_short_name, \
    get_count, encode_url, find_paths, find_local_line_id
from conf_spacin import dir_split_number, items_per_file
import linecache


class GraphEntity(object):
    BIRO = Namespace("http://purl.org/spar/biro/")
    C4O = Namespace("http://purl.org/spar/c4o/")
    CITO = Namespace("http://purl.org/spar/cito/")
    DATACITE = Namespace("http://purl.org/spar/datacite/")
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    DOCO = Namespace("http://purl.org/spar/doco/")
    FABIO = Namespace("http://purl.org/spar/fabio/")
    FOAF = Namespace("http://xmlns.com/foaf/0.1/")
    FRBR = Namespace("http://purl.org/vocab/frbr/core#")
    LITERAL = Namespace("http://www.essepuntato.it/2010/06/literalreification/")
    OCO = Namespace("https://w3id.org/oc/ontology/")
    PRISM = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
    PRO = Namespace("http://purl.org/spar/pro/")

    # Bibliographic entities
    has_subtitle = FABIO.hasSubtitle
    has_publication_year = FABIO.hasPublicationYear
    bibliographic_reference = BIRO.BibliographicReference
    references = BIRO.references
    has_content = C4O.hasContent
    cites = CITO.cites
    doi = DATACITE.doi
    occ = DATACITE.occ
    pmid = DATACITE.pmid
    pmcid = DATACITE.pmcid
    orcid = DATACITE.orcid
    has_identifier = DATACITE.hasIdentifier
    identifier = DATACITE.Identifier
    isbn = DATACITE.isbn
    issn = DATACITE.issn
    url = DATACITE.url
    uses_identifier_scheme = DATACITE.usesIdentifierScheme
    title = DCTERMS.title
    part = DOCO.Part
    academic_proceedings = FABIO.AcademicProceedings
    book = FABIO.Book
    book_chapter = FABIO.BookChapter
    book_series = FABIO.BookSeries
    book_set = FABIO.BookSet
    data_file = FABIO.DataFile
    expression = FABIO.Expression
    expression_collection = FABIO.ExpressionCollection
    has_sequence_identifier = FABIO.hasSequenceIdentifier
    journal = FABIO.Journal
    journal_article = FABIO.JournalArticle
    journal_issue = FABIO.JournalIssue
    journal_volume = FABIO.JournalVolume
    manifestation = FABIO.Manifestation
    proceedings_paper = FABIO.ProceedingsPaper
    reference_book = FABIO.ReferenceBook
    reference_entry = FABIO.ReferenceEntry
    report_document = FABIO.ReportDocument
    series = FABIO.Series
    specification_document = FABIO.SpecificationDocument
    thesis = FABIO.Thesis
    agent = FOAF.Agent
    family_name = FOAF.familyName
    given_name = FOAF.givenName
    name = FOAF.name
    embodiment = FRBR.embodiment
    part_of = FRBR.partOf
    contains_reference = FRBR.part
    has_literal_value = LITERAL.hasLiteralValue
    ending_page = PRISM.endingPage
    starting_page = PRISM.startingPage
    author = PRO.author
    editor = PRO.editor
    is_held_by = PRO.isHeldBy
    publisher = PRO.publisher
    is_document_context_for = PRO.isDocumentContextFor
    role_in_time = PRO.RoleInTime
    with_role = PRO.withRole
    has_next = OCO.hasNext

    # This constructor creates a new instance of an RDF resource
    def __init__(self, g, res=None, res_type=None, resp_agent=None, source_agent=None,
                 source=None, count=None, label=None, short_name="", g_set=None):
        self.cur_name = "SPACIN " + self.__class__.__name__
        self.resp_agent = resp_agent
        self.source_agent = source_agent
        self.source = source

        existing_ref = False

        # Create the reference if not specified
        if res is None:
            self.res = \
                URIRef(str(g.identifier) + (short_name + "/" if short_name != "" else "") + str(count))
        else:
            self.res = res
            existing_ref = True

        # Associated the graph in input if no existing graph
        # was already used for that entity
        if self.res in g_set.entity_g:
            self.g = g_set.entity_g[self.res]
        else:
            self.g = g
            g_set.entity_g[self.res] = self.g

        if self.res not in g_set.res_to_entity:
            g_set.res_to_entity[self.res] = self

        # If it is a new entity, add all the additional information to it
        if not existing_ref:
            self._create_type(res_type)

            # It creates the label
            if label is not None:
                self.create_label(label)

    def __str__(self):
        return str(self.res)

    # /START Literal Attributes
    def create_title(self, string):
        return self._create_literal(GraphEntity.title, string)

    def create_subtitle(self, string):
        return self._create_literal(GraphEntity.has_subtitle, string)

    def create_pub_year(self, string):
        return self._create_literal(GraphEntity.has_publication_year, string, XSD.gYear)

    def create_starting_page(self, string):
        if re.search("[-–]+", string) is None:
            page_number = string
        else:
            page_number = re.sub("[-–]+.*$", "", string)
        return self._create_literal(GraphEntity.starting_page, page_number)

    def create_ending_page(self, string):
        if re.search("[-–]+", string) is None:
            page_number = string
        else:
            page_number = re.sub("^.*[-–]+", "", string)
        return self._create_literal(GraphEntity.ending_page, page_number)

    def create_number(self, string):
        return self._create_literal(GraphEntity.has_sequence_identifier, string)

    def create_content(self, string):
        return self._create_literal(GraphEntity.has_content, string)

    def create_name(self, string):
        return self._create_literal(GraphEntity.name, string)

    def create_given_name(self, string):
        return self._create_literal(GraphEntity.given_name, string)

    def create_family_name(self, string):
        return self._create_literal(GraphEntity.family_name, string)

    def create_label(self, string):
        return self._create_literal(RDFS.label, string)
    # /END Literal Attributes

    # /START Composite Attributes
    def create_expression_collection(self):
        self._create_type(GraphEntity.expression_collection)

    def create_book_chapter(self):
        self._create_type(GraphEntity.book_chapter)

    def create_book_part(self):
        self._create_type(GraphEntity.part)

    def create_book_section(self):
        self._create_type(GraphEntity.expression_collection)

    def create_book_series(self):
        self._create_type(GraphEntity.book_series)

    def create_book_set(self):
        self._create_type(GraphEntity.book_set)

    def create_book_track(self):
        self._create_type(GraphEntity.expression)

    def create_book(self):
        self._create_type(GraphEntity.book)

    def create_component(self):
        self._create_type(GraphEntity.expression)

    def create_dataset(self):
        self._create_type(GraphEntity.data_file)

    def create_dissertation(self):
        self._create_type(GraphEntity.thesis)

    def create_edited_book(self):
        self._create_type(GraphEntity.book)

    def create_journal(self):
        self._create_type(GraphEntity.journal)

    def create_journal_article(self):
        self._create_type(GraphEntity.journal_article)

    def create_issue(self):
        self._create_type(GraphEntity.journal_issue)

    def create_volume(self):
        self._create_type(GraphEntity.journal_volume)

    def create_monograph(self):
        self._create_type(GraphEntity.book)

    def create_other(self):
        self._create_type(GraphEntity.expression)

    def create_proceedings(self):
        self._create_type(GraphEntity.academic_proceedings)

    def create_proceedings_article(self):
        self._create_type(GraphEntity.proceedings_paper)

    def create_reference_book(self):
        self._create_type(GraphEntity.reference_book)

    def create_reference_entry(self):
        self._create_type(GraphEntity.reference_entry)

    def create_report(self):
        self._create_type(GraphEntity.report_document)

    def create_report_series(self):
        self._create_type(GraphEntity.series)

    def create_standard(self):
        self._create_type(GraphEntity.specification_document)

    def create_standard_series(self):
        self._create_type(GraphEntity.series)

    def create_publisher(self, br_res):
        return self._associate_role_with_document(GraphEntity.publisher, br_res)

    def create_author(self, br_res):
        return self._associate_role_with_document(GraphEntity.author, br_res)

    def create_editor(self, br_res):
        return self._associate_role_with_document(GraphEntity.editor, br_res)

    def create_orcid(self, string):
        return self._associate_identifier_with_scheme(string, GraphEntity.orcid)

    def create_doi(self, string):
        return self._associate_identifier_with_scheme(string.lower(), GraphEntity.doi)

    def create_pmid(self, string):
        return self._associate_identifier_with_scheme(string, GraphEntity.pmid)

    def create_pmcid(self, string):
        return self._associate_identifier_with_scheme(string, GraphEntity.pmcid)

    def create_issn(self, string):
        cur_string = re.sub("–", "-", string)
        if cur_string != "0000-0000":
            return self._associate_identifier_with_scheme(string, GraphEntity.issn)

    def create_isbn(self, string):
        return self._associate_identifier_with_scheme(
            re.sub("–", "-", string), GraphEntity.isbn)

    def create_url(self, string):
        return self._associate_identifier_with_scheme(encode_url(string.lower()), GraphEntity.url)

    def has_id(self, id_res):
        self.g.add((self.res, GraphEntity.has_identifier, URIRef(str(id_res))))

    def has_format(self, re_res):
        self.g.add((self.res, GraphEntity.embodiment, URIRef(str(re_res))))

    def has_part(self, br_res):
        br_res.g.add((URIRef(str(br_res)), GraphEntity.part_of, self.res))

    def contains_in_reference_list(self, be_res):
        self.g.add((self.res, GraphEntity.contains_reference, URIRef(str(be_res))))

    def has_citation(self, br_res):
        self.g.add((self.res, GraphEntity.cites, URIRef(str(br_res))))

    def has_reference(self, be_res):
        be_res.g.add((URIRef(str(be_res)), GraphEntity.references, self.res))

    def has_role(self, ar_res):
        ar_res.g.add((URIRef(str(ar_res)), GraphEntity.is_held_by, self.res))

    def follows(self, ar_res):
        ar_res.g.add((URIRef(str(ar_res)), GraphEntity.has_next, self.res))
    # /END Composite Attributes

    # /START Protected Methods
    def _associate_identifier_with_scheme(self, string, id_type):
        if not is_string_empty(string):
            self._create_literal(GraphEntity.has_literal_value, string)
            self.g.add((self.res, GraphEntity.uses_identifier_scheme, id_type))
            return True
        return False

    def _associate_role_with_document(self, role_type, br_res):
        self.g.add((self.res, GraphEntity.with_role, role_type))
        br_res.g.add((URIRef(str(br_res)), GraphEntity.is_document_context_for, self.res))
        return True

    def _create_literal(self, p, s, dt=None):
        return create_literal(self.g, self.res, p, s, dt)

    def _create_type(self, res_type):
        create_type(self.g, self.res, res_type)
    # /END Private Methods


class GraphSet(object):
    # Labels
    labels = {
        "ar": "agent role",
        "be": "bibliographic entry",
        "br": "bibliographic resource",
        "id": "identifier",
        "ra": "responsible agent",
        "re": "resource embodiment"
    }

    def __init__(self, base_iri, context_path, info_dir):
        self.r_count = 0
        # A list of rdflib.Graphs, one for subject entity
        self.g = []
        # The following variable maps a URIRef with the graph in the graph list related to them
        self.entity_g = {}
        # The following variable maps a URIRef with the related graph entity
        self.res_to_entity = {}
        self.base_iri = base_iri
        self.context_path = context_path
        self.cur_name = "SPACIN " + self.__class__.__name__

        # Graphs
        # The following structure of URL is quite important for the other classes
        # developed and should not be changed. The only part that can change is the
        # value of the base_iri
        self.g_ar = base_iri + "ar/"
        self.g_be = base_iri + "be/"
        self.g_br = base_iri + "br/"
        self.g_id = base_iri + "id/"
        self.g_ra = base_iri + "ra/"
        self.g_re = base_iri + "re/"

        # Local paths
        self.info_dir = info_dir
        self.ar_info_path = info_dir + "ar.txt"
        self.be_info_path = info_dir + "be.txt"
        self.br_info_path = info_dir + "br.txt"
        self.id_info_path = info_dir + "id.txt"
        self.ra_info_path = info_dir + "ra.txt"
        self.re_info_path = info_dir + "re.txt"

        self.reperr = Reporter(True)
        self.reperr.new_article()
        self.repok = Reporter(True)
        self.repok.new_article()

    def res_count(self):
        return self.r_count

    def get_entity(self, res):
        if res in self.res_to_entity:
            return self.res_to_entity[res]

    # Add resources related to bibliographic entities
    def add_ar(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(
            self.g_ar, GraphEntity.role_in_time, res, resp_agent,
            source_agent, source, self.ar_info_path, "ar")

    def add_be(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(
            self.g_be, GraphEntity.bibliographic_reference, res, resp_agent,
            source_agent, source, self.be_info_path, "be")

    def add_br(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(self.g_br, GraphEntity.expression, res, resp_agent,
                         source_agent, source, self.br_info_path, "br")

    def add_id(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(self.g_id, GraphEntity.identifier, res, resp_agent,
                         source_agent, source, self.id_info_path, "id")

    def add_ra(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(self.g_ra, GraphEntity.agent, res, resp_agent,
                         source_agent, source, self.ra_info_path, "ra")

    def add_re(self, resp_agent, source_agent=None, source=None, res=None):
        return self._add(
            self.g_re, GraphEntity.manifestation, res, resp_agent,
            source_agent, source, self.re_info_path, "re")

    def _add(self, graph_url, main_type, res, resp_agent, source_agent,
             source, info_file_path, short_name, list_of_entities=[]):
        cur_g = Graph(identifier=graph_url)
        self._set_ns(cur_g)
        self.g += [cur_g]

        # This is the case when 'res_or_resp_agent' is a resource. It allows one to create
        # the graph entity starting from and existing URIRef, without incrementing anything
        # at the graph set level. However, a new graph is created and reserved for such resource
        # and it is added to the graph set.
        if res is not None:
            return self._generate_entity(cur_g, res=res, resp_agent=resp_agent,
                                         source_agent=source_agent, source=source,
                                         list_of_entities=list_of_entities)
        # This is the case when 'res_or_resp_agent' is actually a string representing the name
        # of the responsible agent. In this case, a new individual will be created.
        else:
            self._increment()
            related_to_label = ""
            related_to_short_label = ""

            # Note: even if list of entities is actually a list, it seems
            # that it would be composed by at most one item (e.g. for provenance)
            if list_of_entities:
                count = GraphSet._add_number(
                    info_file_path, find_local_line_id(list_of_entities[0], items_per_file))
                related_to_label += " related to"
                related_to_short_label += " ->"
                for idx, cur_entity in enumerate(list_of_entities):
                    if idx > 0:
                        related_to_label += ","
                        related_to_short_label += ","
                    cur_short_name = get_short_name(cur_entity)
                    cur_entity_count = get_count(cur_entity)
                    related_to_label += " %s %s" % (self.labels[cur_short_name], cur_entity_count)
                    related_to_short_label += " %s/%s" % (cur_short_name, cur_entity_count)
            else:
                count = GraphSet._add_number(info_file_path)

            label = "%s %s%s [%s/%s%s]" % (
                GraphSet.labels[short_name], str(count), related_to_label,
                short_name, str(count), related_to_short_label)
            return self._generate_entity(
                cur_g, res_type=main_type, resp_agent=resp_agent, source_agent=source_agent,
                source=source, count=count, label=label, short_name=short_name,
                list_of_entities=list_of_entities)

    def _generate_entity(self, g, res=None, res_type=None, resp_agent=None, source_agent=None,
                         source=None, count=None, label=None, short_name="", list_of_entities=[]):
        return GraphEntity(g, res=res, res_type=res_type, resp_agent=resp_agent,
                           source_agent=source_agent, source=source, count=count,
                           label=label, g_set=self)

    def graphs(self):
        result = []
        for cur_g in self.g:
            if len(cur_g) > 0:
                result += [cur_g]
        return result

    def _increment(self):
        self.r_count += 1

    def _set_ns(self, g):
        g.namespace_manager.bind("ar", Namespace(self.g_ar))
        g.namespace_manager.bind("be", Namespace(self.g_be))
        g.namespace_manager.bind("br", Namespace(self.g_br))
        g.namespace_manager.bind("id", Namespace(self.g_id))
        g.namespace_manager.bind("ra", Namespace(self.g_ra))
        g.namespace_manager.bind("re", Namespace(self.g_re))
        g.namespace_manager.bind("biro", GraphEntity.BIRO)
        g.namespace_manager.bind("c4o", GraphEntity.C4O)
        g.namespace_manager.bind("cito", GraphEntity.CITO)
        g.namespace_manager.bind("datacite", GraphEntity.DATACITE)
        g.namespace_manager.bind("dcterms", GraphEntity.DCTERMS)
        g.namespace_manager.bind("doco", GraphEntity.DOCO)
        g.namespace_manager.bind("fabio", GraphEntity.FABIO)
        g.namespace_manager.bind("foaf", GraphEntity.FOAF)
        g.namespace_manager.bind("frbr", GraphEntity.FRBR)
        g.namespace_manager.bind("literal", GraphEntity.LITERAL)
        g.namespace_manager.bind("prism", GraphEntity.PRISM)
        g.namespace_manager.bind("pro", GraphEntity.PRO)

    @staticmethod
    def get_graph_iri(g):
        return str(g.identifier)

    @staticmethod
    def _read_number(file_path, line_number=1):
        cur_number = 0

        try:
            with open(file_path) as f:
                cur_number = long(f.readlines()[line_number - 1])
        except Exception as e:
            pass  # Do nothing

        return cur_number

    @staticmethod
    def _add_number(file_path, line_number=1):
        cur_number = GraphSet._read_number(file_path, line_number) + 1

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        if os.path.exists(file_path):
            with open(file_path) as f:
                all_lines = f.readlines()
        else:
            all_lines = []

        line_len = len(all_lines)
        zero_line_number = line_number - 1
        for i in range(line_number):
            if i >= line_len:
                all_lines += ["\n"]
            if i == zero_line_number:
                all_lines[i] = str(cur_number) + "\n"

        with open(file_path, "wb") as f:
            f.writelines(all_lines)

        return cur_number


class ProvEntity(GraphEntity):
    PROV = Namespace("http://www.w3.org/ns/prov#")

    # Exclusive provenance entities
    prov_agent = PROV.Agent
    entity = PROV.Entity
    activity = PROV.Activity
    create = PROV.Create
    modify = PROV.Modify
    replace = PROV.Replace
    association = PROV.Association
    generated_at_time = PROV.generatedAtTime
    invalidated_at_time = PROV.invalidatedAtTime
    specialization_of = PROV.specializationOf
    was_derived_from = PROV.wasDerivedFrom
    had_primary_source = PROV.hadPrimarySource
    was_generated_by = PROV.wasGeneratedBy
    was_invalidated_by = PROV.wasInvalidatedBy
    qualified_association = PROV.qualifiedAssociation
    description = GraphEntity.DCTERMS.description
    has_update_query = GraphEntity.OCO.hasUpdateQuery
    had_role = PROV.hadRole
    associated_agent = PROV.agent
    curator = GraphEntity.OCO["occ-curator"]
    source_provider = GraphEntity.OCO["source-metadata-provider"]

    def __init__(self, prov_subject, g, res=None, res_type=None,
                 resp_agent=None, source_agent=None, source=None, count=None, label=None,
                 short_name="", g_set=None):
        self.prov_subject = prov_subject
        super(ProvEntity, self).__init__(
            g, res, res_type, resp_agent, source_agent, source, count, label, short_name, g_set)

    # /START Literal Attributes
    def create_generation_time(self, string):
        return self._create_literal(ProvEntity.generated_at_time, string, XSD.dateTime)

    def create_invalidation_time(self, string):
        return self._create_literal(ProvEntity.invalidated_at_time, string, XSD.dateTime)

    def create_description(self, string):
        return self._create_literal(ProvEntity.description, string)

    def create_update_query(self, string):
        return self._create_literal(ProvEntity.has_update_query, string)
        # /END Literal Attributes

    # /START Composite Attributes
    def create_creation_activity(self):
        self._create_type(ProvEntity.create)

    def create_update_activity(self):
        self._create_type(ProvEntity.modify)

    def create_merging_activity(self):
        self._create_type(ProvEntity.replace)

    def snapshot_of(self, se_res):
        self.g.add((self.res, ProvEntity.specialization_of, URIRef(str(se_res))))

    def derives_from(self, se_res):
        self.g.add((self.res, ProvEntity.was_derived_from, URIRef(str(se_res))))

    def has_primary_source(self, any_res):
        self.g.add((self.res, ProvEntity.had_primary_source, URIRef(str(any_res))))

    def generates(self, se_res):
        se_res.g.add((URIRef(str(se_res)), ProvEntity.was_generated_by, self.res))

    def invalidates(self, se_res):
        se_res.g.add((URIRef(str(se_res)), ProvEntity.was_invalidated_by, self.res))

    def involves_agent_with_role(self, cr_res):
        self.g.add((self.res, ProvEntity.qualified_association, URIRef(str(cr_res))))

    def has_role_type(self, any_res):
        self.g.add((self.res, ProvEntity.had_role, URIRef(str(any_res))))

    def has_role_in(self, ca_res):
        ca_res.g.add((URIRef(str(ca_res)), ProvEntity.associated_agent, self.res))

    # /END Composite Attributes


class ProvSet(GraphSet):
    def __init__(self, prov_subj_graph_set, base_iri, context_path, info_dir, resource_finder):
        super(ProvSet, self).__init__(base_iri, context_path, info_dir)
        self.rf = resource_finder
        self.all_subjects = set()
        for cur_subj_g in prov_subj_graph_set.graphs():
            self.all_subjects.add(cur_subj_g.subjects(None, None).next())
        self.resp = "SPACIN ProvSet"
        self.prov_g = prov_subj_graph_set
        GraphSet.labels.update(
            {
                "ca": "curatorial activity",
                "pa": "provenance agent",
                "cr": "curatorial role",
                "se": "snapshot of entity metadata"
            }
        )

    # Add resources related to provenance information
    def add_pa(self, resp_agent=None, res=None):
        return self._add_prov("pa", ProvEntity.prov_agent, res, resp_agent)

    def add_se(self, resp_agent=None, prov_subject=None, res=None):
        return self._add_prov("se", ProvEntity.entity, res, resp_agent, prov_subject)

    def add_ca(self, resp_agent=None, prov_subject=None, res=None):
        return self._add_prov("ca", ProvEntity.activity, res, resp_agent, prov_subject)

    def add_cr(self, resp_agent=None, prov_subject=None, res=None):
        return self._add_prov("cr", ProvEntity.association, res, resp_agent, prov_subject)

    # Note: this method is very basic right now since it considers only the first generation
    def generate_provenance(self):
        time_string = '%Y-%m-%dT%H:%M:%S'
        cur_time = datetime.now().strftime(time_string)

        # Add all existing information for provenance agents
        self.rf.add_prov_triples_in_filesystem(self.base_iri)

        # The 'all_subjects' set includes only the subject of the created graphs that
        # have at least some new triples to add
        for prov_subject in self.all_subjects:
            cur_subj = self.prov_g.get_entity(prov_subject)

            # Load all provenance data of snapshots for that subject
            self.rf.add_prov_triples_in_filesystem(str(prov_subject), "se")

            last_snapshot = None
            last_snapshot_res = self.rf.retrieve_last_snapshot(prov_subject)
            if last_snapshot_res is not None:
                last_snapshot = self.add_se(self.cur_name, cur_subj, last_snapshot_res)

            # Snapshot
            cur_snapshot = self.add_se(self.cur_name, cur_subj)
            cur_snapshot.snapshot_of(cur_subj)
            cur_snapshot.create_generation_time(cur_time)

            # Associations
            cur_curator_ass = None
            cur_source_ass = None
            if cur_subj.resp_agent is not None:
                cur_curator_ass = self.add_cr(self.cur_name, cur_subj)
                cur_curator_ass.has_role_type(ProvEntity.curator)
                cur_curator_agent_res = self.rf.retrieve_provenance_agent_from_name(cur_subj.resp_agent)
                if cur_curator_agent_res is None:
                    cur_curator_agent = self.add_pa(self.cur_name)
                    cur_curator_agent.create_name(cur_subj.resp_agent)
                    self.rf.update_graph_set(self)
                else:
                    cur_curator_agent = self.add_pa(self.cur_name, cur_curator_agent_res)
                cur_curator_agent.has_role_in(cur_curator_ass)
            if cur_subj.source_agent is not None:
                cur_source_ass = self.add_cr(self.cur_name, cur_subj)
                cur_source_ass.has_role_type(ProvEntity.source_provider)
                cur_source_agent_res = self.rf.retrieve_provenance_agent_from_name(cur_subj.source_agent)
                if cur_source_agent_res is None:
                    cur_source_agent = self.add_pa(self.cur_name)
                    cur_source_agent.create_name(cur_subj.source_agent)
                    self.rf.update_graph_set(self)
                else:
                    cur_source_agent = self.add_pa(self.cur_name, cur_source_agent_res)
                cur_source_agent.has_role_in(cur_source_ass)
            if cur_subj.source is not None:
                cur_snapshot.has_primary_source(cur_subj.source)

            # Activity
            cur_activity = self.add_ca(self.cur_name, cur_subj)
            cur_activity.generates(cur_snapshot)
            if cur_curator_ass is not None:
                cur_activity.involves_agent_with_role(cur_curator_ass)
            if cur_source_ass is not None:
                cur_activity.involves_agent_with_role(cur_source_ass)

            # Old snapshot
            if last_snapshot is None:
                cur_activity.create_creation_activity()
                cur_activity.create_description("The entity '%s' has been created." % str(cur_subj.res))
            else:
                update_query_data = self._create_update_query(cur_subj.g)
                update_description = "The entity '%s' has been extended with" % str(cur_subj.res)
                if update_query_data[1]:
                    update_description += " citation data"
                    if update_query_data[2]:
                        update_description += " and"
                if update_query_data[2]:
                    update_description += " new identifiers"
                update_description += "."
                cur_activity.create_update_activity()
                cur_activity.create_description(update_description)
                last_snapshot.create_invalidation_time(cur_time)
                cur_activity.invalidates(last_snapshot)
                cur_snapshot.derives_from(last_snapshot)
                cur_snapshot.create_update_query(update_query_data[0])

    @staticmethod
    def _create_update_query(cur_subj_g):
        query_string = u"INSERT DATA { GRAPH <%s> { " % cur_subj_g.identifier
        is_first = True
        new_citations = False
        new_ids = False

        for s, p, o in cur_subj_g.triples((None, None, None)):
            if not is_first:
                query_string += ". "
            is_first = False
            if p == GraphEntity.cites:
                new_citations = True
            elif p == GraphEntity.has_identifier:
                new_ids = True
            query_string += u"<%s> <%s> <%s> " % (str(s), str(p), str(o))

        return query_string + "} }", new_citations, new_ids

    def _add_prov(self, short_name, prov_type, res, resp_agent, prov_subject=None):
        if prov_subject is None:
            g_prov = self.base_iri + "prov/"
            prov_info_path = g_prov.replace(self.base_iri, self.info_dir) + short_name + ".txt"
        else:
            g_prov = str(prov_subject) + "/prov/"
            res_file_path = \
                find_paths(str(prov_subject), self.info_dir, self.base_iri,
                           dir_split_number, items_per_file)[1][:-5]
            prov_info_path = res_file_path + "/prov/" + short_name + ".txt"
        return self._add(g_prov, prov_type, res, resp_agent, None, None,
                         prov_info_path, short_name, [] if prov_subject is None else [prov_subject])

    def _set_ns(self, g):
        super(ProvSet, self)._set_ns(g)
        g.namespace_manager.bind("oco", ProvEntity.OCO)
        g.namespace_manager.bind("prov", ProvEntity.PROV)

    def _generate_entity(self, g, res=None, res_type=None, resp_agent=None, source_agent=None,
                         source=None, count=None, label=None, short_name="", list_of_entities=[]):
        return ProvEntity(list_of_entities[0] if list_of_entities else None, g,
                          res=res, res_type=res_type, resp_agent=resp_agent,
                          source_agent=source_agent, source=source,
                          count=count, label=label, short_name=short_name, g_set=self)
