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

from reference_processor import ReferenceProcessor
from support import get_data
from support import dict_get as dg
import os
from lxml import html
from datetime import datetime
from time import sleep
import re
from lxml import etree
from support import encode_url


class EuropeanPubMedCentralProcessor(ReferenceProcessor):
    def __init__(self,
                 stored_file,
                 reference_dir,
                 error_dir,
                 pagination_file,
                 stopper,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30,
                 max_query_per_sec=10,
                 p_size=1000):
        if p_size > 1000 or p_size < 1:
            page_size = "1000"
        else:
            page_size = str(p_size)
        self.provider = "Europe PubMed Central"
        self.all_papers_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                              "has_reflist:y+sort_date:y&resulttype=lite&pageSize=%s&format=json" \
                              "&cursorMark=" % page_size
        self.ref_list_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/XXX/YYY/references/" \
                            "1/1000/json"
        self.paper_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?resulttype=lite&" \
                         "format=json&query="
        self.xml_source_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/XXX/fullTextXML"
        self.open_access_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                               "open_access:y+sort_date:y&resulttype=lite&pageSize=%s&format=json" \
                               "&cursorMark=" % page_size
        self.pagination_file = pagination_file
        self.max_query_per_sec = max_query_per_sec
        self.query_count = 1
        self.sec_threshold = None
        self.__last_xml_source = None
        super(EuropeanPubMedCentralProcessor, self).__init__(
            stored_file, reference_dir, error_dir, stopper, headers, sec_to_wait, max_iteration, timeout)

    def __get_data_from_page(self, cur_page, oa=False):
        self.repok.new_article()
        self.repok.add_sentence("Processing page %s." % str(cur_page))
        if oa:
            cur_get_url = self.open_access_api + cur_page
        else:
            cur_get_url = self.all_papers_api + cur_page
        return self.__get_data(cur_get_url), cur_get_url

    def process(self, oa=False):
        while True:
            if self.stopper.can_proceed():
                cur_page = self.__get_next_page()
                
                result, cur_get_url = self.__get_data_from_page(cur_page, oa)
                # Re-run the query with the first page,
                # since a wrong page can be specified
                if result is None:
                    result, cur_get_url = self.__get_data_from_page("*", oa)
                
                # Proceed only if there were no problems in getting the data, otherwise stop
                if result is not None:
                    papers_retrieved = dg(result, ["resultList", "result"])
                    if papers_retrieved is not None and papers_retrieved:
                        for paper in papers_retrieved:
                            if self.stopper.can_proceed():
                                cur_id = dg(paper, ["id"])
                                cur_source = dg(paper, ["source"])
                                cur_doi = dg(paper, ["doi"])
                                cur_pmid = dg(paper, ["pmid"])
                                cur_pmcid = dg(paper, ["pmcid"])
                                if cur_doi is None and cur_pmcid is not None:
                                    cur_doi = self.__get_doi_from_xml_source(cur_pmcid)
                                cur_localid = cur_source + "-" + cur_id
                                id_list = [cur_doi, cur_pmid, cur_pmcid, cur_localid]
                                if not self.rs.is_any_stored(id_list):
                                    self.repok.new_article()
                                    self.repok.add_sentence(
                                        "Processing article with local id '%s'." % cur_localid)

                                    if oa:
                                        ref_list_url = self.__process_xml_source(cur_pmcid)
                                    else:
                                        ref_list_url = self.__process_references(cur_source, cur_id)
                                    if ref_list_url is not None:
                                        self.rs.store(
                                            next(item for item in id_list if item is not None),
                                            cur_localid, cur_doi, cur_pmid, cur_pmcid, self.name,
                                            self.provider, encode_url(ref_list_url))
                                        self.repok.add_sentence(
                                            "References of '%s' have been stored." % cur_localid)
                                    else:
                                        self.reper.add_sentence(
                                            "The article '%s' has no references or its PubMed Central "
                                            "ID is not defined." % cur_localid)
                                else:
                                    self.repok.add_sentence(
                                        "The article '%s' has been already stored." % cur_localid)
                            else:
                                break
                        if self.stopper.can_proceed():
                            self.__store_page_number(dg(result, ["nextCursorMark"]))
                    else:  # We have browsed all the pages with results, and thus the counting is reset
                        self.__reset_page_number()
                        self.repok.add_sentence("All the pages has been processed.")
                        break
                else:
                    self.reper.add_sentence("Problems in retrieving data for '%s'" % cur_get_url)
                    break
            else:  # Process stopped due to external reasons
                self.repok.add_sentence("Process stopped due to external reasons.")
                break

    def __get_paper_data(self, source, paper_id):
        doi = None
        pmid = None
        pmcid = None

        paper_data = self.__get_data(
            self.paper_api + "ext_id:%s+src:%s" %
            (paper_id, source))

        matched_results = dg(paper_data, ["resultList", "result"])
        if matched_results is not None and \
                        len(matched_results) > 0:
            doi = dg(matched_results[0], ["doi"])
            pmid = dg(matched_results[0], ["pmid"])
            pmcid = dg(matched_results[0], ["pmcid"])

        return {
            "doi": doi,
            "pmid": pmid,
            "pmcid": pmcid
        }

    def __create_entry_xml(self, xml_ref):
        entry_string = u""
        el_citation = xml_ref.xpath("./element-citation | ./mixed-citation")
        if len(el_citation):
            cur_el = el_citation[0]
            is_element_citation = cur_el.tag == "element-citation"
            has_list_of_people = False
            first_text_passed = False
            for el in cur_el.xpath(".//node()"):
                type_name = type(el).__name__
                if type_name == "_Element":
                    cur_text = el.text
                    if cur_text is not None and " ".join(cur_text.split()) != "":
                        if first_text_passed:
                            is_in_person_group = len(el.xpath("ancestor::person-group")) > 0
                            if is_in_person_group:
                                entry_string += ", "
                                has_list_of_people = True
                            elif not is_in_person_group and has_list_of_people:
                                entry_string += ". "
                                has_list_of_people = False
                            else:
                                if is_element_citation:
                                    entry_string += ", "
                                else:
                                    entry_string += " "
                        else:
                            first_text_passed = True
                    if el.tag == "pub-id":
                        if el.xpath("./@pub-id-type = 'doi'"):
                            entry_string += "DOI: "
                        elif el.xpath("./@pub-id-type = 'pmid'"):
                            entry_string += "PMID: "
                        elif el.xpath("./@pub-id-type = 'pmcid'"):
                            entry_string += "PMC: "
                elif type_name == "_ElementStringResult" or type_name == "_ElementUnicodeResult":
                    entry_string += el

        entry_string = " ".join(entry_string.split())
        entry_string = re.sub(" ([,\.!\?;:])", "\\1", entry_string)
        entry_string = re.sub(u"([\-–––]) ", "\\1", entry_string)
        entry_string = re.sub(u"[\-–––,\.!\?;:] ?([\-–––,\.!\?;:])", "\\1", entry_string)
        entry_string = re.sub("(\(\. ?)+", "(", entry_string)
        entry_string = re.sub("(\( +)", "(", entry_string)

        if entry_string is not None and entry_string != "":
            return entry_string
        else:
            return None

    def __get_xml_source(self, cur_pmcid):
        if cur_pmcid is not None:
            xml_source_url = self.xml_source_api.replace("XXX", cur_pmcid)
            return self.__get_data(xml_source_url, is_json=False)

    def __get_doi_from_xml_source(self, cur_pmcid):
        self.__last_xml_source = self.__get_xml_source(cur_pmcid)
        if self.__last_xml_source is not None:
            cur_xml = etree.fromstring(self.__last_xml_source)
            doi = cur_xml.xpath("/article/front/article-meta/article-id[@pub-id-type='doi']")
            if len(doi):
                doi_string = u"" + etree.tostring(doi[0], method="text", encoding='UTF-8').strip()
                if doi_string != "":
                    return doi_string

    def __process_xml_source(self, cur_pmcid):
        if cur_pmcid is not None:
            xml_source_url = self.xml_source_api.replace("XXX", cur_pmcid)

            if self.__last_xml_source is None:
                xml_source = self.__get_xml_source(cur_pmcid)
            else:
                xml_source = self.__last_xml_source
                self.__last_xml_source = None

            if xml_source is not None:
                cur_xml = etree.fromstring(xml_source)

                references = cur_xml.xpath("//ref-list/ref")
                if len(references):
                    self.rs.new_ref_list()
                    for reference in references:
                        entry_text = self.__create_entry_xml(reference)
                        process_entry_text = None if entry_text is None else True

                        ref_pmid = None
                        ref_doi = None
                        ref_pmcid = None
                        ref_url = None

                        ref_pmid_el = reference.xpath(".//pub-id[@pub-id-type='pmid']")
                        if len(ref_pmid_el):
                            ref_pmid = etree.tostring(
                                ref_pmid_el[0], method="text", encoding='UTF-8').strip()
                            if ref_pmid != "":
                                ref_paper_ids = self.__get_paper_data("MED", ref_pmid)
                                ref_doi = ref_paper_ids["doi"]
                                ref_pmcid = ref_paper_ids["pmcid"]
                            else:
                                ref_pmid = None

                        if ref_doi is None:
                            ref_doi_el = reference.xpath(".//pub-id[@pub-id-type='doi']")
                            if len(ref_doi_el):
                                ref_doi = etree.tostring(
                                    ref_doi_el[0], method="text", encoding='UTF-8').lower().strip()
                                if ref_doi == "":
                                    ref_doi = None

                        if ref_pmcid is None:
                            ref_pmcid_el = reference.xpath(".//pub-id[@pub-id-type='pmcid']")
                            if len(ref_pmcid_el):
                                ref_pmcid = etree.tostring(
                                    ref_pmcid_el[0], method="text", encoding='UTF-8').strip()
                                if ref_pmcid == "":
                                    ref_pmcid = None
                                elif not ref_pmcid.startswith("PMC"):
                                    ref_pmcid = "PMC" + ref_pmcid

                        ref_url_el = reference.xpath(".//ext-link")
                        if len(ref_url_el):
                            ref_url = etree.tostring(
                                ref_url_el[0], method="text", encoding='UTF-8').strip()
                            if not ref_url.startswith("http"):
                                ref_url = None

                        self.rs.add_reference(entry_text, process_entry_text,
                                              None, ref_doi, ref_pmid, ref_pmcid, ref_url)

                    return xml_source_url

    def __process_references(self, cur_source, cur_id):
        ref_list_url = self.ref_list_api.replace(
            "XXX", cur_source).replace("YYY", cur_id)

        paper_references = self.__get_data(ref_list_url)

        references = dg(paper_references, ["referenceList", "reference"])
        if references is not None:
            self.rs.new_ref_list()
            for reference in references:
                ref_entry = self.__create_entry(reference)
                entry_text = None if ref_entry is None else ref_entry[0]
                process_entry_text = \
                    True if ref_entry is None else ref_entry[1]

                # Add special data if the reference matches with
                # the ePMC database
                if reference["match"] == "Y":
                    ref_id = reference["id"]
                    ref_source = reference["source"]
                    ref_localid = ref_source + "-" + ref_id

                    paper_ids = self.__get_paper_data(ref_source, ref_id)

                    ref_doi = paper_ids["doi"]
                    ref_pmid = paper_ids["pmid"]
                    ref_pmcid = paper_ids["pmcid"]
                else:
                    ref_localid = None
                    ref_doi = dg(reference, ["doi"])
                    ref_pmid = dg(reference, ["pmid"])
                    ref_pmcid = dg(reference, ["pmcid"])
                ref_url = dg(reference, ["externalLink"])

                self.rs.add_reference(entry_text, process_entry_text,
                                      ref_localid, ref_doi,
                                      ref_pmid, ref_pmcid, ref_url)
            return ref_list_url

    def __get_data(self, get_url, is_json=True):
        if self.sec_threshold is None:
            self.sec_threshold = datetime.now()
        if self.query_count % self.max_query_per_sec == 0:
            self.query_count = 1
            if (datetime.now() - self.sec_threshold).seconds == 0:
                sleep(1)

            self.sec_threshold = datetime.now()
        else:
            self.query_count += 1

        return get_data(self.max_iteration, self.sec_to_wait, get_url,
                        self.headers, self.timeout, self.repok, self.reper, is_json)

    @staticmethod
    def __create_entry(entry):
        result = None

        author = dg(entry, ["authorString"])
        unstructured = dg(entry, ["unstructuredInformation"])
        if author is not None and author.lower() != "author unknown":
            to_process = True
            entry_string = author

            year = dg(entry, ["pubYear"])
            if year is not None and year > 0:
                entry_string += " (%s)" % str(year)
            else:
                to_process &= False

            title = dg(entry, ["title"])
            if title is not None and title.strip() != "":
                entry_string += "%s %s" % ("" if entry_string[-1] == "." else ".", title.strip())
            else:
                to_process &= False

            editors = dg(entry, ["editors"])
            if editors is not None and editors.strip() != "":
                entry_string += "%s %s (Eds.)" % ("" if entry_string[-1] == "." else ".", editors.strip())

            journal = dg(entry, ["journalAbbreviation"])
            if journal is not None and journal.strip() != "":
                entry_string += "%s %s" % \
                                ("," if entry_string.endswith("(Eds.)") else
                                 "" if re.search("[\.\?\!]$", entry_string) is not None else ".",
                                 journal.strip())

            container = dg(entry, ["publicationTitle"])
            if container is not None and container.strip() != "":
                entry_string += "%s %s" % \
                                ("," if entry_string.endswith("(Eds.)") else
                                 "" if re.search("[\.\?\!]$", entry_string) is not None else ".",
                                 container.strip())

            series = dg(entry, ["seriesName"])
            if series is not None and series.strip() != "":
                entry_string += "%s %s" % \
                                ("," if entry_string.endswith("(Eds.)") else
                                 "" if re.search("[\.\?\!]$", entry_string) is not None else ".",
                                 series.strip())

            volume = dg(entry, ["volume"])
            if volume is not None and volume.strip() != "":
                entry_string += "%s %s" % ("" if re.search("[\.\?\!]$", entry_string) is not None
                                           else ",", volume.strip())

            issue = dg(entry, ["issue"])
            if issue is not None and issue.strip() != "":
                is_digit = entry_string[-1].isdigit()
                entry_string += "%s%s%s" % \
                                (" (" if is_digit else " ", issue.strip(), ")" if is_digit else "")

            page = dg(entry, ["pageInfo"])
            if page is not None and page.strip() != "":
                entry_string += "%s %s" % ("" if re.search("[\.\?\!]$", entry_string) is not None
                                else ":", page.strip())

            edition = dg(entry, ["edition"])
            if edition is not None and edition.strip() != "":
                entry_string += "%s %s" % ("" if re.search("[\.\?\!]$", entry_string) is not None
                                else ".", edition.strip())

            doi = dg(entry, ["doi"])
            if doi is not None and doi.strip() != "":
                entry_string += "%s https://doi.org/%s" % \
                                ("" if entry_string[-1] == "." else ".", doi.strip())

            result = (entry_string, to_process)
        elif unstructured is not None and len(unstructured.strip()):
            result = (html.document_fromstring(unstructured.strip()).text_content(), True)

        return result

    def __get_next_page(self):
        result = "*"

        if os.path.exists(self.pagination_file):
            with open(self.pagination_file) as f:
                result = f.read().strip()

        return result

    def __reset_page_number(self):
        self.__store_page_number("*")

    def __store_page_number(self, p_num):
        with open(self.pagination_file, "w") as f:
            if p_num is None:
                f.write("*")
            else:
                f.write(p_num)
