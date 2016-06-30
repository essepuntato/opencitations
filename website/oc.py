#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, S. <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
__author__ = 'essepuntato'
import web
import json
from src.wl import WebLogger
from src.rrh import RewriteRuleHandler
from src.ldd import LinkedDataDirector
import requests
import urlparse
import re

# Load the configuration file
with open("conf.json") as f:
    c = json.load(f)

# For redirecting to classes
urls = (
    "/", "WorkInProgress",
    "/corpus/(.+)", "Corpus",
    "/corpus/", "Corpus",
    "/sparql", "Sparql"
)

# For rendering
render = web.template.render(c["html"])

# Additional rewrite rules for any URLs
rewrite = RewriteRuleHandler(
    "Redirect",
    [
        ("^/corpus/context.json$",
         "http://rawgit.com/essepuntato/opencitations/master/corpus/context.json",
         True)
    ],
    urls
)

# Set the web logger
web_logger = WebLogger("opencitations.net", "opencitations_log.txt", [
    "REMOTE_ADDR",      # The IP address of the visitor
    "HTTP_USER_AGENT",  # The browser type of the visitor
    "HTTP_REFERER",     # The URL of the page that called your program
    "HTTP_HOST",        # The hostname of the page being attempted
    "REQUEST_URI"       # The interpreted pathname of the requested document
                        # or CGI (relative to the document root)
    ],
    {"REMOTE_ADDR": ["130.136.2.47", "127.0.0.1"]}  # uncomment this for real app
)


class Redirect:
    def GET(self, u):
        web_logger.mes()
        raise web.seeother(rewrite.rewrite(u))


class WorkInProgress:
    def GET(self):
        web_logger.mes()
        return render.wip()


class Sparql:
    def GET(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')
        query_string = web.ctx.env.get("QUERY_STRING")
        parsed_query = urlparse.parse_qs(query_string)
        if query_string is None or query_string.strip() == "":
            web_logger.mes()
            return render.sparql()
        if re.search("updates?", query_string, re.IGNORECASE) is None:
            if "query" in parsed_query:
                req = requests.get("%s?%s" % (c["sparql_endpoint"], query_string))
                if req.status_code == 200:
                    web_logger.mes()
                    return req.text
                else:
                    raise web.HTTPError(
                        str(req.status_code), {"Content-Type": req.headers["content-type"]}, req.text)
            else:
                raise web.redirect("/sparql")
        else:
            raise web.HTTPError(
                "403", {"Content-Type": "text/plain"}, "SPARQL Update queries are not permitted.")



class Corpus:
    def GET(self, file_path=None):
        director = LinkedDataDirector(
            c["occ_base_path"], c["html"], c["occ_base_url"], c["json_context_path"],
            label_conf={
                "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "is a",
                "http://xmlns.com/foaf/0.1/givenName": "given name",
                "http://xmlns.com/foaf/0.1/familyName": "family name",
                "http://prismstandard.org/namespaces/basic/2.0/startingPage": "first page",
                "http://prismstandard.org/namespaces/basic/2.0/endingPage": "last page"
            },
            tmp_dir=c["tmp_dir"])
        cur_page = director.redirect(file_path)
        if cur_page is None:
            raise web.notfound()
        else:
            web_logger.mes()
            return cur_page



if __name__ == "__main__":
    app = web.application(rewrite.get_urls(), globals())
    app.run()
