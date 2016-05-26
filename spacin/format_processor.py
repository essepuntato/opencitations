#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'
from urllib import quote
import re
from reporter import Reporter
from graphlib import GraphSet


class FormatProcessor(object):
    doi_pattern = "[^A-z0-9\.]([0-9]+\.[0-9]+(\.[0-9]+)*/[^%\"# \?<>{}\^\[\]`\|\\\+]+)"
    http_pattern = "(https?://([A-z]|[0-9]|%|&|\?|/|\.|_|~|-|:)+)"

    """This class is the abstract one for any kind of processors."""
    def __init__(self, base_iri, context_base, info_dir, entries, agent_id=None):
        self.citing_id = entries["citing_id"]
        self.curator = entries["curator"]
        if "source" in entries:
            self.source = entries["source"]
        else:
            self.source = None
        if "source_provider" in entries:
            self.source_provider = entries["source_provider"]
        else:
            self.source_provider = None

        self.entries = entries["references"]
        self.name = "SPACIN " + self.__class__.__name__
        self.g_set = GraphSet(base_iri, context_base, info_dir)
        self.id = agent_id
        self.reperr = Reporter(True)
        self.reperr.new_article()
        self.repok = Reporter(True)
        self.repok.new_article()

    def process(self):
        pass  # Implemented in the subclasses

    def graph_set(self):
        return self.g_set

    def graphs(self):
        return self.g_set.graphs()

    def message(self, mess):
        return "\n[%s] %s" % (self.name, mess)

    @staticmethod
    def clean_entry(entry):
        return quote(re.sub(":", ",", entry).encode("utf-8"))

    @staticmethod
    def extract_data(string, pattern):
        result = re.search(pattern, string)
        if result:
            return result.group(1)

    @staticmethod
    def extract_doi(string):
        result = FormatProcessor.extract_data(string, FormatProcessor.doi_pattern)
        if result:
            result = re.sub("(\.|,)?$", "", result)

        return result

    @staticmethod
    def extract_url(string):
        result = FormatProcessor.extract_data(string, FormatProcessor.http_pattern)
        if result:
            result = re.sub("\\\\", "", re.sub("/?\.?$", "", result))

        return result
