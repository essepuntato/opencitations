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
import web
import json
from src.wl import WebLogger
from src.rrh import RewriteRuleHandler
from src.ldd import LinkedDataDirector
from src.ved import VirtualEntityDirector
import requests
import urlparse
import re
from src.oh import OntologyHandler
import csv
from datetime import datetime

# Load the configuration file
with open("conf.json") as f:
    c = json.load(f)

pages = ["/", "about", "corpus", "model", "download", "sparql", "search", "oci",
         "publications", "licenses", "contacts"]

urls = (
    "(/)", "Home",
    "/(about)", "About",
    "/(model)", "Model",
    "/(corpus)", "CorpusIntro",
    "/corpus/(.+)", "Corpus",
    "/virtual/(.+)", "Virtual",
    "/(oci)(/.+)?", "OCI",
    "/corpus/", "Corpus",
    "/(download)", "Download",
    "/(sparql)", "Sparql",
    "/(search)", "Search",
    "/(publications)", "Publications",
    "/(licenses)", "Licenses",
    "/(contacts)", "Contacts",
    "/ontology(.+)?", "Ontology",
    "(/paper/.+)", "RawGit"
)

render = web.template.render(c["html"])

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


class RawGit:
    def GET(self, u):
        web_logger.mes()
        raise web.seeother("http://rawgit.com/essepuntato/opencitations/master" + u)


class Redirect:
    def GET(self, u):
        web_logger.mes()
        raise web.seeother(rewrite.rewrite(u))


class WorkInProgress:
    def GET(self, active):
        web_logger.mes()
        return render.wip(pages, active)


class Home:
    def GET(self, active):
        web_logger.mes()
        cur_date = ""
        cur_tot = ""
        cur_cit = ""

        with open(c["statistics"]) as f:
            lastrow = None
            for lastrow in csv.reader(f): pass
            cur_date = datetime.strptime(
                lastrow[0], "%Y-%m-%dT%H:%M:%S").strftime("%B %d, %Y")
            cur_tot = lastrow[5]
            cur_cit = lastrow[2]
            cur_cited = lastrow[6]

        return render.home(pages, active, cur_date, cur_tot, cur_cit, cur_cited)


class About:
    def GET(self, active):
        web_logger.mes()
        return render.about(pages, active)


class CorpusIntro:
    def GET(self, active):
        web_logger.mes()
        return render.corpus(pages, active)


class OCI:
    def GET(self, active, oci):
        data = web.input()
        if "oci" in data:
            clean_oci = re.sub("\s+", "", re.sub("^oci:", "", data.oci.strip(), flags=re.IGNORECASE))
            raise web.seeother(c["oc_base_url"] + "/" + active + "/" + clean_oci)
        elif oci is None or oci.strip() == "":
            web_logger.mes()
            return render.oci(pages, active)
        else:
            web_logger.mes()
            raise web.seeother(c["oc_base_url"] + c["virtual_local_url"] + "ci" + oci)



class Download:
    def GET(self, active):
        web_logger.mes()
        return render.download(pages, active)


class Search:
    def GET(self, active):
        web_logger.mes()
        query_string = web.ctx.env.get("QUERY_STRING")
        parsed_query = urlparse.parse_qs(query_string)
        if "text" in parsed_query:
            return render.search(pages, active, parsed_query['text'][0])
        else:
            return render.search(pages, active, "")


class Model:
    def GET(self, active):
        web_logger.mes()
        return render.model(pages, active)


class Publications:
    def GET(self, active):
        web_logger.mes()
        return render.publications(pages, active)

class Licenses:
    def GET(self, active):
        web_logger.mes()
        return render.licenses(pages, active)

class Contacts:
    def GET(self, active):
        web_logger.mes()
        return render.contacts(pages, active)


class Sparql:
    def GET(self, active):
        content_type = web.ctx.env.get('CONTENT_TYPE')
        return self.__run_query_string(active, web.ctx.env.get("QUERY_STRING"), content_type)

    def POST(self, active):
        content_type = web.ctx.env.get('CONTENT_TYPE')
        web.debug("The content_type value: ")
        web.debug(content_type)

        cur_data = web.data()
        if "application/x-www-form-urlencoded" in content_type:
            return self.__run_query_string(active, cur_data, True, content_type)
        elif "application/sparql-query" in content_type:
            return self.__contact_tp(cur_data, True, content_type)
        else:
            raise web.redirect("/sparql")

    def __contact_tp(self, data, is_post, content_type):
        accept = web.ctx.env.get('HTTP_ACCEPT')
        if accept is None or accept == "*/*" or accept == "":
            accept = "application/sparql-results+xml"
        if is_post:
            req = requests.post(c["sparql_endpoint"], data=data,
                                headers={'content-type': content_type, "accept": accept})
        else:
            req = requests.get("%s?%s" % (c["sparql_endpoint"], data),
                               headers={'content-type': content_type, "accept": accept})

        if req.status_code == 200:
            web.header('Access-Control-Allow-Origin', '*')
            web.header('Access-Control-Allow-Credentials', 'true')
            web.header('Content-Type', req.headers["content-type"])
            web_logger.mes()
            return req.text
        else:
            raise web.HTTPError(
                str(req.status_code), {"Content-Type": req.headers["content-type"]}, req.text)

    def __run_query_string(self, active, query_string, is_post=False,
                           content_type="application/x-www-form-urlencoded"):
        parsed_query = urlparse.parse_qs(query_string)
        if query_string is None or query_string.strip() == "":
            web_logger.mes()
            return render.sparql(pages, active)
        if re.search("updates?", query_string, re.IGNORECASE) is None:
            if "query" in parsed_query:
                return self.__contact_tp(query_string, is_post, content_type)
            else:
                raise web.redirect("/sparql")
        else:
            raise web.HTTPError(
                "403", {"Content-Type": "text/plain"}, "SPARQL Update queries are not permitted.")


class Virtual:
    def GET(self, file_path=None):
        ldd = LinkedDataDirector(
            c["occ_base_path"], c["html"], c["oc_base_url"],
            c["json_context_path"], c["corpus_local_url"],
            label_conf=c["label_conf"], tmp_dir=c["tmp_dir"],
            dir_split_number=int(c["dir_split_number"]),
            file_split_number=int(c["file_split_number"]))
        ved = VirtualEntityDirector(ldd, c["virtual_local_url"], c["ved_conf"])
        cur_page = ved.redirect(file_path)
        if cur_page is None:
            raise web.notfound()
        else:
            web_logger.mes()
            return cur_page

class Corpus:
    def GET(self, file_path=None):
        ldd = LinkedDataDirector(
            c["occ_base_path"], c["html"], c["oc_base_url"],
            c["json_context_path"], c["corpus_local_url"],
            label_conf=c["label_conf"], tmp_dir=c["tmp_dir"],
            dir_split_number=int(c["dir_split_number"]),
            file_split_number=int(c["file_split_number"]))
        cur_page = ldd.redirect(file_path)
        if cur_page is None:
            raise web.notfound()
        else:
            web_logger.mes()
            return cur_page


class Ontology:
    def GET(self, ext):
        cur_extension = "" if ext is None else ext
        ontology_handler = OntologyHandler(
            c["ontology_base_url"], c["documentation_base_path"],
            {c["onto_acronym"]: c["ontology_url"]}, c["tmp_dir"])
        cur_page = ontology_handler.redirect(
            c["ontology_base_url"] + c["onto_acronym"] + cur_extension)
        if cur_page is None:
            raise web.notfound()
        else:
            web_logger.mes()
            return cur_page


if __name__ == "__main__":
    app = web.application(rewrite.get_urls(), globals())
    app.run()
