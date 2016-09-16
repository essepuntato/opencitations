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

import sys
import os
import re

done = set()

dar_path = "dar"
if len(sys.argv) > 1:
    dar_path = sys.argv[1]
else:
    dar_path = "dar"

base_dir = os.path.dirname(sys.argv[0])
for cur_dir, cur_subdir, cur_files in os.walk(base_dir):
    for cur_file in cur_files:
        if cur_file.endswith(".dar"):
            # ex: base_name =
            base_name = re.sub("^(.+)\.[0-9]+.dar$", "\\1", cur_file)
            if base_name not in done:
                done.add(base_name)
                final_dir = os.sep.join(re.sub("^[0-9]+-[0-9]+-[0-9]+-", "", base_name).split("_"))
                # $BACKUP_DATE-corpus_re_$CUR_DIR
                # Be OS indipendent
                # TODO: check if dar is removed

# dar -x pippo/my_backup -R /some/where/else