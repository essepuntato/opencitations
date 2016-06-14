#!/usr/bin/python
# -*- coding: utf-8 -*-
from reference_processor import ReferenceProcessor
from script.support import get_data
from script.support import dict_get as dg
import os


class EuropeanPubMedCentralProcessor(ReferenceProcessor):
    def __init__(self,
                 stored_file,
                 reference_dir,
                 pagination_file,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30):
        self.all_papers_api = "http://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                              "has_reflist:y+sort_date:y&resulttype=lite&pageSize=1000&format=json&page="
        self.ref_list_api = "http://www.ebi.ac.uk/europepmc/webservices/rest/XXX/YYY/references/" \
                            "1/1000/json"
        self.pagination_file = pagination_file
        super(ReferenceProcessor, self).__init__(
            stored_file, reference_dir, headers, sec_to_wait, max_iteration, timeout)

    # http://www.ebi.ac.uk/europepmc/webservices/rest/MED/18489897/references/1/1000/json
    def process(self):
        cur_page = self.__get_next_page()
        result = get_data(self.max_iteration, self.sec_to_wait,
                          self.all_papers_api + str(cur_page),
                          self.headers, self.timeout, self.repok, self.reper)
        # TODO: check if that page exist, otherwise go back to page 1 and handle mechanism to stop the process if something existing has been encountered (only after the go-back phase)
        if result is not None:
            papers_with_ref_list = dg(result, ["resultList", "result"])
            if papers_with_ref_list is not None:
                for paper in papers_with_ref_list:
                    cur_doi = dg(paper, ["doi"])
                    cur_id = dg(paper, ["id"])
                    cur_source = dg(paper, ["source"])
                    # TODO: check if source+id has been already processed, in that case avoid to process it again
                    if cur_doi is not None:
                        paper_references = \
                            get_data(self.max_iteration, self.sec_to_wait,
                                     self.ref_list_api.replace("XXX", cur_source).replace("YYY", cur_id),
                                     self.headers, self.timeout, self.repok, self.reper)
                        if paper_references is not None:
                            references = dg(paper_references, ["referenceList", "reference"])
                            if references is not None:
                                self.rs.new_ref_list()
                                for reference in references:
                                    # TODO: handling "match": "Y" - in this case we could retrieve the DOI and other ids (PMID and PMCID)
                                    # TODO: ex URL: http://www.ebi.ac.uk/europepmc/webservices/rest/search?resulttype=lite&query=ext_id:7045624+src:MED
                                    if reference["match"] == "Y":
                                        pass
                                    else:
                                        pass
                            else:
                                pass  # TODO: do something or not?
                        else:
                            pass  # TODO: do something or not?
                    else:
                        pass  # TODO: store information in some way, so as to process it in the future
        else:
            pass  # TODO: do something or not?

    def __get_next_page(self):
        result = 1

        if os.path.exists(self.pagination_file):
            with open(self.pagination_file) as f:
                result = int(f.read().strip()) + 1

        return result

    def __store_page_number(self, p_num):
        with open(self.pagination_file, "w") as f:
            f.write(str(p_num))
