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
from rdflib.namespace import RDF, Namespace
import glob

context_path = "https://w3id.org/oc/corpus/context.json"
context_json = {}
repok = Reporter(True, prefix="[organize_files.py: INFO] ")
reperr = Reporter(True, prefix="[organize_files.py: ERROR] ")
repok.new_article()
reperr.new_article()


def load(cur_graph, rdf_file_path, tmp_dir=None):
    if os.path.isfile(rdf_file_path):
        try:
            cur_graph = __load_graph(cur_graph, rdf_file_path)
        except IOError:
            if tmp_dir is not None:
                current_file_path = tmp_dir + os.sep + "tmp_rdf_file.rdf"
                shutil.copyfile(rdf_file_path, current_file_path)
                try:
                    cur_graph = __load_graph(cur_graph, current_file_path)
                except IOError as e:
                    reperr.add_sentence("It was impossible to handle the format used for "
                                        "storing the file (stored in the temporary path) '%s'. "
                                        "Additional details: %s"
                                        % (current_file_path, str(e)))
                os.remove(current_file_path)
            else:
                reperr.add_sentence("It was impossible to try to load the file from the "
                                    "temporary path '%s' since that has not been specified in "
                                    "advance" % rdf_file_path)
    else:
        reperr.add_sentence("The file specified ('%s') doesn't exist."
                            % rdf_file_path)

    return cur_graph


def __load_graph(current_graph, file_path):
    errors = ""

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

    raise IOError("It was impossible to handle the format used for storing the file '%s'%s" %
                  (file_path, errors))


def do_file_exist(cur_dir):
    try:
        glob.iglob(cur_dir + os.sep + "[0-9]*.json").next()
        return True
    except:
        return False


def store(cur_g, prov_gs, dest_file, dest_prov_files, files_to_remove, dirs_to_remove):
    if cur_g is not None and len(cur_g):
        try:
            cur_json_ld = json.loads(cur_g.serialize(format="json-ld", context=context_json))
            cur_json_ld["@context"] = context_path
            with open(dest_file, "w") as f:
                json.dump(cur_json_ld, f, indent=4)
            repok.add_sentence("File '%s' added." % dest_file)
        except Exception as e:
            reperr.add_sentence("It was impossible to store the RDF statements in %s. %s" %
                                (dest_file, str(e)))
            reperr.add_sentence("Files not changed:\n\t" + "\n\t".join(files_to_remove))
            return False

        for file_to_remove in files_to_remove:
            try:
                os.remove(file_to_remove)
            except Exception as e:
                reperr.add_sentence("It was impossible to remove an existing file (%s) "
                                    "already copied in the global one. %s" %
                                    (file_to_remove, str(e)))
        final_file = dest_file.replace("n_", "")
        shutil.move(dest_file, final_file)

        cur_dir = os.path.dirname(dest_prov_files[0])
        for idx, prov_g in enumerate(prov_gs):
            if len(prov_g):
                cur_prov_file = dest_prov_files[idx]
                try:
                    cur_json_ld = json.loads(prov_g.serialize(format="json-ld", context=context_json))
                    cur_json_ld["@context"] = context_path
                    if not os.path.exists(cur_dir):
                        os.makedirs(cur_dir)
                    with open(cur_prov_file, "w") as f:
                        json.dump(cur_json_ld, f, indent=4)
                    repok.add_sentence("Provenance file '%s' added." % cur_prov_file)
                except Exception as e:
                    reperr.add_sentence("It was impossible to store the RDF statements in %s. %s" %
                                        (cur_prov_file, str(e)))
                    reperr.add_sentence("Files not changed:\n\t" + "\n\t".join(dirs_to_remove))
                    return False

        for dir_to_remove in dirs_to_remove:
            try:
                shutil.rmtree(dir_to_remove)
            except Exception as e:
                reperr.add_sentence("It was impossible to remove existing prov files (%s) "
                                    "already copied in the global one. %s" %
                                    (dir_to_remove, str(e)))

        if os.path.exists(cur_dir):
            final_dir = cur_dir.replace("n_", "")
            os.renames(cur_dir, final_dir)

    return True


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("organize_files.py",
                                         description="This script organizes the files into directories "
                                                     "and bigger files.")
    arg_parser.add_argument("-i", "--input", dest="input", required=True,
                            help="The directory containing the data to organize.")
    arg_parser.add_argument("-ds", "--dir_split", dest="dir_split", required=True,
                            help="The max number of resources a directory can contain.")
    arg_parser.add_argument("-fs", "--file_split", dest="file_split",
                            help="The max number of resources a file can contain.")
    arg_parser.add_argument("-t", "--tmp_dir", dest="tmp_dir",
                            help="The directory for easing the RDF loading.")
    arg_parser.add_argument("-c", "--context", dest="context", required=True,
                            help="The JSON-LD context to use.")

    args = arg_parser.parse_args()

    with open(args.context) as f:
        context_json = json.load(f)

    if do_file_exist(args.input):
        res_count = 0
        dir_count = 0
        new_dir = None
        repok.add_sentence("Organize all files in directory each containing at "
                           "most %s resources" % args.dir_split)
        new_dirs = []
        new_files = []
        while True:
            res_count += 1
            if res_count > dir_count:
                dir_count += long(args.dir_split)
                new_dir = args.input + os.sep + "n_" + str(dir_count)
                new_dirs += [new_dir]
            src_dir = args.input + os.sep + str(res_count)
            dst_dir = new_dir + os.sep + str(res_count)
            src_file = src_dir + ".json"
            if os.path.exists(src_file):
                try:
                    if os.path.exists(src_dir):
                        os.renames(src_dir, dst_dir)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    shutil.move(src_file, new_dir)
                except Exception:
                    if not do_file_exist(args.input):
                        break
            elif not do_file_exist(args.input):
                break

        for new_dir in new_dirs:
            os.renames(new_dir, new_dir.replace("n_", ""))

    if args.file_split is not None:
        repok.add_sentence("Merge files in bigger ones (each file will contains "
                           "at most %s resources)" % args.file_split)
        for cur_dir in glob.iglob(args.input + os.sep + "[0-9]*/"):
            last_res_id = long(re.sub("^.+/([0-9]+)/?$", "\\1", cur_dir))
            file_count = last_res_id - long(args.dir_split)
            res_count = file_count
            file_done = None
            dir_done = None
            new_file = None
            new_prov_files = None
            cur_g = None
            cur_prov_se = None
            cur_prov_ca = None
            cur_prov_cr = None
            while True:
                if res_count < last_res_id:
                    res_count += 1
                    if res_count > file_count:
                        # Store new graph if existing
                        store(cur_g, [cur_prov_se, cur_prov_ca, cur_prov_cr],
                              new_file, new_prov_files, file_done, dir_done)

                        # Update variables
                        file_done = []
                        dir_done = []
                        file_count += long(args.file_split)
                        cur_g = ConjunctiveGraph()
                        cur_prov_se = ConjunctiveGraph()
                        cur_prov_ca = ConjunctiveGraph()
                        cur_prov_cr = ConjunctiveGraph()
                        new_dir = cur_dir + os.sep + "n_" + str(file_count)
                        new_file = new_dir + ".json"
                        new_prov_files = [
                            new_dir + os.sep + "prov/se.json",
                            new_dir + os.sep + "prov/ca.json",
                            new_dir + os.sep + "prov/cr.json"]


                    base_dir = cur_dir + os.sep + str(res_count)
                    cur_file = base_dir + ".json"
                    if os.path.exists(cur_file):
                        # Load resource data
                        cur_g = load(cur_g, cur_file, args.tmp_dir)
                        file_done += [cur_file]

                        if os.path.exists(base_dir):
                            dir_done += [base_dir]

                            # Load provenance data
                            base_prov_dir = base_dir + os.sep + "prov" + os.sep
                            for cur_prov_file in \
                                    glob.iglob(base_prov_dir + "se" + os.sep + "[0-9]*.json"):
                                cur_prov_se = load(cur_prov_se, cur_prov_file, args.tmp_dir)
                            for cur_prov_file in \
                                    glob.iglob(base_prov_dir + "ca" + os.sep + "[0-9]*.json"):
                                cur_prov_ca = load(cur_prov_ca, cur_prov_file, args.tmp_dir)
                            for cur_prov_file in \
                                    glob.iglob(base_prov_dir + "cr" + os.sep + "[0-9]*.json"):
                                cur_prov_cr = load(cur_prov_cr, cur_prov_file, args.tmp_dir)
                else:
                    # Store the last graph and process another directory
                    store(cur_g, [cur_prov_se, cur_prov_ca, cur_prov_cr],
                          new_file, new_prov_files, file_done, dir_done)
                    break

    # repok.write_file("organize_files.rep.ok.txt")
    reperr.write_file("organize_files.rep.%s.err.txt" % re.sub("[\.%s/]" % os.sep, "_", args.input))