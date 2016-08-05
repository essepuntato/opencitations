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

import re


class RewriteRuleHandler(object):
    def __init__(self, class_name, r_list=None, urls=()):
        self.urls = urls
        self.class_name = class_name
        self.rr = []
        if r_list is not None:
            self.add_rules(r_list)

    def add_rule(self, p, r, is_last=False):
        self.rr += [(p, r, is_last)]

    def add_rules(self, r_list):
        for r in r_list:
            if len(r) > 2:
                self.add_rule(r[0], r[1], r[2])
            else:
                self.add_rule(r[0], r[1])
            self.urls = ("(" + r[0] + ")", self.class_name) + self.urls

    def rewrite(self, u):
        res = u
        for p, r, is_last in self.rr:
            if re.search(p, res) is not None:
                res = re.sub(p, r, res)
                if is_last:
                    break
        return res

    def get_urls(self):
        return self.urls