#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

from rdflib import ConjunctiveGraph
from conf_spacin import *
from datetime import datetime

queries = [
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
      ?citing a fabio:Expression .
      FILTER EXISTS { ?citing cito:cites [] }
    }""",
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?cited) as ?tot) {
      ?cited a fabio:Expression .
      FILTER EXISTS { ?cited ^cito:cites [] }
    }""",
    """
    PREFIX cito: <http://purl.org/spar/cito/>
    SELECT (count(?citing) as ?tot) {
        ?citing cito:cites ?cited
    }""",
    """
    PREFIX fabio: <http://purl.org/spar/fabio/>
    PREFIX frbr: <http://purl.org/vocab/frbr/core#>
    SELECT (count(DISTINCT ?container) as ?tot) {
        ?container a fabio:Expression ; ^frbr:partOf ?something .
        FILTER NOT EXISTS { ?container frbr:partOf ?other_container }
    }""",
    """
    PREFIX pro: <http://purl.org/spar/pro/>
    SELECT (count(DISTINCT ?publisher) as ?tot) {
        ?role pro:withRole pro:publisher ; pro:isHeldBy ?publisher
    }""",
    """
    PREFIX pro: <http://purl.org/spar/pro/>
    SELECT (count(?author) as ?tot) {
        ?role pro:withRole pro:author ; pro:isHeldBy ?author
    }""",
    """
    PREFIX datacite: <http://purl.org/spar/datacite/>
    PREFIX pro: <http://purl.org/spar/pro/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT (count(DISTINCT ?author) as ?tot) {
      ?author a foaf:Agent ; datacite:hasIdentifier []
    }"""
]

ts = ConjunctiveGraph('SPARQLUpdateStore')
ts.open((triplestore_url, triplestore_url))

res = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
for query in queries:
    for tot, in ts.query(query):
        res += "," + str(tot)
with open(base_home + "statistics.csv", "a") as f:
    f.write(res + "\n")
