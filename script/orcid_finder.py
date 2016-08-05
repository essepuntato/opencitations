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

import json
import argparse
from reporter import Reporter
from support import dict_get as dg
from support import dict_add as da
from support import normalise_ascii as na
from support import get_data
from urllib import quote


class ORCIDFinder(object):
    __api_url = "https://pub.orcid.org/v1.2/search/orcid-bio/?q="

    def __init__(self, conf_file, sec_to_wait=10, max_iteration=6, timeout=30):
        with open(conf_file) as f:
            conf_json = json.load(f)
            self.headers = {
                "Authorization": "Bearer %s" % conf_json["access_token"],
                "Content-Type": "application/json"
            }
            self.id = "ORCID"
            self.name = "SPACIN " + self.__class__.__name__
            self.repok = Reporter(prefix="[%s - INFO] " % self.name)
            self.reper = Reporter(prefix="[%s - ERROR] " % self.name)
            self.__last_query_done = None
            self.sec_to_wait = sec_to_wait
            self.max_iteration = max_iteration
            self.timeout = timeout

    def get_last_query(self):
        return self.__last_query_done

    def get_orcid_records(self, doi_string, family_names=[]):
        self.repok.new_article()
        self.reper.new_article()

        cur_query = "digital-object-ids:\"%s\"" % doi_string
        if family_names:
            cur_query += " AND ("
            first_name = True
            for idx, family_name in enumerate(family_names):
                if family_name is not None:
                    if first_name:
                        first_name = False
                    else:
                        cur_query += " OR "
                    cur_query += "family-name:\"%s\"" % na(u"" + family_name)

            cur_query += ")"

        self.__last_query_done = ORCIDFinder.__api_url + quote(cur_query)

        return get_data(self.max_iteration, self.sec_to_wait, self.__last_query_done,
                        self.headers, self.timeout, self.repok, self.reper)

    def get_orcid_ids(self, doi_string, family_names=[]):
        result = []

        records = self.get_orcid_records(doi_string, family_names)
        if records is not None:
            rec_results = dg(records, ["orcid-search-results", "orcid-search-result"])
            if rec_results is not None:
                for record in rec_results:
                    orcid_profile = dg(record, ["orcid-profile"])
                    if orcid_profile is not None:
                        orcid_id = dg(orcid_profile, ["orcid-identifier", "path"])
                        if orcid_id is not None:
                            personal_details = dg(orcid_profile, ["orcid-bio", "personal-details"])
                            if personal_details is not None:
                                given_name = dg(personal_details, ["given-names", "value"])
                                family_name = dg(personal_details, ["family-name", "value"])
                                credit_name = dg(personal_details, ["credit-name", "value"])
                                other_names = dg(personal_details, ["other-names", "other-name", "value"])
                                result += [da({
                                    "orcid": orcid_id,
                                    "given": given_name,
                                    "family": family_name,
                                    "credit": credit_name,
                                    "other": other_names
                                })]

        return result




# Main
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("orcid_finder.py")
    arg_parser.add_argument("-c", "--conf", metavar="file_path", dest="c", required=True,
                            help="The configuration file to access the ORCID API.")
    arg_parser.add_argument("-d", "--doi", dest="doi", required=True,
                            help="The DOI of the paper to look for.")
    arg_parser.add_argument("-n", "--family_names", metavar="name", type=str, nargs="+", dest="n",
                            help="The family names of the possible authors of the paper "
                                 "indicated by the DOI.")
    args = arg_parser.parse_args()

    of = ORCIDFinder(args.c)
    print json.dumps(of.get_orcid_ids(args.doi, args.n), indent=4)

