var yasqe = YASQE(document.getElementById("yasqe"), {
	sparql: {
		showQueryButton: true,
		endpoint: "https://w3id.org/oc/sparql",
		requestMethod: "GET"
	}
});
var yasr = YASR(document.getElementById("yasr"), {
	//this way, the URLs in the results are prettified using the defined prefixes in the query
	getUsedPrefixes: yasqe.getPrefixesFromQuery
});

//link both together
yasqe.setValue("PREFIX cito: <http://purl.org/spar/cito/>\nPREFIX dcterms: <http://purl.org/dc/terms/>\nPREFIX datacite: <http://purl.org/spar/datacite/>\nPREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>\nPREFIX biro: <http://purl.org/spar/biro/>\nPREFIX frbr: <http://purl.org/vocab/frbr/core#>\nPREFIX c4o: <http://purl.org/spar/c4o/>\nSELECT ?cited ?cited_ref ?title ?url WHERE {\n\t<https://w3id.org/oc/corpus/br/1> cito:cites ?cited .\n\tOPTIONAL { \n\t\t<https://w3id.org/oc/corpus/br/1> frbr:part ?ref .\n\t\t?ref biro:references ?cited ;\n\t\t\tc4o:hasContent ?cited_ref \n\t}\n\tOPTIONAL { ?cited dcterms:title ?title }\n\tOPTIONAL {\n\t\t?cited datacite:hasIdentifier [\n\t\t\tdatacite:usesIdentifierScheme datacite:url ;\n\t\t\tliteral:hasLiteralValue ?url\n\t\t]\n\t}\n}")
yasqe.options.sparql.callbacks.complete = yasr.setResponse;