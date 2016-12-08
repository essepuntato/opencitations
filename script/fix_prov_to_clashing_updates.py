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

import argparse
import os
import re
import rdflib
import shutil
import json
from reporter import Reporter
from rdflib import Graph, ConjunctiveGraph, URIRef, Literal
from rdflib.namespace import RDF, Namespace, RDFS
import csv
from support import find_paths
from datetime import datetime

context_path = "https://w3id.org/oc/corpus/context.json"
repok = Reporter(True, prefix="[fix_prov.py: INFO] ")
reperr = Reporter(True, prefix="[fix_prov.py: ERROR] ")
repok.new_article()
reperr.new_article()
context_json = {}
PROV = Namespace("http://www.w3.org/ns/prov#")
OCO = Namespace("https://w3id.org/oc/ontology/")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CITO = Namespace("http://purl.org/spar/cito/")
DATACITE = Namespace("http://purl.org/spar/datacite/")
FRBR = Namespace("http://purl.org/vocab/frbr/core#")
LITERAL = Namespace("http://www.essepuntato.it/2010/06/literalreification/")


def create_citation_update_part(cur_subj_g, is_f=True):
    query_part = u""
    is_first = is_f
    
    for s, p, o in cur_subj_g.triples((None, None, None)):
        if p == CITO.cites or p == FRBR.part:
            if not is_first:
                query_part += ". "
            is_first = False
            query_part += u"<%s> <%s> <%s> " % (str(s), str(p), str(o))
    return query_part


def create_identifier_update_part(cur_subj, cur_ids, is_f=True):
    query_part = u""
    is_first = is_f
    
    for cur_id in cur_ids:
        if not is_first:
            query_part += u". "
        is_first = False
        query_part += u"<%s> <%s> <%s> " % (str(cur_subj), DATACITE.hasIdentifier, cur_id)

    return query_part


def create_update_query(cur_subj_g, cur_subj, cur_ids=[], citations_exist=False):
    query_string = u"INSERT DATA { GRAPH <%s> { " % cur_subj_g.identifier
    if citations_exist:
        query_string += create_citation_update_part(cur_subj_g)
    if cur_ids:
        query_string += create_identifier_update_part(cur_subj, cur_ids, not citations_exist)

    return query_string + "} }"


def load(rdf_iri_string, tmp_dir=None):
    res_dir, rdf_file_path = \
        find_paths(rdf_iri_string, args.base + os.sep, "https://w3id.org/oc/corpus/", 10000, 1000)
    
    cur_graph = None

    if os.path.isfile(rdf_file_path):
        try:
            cur_graph = __load_graph(rdf_file_path)
        except IOError:
            if tmp_dir is not None:
                current_file_path = tmp_dir + os.sep + "tmp_rdf_file.rdf"
                shutil.copyfile(rdf_file_path, current_file_path)
                try:
                    cur_graph = __load_graph(current_file_path)
                except IOError as e:
                    reperr.add_sentence("[2] "
                                        "It was impossible to handle the format used for "
                                        "storing the file (stored in the temporary path) '%s'. "
                                        "Additional details: %s"
                                        % (current_file_path, str(e)))
                os.remove(current_file_path)
            else:
                reperr.add_sentence("[3] "
                                    "It was impossible to try to load the file from the "
                                    "temporary path '%s' since that has not been specified in "
                                    "advance" % rdf_file_path)
    else:
        reperr.add_sentence("[4] "
                            "The file specified ('%s') doesn't exist."
                            % rdf_file_path)

    return cur_graph


def __load_graph(file_p, tmp_dir=None):
    errors = ""
    current_graph = ConjunctiveGraph()

    if tmp_dir is not None:
        file_path = tmp_dir + os.sep + "tmp_rdf_file.rdf"
        shutil.copyfile(file_p, file_path)
    else:
        file_path = file_p

    try:
        with open(file_path) as f:
            json_ld_file = json.load(f)
            if isinstance(json_ld_file, dict):
                json_ld_file = [json_ld_file]

            for json_ld_resource in json_ld_file:
                # Trick to force the use of a pre-loaded context if the format
                # specified is JSON-LD
                cur_context = json_ld_resource["@context"]
                json_ld_resource["@context"] = context_json

                current_graph.parse(data=json.dumps(json_ld_resource), format="json-ld")
            
            return current_graph
    except Exception as e:
        errors = " | " + str(e)  # Try another format

    if tmp_dir is not None:
        os.remove(file_path)

    raise IOError("[1]", "It was impossible to handle the format used for storing the file '%s'%s" %
                  (file_path, errors))


def __store_graph(cur_g, rdf_iri_string, d_dir):
    try:
        res_dir, dest_file = \
            find_paths(rdf_iri_string, args.base + os.sep, "https://w3id.org/oc/corpus/", 10000, 1000)
        
        dest_dir = res_dir.replace(args.base + os.sep, d_dir + os.sep)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        cur_file = dest_file.replace(res_dir, dest_dir)
        if os.path.exists(cur_file):
            c_graph = __load_graph(cur_file)
        else:
            c_graph = ConjunctiveGraph()

        c_graph.remove_context(c_graph.get_context(cur_g.identifier))
        c_graph.addN([item + (cur_g.identifier,) for item in list(cur_g)])
        
        with open(dest_file.replace(res_dir, dest_dir), "w") as f:
            cur_json_ld = json.loads(c_graph.serialize(format="json-ld", context=context_json))
            cur_json_ld["@context"] = context_path
            json.dump(cur_json_ld, f, indent=4)
        # repok.add_sentence("File '%s' added." % cur_file)
        return dest_file
    except Exception as e:
        reperr.add_sentence("[5] It was impossible to store the RDF statements in %s. %s" %
                            (dest_file, str(e)))


def store(cur_g, entity_iri, d_dir):
    prov_base = entity_iri + "/prov/"
    se_graph = Graph(identifier=prov_base)
    ca_graph = Graph(identifier=prov_base)
    cr_graph = Graph(identifier=prov_base)
    
    for s, p, o in cur_g:
        if s.startswith(prov_base + "se"):
            se_graph.add((s, p, o))
        elif s.startswith(prov_base + "ca"):
            ca_graph.add((s, p, o))
        else:
            cr_graph.add((s, p, o))
    
    __store_graph(se_graph, prov_base + "se/1", d_dir)
    __store_graph(ca_graph, prov_base + "ca/1", d_dir)
    __store_graph(cr_graph, prov_base + "cr/1", d_dir)


def get_entity_graph(string_iri, cur_g, use_graph_iri=False):
    if "/prov/" in string_iri:
        graph_iri = string_iri.split("/prov/")[0] + "/prov/"
    else:
        graph_iri = "/".join(string_iri.split("/")[:-1]) + "/"
    
    result = Graph(identifier=graph_iri)
    
    cur_graph = cur_g.get_context(URIRef(graph_iri))
    string_to_check = "/".join(string_iri.split("/")[:-1]) + "/" if use_graph_iri else string_iri
    
    for s, p, o in cur_graph:
        if str(s).startswith(string_to_check):
            result.add((s, p, o))
    
    return result


def add_modification_info(prov_g, br_res, se_num, inv_time, update_query):
    prev_se_res = URIRef(br_res + "/prov/se/" + str(int(se_num) - 1))
    se_res = URIRef(br_res + "/prov/se/" + se_num)
    ca_res = URIRef(br_res + "/prov/ca/" + se_num)

    # se
    prov_g.add((prev_se_res, PROV.invalidatedAtTime, inv_time))
    prov_g.add((prev_se_res, PROV.wasInvalidatedBy, ca_res))
    prov_g.add((se_res, OCO.hasUpdateQuery, Literal(update_query)))
    prov_g.add((se_res, PROV.wasDerivedFrom, prev_se_res))


def add_creation_info(prov_g, br_res, se_num, gen_time, cr_start, description,
                      curator_id, source_id, activity_type):
    se_res = URIRef(br_res + "/prov/se/" + se_num)
    ca_res = URIRef(br_res + "/prov/ca/" + se_num)

    br_num = str(br_res).split("/")[-1]
    cr_curator_num = cr_start
    cr_source_num = str(int(cr_start) + 1)

    cr_curator_res = URIRef(br_res + "/prov/cr/" + cr_curator_num)
    cr_source_res = URIRef(br_res + "/prov/cr/" + cr_source_num)
    
    # se
    prov_g.add((se_res, RDF.type, PROV.Entity))
    prov_g.add((se_res, RDFS.label, Literal(
        "snapshot of entity metadata %s related to bibliographic resource %s [se/%s -> br/%s]" %
        (se_num, br_num, se_num, br_num))))
    prov_g.add((se_res, PROV.specializationOf, br_res))
    prov_g.add((se_res, PROV.generatedAtTime, gen_time))
    prov_g.add((se_res, PROV.wasGeneratedBy, ca_res))
    
    # ca
    prov_g.add((ca_res, RDF.type, PROV.Activity))
    prov_g.add((ca_res, RDF.type, activity_type))
    prov_g.add((ca_res, RDFS.label, Literal(
        "curatorial activity %s related to bibliographic resource %s [ca/%s -> br/%s]" %
        (se_num, br_num, se_num, br_num))))
    prov_g.add((ca_res, DCTERMS.description,
                Literal("The entity '%s' has been %s." % (br_res, description))))
    prov_g.add((ca_res, PROV.qualifiedAssociation, cr_curator_res))
    prov_g.add((ca_res, PROV.qualifiedAssociation, cr_source_res))
    
    # cr
    prov_g.add((cr_curator_res, RDF.type, PROV.Association))
    prov_g.add((cr_curator_res, RDFS.label, Literal(
        "curatorial role %s related to bibliographic resource %s [cr/%s -> br/%s]" %
        (cr_curator_num, br_num, cr_curator_num, br_num))))
    prov_g.add((cr_curator_res, PROV.agent, URIRef("https://w3id.org/oc/corpus/prov/pa/" + curator_id)))
    prov_g.add((cr_curator_res, PROV.hadRole, URIRef("https://w3id.org/oc/ontology/occ-curator")))
    prov_g.add((cr_source_res, RDF.type, PROV.Association))
    prov_g.add((cr_source_res, RDFS.label, Literal(
        "curatorial role %s related to bibliographic resource %s [cr/%s -> br/%s]" %
        (cr_source_num, br_num, cr_source_num, br_num))))
    prov_g.add((cr_source_res, PROV.agent, URIRef("https://w3id.org/oc/corpus/prov/pa/" + source_id)))
    prov_g.add((cr_source_res, PROV.hadRole,
                URIRef("https://w3id.org/oc/ontology/source-metadata-provider")))
    
    return se_res


def get_source(all_sources, sources_by_date, cur_date, source_iri):
    if cur_date in sources_by_date:
        for source in sources_by_date[cur_date]:
            if source in all_sources:
                return source
    
    # Get the source not included by ids
    not_included = set(all_sources) - set.union(*sources_by_date.values())
    if len(not_included) == 1:
        return not_included.pop()
    elif len(not_included) > 1:
        reperr.add_sentence("Too many context for '%s': %s" % (source_iri, list(not_included)))
    else:
        reperr.add_sentence("No context for '%s'" % source_iri)

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("fix_prov.py",
                                         description="This script fixes the bug of having multiple "
                                                     "creation activity for the same resource.")
    arg_parser.add_argument("-i", "--input_file", dest="input", required=True,
                            help="The file containing all the provenance entities that must be modified.")
    arg_parser.add_argument("-o", "--out_dir", dest="dest_dir", required=True,
                            help="The directory where to store data.")
    arg_parser.add_argument("-b", "--corpus_base_dir", dest="base", required=True,
                            help="The base dir of the corpus.")
    arg_parser.add_argument("-t", "--tmp_dir", dest="tmp_dir",
                            help="The directory for easing the RDF loading.")
    arg_parser.add_argument("-c", "--context", dest="context", required=True,
                            help="The JSON-LD context to use.")
    arg_parser.add_argument("--id", dest="id", default=False, action="store_true",
                            help="Get the id names only.")

    args = arg_parser.parse_args()
    
    repok.new_article()
    reperr.new_article()
    result = set()
    last_res = None
    
    try:
        with open(args.context) as f, open(args.input) as g:
            context_json = json.load(f)
            csv_reader = csv.reader(g)
            for res, n_mod, m_type in csv_reader:
                last_res = res
                prov_entity = URIRef(res)
                
                if args.id:
                    prov_g = load(res)
                    prov_entity_g = get_entity_graph(res, prov_g)
                    spec_entity = prov_entity_g.value(prov_entity, PROV.specializationOf)
                    res_g = load(str(spec_entity))
                    res_entity_g = get_entity_graph(spec_entity, res_g)
                    for id_entity in [o for s, p, o in list(
                            res_entity_g.triples((spec_entity, DATACITE.hasIdentifier, None)))]:
                        rdf_dir, rdf_file_path = find_paths(
                            id_entity, args.base + os.sep, "https://w3id.org/oc/corpus/", 10000, 1000)
                        result.add(rdf_file_path)
                else:
                    repok.add_sentence("Processing '%s'" % res)
                    
                    prov_g = load(res)
                    spec_entity_iri = res.split("/prov/")[0]
                    prov_entity_g = get_entity_graph(res, prov_g, True)
        
                    generation_dates = [o for s, p, o in
                                        list(prov_entity_g.triples(
                                            (None, PROV.generatedAtTime, None)))]
                    sources = [o for s, p, o in
                               list(prov_entity_g.triples((None, PROV.hadPrimarySource, None)))]
                    
                    # Get all identifiers creation dates and sources
                    spec_entity = URIRef(spec_entity_iri)
                    res_g = load(str(spec_entity))
                    res_entity_g = get_entity_graph(spec_entity, res_g)
                    sources_per_date = {}
                    ids_per_date = {}
                    for id_entity in [o for s, p, o in list(
                            res_entity_g.triples((spec_entity, DATACITE.hasIdentifier, None)))]:
                        id_iri = str(id_entity)
                        id_snap_entity = URIRef(id_iri + "/prov/se/1")
                        id_snap_g = get_entity_graph(id_snap_entity, load(str(id_snap_entity), True))
                        new_generation_date = id_snap_g.value(id_snap_entity, PROV.generatedAtTime)
                        new_source = id_snap_g.value(id_snap_entity, PROV.hadPrimarySource)
                        new_id_string = id_snap_g.value(id_snap_entity, LITERAL.hasLiteralValue)
                        if new_generation_date not in sources_per_date:
                            sources_per_date[new_generation_date] = set()
                        sources_per_date[new_generation_date].add(new_source)
                        generation_dates += [new_generation_date]
                        
                        if new_generation_date not in ids_per_date:
                            ids_per_date[new_generation_date] = []
                        ids_per_date[new_generation_date] += [id_iri]
                    
                    generation_dates = sorted(list(set(generation_dates)))
                    
                    new_prov = Graph(identifier=str(spec_entity) + "/prov/")
                    for idx, generation_date in enumerate(generation_dates, 1):
                        description = None
                        update_query = None
                        
                        if idx == 1:
                            description = "created"
                        elif "[ID]" in m_type:
                            description = "extended with new identifiers"
                            update_query = create_update_query(
                                res_entity_g, spec_entity,
                                ids_per_date[generation_date] if generation_date in ids_per_date else [],
                                False)
                        elif "[CIT]" in m_type:
                            description = "extended with citation data"
                            update_query = create_update_query(
                                res_entity_g, spec_entity, [], True)
                        elif "[CIT+ID]" in m_type:
                            description = "extended with citation data and new identifiers"
                            update_query = create_update_query(
                                res_entity_g, spec_entity,
                                ids_per_date[generation_date] if generation_date in ids_per_date else [],
                                True)
                        else:
                            reperr.add_sentence("No type for '%s'" % res)
                        
                        if description is not None:
                            cur_se = add_creation_info(new_prov, spec_entity, str(idx), generation_date,
                                                       str((idx - 1) * 2 + 1), description, "1", "2",
                                                       PROV.Create if idx == 1 else PROV.Modify)
                            if idx > 1:
                                add_modification_info(new_prov, spec_entity, str(idx),
                                                      generation_date, update_query)
    
                            se_source = get_source(
                                sources, sources_per_date, generation_date, str(cur_se))
                            if se_source is not None:
                                new_prov.add((cur_se, PROV.hadPrimarySource, se_source))
    
                    store(new_prov, str(spec_entity), args.dest_dir)
    except Exception as e:
        reperr.add_sentence("Last res: %s. %s" % (last_res, e))
        
    if result:
        for it in result:
            print it
    
    if not reperr.is_empty():
        reperr.write_file("fix_prov_to_clashing_updates_%s_.rep.err.txt" %
                          datetime.now().strftime('%Y_%m_%dT%H_%M_%S'))