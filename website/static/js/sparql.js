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
yasqe.setValue("PREFIX cito: <http://purl.org/spar/cito/>\nPREFIX dcterms: <http://purl.org/dc/terms/>\nSELECT ?title (count(?o) as ?cit_n) WHERE {\n\t?citing\n\t\tdcterms:title ?title ;\n\t\tcito:cites ?o\n}\nGROUP BY ?title\nORDER BY DESC(?cit_n)\nLIMIT 10")
yasqe.options.sparql.callbacks.complete = yasr.setResponse;