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

# Load the configuration file
with open("conf.json") as f:
    c = json.load(f)

# For redirecting to classes
urls = (
    "/", "WorkInProgress"
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
    # {"REMOTE_ADDR": ["127.0.0.1"]}  # uncomment this for test
)


class Redirect:
    def GET(self, u):
        web_logger.mes()
        raise web.seeother(rewrite.rewrite(u))


class WorkInProgress:
    def GET(self):
        web_logger.mes()
        return render.wip()


if __name__ == "__main__":
    app = web.application(rewrite.get_urls(), globals())
    app.run()
