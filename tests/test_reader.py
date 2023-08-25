from pytest import raises
from rdflib import Literal, URIRef, RDF
from typing import Optional, List

from edpop_explorer import Record, Reader, Field, RecordError
from edpop_explorer import EDPOPREC


class SimpleReader(Reader):
    CATALOG_URIREF = URIRef('http://example.com/reader')

    def fetch(self):
        self.records = [Record(self.__class__)]
        self.number_of_results = 1
        self.number_fetched = 1

    def fetch_next(self):
        pass

    def transform_query(self, query):
        return query.capitalize()


class TestReader:
    def test_catalog_to_graph(self):
        reader = SimpleReader()
        g = reader.catalog_to_graph()
        assert (reader.CATALOG_URIREF, RDF.type, EDPOPREC.Catalog) in g
