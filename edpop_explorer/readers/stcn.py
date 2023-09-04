from rdflib import Graph, Namespace, URIRef
from rdflib.term import Node
from typing import List

from edpop_explorer import Field
from edpop_explorer.sparqlreader import (
    SparqlReader, BibliographicalRDFRecord
)


def _get_properties_from_iri(iri: str, properties: List[Node]) -> (List[Node], Graph):
    '''Get the first objects of the requested properties of a certain IRI
    as strings.'''
    subject_graph = Graph()
    subject_graph.parse(iri)
    objects: List[Node] = []
    for prop in properties:
        for obj in subject_graph.objects(URIRef(iri), prop):
            objects.append(obj)
    return objects, subject_graph


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
        assert record.identifier is not None
        subject_node = URIRef(record.identifier)
        for name in graph.objects(subject_node, SCHEMA.name):
            record.title = Field(str(name))
            break
        record.languages = []
        for language in graph.objects(subject_node, SCHEMA.inLanguage):
            record.languages.append(Field(str(language)))
        # Now get the information from blank nodes
        record.contributors = []
        for author in graph.objects(subject_node, SCHEMA.author):
            name_field = None
            for name in graph.objects(author, SCHEMA.name):
                name_field = Field(str(name))
                # TODO: add role and authority record
            if name_field:
                record.contributors.append(name_field)
        for publication in graph.objects(subject_node, SCHEMA.publication):
            year_field = None
            for startDate in graph.objects(publication, SCHEMA.startDate):
                year_field = Field(str(startDate))
            if year_field:
                record.dating = year_field
            # TODO: publisher and location (not a blank node)
            published_by_iri = None
            for publishedBy in graph.objects(publication, SCHEMA.publishedBy):
                published_by_iri = str(publishedBy)
                break
            if published_by_iri:
                [name, location_node], pubgraph = _get_properties_from_iri(
                    published_by_iri, [SCHEMA.name, SCHEMA.location]
                )
                record.publisher_or_printer = Field(str(name))
                address_node = None
                for address in pubgraph.objects(location_node, SCHEMA.address):
                    address_node = address
                    break
                if address_node:
                    for addressLocality in pubgraph.objects(
                            address_node, SCHEMA.addressLocality
                    ):
                        record.place_of_publication = Field(
                            str(addressLocality)
                        )
                        break

    @classmethod
    def _create_lazy_record(
        cls, iri: str, name: str
    ) -> BibliographicalRDFRecord:
        record = BibliographicalRDFRecord(cls)
        record.identifier = iri
        record.link = iri
        record.title = Field(name)
        return record
