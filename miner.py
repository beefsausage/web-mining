from SPARQLWrapper import SPARQLWrapper, JSON

from collections import Counter
from difflib import SequenceMatcher
from graphviz import Graph
import random
import re
import string

delimiters = ":", ",", ";", "/", " and "
delRegexPattern = '|'.join(map(re.escape, delimiters))

replacers = {
"programming" : "",
"language" : "",
" later " : " ",
"-" : " ",
"_" : " ",
"(" : "",
")" : "",
}
repRegexPattern = re.compile("(%s)" % "|".join(map(re.escape, replacers.keys())))

def normalize(str):
    return repRegexPattern.sub(lambda x: replacers[x.string[x.start():x.end()]], str).strip().lower()

def split(str):
    return [x.strip() for x in re.split(delRegexPattern, str)]

def similar(str1, str2):
    return SequenceMatcher(None, str1, str2).quick_ratio()

def occurrenceCounter(dic, str):
    if str in dic:
        dic[str] += 1
    else:
        dic[str] = 1

def appendToDicValue(dic, key, value):
    if key in dic:
        dic[key].append(value)
    else:
        dic[key] = [value]

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
queried = {}
paradigmaOccurences = {}
languages = {}
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

        #print('%s: %s' % (name[1], queried.get(paradigm)))
        occurrenceCounter(paradigmaOccurences, queried.get(paradigm))
        appendToDicValue(languages, name[1], queried.get(paradigm))

    else:
        #print('%s: %s' % (name[1], result["paradigm"]["value"]))
        languages[name[1]] = split(result["paradigm"]["value"])

for language, paradigmlist in languages.items():
    for e in paradigmlist:
        for pname, count in sorted(paradigmaOccurences.items(), key=lambda x: x[1], reverse = True):
            s = similar(normalize(e),normalize(pname))
            if s > 0.95:
                print('%s: %s => %s: %s %%' % (language, e, pname,s*100))
                renderSet.append((pname,language))
                break

g.node_attr.update(color='#9dd600', style='filled', fontname='helvetica')
counterResults = dict(Counter([i[0] for i in renderSet]))
for count in counterResults.keys():
    occurrence = counterResults.get(count)
    g.attr('node',
    fixedsize='shape',
    color='#00a2ed',
    fontsize=str((occurrence*5)+100),
     width=str((occurrence/2)), height=str((occurrence/2)))
    g.node(count)

g.attr('node',
    color='#fc4e0f',
    fontsize="0",
    width="2", height="2")
for renderEntry in renderSet:
    g.edge(renderEntry[0], renderEntry[1])
    #print(renderEntry)

print(len(renderSet))
g.render()

