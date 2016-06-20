#!/usr/bin/python
# -*- coding: utf-8 -*-
from reference_processor import ReferenceProcessor
from support import get_data
from support import dict_get as dg
import os
from lxml import html
from datetime import datetime
from time import sleep


class EuropeanPubMedCentralProcessor(ReferenceProcessor):
    def __init__(self,
                 stored_file,
                 reference_dir,
                 error_dir,
                 pagination_file,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30,
                 max_query_per_sec=10):
        self.provider = "Europe PubMed Central"
        self.all_papers_api = "http://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                              "has_reflist:y+sort_date:y&resulttype=lite&pageSize=1000&format=json&page="
        self.ref_list_api = "http://www.ebi.ac.uk/europepmc/webservices/rest/XXX/YYY/references/" \
                            "1/1000/json"
        self.paper_api = "http://www.ebi.ac.uk/europepmc/webservices/rest/search?resulttype=lite&query="
        self.pagination_file = pagination_file
        self.max_query_per_sec = max_query_per_sec
        self.query_count = 0
        self.sec_threshold = None
        super(ReferenceProcessor, self).__init__(
            stored_file, reference_dir, error_dir, headers, sec_to_wait, max_iteration, timeout)

    def process(self):
        while True:
            cur_page = self.__get_next_page()
            self.repok.new_article()
            self.repok.add_sentence("Processing page %s." % str(cur_page))
            result = self.__get_data(self.all_papers_api + str(cur_page))
            # Proceed only if there were no problems in getting the data, otherwise stop
            if result is not None:
                papers_with_ref_list = dg(result, ["resultList", "result"])
                if papers_with_ref_list is not None and papers_with_ref_list:
                    for paper in papers_with_ref_list:

                        cur_id = dg(paper, ["id"])
                        cur_source = dg(paper, ["source"])
                        cur_doi = dg(paper, ["doi"])
                        cur_pmid = dg(paper, ["pmid"])
                        cur_pmcid = dg(paper, ["pmcid"])
                        cur_localid = cur_id + "-" + cur_source
                        id_list = [cur_doi, cur_pmid, cur_pmcid, cur_localid]
                        if not self.rs.is_any_stored(id_list):
                            self.repok.new_article()
                            self.repok.add_sentence(
                                "Processing article with local id '%s'." % cur_localid)
                            ref_list_url = self.ref_list_api.replace(
                                "XXX", cur_source).replace("YYY", cur_id)

                            paper_references = self.__get_data(ref_list_url)

                            references = dg(paper_references, ["referenceList", "reference"])
                            if references is not None:
                                self.rs.new_ref_list()
                                for reference in references:
                                    ref_entry = self.__create_entry(reference)
                                    entry_text = None if ref_entry is None else ref_entry[0]
                                    process_entry_text = True if ref_entry is None else ref_entry[1]

                                    # Add special data if the reference matches with the ePMC database
                                    if reference["match"] == "Y":
                                        paper_data = self.__get_data(self.paper_api + "ext_id:%s+src:%s" %
                                                                     (cur_id, cur_source))
                                        matched_results = dg(paper_data, ["resultList", "result"])
                                        if matched_results is not None and len(matched_results) > 0:
                                            ref_doi = dg(matched_results, ["doi"])
                                            ref_pmid = dg(matched_results, ["pmid"])
                                            ref_pmcid = dg(matched_results, ["pmcid"])
                                    else:
                                        ref_doi = dg(reference, ["doi"])
                                        ref_pmid = dg(reference, ["pmid"])
                                        ref_pmcid = dg(reference, ["pmcid"])

                                    self.rs.add_reference(entry_text, process_entry_text,
                                                          ref_doi, ref_pmid, ref_pmcid)
                                self.rs.store(
                                    next(item for item in id_list if item is not None),
                                    cur_doi, cur_pmid, cur_pmcid, self.name, self.provider, ref_list_url)
                                self.repok.add_sentence(
                                    "References of '%s' have been stored." % cur_localid)
                            else:
                                self.reper.add_sentence(
                                    "The article '%s' has no references." % cur_localid)
                    self.__store_page_number(cur_page)
                else:  # We have browsed all the pages with results, and thus the counting is reset
                    self.__reset_page_number()
                    break
            else:
                break

    def __get_data(self, get_url):
        if self.sec_threshold is None:
            self.sec_threshold = datetime.now()
        if self.query_count % self.max_query_per_sec:
            self.query_count = 1
            if (datetime.now() - self.sec_threshold).seconds == 0:
                sleep(1)

            self.sec_threshold = datetime.now()
        else:
            self.query_count += 1

        return get_data(self.max_iteration, self.sec_to_wait, get_url,
                        self.headers, self.timeout, self.repok, self.reper)

    @staticmethod
    def __create_entry(entry):
        result = None

        author = dg(entry, ["authorString"])
        unstructored = dg(entry, ["unstructuredInformation"])
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
                                ("," if entry_string.endswith("(Eds.)") else ".", journal.strip())

            container = dg(entry, ["publicationTitle"])
            if container is not None and container.strip() != "":
                entry_string += "%s %s" % \
                                ("," if entry_string.endswith("(Eds.)") else ".", container.strip())

            series = dg(entry, ["seriesName"])
            if series is not None and series.strip() != "":
                entry_string += "%s %s" % \
                                ("," if entry_string.endswith("(Eds.)") else ".", series.strip())

            volume = dg(entry, ["volume"])
            if volume is not None and volume.strip() != "":
                entry_string += "%s %s" % ("" if entry_string[-1] == "." else ",", volume.strip())

            issue = dg(entry, ["issue"])
            if issue is not None and issue.strip() != "":
                is_digit = entry_string[-1].isdigit()
                entry_string += "%s%s%s" % \
                                (" (" if is_digit else " ", issue.strip(), ")" if is_digit else "")

            page = dg(entry, ["pageInfo"])
            if page is not None and page.strip() != "":
                entry_string += "%s %s" % ("" if entry_string[-1] == "." else ":", page.strip())

            edition = dg(entry, ["edition"])
            if edition is not None and edition.strip() != "":
                entry_string += "%s %s" % ("" if entry_string[-1] == "." else ".", edition.strip())

            doi = dg(entry, ["doi"])
            if doi is not None and doi.strip() != "":
                entry_string += "%s http://dx.doi.org/%s" % \
                                ("" if entry_string[-1] == "." else ".", edition.strip())

            result = (entry_string, to_process)
        elif unstructored is not None and len(unstructored.strip()):
            result = (html.document_fromstring(unstructored.strip()).text_content(), True)

        return result

    def __get_next_page(self):
        result = 1

        if os.path.exists(self.pagination_file):
            with open(self.pagination_file) as f:
                result += int(f.read().strip())

        return result

    def __reset_page_number(self):
        self.__store_page_number(0)

    def __store_page_number(self, p_num):
        with open(self.pagination_file, "w") as f:
            f.write(str(p_num))
