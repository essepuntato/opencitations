#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import csv
import json
from support import normalise_id


class BibliographicReferenceStorer(object):
    def __init__(self, stored_file, reference_dir, error_dir):
        self.ref_dir = reference_dir
        self.err_dir = error_dir
        self.stored = set()
        self.last_ref_list = None
        self.error = False
        self.csv_file = stored_file
        if os.path.exists(self.csv_file):
            with open(self.csv_file) as f:
                csv_ids = csv.reader(f)
                for row in csv_ids:
                    self.stored.add(row[0])

    def is_any_stored(self, id_list):
        for string_id in id_list:
            if self.is_stored(string_id):
                return True
        return False

    def is_stored(self, string_id):
        if string_id is None:
            return False
        else:
            return string_id in self.stored

    def new_ref_list(self):
        self.last_ref_list = []
        self.error = False

    def add_reference(self, bib_entry=None, process_it=True,
                      string_doi=None, string_pmid=None, string_pmcid=None):
        if self.last_ref_list is not None:
            cur_reference = {}

            if bib_entry is not None:
                cur_reference["bibentry"] = bib_entry,
                cur_reference["process_entry"] = str(process_it)
            if string_doi is not None:
                cur_reference["doi"] = string_doi
            if string_pmid is not None:
                cur_reference["pmid"] = string_pmid
            if string_pmcid is not None:
                cur_reference["pmcid"] = string_pmcid

            if cur_reference:
                self.last_ref_list += [cur_reference]
            else:
                self.error = True

            return True
        else:
            return False

    def store(self, id_string, citing_doi=None, citing_pmid=None, citing_pmcid=None,
              curator=None, source_provider=None, source=None):
        if self.last_ref_list is not None:
            json_item = {
                "references": self.last_ref_list
            }
            if citing_doi is not None:
                json_item["doi"] = citing_doi
            if citing_pmid is not None:
                json_item["pmid"] = citing_pmid
            if citing_pmcid is not None:
                json_item["pmcid"] = citing_pmcid
            if curator is not None:
                json_item["curator"] = curator
            if source_provider is not None:
                json_item["source_provider"] = source_provider
            if source is not None:
                json_item["source"] = source

            # The error variable is True if a reference in the reference list has no information at all
            if self.error:
                new_file_path = self.err_dir + os.sep + normalise_id(id_string) + ".json"
            else:
                new_file_path = self.ref_dir + os.sep + normalise_id(id_string) + ".json"

            with open(new_file_path, "w") as f:
                json.dump(json_item, f)

            if id_string not in self.stored:
                with open(self.csv_file, "a") as name_f:
                    name_f.write(id_string + "\n")
                    self.stored.add(id_string)

            self.new_ref_list()
            return True

        return False

