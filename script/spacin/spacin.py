#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

import json
from crossref_processor import CrossrefProcessor
from script.spacin.conf import *
from resource_finder import ResourceFinder
from orcid_finder import ORCIDFinder
from graphlib import ProvSet
from storer import Storer
import os
from script.stopper import Stopper
from script.support import move_file
import traceback
from dataset_handler import DatasetHandler
from datetime import datetime

start_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
error = False
last_file = None
s = Stopper(reference_dir)
try:
    for cur_dir, cur_subdir, cur_files in os.walk(reference_dir):
        if s.can_proceed():
            for cur_file in cur_files:
                if s.can_proceed():
                    if cur_file.endswith(".json"):
                        cur_file_path = cur_dir + os.sep + cur_file
                        with open(cur_file_path) as fp:
                            last_file = cur_file_path
                            print "\n\nProcess file '%s'\n" % cur_file_path
                            json_object = json.load(fp)
                            crp = CrossrefProcessor(base_iri, context_path, info_dir, json_object,
                                                    ResourceFinder(ts_url=triplestore_url),
                                                    ORCIDFinder(orcid_conf_path))
                            result = crp.process()
                            if result is not None:
                                prov = ProvSet(result, base_iri, context_path, info_dir,
                                               ResourceFinder(ts_url=triplestore_url))
                                prov.generate_provenance()

                                res_storer = Storer(result, context_map={context_path: context_file_path})
                                res_storer.upload_and_store(
                                    base_dir, triplestore_url, base_iri, context_path,
                                    temp_dir_for_rdf_loading)

                                prov_storer = Storer(prov, context_map={context_path: context_file_path})
                                prov_storer.upload_and_store(
                                    base_dir, triplestore_url, base_iri, context_path,
                                    temp_dir_for_rdf_loading)

                                dset_handler = DatasetHandler(triplestore_url, context_path,
                                                              context_file_path, base_iri,
                                                              base_dir, info_dir, dataset_home,
                                                              temp_dir_for_rdf_loading)
                                dset_handler.update_dataset_info(result)

                                # If everything went fine, move the input file to the done directory
                                move_file(cur_file_path, reference_dir_done)

                            # If something in the process went wrong, move the input file
                            # in an appropriate directory
                            else:
                                if crp.reperr.is_empty():  # The resource has been already processed
                                    move_file(cur_file_path, reference_dir_done)
                                else:
                                    moved_file = move_file(cur_file_path, reference_dir_error)
                                    crp.reperr.write_file(moved_file + ".err")
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
        moved_file = move_file(last_file, reference_dir_error)
        with open(moved_file + ".err", "w") as f:
            f.write(exception_string)
end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
print "\nStarted at:\t%s\nEnded at:\t%s" % (start_time, end_time)