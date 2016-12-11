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
from crossref_processor import CrossrefProcessor
from conf_spacin import *
from stopper import Stopper
from support import move_file
from resource_finder import ResourceFinder
from orcid_finder import ORCIDFinder
from graphlib import ProvSet
from storer import Storer
import os
import traceback
from dataset_handler import DatasetHandler
from datetime import datetime
import re
import shutil

start_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
error = False
last_file = None
s = Stopper(reference_dir)
try:
    for cur_dir, cur_subdir, cur_files in os.walk(reference_dir):
        if s.can_proceed():
            for cur_file in sorted(cur_files):
                if s.can_proceed():
                    if cur_file.endswith(".json"):
                        cur_file_path = cur_dir + os.sep + cur_file
                        cur_local_dir_path = re.sub("^([0-9]+-[0-9]+-[0-9]+-[0-9]+).+$", "\\1", cur_file)
                        with open(cur_file_path) as fp:
                            last_file = cur_file_path
                            last_local_dir = cur_local_dir_path
                            print "\n\nProcess file '%s'\n" % cur_file_path
                            json_object = json.load(fp)
                            crp = CrossrefProcessor(base_iri, context_path, info_dir, json_object,
                                                    ResourceFinder(ts_url=triplestore_url),
                                                    ORCIDFinder(orcid_conf_path))
                            result = crp.process()
                            if result is not None:
                                prov = ProvSet(result, base_iri, context_path, info_dir,
                                               ResourceFinder(base_dir=base_dir, base_iri=base_iri,
                                                              tmp_dir=temp_dir_for_rdf_loading,
                                                              context_map=
                                                              {context_path: context_file_path}))
                                prov.generate_provenance()

                                res_storer = Storer(result,
                                                    context_map={context_path: context_file_path},
                                                    dir_split=dir_split_number,
                                                    n_file_item=items_per_file)
                                res_storer.upload_and_store(
                                    base_dir, triplestore_url, base_iri, context_path,
                                    temp_dir_for_rdf_loading)

                                prov_storer = Storer(prov,
                                                     context_map={context_path: context_file_path},
                                                     dir_split=dir_split_number,
                                                     n_file_item=items_per_file)
                                prov_storer.store_all(
                                    base_dir, base_iri, context_path,
                                    temp_dir_for_rdf_loading)

                                dset_handler = DatasetHandler(triplestore_url_real,
                                                              context_path,
                                                              context_file_path, base_iri,
                                                              base_dir, info_dir, dataset_home,
                                                              temp_dir_for_rdf_loading)
                                dset_handler.update_dataset_info(result)

                                # If everything went fine, move the input file to the done directory
                                move_file(cur_file_path,
                                          reference_dir_done + os.sep + cur_local_dir_path)

                            # If something in the process went wrong, move the input file
                            # in an appropriate directory
                            else:
                                if crp.reperr.is_empty():  # The resource has been already processed
                                    move_file(cur_file_path,
                                              reference_dir_done + os.sep + cur_local_dir_path)
                                else:
                                    moved_file = \
                                        move_file(cur_file_path,
                                                  reference_dir_error + os.sep + cur_local_dir_path)
                                    crp.reperr.write_file(moved_file + ".err")
                            
                            cur_dir_path = os.path.dirname(cur_file_path)
                            if len([name for name in os.listdir(cur_dir_path)
                                    if name.endswith(".json")]) == 0:
                                shutil.rmtree(cur_dir_path)
                else:
                    print "\n\nProcess stopped due to external reasons"
                    break
        else:
            print "\n\nProcess stopped due to external reasons"
            break
except Exception as e:
    exception_string = str(e) + " " + traceback.format_exc().rstrip("\n+")
    print exception_string
    if last_file is not None:
        moved_file = move_file(last_file, reference_dir_error + os.sep + last_local_dir)
        with open(moved_file + ".err", "w") as f:
            f.write(exception_string)
        cur_dir_path = os.path.dirname(last_file)
        if len([name for name in os.listdir(cur_dir_path)
                if name.endswith(".json")]) == 0:
            shutil.rmtree(cur_dir_path)
end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
print "\nStarted at:\t%s\nEnded at:\t%s" % (start_time, end_time)