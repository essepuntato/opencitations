#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

from requests.exceptions import ReadTimeout, ConnectTimeout
from format_processor import *
import requests
from time import sleep
import json
from graphlib import GraphEntity as ge


class CrossRefProcessor(FormatProcessor):
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
                 tmp_dir,
                 entries,
                 res_finder,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=0,
                 timeout=10,
                 use_doi_in_bibentry_as_id=True,
                 use_url_in_bibentry_as_id=False,
                 crossref_min_similarity_score=2.7):
        self.crossref_api_works = "http://api.crossref.org/works/"
        self.crossref_api_journals = "http://api.crossref.org/journals/"
        self.crossref_api_members = "http://api.crossref.org/members/"
        self.crossref_api_search = "http://api.crossref.org/works?rows=1&query="
        self.headers = headers
        self.sec_to_wait = sec_to_wait
        self.timeout = timeout
        self.rf = res_finder
        self.get_bib_entry_url = use_url_in_bibentry_as_id
        self.get_bib_entry_doi = use_doi_in_bibentry_as_id
        self.crossref_min_similarity_score = crossref_min_similarity_score
        super(CrossRefProcessor, self).__init__(
            base_iri, context_base, info_dir, tmp_dir, entries, "SPACIN CrossRef Processor", "CrossRef")

    def __process_entity(self, entity, entity_type, api_url):
        try:
            url_request = api_url + entity
            entry_data = requests.get(url_request, headers=self.headers, timeout=self.timeout)
            if entry_data.status_code == 200:
                try:
                    return json.loads(entry_data.text)
                except ValueError as e:
                    self.reperr.add_sentence(self.message(
                        "The JSON returned is malformed. %s" %
                        str(e), entity_type, entity, url_request))
            else:
                self.reperr.add_sentence(self.message(
                    "We got an HTTP error when retrieving data (HTTP status code: %s)." %
                    str(entry_data.status_code), entity_type, entity, url_request))
        except ReadTimeout as e:
            self.reperr.add_sentence(self.message(
                "A timeout error happened when reading results from the API. %s" %
                str(e), entity_type, entity, url_request))
        except ConnectTimeout as e:
            self.reperr.add_sentence(self.message(
                "A timeout error happened when connecting to the API. %s" %
                str(e), entity_type, entity, url_request))

    def process_entry(self, entry, resp_agent=None):
        entry_cleaned = FormatProcessor.clean_entry(entry)
        cur_json = self.get_crossref_item(
            self.__process_entity(entry_cleaned, "entry", self.crossref_api_search))
        if cur_json is not None:
            return self.process_crossref_json(cur_json, resp_agent)

    def process_doi(self, doi, resp_agent=None):
        existing_res = self.rf.retrieve_from_doi(doi)
        if existing_res is None:
            cur_json = self.get_crossref_item(self.__process_entity(doi, "doi", self.crossref_api_works))
            if cur_json is not None:
                return self.process_crossref_json(cur_json, resp_agent)
        else:
            result = self.g_set.add_br(existing_res)
            self.rf.update_graph_set(self.g_set)
            return result

    def process_issn(self, issn, resp_agent=None):
        existing_res = self.rf.retrieve_from_issn(issn)
        if existing_res is None:
            cur_json = \
                self.get_crossref_item(self.__process_entity(issn, "issn", self.crossref_api_journals))
            if cur_json is not None:
                return self.process_crossref_json(cur_json, resp_agent)
        else:
            result = self.g_set.add_br(existing_res)
            self.rf.update_graph_set(self.g_set)
            return result

    def process_member(self, member, resp_agent):
        existing_res = self.rf.retrieve_from_url(member)
        if existing_res is None:
            cur_json = \
                self.get_crossref_item(self.__process_entity(member, "member", self.crossref_api_members))
            if cur_json is not None:
                return self.process_crossref_json(cur_json, resp_agent)
        else:
            result = self.g_set.add_ra(existing_res)
            self.rf.update_graph_set(self.g_set)
            return result

    def process(self):
        result = []

        for full_entry in self.entries:
            sleep(self.sec_to_wait)
            cur_res = None

            entry = full_entry["bibentry"]

            extracted_doi = FormatProcessor.extract_doi(entry)
            extracted_url = FormatProcessor.extract_url(entry)

            if "doi" in full_entry:
                provided_doi = full_entry["doi"]
                cur_res = self.process_doi(provided_doi)
                if cur_res is not None:
                    self.repok.add_sentence(
                        self.message("The entity for '%s' has been found by means of the "
                                     "DOI provided as input." % entry,
                                     "DOI", provided_doi))

            if cur_res is None:
                cur_res = self.process_entry(entry, self.id)
                if cur_res is None:
                    if self.get_bib_entry_doi and extracted_doi is not None:
                        cur_res = self.process_doi(extracted_doi, self.name)
                        if cur_res is not None:
                            self.repok.add_sentence(
                                self.message("The entity for '%s' has been found by means of the "
                                             "DOI extracted from it." % entry,
                                             "DOI", extracted_doi))
                    if cur_res is None and self.get_bib_entry_url and extracted_url is not None:
                        existing_res = self.rf.retrieve_from_url(extracted_url)
                        if existing_res is not None:
                            cur_res = self.g_set.add_br(existing_res)
                            self.repok.add_sentence(
                                self.message("The entity for '%s' has been found by means of the "
                                             "URL extracted from it." % entry,
                                             "URL", extracted_url))

                else:
                    self.repok.add_sentence(
                        self.message(
                            "The entity has been retrieved by using the search API.",
                            "entry", entry))

            # If it is none, create it anyway
            if cur_res is None:
                cur_res = self.g_set.add_br(self.name)
                self.rf.update_graph_set(self.g_set)
                self.repok.add_sentence(
                    self.message("The entity has been created even if no results have "
                                 "been returned by the API.",
                                 "entry", entry))

            # Add any URL extracted from the entry if it is not already included
            if self.get_bib_entry_url:
                self.__add_url(cur_res, extracted_url)

            # Add any DOI extracted from the entry if it is not already included
            if self.get_bib_entry_doi:
                self.__add_doi(cur_res, extracted_doi)

            result += [cur_res]
            self.rf.update_graph_set(self.g_set)

        return result

    def __add_url(self, cur_res, extracted_url):
        if extracted_url is not None:
            cur_id = self.rf.retrieve_br_url(cur_res, extracted_url)

            if cur_id is None:
                cur_id = self.g_set.add_id(self.name)
                cur_id.create_url(extracted_url)

            cur_res.has_id(cur_id)

    def __add_doi(self, cur_res, extracted_doi):
        if extracted_doi is not None:
            cur_id = self.rf.retrieve_br_doi(cur_res, extracted_doi)

            if cur_id is None:
                cur_id = self.g_set.add_id(self.name)
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

    def process_crossref_json(self, crossref_json, resp_for_doi):
        # Check if the found bibliographic resource already exist either
        # in the triplestore or in the current graph set.
        self.rf.update_graph_set(self.g_set)
        retrieved_resource = self.rf.retrieve(self.__get_ids_for_type(crossref_json))

        if retrieved_resource is not None:
            cur_br = self.g_set.add_br(retrieved_resource)
        else:
            cur_br = self.g_set.add_br(self.id)
            for key in crossref_json:
                if key == "title":
                    cur_title = ""
                    for title in crossref_json[key]:
                        if len(title) > len(cur_title):
                            cur_title = title
                    cur_br.create_title(cur_title)
                elif key == "subtitle":
                    cur_subtitle = ""
                    for subtitle in crossref_json[key]:
                        if len(subtitle) > len(cur_subtitle):
                            cur_subtitle = subtitle
                    cur_br.create_subtitle(cur_subtitle)
                elif key == "author":
                    for author in crossref_json["author"]:
                        cur_agent = self.g_set.add_ra(self.id)
                        if "given" in author:
                            cur_agent.create_given_name(author["given"])
                        if "family" in author:
                            cur_agent.create_family_name(author["family"])
                        cur_role = self.g_set.add_ar(self.id)
                        cur_agent.has_role(cur_role)
                        if crossref_json["type"] == "edited-book":
                            cur_role.create_editor(cur_br)
                        else:
                            cur_role.create_author(cur_br)
                elif key == "publisher":
                    cur_agent = None

                    # Check if the publishier already exists
                    if "member" in crossref_json and crossref_json["member"] is not None:
                        cur_member_url = crossref_json["member"]
                        retrieved_agent = self.rf.retrieve_from_url(cur_member_url)
                        if retrieved_agent is not None:
                            cur_agent = self.g_set.add_ra(retrieved_agent)
                    else:
                        cur_member_url = None

                    # If the publisher is not already defined in the knowledge base,
                    # create a new one.
                    if cur_agent is None:
                        cur_agent = self.g_set.add_ra(self.id)
                        cur_agent.create_name(crossref_json[key])

                        if cur_member_url is not None:
                            cur_agent_id = self.g_set.add_id(self.id)
                            cur_agent_id.create_url(crossref_json["member"])
                            cur_agent.has_id(cur_agent_id)

                        # TODO: handle prefix (or DOI part) for another ID

                    cur_role = self.g_set.add_ar(self.id)
                    cur_role.create_publisher(cur_br)
                    cur_agent.has_role(cur_role)
                elif key == "DOI":
                    cur_id = self.g_set.add_id(resp_for_doi)
                    if cur_id.create_doi(crossref_json[key]):
                        cur_br.has_id(cur_id)
                elif key == "issued":
                    cur_br.create_pub_year(crossref_json[key]["date-parts"][0][0])
                elif key == "URL":
                    cur_id = self.g_set.add_id(self.id)
                    if cur_id.create_url(crossref_json[key]):
                        cur_br.has_id(cur_id)
                elif key == "page":
                    cur_page = crossref_json[key]
                    cur_re = self.g_set.add_re(self.id)
                    if cur_re.create_starting_page(cur_page):
                        cur_re.create_ending_page(cur_page)
                        cur_br.has_format(cur_re)
                elif key == "container-title":
                    retrieved_container = None
                    cur_type = crossref_json["type"]
                    # TODO: add this approach also when creating new issues and volume below

                    container_ids = self.__get_ids_for_container(crossref_json)
                    if cur_type == "journal-article":
                        cur_issue_id = crossref_json["issue"] if "issue" in crossref_json else None
                        if cur_issue_id is None:
                            cur_volume_id = crossref_json["volume"] if "volume" in crossref_json else None
                            if cur_volume_id is None:
                                retrieved_container = \
                                    self.rf.retrieve(container_ids)
                            else:
                                retrieved_container = \
                                    self.rf.retrieve_volume_from_journal(container_ids, cur_volume_id)
                        else:
                            retrieved_container = \
                                self.rf.retrieve_issue_from_journal(container_ids, cur_issue_id)
                    else:
                        retrieved_container = \
                            self.rf.retrieve(container_ids)

                    if retrieved_container is not None:
                        cont_br = self.g_set.add_br(retrieved_container)
                    else:
                        cur_container_title = None
                        if len(crossref_json[key]) > 0:
                            cur_container_title = crossref_json[key][0]

                        if cur_container_title is not None:
                            cur_container_type = None
                            cont_br = self.g_set.add_br(self.id)

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
                                cont_book = self.g_set.add_br(self.id)
                                cont_book.create_book()
                                cont_book.create_title(cur_container_title)
                                self.__associate_isbn(cont_book, crossref_json)
                                cont_book.has_part(cont_br)
                                cont_br.create_book_section()
                            elif cur_type == "component":
                                cur_container_type = "component"
                                cont_br.create_expression_collection()
                            elif cur_type == "dataset":
                                cur_container_type = "dataset"
                                cont_br.create_expression_collection()
                            elif cur_type == "journal-article":
                                if "issue" not in crossref_json and "volume" not in crossref_json:
                                    cur_container_type = "journal"
                                    jou_br = cont_br
                                else:
                                    jou_br = self.g_set.add_br(self.id)
                                    self.__associate_issn(jou_br, crossref_json)

                                self.__add_journal_data(jou_br, cur_container_title, crossref_json)

                                if "issue" in crossref_json:
                                    cur_container_type = "issue"
                                    cont_br.create_issue()
                                    cont_br.create_number(crossref_json["issue"])
                                    if "volume" not in crossref_json:
                                        jou_br.has_part(cont_br)

                                if "volume" in crossref_json:
                                    if "issue" in crossref_json:
                                        vol_br = self.g_set.add_br(self.id)
                                        vol_br.has_part(cont_br)
                                    else:
                                        cur_container_type = "volume"
                                        vol_br = cont_br

                                    self.__add_volume_data(vol_br, crossref_json["volume"])

                                    jou_br.has_part(vol_br)
                            elif cur_type == "journal-issue":
                                cur_container_type = "journal"
                                if "volume" in crossref_json:
                                    cur_container_type = "volume"
                                    self.__add_volume_data(cont_br, crossref_json["volume"])
                                    jou_br = self.g_set.add_br(self.id)
                                    jou_br.has_part(cont_br)
                                else:
                                    jou_br = cont_br

                                self.__add_journal_data(jou_br, cur_container_title, crossref_json)

                            elif cur_type == "journal-volume":
                                cur_container_type = "volume"
                                self.__add_journal_data(cont_br, cur_container_title, crossref_json)
                            elif cur_type == "other":
                                cont_br.create_expression_collection()
                            elif cur_type == "proceedings-article":
                                cur_container_type = "proceedings"
                                cont_br.create_proceedings()
                            elif cur_type == "reference-entry":
                                cur_container_type = "reference-book"
                                cont_br.create_expression_collection()
                            elif cur_type == "report":
                                cur_container_type = "report-series"
                                cont_br.create_expression_collection()
                            elif cur_type == "standard":
                                cur_container_type = "standard-series"
                                cont_br.create_expression_collection()

                            # If the current type is in any of the ISSN or ISBN list
                            # add the identifier to the resource
                            if cur_container_type is not None:
                                if cur_container_type in self.issn_types:
                                    self.__associate_issn(cont_br, crossref_json)
                                if cur_container_type in self.isbn_types:
                                    self.__associate_isbn(cont_br, crossref_json)

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
                        self.__add_journal_data(cur_br, cur_title, crossref_json)
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
                        self.__associate_issn(cur_br, crossref_json)
                    if cur_type in self.isbn_types:
                        self.__associate_isbn(cur_br, crossref_json)

        return cur_br

    def message(self, mess, entity_type, entity, url="not provided"):
        return super(CrossRefProcessor, self).message(mess) + \
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

    def __associate_issn(self, res, crossref_data):
        for string in self.__get_all_issns(crossref_data):
            cur_id = self.g_set.add_id(self.id)
            if cur_id.create_issn(string):
                res.has_id(cur_id)

    def __get_all_issns(self, crossref_data):
        result = []
        if "ISSN" in crossref_data:
            for string in crossref_data["ISSN"]:
                if string != "0000-0000":
                    result += [string]
        return result

    def __associate_isbn(self, res, crossref_data):
        for string in self.__get_all_isbns(crossref_data):
            cur_id = self.g_set.add_id(self.id)
            if cur_id.create_isbn(string):
                res.has_id(cur_id)

    def __get_all_isbns(self, crossref_data):
        result = []
        if "ISBN" in crossref_data:
            for string in crossref_data["ISBN"]:
                result += [re.sub("^" + CrossRefProcessor.isbn_base_url, "", string)]
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

    def __add_journal_data(self, jou, title, crossref_data):
        jou.create_journal()
        jou.create_title(title)

    def __add_volume_data(self, vol, num):
        vol.create_volume()
        vol.create_number(num)