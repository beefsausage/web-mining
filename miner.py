from SPARQLWrapper import SPARQLWrapper, JSON
from graphviz import Graph
from collections import Counter

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
renderSet = []

g = Graph(filename='miner.gv', engine='sfdp', format='png')
g.attr(size='20', repulsiveforce='0.1', overlap='false',splines='curved')
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
        renderSet.append((queried.get(paradigm).replace("programming ","").replace(" programming", ""),name[1]))
    else:
        print('%s: %s' % (name[1], result["paradigm"]["value"]))


g.node_attr.update(color='lightblue2', style='filled', fontname='helvetica')
counterResults = dict(Counter([i[0] for i in renderSet]))
for count in counterResults.keys():
    occurrence = counterResults.get(count)
    g.attr('node',
    fontsize=str((occurrence*6)+20),
     width=str((occurrence/2)), height=str((occurrence/2)))
    g.node(count)

g.attr('node',
    fontsize="0",
     width="2", height="2")
for renderEntry in renderSet:
    g.edge(renderEntry[0], renderEntry[1])


g.render()

