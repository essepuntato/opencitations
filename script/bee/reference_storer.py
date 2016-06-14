#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import csv
import json


class BibliographicReferenceStorer(object):
    def __init__(self, stored_file, reference_dir):
        self.ref_dir = reference_dir
        self.stored = set()
        self.last_ref_list = None
        self.csv_file = stored_file
        if os.path.exists(self.csv_file):
            with open(self.csv_file) as f:
                csv_ids = csv.reader(f)
                for row in csv_ids:
                    self.stored.add(row[0])

    def is_stored(self, string_id):
        return string_id in self.stored

    def new_ref_list(self):
        self.last_ref_list = []

    def add_reference(self, bib_entry, string_doi=None):
        if self.last_ref_list is not None:
            cur_reference = {
                "bibentry": bib_entry
            }
            if string_doi is not None:
                cur_reference["doi"] = string_doi

            self.last_ref_list += [cur_reference]
            return True
        else:
            return False

    def store(self, id_string, citing_doi, curator=None, source_provider=None, source=None):
        if self.last_ref_list is not None:
            json_item = {
                "doi": citing_doi,
                "references": self.last_ref_list
            }
            if curator is not None:
                json_item["curator"] = curator
            if source_provider is not None:
                json_item["source_provider"] = source_provider
            if source is not None:
                json_item["source"] = source

            new_file_path = self.ref_dir + os.sep + id_string + ".json"
            with open(new_file_path, "w") as f:
                json.dump(json_item, f)

            if id_string not in self.stored:
                with open(self.csv_file, "a") as name_f:
                    name_f.write(id_string + "\n")
                    self.stored.add(id_string)

            return True

        return False

