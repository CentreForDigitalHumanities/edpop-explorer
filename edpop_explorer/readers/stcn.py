from edpop_explorer.sparqlreader import SparqlReader


class STCNReader(SparqlReader):
    url = 'http://data.bibliotheken.nl/sparql'
    filter = '?s schema:mainEntityOfPage/schema:isPartOf ' \
        '<http://data.bibliotheken.nl/id/dataset/stcn> .'
    name_predicate = '<http://schema.org/name>'
