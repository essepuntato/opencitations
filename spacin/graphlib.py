#!/usr/bin/python
# -*- coding: utf-8 -*-
from xml.sax import SAXParseException

__author__ = 'essepuntato'
from rdflib import Graph, Literal, Namespace, URIRef
from SPARQLWrapper import SPARQLWrapper
from rdflib.namespace import RDF, XSD
from reporter import Reporter
import re
import os
import shutil


class GraphEntity(object):
    BIRO = Namespace("http://purl.org/spar/biro/")
    C4O = Namespace("http://purl.org/spar/c4o/")
    CITO = Namespace("http://purl.org/spar/cito/")
    PRO = Namespace("http://purl.org/spar/pro/")
    FOAF = Namespace("http://xmlns.com/foaf/0.1/")
    DATACITE = Namespace("http://purl.org/spar/datacite/")
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    DOCO = Namespace("http://purl.org/spar/doco/")
    FABIO = Namespace("http://purl.org/spar/fabio/")
    FRBR = Namespace("http://purl.org/vocab/frbr/core#")
    LITERAL = Namespace("http://www.essepuntato.it/2010/06/literalreification/")
    PRISM = Namespace("http://prismstandard.org/namespaces/basic/2.0/")

    has_subtitle = FABIO.hasSubtitle
    has_publication_year = FABIO.hasPublicationYear
    bibliographic_reference = BIRO.BibliographicReference
    references = BIRO.references
    has_content = C4O.hasContent
    cites = CITO.cites
    doi = DATACITE.doi
    occ = DATACITE.occ
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
    has_literal_value = LITERAL.hasLiteralValue
    ending_page = PRISM.endingPage
    starting_page = PRISM.startingPage
    author = PRO.author
    editor = PRO.editor
    holds_role_in_time = PRO.holdsRoleInTime
    publisher = PRO.publisher
    relates_to_document = PRO.relatesToDocument
    role_in_time = PRO.RoleInTime
    with_role = PRO.withRole

    # This constructor creates a new instance of an RDF resource
    def __init__(self, g, base_iri=None, res=None, res_type=None,
                 resp_agent=None, count=None, local_id=None, g_set=None):
        existing_ref = False

        # Create the reference if not specified
        if res is None:
            self.res = URIRef(str(g.identifier) + str(count))
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

        # If it is a new entity, add all the additional information to it
        if not existing_ref:
            self.resp_agent = resp_agent
            self.__create_type(res_type)
            if local_id is not None:
                self.has_id(local_id)
                local_id.create_occ(re.sub(base_iri, "", GraphSet.get_graph_iri(g)) + str(count))

    def __str__(self):
        return str(self.res)

    # /START Literal Attributes
    def create_title(self, string):
        return self.__create_literal(GraphEntity.title, string)

    def create_subtitle(self, string):
        return self.__create_literal(GraphEntity.has_subtitle, string)

    def create_pub_year(self, string):
        return self.__create_literal(GraphEntity.has_publication_year, string, XSD.gYear)

    def create_starting_page(self, string):
        return self.__create_literal(GraphEntity.starting_page, re.sub("[-–]+.*$", "", string))

    def create_ending_page(self, string):
        return self.__create_literal(GraphEntity.ending_page, re.sub("^.*[-–]+", "", string))

    def create_number(self, string):
        return self.__create_literal(GraphEntity.has_sequence_identifier, string)

    def create_content(self, string):
        return self.__create_literal(GraphEntity.has_content, string)

    def create_name(self, string):
        return self.__create_literal(GraphEntity.name, string)

    def create_given_name(self, string):
        return self.__create_literal(GraphEntity.given_name, string)

    def create_family_name(self, string):
        return self.__create_literal(GraphEntity.family_name, string)
    # /END Literal Attributes

    # /START Composite Attributes
    def create_expression_collection(self):
        self.__create_type(GraphEntity.expression_collection)

    def create_book_chapter(self):
        self.__create_type(GraphEntity.book_chapter)

    def create_book_part(self):
        self.__create_type(GraphEntity.part)

    def create_book_section(self):
        self.__create_type(GraphEntity.expression_collection)

    def create_book_series(self):
        self.__create_type(GraphEntity.book_series)

    def create_book_set(self):
        self.__create_type(GraphEntity.book_set)

    def create_book_track(self):
        self.__create_type(GraphEntity.expression)

    def create_book(self):
        self.__create_type(GraphEntity.book)

    def create_component(self):
        self.__create_type(GraphEntity.expression)

    def create_dataset(self):
        self.__create_type(GraphEntity.data_file)

    def create_dissertation(self):
        self.__create_type(GraphEntity.thesis)

    def create_edited_book(self):
        self.__create_type(GraphEntity.book)

    def create_journal(self):
        self.__create_type(GraphEntity.journal)

    def create_journal_article(self):
        self.__create_type(GraphEntity.journal_article)

    def create_issue(self):
        self.__create_type(GraphEntity.journal_issue)

    def create_volume(self):
        self.__create_type(GraphEntity.journal_volume)

    def create_monograph(self):
        self.__create_type(GraphEntity.book)

    def create_other(self):
        self.__create_type(GraphEntity.expression)

    def create_proceedings(self):
        self.__create_type(GraphEntity.academic_proceedings)

    def create_proceedings_article(self):
        self.__create_type(GraphEntity.proceedings_paper)

    def create_reference_book(self):
        self.__create_type(GraphEntity.reference_book)

    def create_reference_entry(self):
        self.__create_type(GraphEntity.reference_entry)

    def create_report(self):
        self.__create_type(GraphEntity.report_document)

    def create_report_series(self):
        self.__create_type(GraphEntity.series)

    def create_standard(self):
        self.__create_type(GraphEntity.specification_document)

    def create_standard_series(self):
        self.__create_type(GraphEntity.series)

    def create_publisher(self, br_res):
        return self.__associate_role_with_document(GraphEntity.publisher, br_res)

    def create_author(self, br_res):
        return self.__associate_role_with_document(GraphEntity.author, br_res)

    def create_editor(self, br_res):
        return self.__associate_role_with_document(GraphEntity.editor, br_res)

    def create_doi(self, string):
        return self.__associate_identifier_with_scheme(string, GraphEntity.doi)

    def create_occ(self, string):
        return self.__associate_identifier_with_scheme(string, GraphEntity.occ)

    def create_issn(self, string):
        cur_string = re.sub("–", "-", string)
        if cur_string != "0000-0000":
            return self.__associate_identifier_with_scheme(string, GraphEntity.issn)

    def create_isbn(self, string):
        return self.__associate_identifier_with_scheme(
            re.sub("–", "-", string), GraphEntity.isbn)

    def create_url(self, string):
        return self.__associate_identifier_with_scheme(string, GraphEntity.url)

    def has_id(self, id_res):
        self.g.add((self.res, GraphEntity.has_identifier, URIRef(str(id_res))))

    def has_format(self, re_res):
        self.g.add((self.res, GraphEntity.embodiment, URIRef(str(re_res))))

    def has_part(self, br_res):
        br_res.g.add((URIRef(str(br_res)), GraphEntity.part_of, self.res))

    def has_citation(self, br_res):
        self.g.add((self.res, GraphEntity.cites, URIRef(str(br_res))))

    def has_reference(self, be_res):
        be_res.g.add((URIRef(str(be_res)), GraphEntity.references, self.res))

    def has_role(self, ar_res):
        self.g.add((self.res, GraphEntity.holds_role_in_time, URIRef(str(ar_res))))
    # /END Composite Attributes

    # /START Private Methods
    def __associate_identifier_with_scheme(self, string, id_type):
        if not GraphEntity.__is_empty(string):
            self.__create_literal(GraphEntity.has_literal_value, string)
            self.g.add((self.res, GraphEntity.uses_identifier_scheme, id_type))
            return True
        return False

    def __associate_role_with_document(self, role_type, br_res):
        self.g.add((self.res, GraphEntity.with_role, role_type))
        self.g.add((self.res, GraphEntity.relates_to_document, URIRef(str(br_res))))
        return True

    def __create_literal(self, p, s, dt=None):
        if isinstance(s, basestring):
            string = s
        else:
            string = str(s)
        if not GraphEntity.__is_empty(string):
            self.g.add((self.res, p, Literal(string, datatype=dt)))
            return True
        return False

    def __create_type(self, res_type):
        self.g.add((self.res, RDF.type, res_type))

    @staticmethod
    def __is_empty(string):
        return string is None or string.strip() == ""
    # /END Private Methods


class GraphSet(object):

    def __init__(self, base_iri, context_path, info_dir, tmp_dir):
        self.r_count = 0
        self.g = []
        self.entity_g = {}
        self.base_iri = base_iri
        self.context_path = context_path
        self.tmp_dir = tmp_dir

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

    def add_ar(self, res_or_resp_agent):
        return self.__add(self.g_ar, GraphEntity.role_in_time, res_or_resp_agent, self.ar_info_path)

    def add_be(self, res_or_resp_agent):
        return self.__add(
            self.g_be, GraphEntity.bibliographic_reference, res_or_resp_agent, self.be_info_path)

    def add_br(self, res_or_resp_agent):
        return self.__add(self.g_br, GraphEntity.expression, res_or_resp_agent, self.br_info_path)

    def add_id(self, res_or_resp_agent):
        return self.__add(self.g_id, GraphEntity.identifier, res_or_resp_agent, self.id_info_path, False)

    def add_ra(self, res_or_resp_agent):
        return self.__add(self.g_ra, GraphEntity.agent, res_or_resp_agent, self.ra_info_path)

    def add_re(self, res_or_resp_agent):
        return self.__add(self.g_re, GraphEntity.manifestation, res_or_resp_agent, self.re_info_path)

    def __add(self, graph_url, main_type, res_or_resp_agent, info_file_path, generate_id=True):
        cur_g = Graph(identifier=graph_url)
        self.__set_ns(cur_g)
        self.g += [cur_g]

        # This is the case when 'res_or_resp_agent' is a resource. It allows one to create
        # the graph entity starting from and existing URIRef, without incrementing anything
        # at the graph set level. However, a new graph is created and reserved for such resource
        # and it is added to the graph set.
        if type(res_or_resp_agent) is URIRef:
            return GraphEntity(cur_g, res=res_or_resp_agent, g_set=self)
        # This is the case when 'res_or_resp_agent' is actually a string representing the name
        # of the responsible agent. In this case, a new individual will be created.
        else:
            self.__increment()
            if generate_id:
                local_id = self.add_id("SPACIN GraphSet")
            else:
                local_id = None
            return GraphEntity(
                cur_g, base_iri=self.base_iri, res_type=main_type, resp_agent=res_or_resp_agent,
                count=GraphSet.__add_number(info_file_path), local_id=local_id, g_set=self)

    def graphs(self):
        return self.g

    def store(self, base_dir):
        for cur_g in self.g:
            self.__store_graph(cur_g, base_dir)

    def push_on_triplestore_and_store(self, base_dir, triplestore_url):
        self.repok.add_sentence("[Triplestore: INFO] Starting the process")

        tp = SPARQLWrapper(triplestore_url + "/sparql")
        tp.setMethod('POST')
        for idx, cur_g in enumerate(self.g):
            cur_g_iri = GraphSet.get_graph_iri(cur_g)
            try:
                tp.setQuery("INSERT DATA { GRAPH <%s> { %s } }" %
                            (cur_g_iri,
                             cur_g.serialize(format="nt")))
                tp.query()

                self.repok.add_sentence(
                    "[Triplestore: INFO] "
                    "Triplestore updated with %s more RDF statements (graph '%s') contained "
                    "in the graph number '%s'." %
                    (len(cur_g), cur_g_iri, str(idx+1)))
            except Exception as e:
                self.reperr.add_sentence("[Triplestore: ERROR] "
                                         "Graph number '%s' was not loaded into the "
                                         "triplestore due to communication problems: %s" %
                                         (str(idx+1), str(e)))

            # The file will be added anyway to the file system, so as to have a backup for the
            # triplestore
            self.__store_graph(cur_g, base_dir)

    def __store_graph(self, cur_g, base_dir):
        if len(cur_g) > 0:
            cur_g_iri = GraphSet.get_graph_iri(cur_g)

            cur_graph_short_name = re.sub("^%s" % self.base_iri, "", cur_g_iri)
            cur_dir_path = base_dir + re.sub("^%s" % self.base_iri, "", cur_g_iri)
            if not os.path.exists(cur_dir_path):
                os.makedirs(cur_dir_path)

            cur_subject = set(cur_g.subjects(None, None)).pop()
            cur_file_path = cur_dir_path + re.sub("^%s" % cur_g_iri, "", str(cur_subject)) + ".json"

            # Merging the data
            if os.path.exists(cur_file_path):
                existing_g = self.load_graph(cur_file_path, cur_g)

            cur_g.serialize(cur_file_path, format="json-ld", indent=4, context=self.context_path)

            self.repok.add_sentence("[Store: INFO] File '%s' added." % cur_file_path)

    def __increment(self):
        self.r_count += 1

    def __set_ns(self, g):
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
    def __read_number(file_path):
        cur_number = 0

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    cur_number = int(f.read())
                except Exception as e:
                    pass  # Do nothing

        return cur_number

    @staticmethod
    def __add_number(file_path):
        cur_number = GraphSet.__read_number(file_path) + 1

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        with open(file_path, "wb") as f:
            f.write(str(cur_number))

        return cur_number

    def load_graph(self, rdf_file_path, cur_graph=None):
        current_graph = cur_graph

        if os.path.isfile(rdf_file_path):
            try:
                current_graph = GraphSet.__load_graph(rdf_file_path, current_graph)
            except IOError:
                current_file_path = self.tmp_dir + os.sep + "tmp_rdf_file.rdf"
                shutil.copyfile(rdf_file_path, current_file_path)
                current_graph = GraphSet.__load_graph(current_file_path, current_graph)
                os.remove(current_file_path)
        else:
            raise IOError("1", "The file specified doesn't exist.")

        return current_graph

    @staticmethod
    def __load_graph(file_path, cur_graph):
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

        raise IOError("2", "It was impossible to handle the format used for storing the file")

