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
import json


class LinkedDataDirector(object):
    __extensions = (".rdf", ".ttl", ".json", ".html")
    __rdfxml = ("application/rdf+xml",)
    __turtle = ("text/turtle", "text/n3")
    __jsonld = ("application/ld+json", "application/json")
    __rdfs_label = "http://www.w3.org/2000/01/rdf-schema#label"
    __rdfs_comment = "http://www.w3.org/2000/01/rdf-schema#comment"
    __rdf_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    __entityiri = "__entityiri"

    def __init__(self, file_basepath, template_path, baseurl, jsonld_context_path,
                 label_conf=None, tmp_dir=None):
        self.basepath = file_basepath
        self.baseurl = baseurl

        with open(jsonld_context_path) as f:
            self.jsonld_context = json.load(f)["@context"]

        self.tmp_dir = tmp_dir
        self.render = web.template.render(template_path)
        self.label_conf = self.__generate_from_context()
        if label_conf is not None:
            self.label_conf.update(label_conf)

        self.label_iri = self.__generate_from_label_conf()

        if self.__rdfs_label not in self.label_conf:
            self.label_conf[self.__rdfs_label] = "label"
        if self.__rdfs_comment not in self.label_conf:
            self.label_conf[self.__rdfs_comment] = "comment"
        if self.__rdf_type not in self.label_conf:
            self.label_conf[self.__rdf_type] = "type"

    def __generate_from_label_conf(self):
        result = {}

        for key in self.label_conf:
            result[self.label_conf[key]] = key

        return result

    def __generate_from_context(self):
        result = {}

        http_items = {}
        for key in self.jsonld_context:
            value = self.jsonld_context[key]
            if isinstance(value, dict):
                value = value["@id"]
            if value.startswith("http"):
                http_items[key] = value
                result[value] = key.replace("_", " ")

        for key in self.jsonld_context:
            value = self.jsonld_context[key]
            if isinstance(value, dict):
                value = value["@id"]
            if not value.startswith("http"):
                while True:
                    split_value = value.split(":", 1)
                    if len(split_value) > 1:
                        pref = split_value[0]
                        if pref in http_items.keys():
                            value = value.replace(pref + ":", http_items[pref])
                        else:
                            break
                    else:
                        break
                result[value] = key.replace("_", " ")

        return result

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
        if url is None:
            raise web.seeother(self.baseurl + "index")
        elif url.endswith(self.__extensions):
            cur_extension = "." + url.split(".")[-1]
            no_extension = url.replace(cur_extension, "")
            if no_extension == "" or no_extension.endswith("/"):
                raise web.seeother(self.baseurl + no_extension + "index" + cur_extension)
            else:
                return self.get_representation(url)
        elif url.endswith("/prov/"):
            pass  # TODO: it must be handled somehow
        else:
            content_type = web.ctx.env.get("HTTP_ACCEPT")
            if content_type:
                for accept_block in content_type.split(";")[::2]:
                    accept_types = accept_block.split(",")

                    if url.endswith("/"):
                        cur_url = url + "index"
                    else:
                        cur_url = url

                    if any(mime in accept_types for mime in self.__rdfxml):
                        raise web.seeother(self.baseurl + cur_url + ".rdf")
                    elif any(mime in accept_types for mime in self.__turtle):
                        raise web.seeother(self.baseurl + cur_url + ".ttl")
                    elif any(mime in accept_types for mime in self.__jsonld):
                        raise web.seeother(self.baseurl + cur_url + ".json")
                    else:  # HTML
                        raise web.seeother(self.baseurl + cur_url + ".html")

    @staticmethod
    def __add_license(g):
        g.add((
            rdflib.URIRef(""),
            rdflib.URIRef("http://purl.org/dc/terms/license"),
            rdflib.URIRef("https://creativecommons.org/publicdomain/zero/1.0/legalcode")))

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
            for item in os.listdir(cur_full_dir):
                item_no_extension = re.sub("\.[^.]+$", "", item)
                if item_no_extension == cur_name and item.endswith(self.__extensions):
                    cur_file_ex = item

            cur_file_path = cur_full_dir + os.sep + cur_name + ".json"
            if os.path.exists(cur_file_path):
                cur_graph = self.load_graph(cur_file_path, self.tmp_dir)
                if len(cur_graph):
                    if url.endswith(".rdf"):
                        LinkedDataDirector.__add_license(cur_graph)
                        return self.serialise(cur_graph, "xml")
                    elif url.endswith(".ttl"):
                        LinkedDataDirector.__add_license(cur_graph)
                        return self.serialise(cur_graph, "turtle")
                    elif url.endswith(".json"):
                        LinkedDataDirector.__add_license(cur_graph)
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

                                    str_o = unicode(o)
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
                                                         cur_entity[
                                                             self.label_conf[self.__rdfs_label]] = []
                                                    cur_entity[
                                                        self.label_conf[self.__rdfs_label]] += [str(o2)]
                                            except Exception as e:
                                                pass  # do not add anything

                                        if not has_label and label_o is not None:
                                            cur_entity[self.label_conf[self.__rdfs_label]] = [label_o]

                                        cur_data[str_p] += [cur_entity]
                                    else:
                                        cur_data[str_p] += [str_o]

                                    cur_data[str_p].sort()
                        return self.render.ldd(cur_data, sorted(cur_data.keys()), self.label_iri)

    def load_graph(self, file_path, temp_dir_for_rdf_loading=None):
        current_graph = None

        if re.match("https?://", file_path) or os.path.isfile(file_path):
            try:
                current_graph = self.__load_graph(file_path)
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

    def __load_graph(self, file_path):
        current_graph = None

        with open(file_path) as f:
            json_ld_file = json.load(f)
            # Trick to force the use of a pre-loaded context
            json_ld_file["@context"] = self.jsonld_context

            # Note: the loading of the existing graph will work correctly if and only if
            # the IRI of the graph is specified as identifier in the constructor
            if "@graph" in json_ld_file and "iri" in json_ld_file:
                graph_id = json_ld_file["iri"]
                if re.search("^.+:", graph_id) is not None:
                    cur_prefix = graph_id.split(":", 1)[0]
                    if cur_prefix in self.jsonld_context:
                        graph_id = graph_id.replace(cur_prefix + ":", self.jsonld_context[cur_prefix])
            else:
                graph_id = None
            current_graph = rdflib.Graph(identifier=graph_id)

            current_graph.parse(data=json.dumps(json_ld_file), format="json-ld")

        return current_graph
