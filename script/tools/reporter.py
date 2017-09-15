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

import codecs


class Reporter:
    """This class is used as a metaphoric agent being a reporter"""

    def __init__(self, print_sentences=False, prefix=""):
        self.articles = []
        self.last_article = None
        self.last_sentence = None
        self.print_sentences = print_sentences
        self.prefix = prefix

    def new_article(self):
        if self.last_article is None or len(self.last_article) > 0:
            self.last_article = []
            self.last_sentence = None
            self.articles.append(self.last_article)
            if self.print_sentences and len(self.last_article) > 0:
                print "\n"

    def add_sentence(self, sentence, print_this_sentence=True):
        cur_sentence = self.prefix + sentence
        self.last_sentence = cur_sentence
        self.last_article.append(cur_sentence)
        if self.print_sentences and print_this_sentence:
            print cur_sentence

    def get_last_sentence(self):
        return self.last_sentence

    def get_articles_as_string(self):
        result = ""
        for article in self.articles:
            for sentence in article:
                result += sentence + "\n"
            result += "\n"
        return result

    def write_file(self, file_path):
        with codecs.open(file_path, 'w') as f:
            f.write(self.get_articles_as_string())

    def is_empty(self):
        return self.last_sentence is None