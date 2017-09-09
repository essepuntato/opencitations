#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Silvio Peroni <essepuntato@gmail.com>
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

# This script unpacks all the DAR files related to a monthly OpenCitations Corpus dump
# and recreates the Corpus file system

import argparse
import zipfile
import re
import os
import subprocess
import glob
from multiprocessing import Process, Pool
from time import sleep


def unpack(zip_file, out_d=None):
    if out_d is None:
        out_dir = os.path.dirname(zip_file)
    else:
        out_dir = out_d

    zip_file_basename = os.path.basename(zip_file)
    print("[File '%s'] Start processing" % zip_file_basename)

    current_dir = re.sub("[0-9-]+corpus_([^_\.]+).*", "\\1", zip_file_basename)

    dir_path = out_dir + os.sep + current_dir

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print("[File '%s'] Directory '%s' created" % (zip_file_basename, dir_path))

    f_null = open(os.devnull, 'w')

    zip_ref = zipfile.ZipFile(zip_file, 'r')
    zip_ref.extractall(dir_path)
    zip_ref.close()

    print("[File '%s'] File unzipped correctly" % zip_file_basename)

    dar_name = zip_file_basename[:-4]

    if subprocess.call(["dar", "-O", "-R", dir_path + os.sep, "-x", dir_path + os.sep + dar_name],
                       stdout=f_null, stderr=subprocess.STDOUT):
        print("[File '%s'] DAR was not extracted due to issues" % zip_file_basename)
    else:
        print("[File '%s'] DAR was extracted correctly" % zip_file_basename)

        for dar_file in glob.glob(dir_path + os.sep + dar_name + ".[0-9]*.dar"):
            os.remove(dar_file)
        print("[File '%s'] DAR files deleted" % zip_file_basename)

        os.remove(zip_file)
        print("[File '%s'] Original zip file deleted" % zip_file_basename)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("unpack.py",
                                         description="This script unpack all the DAR files related to a monthly "
                                                     "OpenCitations Corpus dump (stored in ZIP files) and "
                                                     "recreates the Corpus file system")
    arg_parser.add_argument("-i", "--input", dest="input", required=True,
                            help="The directory containing all the ZIP files to unpack.")
    arg_parser.add_argument("-o", "--output", dest="output",
                            help="The directory where to store the Corpus data. If no "
                                 "directory is specified, the script use the one specified "
                                 "as input.")

    args = arg_parser.parse_args()
    in_dir = args.input
    out_dir = in_dir
    if args.output is not None:
        out_dir = args.output

    # job_server = pp.Server()
    #
    # jobs = []
    #
    # for cur_file in [zip_file for zip_file in os.listdir(in_dir) if zip_file.endswith(".zip")]:
    #     jobs += [job_server.submit(unpack, (in_dir + os.sep + cur_file, out_dir), modules=('re', 'os', 'zipfile', 'subprocess', 'glob'))]
    #
    # for job in jobs:
    #     job()

    # procs = []
    #
    # for idx, cur_file in enumerate([zip_file for zip_file in os.listdir(in_dir) if zip_file.endswith(".zip")]):
    #     p = Process(target=unpack, args=(in_dir + os.sep + cur_file, out_dir))
    #     procs.append(p)
    #
    # for p in procs:
    #     p.start()
    #     sleep(5)
    #
    # for p in procs:
    #     p.join()

    inputs = ()
    for idx, cur_file in enumerate([zip_file for zip_file in os.listdir(in_dir) if zip_file.endswith(".zip")]):
        inputs += (in_dir + os.sep + cur_file,)
    print inputs
    p = Pool(len(inputs))
    p.map_async(unpack, inputs)

    p.close()
    p.join()

    print("DONE")
