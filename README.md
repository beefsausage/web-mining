# web-mining
Mining programming languages and graphing them by their paradigms

## Requirements
SPARQLWrapper
```
pip install SPARQLWrapper
```
Graphviz
```
pip install graphviz
```
Also make sure to install Graphviz standalone on your OS.  
https://www.graphviz.org/

## Usage
Run the **miner.py** File with Python3 to reproduce the graph :)

There will be 2 outputs: 
- **miner.gv.png** that contains the graph
- **data.csv** that contains the data structured in a csv

It will output the total number of programming languages examined that contained a paradigm.  
There will also be total number of programming languages. Unfortunately this number will be inaccurate due to the broken template "ProgrammingLanguage" provided by DBpedia that mismaps entries.
