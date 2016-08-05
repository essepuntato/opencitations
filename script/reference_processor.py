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

from reporter import Reporter
from reference_storer import BibliographicReferenceStorer


class ReferenceProcessor(object):
    def __init__(self,
                 stored_file,
                 reference_dir,
                 error_dir,
                 stopper,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30):
        self.headers = headers
        self.sec_to_wait = sec_to_wait
        self.max_iteration = max_iteration
        self.timeout = timeout
        self.stopper = stopper
        self.name = "BEE " + self.__class__.__name__
        self.repok = Reporter(prefix="[%s - INFO] " % self.name)
        self.repok.new_article()
        self.reper = Reporter(prefix="[%s - ERROR] " % self.name)
        self.reper.new_article()
        self.rs = BibliographicReferenceStorer(stored_file, reference_dir, error_dir)

    def process(self):
        pass  # To implement in subclasses
