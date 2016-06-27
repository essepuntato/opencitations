# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

from xml.sax import SAXParseException
import web
import rdflib
import os
import shutil
import re
import urllib
from rdflib import RDFS

class LinkedDataDirector(object):
    __extensions = (".rdf", ".ttl", ".json", ".html")
    __rdfxml = ("application/rdf+xml",)
    __turtle = ("text/turtle", "text/n3")
    __jsonld = ("application/ld+json", "application/json")
    __rdfs_label = "http://www.w3.org/2000/01/rdf-schema#label"
    __rdfs_comment = "http://www.w3.org/2000/01/rdf-schema#comment"
    __rdf_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    __entityiri = "__entityiri"

    def __init__(self, file_basepath, baseurl, label_conf=None, tmp_dir=None):
        self.basepath = file_basepath
        self.baseurl = baseurl
        self.tmp_dir = tmp_dir
        self.render = web.template.render(file_basepath)
        if label_conf is None:
            self.label_conf = {}
        else:
            self.label_conf = label_conf
        if self.__rdfs_label not in self.label_conf:
            self.label_conf[self.__rdfs_label] = "label"
        if self.__rdfs_comment not in self.label_conf:
            self.label_conf[self.__rdfs_comment] = "comment"
        if self.__rdf_type not in self.label_conf:
            self.label_conf[self.__rdf_type] = "type"

    def log(self):
        if self.logger is not None:
            self.logger.mes()

    def get_render(self):
        return self.render

    def serialise(self, cur_graph, format):
        final_graph = rdflib.Graph()

        for ns in cur_graph.namespaces():
            final_graph.namespace_manager.bind(ns[0], ns[1])

        for s, p, o in cur_graph.triples((None, None, None)):
            s_str = str(s)
            if s_str.startswith("file://"):
                s_str = ""
            final_graph.add((rdflib.URIRef(s_str), p, o))
        return final_graph.serialize(format=format)

    def redirect(self, url):
        if url.endswith(self.__extensions):
            return self.get_representation(url)
        else:
            content_type = web.ctx.env.get("HTTP_ACCEPT")
            if content_type:
                for accept_block in content_type.split(";")[::2]:
                    accept_types = accept_block.split(",")

                    if any(mime in accept_types for mime in self.__rdfxml):
                        raise web.seeother(self.baseurl + url + ".rdf")
                    elif any(mime in accept_types for mime in self.__turtle):
                        raise web.seeother(self.baseurl + url + ".ttl")
                    elif any(mime in accept_types for mime in self.__jsonld):
                        raise web.seeother(self.baseurl + url + ".json")
                    else:  # HTML
                        raise web.seeother(self.baseurl + url + ".html")

    def get_representation(self, url):
        local_file = ".".join(url.split(".")[:-1])

        if "/" in local_file:
            slash_split = local_file.split("/")
            cur_dir = "/".join(slash_split[:-1])
            cur_name = slash_split[-1]
        else:
            cur_dir = "."
            cur_name = local_file

        cur_file_ex = None

        cur_full_dir = self.basepath + os.sep + cur_dir
        if os.path.isdir(cur_full_dir):
            for item in os.listdir(self.basepath + os.sep + cur_dir):
                item_no_extension = re.sub("\.[^.]+$", "", item)
                if item_no_extension == cur_name and item.endswith(self.__extensions):
                    cur_file_ex = item

            if cur_file_ex is not None:
                cur_graph = self.load_graph(
                    self.basepath + os.sep + cur_dir + os.sep + cur_file_ex,
                    self.tmp_dir)
                if len(cur_graph):
                    if url.endswith(".rdf"):
                        return self.serialise(cur_graph, "xml")
                    elif url.endswith(".ttl"):
                        return self.serialise(cur_graph, "turtle")
                    elif url.endswith(".json"):
                        return self.serialise(cur_graph, "json-ld")
                    elif url.endswith(".html"):
                        # {
                        #   "__entityiri": "http://..." ,
                        #   "label": ["donald", "duck"] ,
                        #   "type": [
                        #       { "__entityiri": "http://...", "label": ["daisy", "duck"] } , ...]
                        # }
                        cur_data = {}
                        for s, p, o in cur_graph.triples((None, None, None)):
                            str_s = str(s)
                            # If the starting URL is not a "current document entity" proceed
                            if not str_s.startswith("file://"):
                                cur_data[self.__entityiri] = str_s

                                str_p = str(p)
                                if str_p in self.label_conf:
                                    str_p = self.label_conf[str_p]

                                    str_o = str(o)
                                    label_o = None
                                    if str_o in self.label_conf:
                                        label_o = self.label_conf[str_o]

                                    if str_p not in cur_data:
                                        cur_data[str_p] = []

                                    has_label = False
                                    if isinstance(o, rdflib.URIRef):
                                        cur_entity = {self.__entityiri: str_o}
                                        if str_o.startswith(self.baseurl):

                                        # The following 'if' is for internal testing
                                        # (comment the above one if needed)
                                        # if str_o.startswith(
                                        #   "http://www.sparontologies.net/mediatype/"):
                                            try:
                                                # The following two lines are for internal testing
                                                # (comment the above one if needed)
                                                external_graph = self.load_graph(
                                                    self.basepath + os.sep +
                                                    urllib.unquote_plus(
                                                        str_o.replace(self.baseurl, "")) +
                                                    # The following line is for internal testing
                                                    # (comment the above one if needed)
                                                        # str_o.replace(
                                                        #     "http://www.sparontologies.net/mediatype/", "")) +
                                                    ".rdf", self.tmp_dir)
                                                is_first = True
                                                for s2, p2, o2 in \
                                                        external_graph.triples((o, RDFS.label, None)):
                                                    has_label = True
                                                    if is_first:
                                                         cur_entity[self.label_conf[self.__rdfs_label]] = []
                                                    cur_entity[self.label_conf[self.__rdfs_label]] += \
                                                        [str(o2)]
                                            except Exception as e:
                                                pass  # do not add anything

                                        if not has_label and label_o is not None:
                                            cur_entity[self.label_conf[self.__rdfs_label]] = [label_o]

                                        cur_data[str_p] += [cur_entity]
                                    else:
                                        cur_data[str_p] += [str_o]

                                    cur_data[str_p].sort()
                        return self.render.ldd(cur_data)

    def load_graph(self, file_path, temp_dir_for_rdf_loading=None):
        current_graph = None

        if re.match("https?://", file_path) or os.path.isfile(file_path):
            try:
                current_graph = LinkedDataDirector.__load_graph(file_path)
            except IOError:
                if temp_dir_for_rdf_loading is not None:
                    current_file_path = temp_dir_for_rdf_loading + os.sep + "tmp_rdf_file.rdf"
                    shutil.copyfile(file_path, current_file_path)
                    try:
                        current_graph = LinkedDataDirector.__load_graph(current_file_path)
                        os.remove(current_file_path)
                    except Exception as e:
                        os.remove(current_file_path)
                        raise e
        else:
            raise IOError("1", "The file specified doesn't exist.")

        return current_graph

    @staticmethod
    def __load_graph(file_path):
        current_graph = rdflib.Graph()

        try:
            current_graph.load(file_path)
        except SAXParseException:
            current_graph.load(file_path, format="turtle")

        return current_graph
