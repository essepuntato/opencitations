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

from format_processor import *
from graphlib import GraphEntity as ge
from support import dict_get as dg
from support import dict_list_get_by_value_ascii as dgt
from support import string_list_close_match as slc
from support import get_data
from support import encode_url


class CrossrefProcessor(FormatProcessor):
    isbn_base_url = "http://id.crossref.org/isbn/"
    member_base_url = "http://id.crossref.org/member/"

    isbn_types = [
        "book", "book-set", "dissertation", "edited-book",
        "monograph", "proceedings", "reference-book"
    ]
    issn_types = ["book-series", "book-set", "journal", "report-series", "standard-series"]

    def __init__(self,
                 base_iri,
                 context_base,
                 info_dir,
                 entries,
                 res_finder,
                 of_finder,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30,
                 use_doi_in_bibentry_as_id=True,
                 use_url_in_bibentry_as_id=True,
                 crossref_min_similarity_score=75.0):
        self.crossref_api_works = "http://api.crossref.org/works/"
        self.crossref_api_search = "http://api.crossref.org/works?rows=1&query="
        self.headers = headers
        self.sec_to_wait = sec_to_wait
        self.max_iteration = max_iteration
        self.timeout = timeout
        self.rf = res_finder
        self.of = of_finder
        self.get_bib_entry_url = use_url_in_bibentry_as_id
        self.get_bib_entry_doi = use_doi_in_bibentry_as_id
        self.crossref_min_similarity_score = crossref_min_similarity_score
        super(CrossrefProcessor, self).__init__(
            base_iri, context_base, info_dir, entries, "Crossref")

    def __process_entity(self, entity, api_url):
        return get_data(self.max_iteration, self.sec_to_wait, api_url + entity,
                        self.headers, self.timeout, self.repok, self.reperr)

    def process_entry(self, entry):
        entry_cleaned = FormatProcessor.clean_entry(entry)
        cur_json = self.get_crossref_item(
            self.__process_entity(entry_cleaned, self.crossref_api_search))
        if cur_json is not None:
            return self.process_crossref_json(
                cur_json, self.crossref_api_search + entry_cleaned,
                self.name, self.id, self.source)

    def process_doi(self, doi, doi_curator, doi_source_provider):
        existing_res = self.rf.retrieve_from_doi(doi)
        if existing_res is None:
            cur_json = self.get_crossref_item(self.__process_entity(doi, self.crossref_api_works))
            if cur_json is not None:
                return self.process_crossref_json(
                    cur_json, self.crossref_api_works + encode_url(doi), doi_curator,
                    doi_source_provider, self.source)
        else:
            return self.process_existing_by_id(existing_res, self.id)

    def process_pmid(self, pmid):
        existing_res = self.rf.retrieve_from_pmid(pmid)
        return self.process_existing_by_id(existing_res, self.id)

    def process_pmcid(self, pmcid):
        existing_res = self.rf.retrieve_from_pmcid(pmcid)
        return self.process_existing_by_id(existing_res, self.id)

    def process_url(self, url):
        existing_res = self.rf.retrieve_from_url(url)
        return self.process_existing_by_id(existing_res, self.id)

    def process_existing_by_id(self, existing_res, source_provider):
        if existing_res is not None:
            result = self.g_set.add_br(self.name, source_provider, self.source, existing_res)
            self.rf.update_graph_set(self.g_set)
            return result

    def process(self):
        """This methods returns a GraphSet populated with the citation data form the input
        source, or None if any issue has been encountered."""
        if self.doi is not None:
            citing_resource = self.rf.retrieve_citing_from_doi(self.doi)
            if citing_resource is None and self.pmid is not None:
                citing_resource = self.rf.retrieve_citing_from_pmid(self.pmid)
            if citing_resource is None and self.pmcid is not None:
                citing_resource = self.rf.retrieve_citing_from_pmcid(self.pmcid)
            if citing_resource is None and self.url is not None:
                citing_resource = self.rf.retrieve_citing_from_url(self.url)

            if citing_resource is None:
                citing_entity = self.process_doi(self.doi, self.curator, self.source_provider)
                if citing_entity is None:
                    citing_entity = self.g_set.add_br(self.name)
                    self.__add_doi(citing_entity, self.doi, self.curator)
                    self.rf.update_graph_set(self.g_set)
                    self.repok.add_sentence(
                        self.message("The citing entity has been created even if no results have "
                                     "been returned by the API.",
                                     "doi", self.doi))

                # Add other ids if they exist
                self.__add_pmid(citing_entity, self.pmid)
                self.__add_pmcid(citing_entity, self.pmcid)

                cited_entities = self.process_references()

                if cited_entities is not None:
                    for idx, cited_entity in enumerate(cited_entities):
                        citing_entity.has_citation(cited_entity)
                        cur_bibentry = dg(self.entries[idx], ["bibentry"])
                        if cur_bibentry is not None and cur_bibentry.strip():
                            cur_be = self.g_set.add_be(self.curator, self.source_provider, self.source)
                            citing_entity.contains_in_reference_list(cur_be)
                            cited_entity.has_reference(cur_be)
                            cur_be.create_content(cur_bibentry.strip())

                    return self.g_set
            else:
                self.repok.add_sentence(
                    "The citing entity with DOI '%s' has been already "
                    "processed in the past." % self.doi)
        else:  # No DOI has been specified for the citing resource
            self.reperr.add_sentence("No DOI has been specified for the citing resource.")

    def process_references(self):
        result = []

        for full_entry in self.entries:
            self.repok.new_article()
            self.reperr.new_article()
            cur_res = None

            entry = dg(full_entry, ["bibentry"])
            do_process_entry = True
            process_string = dg(full_entry, ["process_entry"])
            if process_string is not None:
                do_process_entry = process_string.lower().strip() == "true"
            provided_doi = dg(full_entry, ["doi"])
            provided_pmid = dg(full_entry, ["pmid"])
            provided_pmcid = dg(full_entry, ["pmcid"])
            provided_url = dg(full_entry, ["url"])

            # This is useful if additional data are stored in the field URL, e.g.:
            # 'http://pub.stat.ee/px/web.2001/dialog/statfile1.asp. Accessed on 2009'
            if provided_url is not None:
                provided_url = FormatProcessor.extract_url(provided_url)

            extracted_doi = FormatProcessor.extract_doi(entry)
            extracted_doi_used = False
            extracted_url = FormatProcessor.extract_url(entry)

            if provided_doi is not None:
                cur_res = self.process_doi(provided_doi, self.curator, self.source_provider)
                if cur_res is not None:
                    self.repok.add_sentence(
                        self.message("The entity has been found by means of the "
                                     "DOI provided as input by %s." % self.source_provider,
                                     "DOI", provided_doi))

            if cur_res is None and provided_pmid is not None:
                cur_res = self.process_pmid(provided_pmid)
                if cur_res is not None:
                    self.repok.add_sentence(
                        self.message("The entity has been found by means of the "
                                     "PMID provided as input by %s." % self.source_provider,
                                     "PMID", provided_pmid))

            if cur_res is None and provided_pmcid is not None:
                cur_res = self.process_pmcid(provided_pmcid)
                if cur_res is not None:
                    self.repok.add_sentence(
                        self.message("The entity has been found by means of the "
                                     "PMCID provided as input by %s." % self.source_provider,
                                     "PMCID", provided_pmcid))

            if cur_res is None and provided_url is not None:
                cur_res = self.process_url(provided_url)
                if cur_res is not None:
                    self.repok.add_sentence(
                        self.message("The entity has been found by means of the "
                                     "URL provided as input by %s." % self.source_provider,
                                     "URL", provided_url))

            if cur_res is None and entry is not None:
                if do_process_entry:
                    cur_res = self.process_entry(entry)
                if cur_res is None:
                    if self.get_bib_entry_doi and extracted_doi is not None:
                        extracted_doi_used = True
                        cur_res = self.process_doi(extracted_doi, self.name, self.source_provider)
                        if cur_res is not None:
                            self.repok.add_sentence(
                                self.message("The entity for '%s' has been found by means of the "
                                             "DOI extracted from it." % entry,
                                             "DOI", extracted_doi))
                    if cur_res is None and self.get_bib_entry_url and extracted_url is not None:
                        existing_res = self.rf.retrieve_from_url(extracted_url)
                        if existing_res is not None:
                            cur_res = self.g_set.add_br(
                                self.name, self.source_provider, self.source, existing_res)
                            self.repok.add_sentence(
                                self.message("The entity for '%s' has been found by means of the "
                                             "URL extracted from it." % entry,
                                             "URL", extracted_url))

                else:
                    self.repok.add_sentence(
                        self.message(
                            "The entity has been retrieved by using the search API.",
                            "entry", entry))

            # If no errors were generated, proceed
            if self.reperr.is_empty():
                # If it is none
                if cur_res is None:
                    cur_res = self.g_set.add_br(self.name)
                    self.rf.update_graph_set(self.g_set)
                    self.repok.add_sentence(
                        self.message("The entity has been created even if no results have "
                                     "been returned by the API.",
                                     "entry", entry))

                # Add the DOI, the PMID and the PMCID if they have been provided by the curator
                # (if they are not already associated to the resource)
                self.__add_doi(cur_res, provided_doi, self.curator)
                self.__add_pmid(cur_res, provided_pmid)
                self.__add_pmcid(cur_res, provided_pmcid)
                self.__add_url(cur_res, provided_url)

                # Add any DOI extracted from the entry if it is not already included (and only if
                # a resource has not been retrieved by a DOI specified in the entry explicitly, or
                # by a Crossref search.
                if self.get_bib_entry_doi and extracted_doi_used:
                    self.__add_doi(cur_res, extracted_doi, self.name)

                # Add any URL extracted from the entry if it is not already included
                if self.get_bib_entry_url:
                    self.__add_url(cur_res, extracted_url)

                result += [cur_res]
                self.rf.update_graph_set(self.g_set)

            else:  # If errors have been raised, stop the process for this entry (by returning None)
                return None

        # If the process comes here, then everything worked correctly
        return result

    def __add_url(self, cur_res, extracted_url):
        self.rf.update_graph_set(self.g_set)
        if extracted_url is not None:
            cur_id = self.rf.retrieve_br_url(cur_res.res, extracted_url)

            if cur_id is None:
                cur_id = self.g_set.add_id(self.name, self.source_provider, self.source)
                cur_id.create_url(extracted_url)
                cur_res.has_id(cur_id)

    def __add_pmid(self, cur_res, pmid_string):
        self.rf.update_graph_set(self.g_set)
        if pmid_string is not None:
            cur_id = self.rf.retrieve_br_pmid(cur_res.res, pmid_string)

            if cur_id is None:
                cur_id = self.g_set.add_id(self.curator, self.source_provider, self.source)
                cur_id.create_pmid(pmid_string)
                cur_res.has_id(cur_id)

    def __add_pmcid(self, cur_res, pmcid_string):
        self.rf.update_graph_set(self.g_set)
        if pmcid_string is not None:
            cur_id = self.rf.retrieve_br_pmcid(cur_res.res, pmcid_string)

            if cur_id is None:
                cur_id = self.g_set.add_id(self.curator, self.source_provider, self.source)
                cur_id.create_pmcid(pmcid_string)
                cur_res.has_id(cur_id)

    def __add_doi(self, cur_res, extracted_doi, curator):
        self.rf.update_graph_set(self.g_set)
        if extracted_doi is not None:
            cur_id = self.rf.retrieve_br_doi(cur_res.res, extracted_doi)

            if cur_id is None:
                cur_id = self.g_set.add_id(curator, self.source_provider, self.source)
                cur_id.create_doi(extracted_doi)
                cur_res.has_id(cur_id)

    def get_crossref_item(self, json_crossref):
        result = None
        if json_crossref is not None and json_crossref["status"] == "ok":
            if json_crossref["message-type"] in ["work", "member"]:
                result = json_crossref["message"]
            elif json_crossref["message-type"] == "work-list":
                result = json_crossref["message"]["items"][0]
                if result["score"] < self.crossref_min_similarity_score:
                    result = None
        return result

    def process_crossref_json(
            self, crossref_json, crossref_source,
            doi_curator=None, doi_source_provider=None, doi_source=None):
        # Check if the found bibliographic resource already exist either
        # in the triplestore or in the current graph set.
        self.rf.update_graph_set(self.g_set)
        retrieved_resource = self.rf.retrieve(self.__get_ids_for_type(crossref_json))

        if retrieved_resource is not None:
            cur_br = self.g_set.add_br(self.name, self.id, crossref_source, retrieved_resource)
        else:
            cur_br = self.g_set.add_br(self.name, self.id, crossref_source)
            for key in crossref_json:
                if key == "title":
                    cur_title = self.__create_title_from_list(crossref_json[key])
                    cur_br.create_title(cur_title)
                elif key == "subtitle":
                    cur_br.create_subtitle(self.__create_title_from_list(crossref_json[key]))
                elif key == "author":
                    # Get all ORCID of the authors (if any)
                    all_authors = crossref_json["author"]
                    all_family_names = dg(all_authors, ["family"])
                    author_orcid = []
                    if "DOI" in crossref_json and all_family_names:
                        doi_string = crossref_json["DOI"]
                        author_orcid = self.of.get_orcid_ids(doi_string, all_family_names)

                    # Used to create ordered list of authors/editors of bibliographic entities
                    prev_role = None

                    # Analyse all authors
                    for author in crossref_json["author"]:
                        given_name_string = None
                        if "given" in author:
                            given_name_string = author["given"]
                        family_name_string = None
                        if "family" in author:
                            family_name_string = author["family"]

                        cur_orcid_record = None
                        if family_name_string:
                            # Get all the ORCID/author records retrieved that share the
                            # family name into consideration
                            orcid_with_such_family = dgt(author_orcid, "family", family_name_string)
                            author_with_such_family = dgt(all_authors, "family", family_name_string)
                            if len(orcid_with_such_family) == 1 and len(author_with_such_family) == 1:
                                cur_orcid_record = orcid_with_such_family[0]
                            elif given_name_string is not None and \
                                 len(orcid_with_such_family) >= 1 and len(author_with_such_family) >= 1:
                                # From the previous lists of ORCID/author record, get the list
                                # of all the given name defined
                                orcid_given_with_such_family = dg(orcid_with_such_family, ["given"])
                                author_given_with_such_family = dg(author_with_such_family, ["given"])

                                # Get the indexes of the previous list that best match with the
                                # given name of the author we are considering
                                closest_orcid_matches_idx = \
                                    slc(orcid_given_with_such_family, given_name_string)
                                closest_author_matches_idx = \
                                    slc(author_given_with_such_family, given_name_string)
                                if len(closest_orcid_matches_idx) == 1 and \
                                   len(closest_author_matches_idx) == 1:
                                    closest_author_orcid_matches_idx = slc(
                                        author_given_with_such_family, orcid_given_with_such_family[0])
                                    if closest_author_orcid_matches_idx == closest_author_matches_idx:
                                        cur_orcid_record = \
                                            orcid_with_such_family[closest_orcid_matches_idx[0]]

                        # An ORCID has been found to match with such author record, and we try to
                        # see if such orcid (and thus, the author) has been already added in the
                        # store
                        retrieved_agent = None
                        if cur_orcid_record is not None:
                            retrieved_agent = self.rf.retrieve_from_orcid(cur_orcid_record["orcid"])

                        # If the resource does not exist already, create a new one
                        if retrieved_agent is None:
                            cur_agent = self.g_set.add_ra(self.name, self.id, crossref_source)
                            if cur_orcid_record is not None:
                                cur_agent_orcid = \
                                    self.g_set.add_id(self.of.name, self.of.id, self.of.get_last_query())
                                cur_agent_orcid.create_orcid(cur_orcid_record["orcid"])
                                cur_agent.has_id(cur_agent_orcid)

                            if given_name_string is not None:
                                cur_agent.create_given_name(given_name_string)
                            elif cur_orcid_record is not None and "given" in cur_orcid_record:
                                cur_agent.create_given_name(cur_orcid_record["given"])

                            if family_name_string is not None:
                                cur_agent.create_family_name(family_name_string)
                            elif cur_orcid_record is not None and "family" in cur_orcid_record:
                                cur_agent.create_family_name(cur_orcid_record["family"])
                        else:
                            cur_agent = self.g_set.add_ra(
                                self.name, self.id, crossref_source, retrieved_agent)

                        # Add statements related to the author resource (that could or could not
                        # exist in the store)
                        cur_role = self.g_set.add_ar(self.name, self.id, crossref_source)
                        if crossref_json["type"] == "edited-book":
                            cur_role.create_editor(cur_br)
                        else:
                            cur_role.create_author(cur_br)
                        cur_agent.has_role(cur_role)

                        if prev_role is not None:
                            cur_role.follows(prev_role)

                        prev_role = cur_role

                elif key == "publisher":
                    cur_agent = None

                    # Check if the publishier already exists
                    if "member" in crossref_json and crossref_json["member"] is not None:
                        cur_member_url = crossref_json["member"]
                        retrieved_agent = self.rf.retrieve_from_url(cur_member_url)
                        if retrieved_agent is not None:
                            cur_agent = self.g_set.add_ra(
                                self.name, self.id, crossref_source, retrieved_agent)
                    else:
                        cur_member_url = None

                    # If the publisher is not already defined in the knowledge base,
                    # create a new one.
                    if cur_agent is None:
                        cur_agent = self.g_set.add_ra(self.name, self.id, crossref_source)
                        cur_agent.create_name(crossref_json[key])

                        if cur_member_url is not None:
                            cur_agent_id = self.g_set.add_id(self.name, self.id, crossref_source)
                            cur_agent_id.create_url(crossref_json["member"])
                            cur_agent.has_id(cur_agent_id)

                    cur_role = self.g_set.add_ar(self.name, self.id, crossref_source)
                    cur_role.create_publisher(cur_br)
                    cur_agent.has_role(cur_role)
                elif key == "DOI":
                    cur_id = self.g_set.add_id(doi_curator, doi_source_provider, doi_source)
                    if cur_id.create_doi(crossref_json[key]):
                        cur_br.has_id(cur_id)
                elif key == "issued":
                    cur_br.create_pub_year(crossref_json[key]["date-parts"][0][0])
                elif key == "URL":
                    cur_id = self.g_set.add_id(self.name, self.id, crossref_source)
                    if cur_id.create_url(crossref_json[key]):
                        cur_br.has_id(cur_id)
                elif key == "page":
                    cur_page = crossref_json[key]
                    cur_re = self.g_set.add_re(self.name, self.id, crossref_source)
                    if cur_re.create_starting_page(cur_page):
                        cur_re.create_ending_page(cur_page)
                        cur_br.has_format(cur_re)
                elif key == "container-title":
                    retrieved_container = None
                    cont_br = None
                    cur_type = crossref_json["type"]

                    container_ids = self.__get_ids_for_container(crossref_json)
                    cur_issue_id = crossref_json["issue"] if "issue" in crossref_json else None
                    cur_volume_id = crossref_json["volume"] if "volume" in crossref_json else None
                    if cur_type == "journal-article":
                        if cur_issue_id is None:
                            if cur_volume_id is None:
                                retrieved_container = self.rf.retrieve(container_ids)
                            else:
                                retrieved_container = \
                                    self.rf.retrieve_volume_from_journal(container_ids, cur_volume_id)
                        else:
                            retrieved_container = self.rf.retrieve_issue_from_journal(
                                container_ids, cur_issue_id, cur_volume_id)
                    elif cur_type == "journal-issue":
                        if cur_volume_id is None:
                            retrieved_container = self.rf.retrieve(container_ids)
                        else:
                            retrieved_container = \
                                self.rf.retrieve_volume_from_journal(container_ids, cur_volume_id)
                    else:
                        retrieved_container = self.rf.retrieve(container_ids)

                    if retrieved_container is not None:
                        cont_br = self.g_set.add_br(
                            self.name, self.id, crossref_source, retrieved_container)
                    else:
                        cur_container_title = None
                        if len(crossref_json[key]) > 0:
                            cur_container_title = self.__create_title_from_list(crossref_json[key])

                        if cur_container_title is not None:
                            cur_container_type = None
                            cont_br = self.g_set.add_br(self.name, self.id, crossref_source)

                            if cur_type == "book-chapter":
                                cur_container_type = "book"
                                cont_br.create_book()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "book-part":
                                cur_container_type = "book"
                                cont_br.create_book()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "book-section":
                                cur_container_type = "book"
                                cont_br.create_book()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "book-track":
                                cur_container_type = "book-section"
                                cont_book = self.g_set.add_br(self.name, self.id, crossref_source)
                                cont_book.create_book()
                                cont_book.create_title(cur_container_title)
                                self.__associate_isbn(cont_book, crossref_json, crossref_source)
                                cont_book.has_part(cont_br)
                                cont_br.create_book_section()
                            elif cur_type == "component":
                                cur_container_type = "component"
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "dataset":
                                cur_container_type = "dataset"
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "journal-article":
                                if "issue" not in crossref_json and "volume" not in crossref_json:
                                    cur_container_type = "journal"
                                    jou_br = cont_br
                                    self.__add_journal_data(jou_br, cur_container_title)
                                else:
                                    # If we have an issue or a volume specified, the journal may have
                                    # been already added to the corpus in the past. Thus, check it
                                    # before creating a new object for that journal
                                    retrieved_journal = self.rf.retrieve(container_ids)
                                    if retrieved_journal is None:
                                        jou_br = self.g_set.add_br(self.name, self.id, crossref_source)
                                        self.__associate_issn(jou_br, crossref_json, crossref_source)
                                        self.__add_journal_data(
                                            jou_br, cur_container_title)
                                    else:
                                        jou_br = self.g_set.add_br(
                                            self.name, self.id, crossref_source, retrieved_journal)

                                    if "issue" in crossref_json:
                                        cur_container_type = "issue"
                                        cont_br.create_issue()
                                        cont_br.create_number(crossref_json["issue"])
                                        if "volume" not in crossref_json:
                                            jou_br.has_part(cont_br)

                                    if "volume" in crossref_json:
                                        cur_volume_id = crossref_json["volume"]
                                        if "issue" in crossref_json:
                                            # If we have an issue specified, the volume may have
                                            # been already added to the corpus in the past. Thus, check it
                                            # before creating a new object for that volume
                                            retrieved_volume = self.rf.retrieve_volume_from_journal(
                                                container_ids, cur_volume_id)
                                            if retrieved_volume is None:
                                                vol_br = self.g_set.add_br(
                                                    self.name, self.id, crossref_source)
                                                self.__add_volume_data(vol_br, cur_volume_id)
                                                jou_br.has_part(vol_br)
                                            else:
                                                vol_br = self.g_set.add_br(
                                                    self.name, self.id, crossref_source, retrieved_volume)
                                            vol_br.has_part(cont_br)
                                        else:
                                            cur_container_type = "volume"
                                            vol_br = cont_br
                                            self.__add_volume_data(vol_br, cur_volume_id)
                                            jou_br.has_part(vol_br)
                            elif cur_type == "journal-issue":
                                cur_container_type = "journal"
                                if "volume" in crossref_json:
                                    cur_container_type = "volume"
                                    self.__add_volume_data(cont_br, crossref_json["volume"])
                                    # If we have a volume specified, the journal may have
                                    # been already added to the corpus in the past. Thus, check it
                                    # before creating a new object for that journal
                                    retrieved_journal = self.rf.retrieve(container_ids)
                                    if retrieved_journal is None:
                                        jou_br = self.g_set.add_br(self.name, self.id, crossref_source)
                                        self.__associate_issn(jou_br, crossref_json, crossref_source)
                                        self.__add_journal_data(
                                            jou_br, cur_container_title)
                                    else:
                                        jou_br = self.g_set.add_br(
                                            self.name, self.id, crossref_source, retrieved_journal)

                                    jou_br.has_part(cont_br)
                                else:
                                    jou_br = cont_br
                                    self.__add_journal_data(jou_br, cur_container_title)

                            elif cur_type == "journal-volume":
                                cur_container_type = "volume"
                                self.__add_journal_data(cont_br, cur_container_title)
                                self.__associate_issn(cont_br, crossref_json, crossref_source)
                            elif cur_type == "other":
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "proceedings-article":
                                cur_container_type = "proceedings"
                                cont_br.create_proceedings()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "reference-entry":
                                cur_container_type = "reference-book"
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "report":
                                cur_container_type = "report-series"
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)
                            elif cur_type == "standard":
                                cur_container_type = "standard-series"
                                cont_br.create_expression_collection()
                                cont_br.create_title(cur_container_title)

                            # If the current type is in any of the ISSN or ISBN list
                            # add the identifier to the resource
                            if cur_container_type is not None:
                                if cur_container_type in self.issn_types:
                                    self.__associate_issn(cont_br, crossref_json, crossref_source)
                                if cur_container_type in self.isbn_types:
                                    self.__associate_isbn(cont_br, crossref_json, crossref_source)

                    if cont_br is not None:
                        cont_br.has_part(cur_br)
                elif key == "type":
                    cur_type = crossref_json[key]
                    if cur_type == "book":
                        cur_br.create_book()
                    elif cur_type == "book-chapter":
                        cur_br.create_book_chapter()
                    elif cur_type == "book-part":
                        cur_br.create_book_part()
                    elif cur_type == "book-section":
                        cur_br.create_book_section()
                    elif cur_type == "book-series":
                        cur_br.create_book_series()
                    elif cur_type == "book-set":
                        cur_br.create_book_set()
                    elif cur_type == "book-track":
                        cur_br.create_book_track()
                    elif cur_type == "component":
                        cur_br.create_component()
                    elif cur_type == "dataset":
                        cur_br.create_dataset()
                    elif cur_type == "dissertation":
                        cur_br.create_dissertation()
                    elif cur_type == "edited-book":
                        cur_br.create_edited_book()
                    elif cur_type == "journal":
                        self.__add_journal_data(cur_br, cur_title)
                    elif cur_type == "journal-article":
                        cur_br.create_journal_article()
                    elif cur_type == "journal-issue":
                        cur_br.create_issue()
                    elif cur_type == "journal-volume":
                        cur_br.create_volume()
                    elif cur_type == "monograph":
                        cur_br.create_monograph()
                    elif cur_type == "other":
                        cur_br.create_other()
                    elif cur_type == "proceedings":
                        cur_br.create_proceedings()
                    elif cur_type == "proceedings-article":
                        cur_br.create_proceedings_article()
                    elif cur_type == "reference-book":
                        cur_br.create_reference_book()
                    elif cur_type == "reference-entry":
                        cur_br.create_reference_entry()
                    elif cur_type == "report":
                        cur_br.create_report()
                    elif cur_type == "report-series":
                        cur_br.create_report_series()
                    elif cur_type == "standard":
                        cur_br.create_standard()
                    elif cur_type == "standard-series":
                        cur_br.create_standard_series()

                    # If the current type is in any of the ISSN or ISBN list
                    # add the identifier to the resource
                    if cur_type in self.issn_types:
                        self.__associate_issn(cur_br, crossref_json, crossref_source)
                    if cur_type in self.isbn_types:
                        self.__associate_isbn(cur_br, crossref_json, crossref_source)

        return cur_br

    def message(self, mess, entity_type, entity, url="not provided"):
        return super(CrossrefProcessor, self).message(mess) + \
               "\n\t%s: %s\n\tURL: %s" % (entity_type, entity, url)

    def __get_ids_for_type(self, crossref_data):
        result = {}

        if "DOI" in crossref_data:
            result[ge.doi] = [crossref_data["DOI"]]

        if "URL" in crossref_data:
            result[ge.url] = [crossref_data["URL"]]

        if "container-title" not in crossref_data or len(crossref_data["container-title"]) == 0:
            cur_issns = self.__get_all_issns(crossref_data)
            if cur_issns:
                result[ge.issn] = cur_issns

            cur_isbns = self.__get_all_isbns(crossref_data)
            if cur_isbns:
                result[ge.isbn] = cur_isbns

        return result

    def __get_ids_for_container(self, crossref_data):
        result = {}

        if "container-title" in crossref_data and len(crossref_data["container-title"]) > 0:
            cur_issns = self.__get_all_issns(crossref_data)
            if cur_issns:
                result[ge.issn] = cur_issns

            cur_isbns = self.__get_all_isbns(crossref_data)
            if cur_isbns:
                result[ge.isbn] = cur_isbns

        return result

    def __associate_issn(self, res, crossref_data, crossref_source):
        for string in self.__get_all_issns(crossref_data):
            cur_id = self.g_set.add_id(self.name, self.id, crossref_source)
            if cur_id.create_issn(string):
                res.has_id(cur_id)

    def __get_all_issns(self, crossref_data):
        result = []
        if "ISSN" in crossref_data:
            for string in crossref_data["ISSN"]:
                if string != "0000-0000":
                    result += [string]
        return result

    def __associate_isbn(self, res, crossref_data, crossref_source):
        for string in self.__get_all_isbns(crossref_data):
            cur_id = self.g_set.add_id(self.name, self.id, crossref_source)
            if cur_id.create_isbn(string):
                res.has_id(cur_id)

    def __get_all_isbns(self, crossref_data):
        result = []
        if "ISBN" in crossref_data:
            for string in crossref_data["ISBN"]:
                result += [re.sub("^" + CrossrefProcessor.isbn_base_url, "", string)]
        return result

    def __get_all_urls(self, crossref_data):
        result = []
        if "URL" in crossref_data:
            result += [crossref_data["URL"]]
        return result

    def __get_all_dois(self, crossref_data):
        result = []
        if "DOI" in crossref_data:
            result += [crossref_data["DOI"]]
        return result

    def __add_journal_data(self, jou, title):
        jou.create_journal()
        jou.create_title(title)

    def __add_volume_data(self, vol, num):
        vol.create_volume()
        vol.create_number(num)

    def __create_title_from_list(self, title_list):
        cur_title = ""

        for title in title_list:
            strip_title = title.strip()
            if strip_title != "":
                if cur_title == "":
                    cur_title = strip_title
                else:
                    cur_title += " - " + strip_title

        return cur_title