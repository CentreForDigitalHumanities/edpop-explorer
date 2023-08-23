from rdflib import Graph, Namespace

from edpop_explorer import Field
from edpop_explorer.sparqlreader import (
    SparqlReader, BibliographicalRDFRecord
)


class STCNReader(SparqlReader):
    endpoint = 'http://data.bibliotheken.nl/sparql'
    filter = '?s schema:mainEntityOfPage/schema:isPartOf ' \
        '<http://data.bibliotheken.nl/id/dataset/stcn> .'
    name_predicate = '<http://schema.org/name>'

    def __init__(self):
        super().__init__()

    @classmethod
    def _convert_record(
        cls, graph: Graph, record: BibliographicalRDFRecord
    ) -> None:
        SCHEMA = Namespace('http://schema.org/')
        # First get the title and languages fields, which are simple
        # properties
        for name in graph.objects(None, SCHEMA.name):
            record.title = Field(str(name))
            break
        record.languages = []
        for language in graph.objects(None, SCHEMA.inLanguage):
            record.languages.append(Field(str(language)))
        # Now get the information from blank nodes
        record.contributors = []
        for author in graph.objects(None, SCHEMA.author):
            name_field = None
            for name in graph.objects(author, SCHEMA.name):
                name_field = Field(str(name))
                # TODO: add role and authority record
            if name_field:
                record.contributors.append(name_field)
        for publication in graph.objects(None, SCHEMA.publication):
            year_field = None
            for startDate in graph.objects(publication, SCHEMA.startDate):
                year_field = Field(str(startDate))
            if year_field:
                record.dating = year_field
            # TODO: publisher and location (not a blank node)

    @classmethod
    def _create_lazy_record(
        cls, iri: str, name: str
    ) -> BibliographicalRDFRecord:
        record = BibliographicalRDFRecord(cls)
        record.identifier = iri
        record.link = iri
        record.title = Field(name)
        return record
