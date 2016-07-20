#!/usr/bin/python
# -*- coding: utf-8 -*-
from scipy.special.tests.test_orthogonal import test_p_roots

__author__ = 'essepuntato'

import json
from conf_spacin import *
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON

queries = [
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?citing a fabio:Expression .
            FILTER EXISTS { ?citing cito:cites | ^cito:cites [] }
      }
    }""",
    """
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?citing cito:cites ?cited
        }
    }""",
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX frbr: <http://purl.org/vocab/frbr/core#>
    SELECT (count(DISTINCT ?container) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/br/> {
            ?container ^frbr:partOf ?something .
            FILTER NOT EXISTS { ?container frbr:partOf ?other_container }
        }
    }""",
    """
    PREFIX datacite: <http://purl.org/spar/datacite/>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT (count(?id) as ?tot) {
        GRAPH <https://w3id.org/oc/corpus/id/> {
            ?id datacite:usesIdentifierScheme datacite:orcid
        }
    }"""
]

tp = SPARQLWrapper(triplestore_url)
tp.setMethod('GET')

res = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
for query in queries:
    tp.setQuery(query)
    tp.setReturnFormat(JSON)
    tp_result = tp.query().convert()
    print "RES:", tp_result
    results = json.loads(tp_result)

    for result in results["results"]["bindings"]:
        res += "," + result["tot"]["value"]

with open(base_home + "statistics.csv", "a") as f:
    f.write(res + "\n")
