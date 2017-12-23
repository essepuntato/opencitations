var search_conf = {
"sparql_endpoint": "https://w3id.org/oc/sparql",
"prefixes": [
    {"prefix":"cito","iri":"http://purl.org/spar/cito/"},
    {"prefix":"dcterms","iri":"http://purl.org/dc/terms/"},
    {"prefix":"datacite","iri":"http://purl.org/spar/datacite/"},
    {"prefix":"literal","iri":"http://www.essepuntato.it/2010/06/literalreification/"},
    {"prefix":"biro","iri":"http://purl.org/spar/biro/"},
    {"prefix":"frbr","iri":"http://purl.org/vocab/frbr/core#"},
    {"prefix":"c4o","iri":"http://purl.org/spar/c4o/"},
    {"prefix":"bds","iri":"http://www.bigdata.com/rdf/search#"},
    {"prefix":"fabio","iri":"http://purl.org/spar/fabio/"},
    {"prefix":"pro","iri":"http://purl.org/spar/pro/"},
    {"prefix":"rdf","iri":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"}
  ],

"rules":  [
    {
      "name":"doi",
      "category": "document",
      "regex":"10.\\d{4,9}\/[-._;()/:A-Za-z0-9]+$",
      "query": [
        "SELECT DISTINCT ?doc ?short_iri ?doi ?title ?year ?author ?author_iri (COUNT(distinct ?cited) AS ?out_cits) (COUNT(distinct ?cited_by) AS ?in_cits) where {",
            "?lit bds:search <VAR> . ?lit bds:matchAllTerms 'true' . ?lit bds:relevance ?score . ?lit bds:maxRank '1' .",
            "?iri datacite:hasIdentifier/literal:hasLiteralValue ?lit .",
            "BIND(?lit AS ?doi).",
            "BIND(REPLACE(STR(?iri), 'https://w3id.org/oc/corpus', '', 'i') as ?short_iri) .",
            "BIND(?iri as ?doc) .",
            "OPTIONAL {?iri dcterms:title ?title .}",
            "OPTIONAL {?iri fabio:hasSubtitle ?subtitle .}",
            "OPTIONAL {?iri fabio:hasPublicationYear ?year .}",
            "OPTIONAL {?iri cito:cites ?cited .}",
            "OPTIONAL {?cited_by cito:cites ?iri .}",
            "",
             "OPTIONAL {",
                    "?iri pro:isDocumentContextFor [",
                        "pro:withRole pro:author ;",
                        "pro:isHeldBy ?author_iri",
                    "].",
                    "?author_iri foaf:familyName ?fname .",
                    "?author_iri foaf:givenName ?name .",
                    "BIND(CONCAT(STR(?name),' ', STR(?fname)) as ?author) .",
             "}",
          "} GROUP BY ?doc ?short_iri ?doi ?title ?year ?author ?author_iri"
      ]
    },
    {
      "name":"orcid",
      "category": "author",
      "regex":"[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$",
      "query": [
        "SELECT ?author_iri ?short_iri ?orcid ?author (COUNT(?doc) AS ?num_docs) WHERE {",
              "?lit bds:search <VAR> . ?lit bds:matchAllTerms 'true' . ?lit bds:relevance ?score . ?lit bds:maxRank '1' .",
              "?author_iri datacite:hasIdentifier/literal:hasLiteralValue ?lit .",
              "BIND(?lit as ?orcid) .",
              "BIND(REPLACE(STR(?author_iri), 'https://w3id.org/oc/corpus', '', 'i') as ?short_iri) .",
              "?author_iri rdfs:label ?label .",
              "OPTIONAL {",
                      "?author_iri foaf:familyName ?fname .",
                      "?author_iri foaf:givenName ?name .",
                      "BIND(CONCAT(STR(?name),' ', STR(?fname)) as ?author) .",
               "}",
               "",
               "OPTIONAL {",
                    "?role pro:isHeldBy ?author_iri .",
                    "?role pro:isHeldBy ?author_iri .",
                    "?doc pro:isDocumentContextFor ?role.",
               "}",
          "}GROUP BY ?author_iri ?short_iri ?orcid ?author"
      ]
    },
    {
      "name":"any_text",
      "category": "document",
      "regex":"[-'a-zA-Z ]+$",
      "query": [
        "SELECT DISTINCT ?doc ?short_iri ?doi ?title ?year ?author ?author_iri (COUNT(distinct ?cited) AS ?out_cits) (COUNT(distinct ?cited_by) AS ?in_cits)",
            "WHERE  {",
              "?lit bds:search <VAR> .",
              "?lit bds:matchAllTerms 'true' .",
              "?lit bds:relevance ?score .",
              "?lit bds:minRelevance '0.4' .",
              "?lit bds:maxRank '300' .",
            "",
              "{",
                "?entry c4o:hasContent ?lit .",
                "?entry biro:references ?iri .",
              "}",
              "UNION",
              "{?iri dcterms:title  ?lit }",
              "UNION",
              "{?iri fabio:hasSubtitle ?lit}",
              "UNION",
              "{",
                "?myra foaf:familyName ?lit .",
             "?role pro:isHeldBy ?myra .",
             "?iri pro:isDocumentContextFor ?role .",
              "}",
              ".",
            "",
              "OPTIONAL {",
                "?iri rdf:type ?type .",
                "BIND(REPLACE(STR(?iri), 'https://w3id.org/oc/corpus', '', 'i') as ?short_iri) .",
                "BIND(?iri as ?doc) .",
                "OPTIONAL {?doc dcterms:title  ?title .}",
                "OPTIONAL {?doc fabio:hasSubtitle  ?subtitle .}",
                "OPTIONAL {?doc fabio:hasPublicationYear ?year .}",
                "OPTIONAL {?doc cito:cites ?cited .}",
                "OPTIONAL {?cited_by cito:cites ?doc .}",
                "OPTIONAL {",
                 "?iri datacite:hasIdentifier [",
                  "datacite:usesIdentifierScheme datacite:doi ;",
               "literal:hasLiteralValue ?doi",
                   "]",
               "}",
            "",
               "OPTIONAL {",
                     "?iri pro:isDocumentContextFor [",
                         "pro:withRole pro:author ;",
                         "pro:isHeldBy ?author_iri",
                     "].",
                     "?author_iri foaf:familyName ?fname .",
                     "?author_iri foaf:givenName ?name .",
                     "BIND(CONCAT(STR(?name),' ', STR(?fname)) as ?author) .",
               "}",
              "}",
            "}GROUP BY ?doc ?short_iri ?doi ?title ?year ?author ?author_iri"
      ]
    }
  ],

"categories": [
    {
      "name": "document",
      "fields": [
        {"value":"short_iri", "title": "Corpus ID","column_width":"15%","type": "text", "sort":{"value": true}, "link":{"field":"doc","prefix":""}},
        {"value":"year", "title": "Year", "column_width":"7%","type": "int", "filter":{"type_sort": "int", "min": 8, "sort": "value", "order": "desc"}, "sort":{"value": true, "default": {"order": "desc"}} },
        {"value":"title", "title": "Title","column_width":"33%","type": "text", "sort":{"value": true}, "link":{"field":"doc","prefix":""}},
        {"value":"author", "title": "Authors", "column_width":"32%","type": "text", "sort":{"value": true}, "filter":{"type_sort": "int", "min": 8, "sort": "sum", "order": "desc"}, "link":{"field":"author_iri","prefix":""}},
        {"value":"in_cits", "title": "Cited by", "column_width":"13%","type": "text", "sort":{"value": true}}
      ],
      "group_by": {"keys":["doc"], "concats":["author"]}
    },

    {
      "name": "author",
      "fields": [
        {"value":"short_iri", "title": "Corpus ID","column_width":"25%", "type": "text", "link":{"field":"author_iri","prefix":""}},
        {"value":"author", "title": "Author","column_width":"35%", "type": "text","filter":{"type_sort": "text", "min": 8, "sort": "value", "order": "desc"}, "sort": {"value": true}},
        {"value":"orcid", "title": "ORCID","column_width":"25%", "type": "text", "link":{"field":"orcid","prefix":"https://orcid.org/"}},
        {"value":"num_docs", "title": "Works","column_width":"15%", "type": "text"}
      ]
    }
  ],


"page_limit": [5,10,15,20,30,40,50]

}
