from SPARQLWrapper import SPARQLWrapper, JSON
from graphviz import Digraph
import string
import re

dict = { 
"array" : "array programming",
"concurrent" : "concurrent programming",
"declarative" : "declarative programming",
"educational" : "educational programming language",
"esoteric" : "esoteric programming language",
"event driven" : "event-driven programming",
"event-driven" : "event-driven programming",
"functional" : "functional programming",
"functionqal programming" : "functional programming",
"generic" : "generic programming",
"lazy" : "lazy evaluation",
"logic" : "logic programming",
"meta" : "meta programming",
"modular" : "modular programming",
"multi paradigm" : "multi-paradigm programming language",
"multi-paradigm" : "multi-paradigm programming language",
"non strict" : "non-strict programming language",
"non-strict" : "non-strict programming language",
"imperative" : "imperative programming language",
"object oriented" : "object-oriented programming language",
"object-oriented" : "object-oriented programming language",
"object oriented programming" : "object-oriented programming language",
"parallel" : "parallel programming",
"procedural" : "procedural programming",
"reactive" : "reactive programming",
"reflective" : "reflective programming",
"scripting" : "scripting language",
"structured" : "scructured programming",
"unstructured" : "unstructured programming"
}

def normalize(text):
    text = text.lower().translate(str.maketrans({'(':None, ')':None, ";":None, '_':" "}))
    for i, j in dict.items():
        if text in dict:
            text = text.replace(i, j)
    return text.capitalize()

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
notmatched = {}

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
        notmatched[name[1]] = result["paradigm"]["value"]

for name in notmatched:
    paradigmList = [x.strip() for x in re.split(r'[,:/]', notmatched[name].lower())]
    for elem in paradigmList:
        for k,v in queried.items():
            if normalize(elem) == v:
               print('%s: %s' % (name, v))
               g.edge(v, name)
               break

g.render()

