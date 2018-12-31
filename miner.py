from SPARQLWrapper import SPARQLWrapper, JSON
from graphviz import Digraph

sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.setQuery("""
    SELECT ?pl ?paradigm
    WHERE {
        ?pl dbp:paradigm ?paradigm .
        ?pl rdf:type dbo:ProgrammingLanguage .
    }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

queried = {}
paradigmas = {}
paradigmCount = {}

g = Digraph('G', filename='miner.gv', engine='sfdp')
g.attr(size='6,6')
g.node_attr.update(color='lightblue2', style='filled')
for result in results["results"]["bindings"]:
    name = result["pl"]["value"].split("resource/")
    paradigm = result["paradigm"]["value"]
    if paradigm.startswith("http://dbpedia.org"):
        if paradigm not in queried:
            queryParadigm = """
            SELECT ?label
                WHERE {{
                <{}> rdfs:label  ?label .
                FILTER (lang(?label) = 'en')
            }}
            """.format(paradigm)
            sparql.setQuery(queryParadigm)
            paradigmLabel = sparql.query().convert()
            if len(paradigmLabel["results"]["bindings"]) > 0:
                queried[paradigm] = paradigmLabel["results"]["bindings"][0]["label"]["value"]
            else:
                queried[paradigm] = paradigm.split("resource/")[1]
        print('%s: %s' % (name[1], queried.get(paradigm)))
        paradigmas[name[1]] = queried.get(paradigm)
        g.edge(queried.get(paradigm),name[1] )
    else:
        print('%s: %s' % (name[1], result["paradigm"]["value"]))


g.render()

