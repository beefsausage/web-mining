from SPARQLWrapper import SPARQLWrapper, JSON
from graphviz import Graph
from collections import Counter

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

sparql.setQuery("""
        SELECT DISTINCT  ?lang {
        ?lang rdf:type <http://dbpedia.org/ontology/ProgrammingLanguage>
        }
""")

sparql.setReturnFormat(JSON)
print(len( sparql.query().convert()['results']['bindings']))
sparql.setQuery("""
    SELECT ?pl ?paradigm
    WHERE {
        ?pl dbp:paradigm ?paradigm .
        ?pl rdf:type dbo:ProgrammingLanguage .
    }
""")

results = sparql.query().convert()
sizeOfProgrammingLanguages = len(results['results']['bindings'])
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


biggestOccurrence = 0

g.node_attr.update(color='#BDBDBD', style='filled', fontname='helvetica')
counterResults = dict(Counter([i[0] for i in renderSet]))
for count in counterResults.keys():
    occurrence = counterResults.get(count)

    if(occurrence > biggestOccurrence):
        biggestOccurrence = occurrence

    g.attr('node',
    fixedsize='shape',
    color='#BDBDBD',
    fontsize=str((occurrence*5)+100),
     width=str((occurrence/2)), height=str((occurrence/2)))
    newLabel = count + "\n" + str(occurrence)
    g.node(newLabel) 
    renderSet = [(newLabel, i[1]) if (i[0] == count) else i for i in renderSet]


g.attr('node',
    color='#fc4e0f',
    fontsize="0",
    width="2", height="2")
for renderEntry in renderSet:
    g.edge(renderEntry[0], renderEntry[1])

print(len(renderSet))


g.render()

