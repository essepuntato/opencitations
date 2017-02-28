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

from conf_spacin import *
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON

queries = [
    # 0
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?citing a fabio:Expression .
            FILTER EXISTS { ?citing cito:cites | ^cito:cites [] }
      }
    }""",
    # 1
    """
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?citing cito:cites ?cited
        }
    }""",
    # 2
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX frbr: <http://purl.org/vocab/frbr/core#>
    SELECT (count(DISTINCT ?container) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?container ^frbr:partOf ?something .
            FILTER NOT EXISTS { ?container frbr:partOf ?other_container }
        }
    }""",
    # 3
    """
    PREFIX datacite: <http://purl.org/spar/datacite/>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT (count(?id) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/id/> {
            ?id datacite:usesIdentifierScheme datacite:orcid
        }
    }""",
    # 4
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?citing a fabio:Expression .
            FILTER EXISTS { ?citing cito:cites [] }
      }
    }""",
    # 5
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?cited) as ?tot) {
      GRAPH <https://w3id.org/oc/corpus/br/> {
        ?cited a fabio:Expression .
        FILTER EXISTS { ?cited ^cito:cites [] }
      }
    }""",
    # 6
    """
    PREFIX datacite: <http://purl.org/spar/datacite/>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT (count(?auth) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/ra/> {
            ?auth a foaf:Agent
        }
    }"""
]

tp = SPARQLWrapper(triplestore_url)
tp.setMethod('GET')

res = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
for idx, query in enumerate(queries):
    if idx in (0, 2, 3, 6):
        res += ",-"
    else:
        tp.setQuery(query)
        tp.setReturnFormat(JSON)
        results = tp.query().convert()

        for result in results["results"]["bindings"]:
            res += "," + result["tot"]["value"]

with open(base_home + "statistics.csv", "a") as f:
    f.write(res + "\n")
