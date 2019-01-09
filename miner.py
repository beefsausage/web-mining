from SPARQLWrapper import SPARQLWrapper, JSON

from collections import Counter, defaultdict, OrderedDict
from difflib import SequenceMatcher
from graphviz import Graph
import re
import string
import csv

delimiters = ":", ",", ";", "/", " and "
delRegexPattern = '|'.join(map(re.escape, delimiters))

replacers = dict.fromkeys(['programming', 'language', ' later ', '-', '_', '(', ')', ' '], None)
repRegexPattern = re.compile("(%s)" % "|".join(map(re.escape, replacers.keys())))

# Returns a normalized string. All lower case, stripped whitespaces and removed "replacers"
def normalize(str):
    return repRegexPattern.sub(lambda x: replacers[x.string[x.start():x.end()]], str).lower()

# Splits a string using delimiters and returns a list,
# i.e. "functional, imperative" -> ['functional', 'imperative']
def split(str):
    return [x.strip() for x in re.split(delRegexPattern, str)]

# Compares the similarity of two strings. Returns a float value in the range [0, 1]
def similar(str1, str2):
    return SequenceMatcher(None, str1, str2).quick_ratio()

sparql = SPARQLWrapper("http://dbpedia.org/sparql")

sparql.setQuery("""
        SELECT DISTINCT  ?lang {
        ?lang rdf:type <http://dbpedia.org/ontology/ProgrammingLanguage>
        }
""")

sparql.setReturnFormat(JSON)
totalProgrammingLanguages = len(sparql.query().convert()['results']['bindings'])
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
paradigmOccurences = defaultdict(int)
programmingLanguages = defaultdict(list)
renderSet = []

g = Graph(filename='miner.gv', engine='sfdp', format='png')
g.attr(size='20', repulsiveforce='0.1', overlap='false',splines='curved')

# Iterates through all retrieved results and collects all programming languages
# and their associated paradigms in the programmingLanguages dict for later usage.
for result in results["results"]["bindings"]:
    name = result["pl"]["value"].split("resource/")
    paradigm = result["paradigm"]["value"]

    # If the paradigm of a programming language is an url it can be queried
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

            # The name can be obtained from the value field, if available
            if len(paradigmLabel["results"]["bindings"]) > 0:
                queried[paradigm] = paradigmLabel["results"]["bindings"][0]["label"]["value"]
            # Otherwise extract the paradigm name from the url
            else:
                queried[paradigm] = paradigm.split("resource/")[1]
        print('%s: %s' % (name[1], queried.get(paradigm)))
        paradigmOccurences[queried.get(paradigm)] += 1
        programmingLanguages[name[1]].append(queried.get(paradigm))

    # Otherwise we only receive a string value. A string might contain multiple paradigms.
    # A matching with the pool of properly retrieved paradigms will take place later. 
    else:
        print('%s: %s' % (name[1], result["paradigm"]["value"]))
        programmingLanguages[name[1]] = split(result["paradigm"]["value"])

paradigmOccurences = sorted(paradigmOccurences.items(), key=lambda x: x[1], reverse = True)
normalizedParadigma = {k:normalize(k) for k,v in paradigmOccurences}

# Matching all programming languages and their paradigms with the most common way to spell that paradigm,
# i.e. "functionqal" -> "functional", "object oriented" -> "object-oriented".
# Subsequently add (programming language, paradigm) tuples to the renderSet
for language, paradigmlist in programmingLanguages.items():
    for p in paradigmlist:
        n = normalize(p)
        for pname, count in paradigmOccurences:
            s = similar(n,normalizedParadigma.get(pname))
            if s > 0.95:
                print('%s: %s => %s: %s %%' % (language, p, pname,s*100))
                renderSet.append((pname.replace("programming ","").replace(" programming", ""),language))
                break

biggestOccurrence = 0

g.node_attr.update(color='#BDBDBD', style='filled', fontname='helvetica')
counterResults = OrderedDict(Counter([i[0] for i in renderSet]).most_common())


# Write to CSV and map occurrences to nodes
with open('data.csv', 'w') as csvfile:
    fieldnames = ['paradigm', 'occurrence']
    csvwriter = csv.DictWriter(csvfile, fieldnames = fieldnames)
    csvwriter.writeheader()

    for count in counterResults.keys():
        occurrence = counterResults.get(count)

        csvwriter.writerow({fieldnames[0] : count, fieldnames[1] : occurrence})

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

g.render()
print("Rendering finished")

withParadigm = len(set([i[1] for i in renderSet]))

print("Programming languages from DBpedia: %i \nwith Paradigm: %i" % (totalProgrammingLanguages, withParadigm))