import pytest

from rdflib import URIRef, RDF

from edpop_explorer import Record, Reader, ReaderError
from edpop_explorer import EDPOPREC


class SimpleReader(Reader):
    CATALOG_URIREF = URIRef('http://example.com/reader')
    IRI_PREFIX = "http://example.com/records/reader/"

    def fetch(self):
        self.records = [Record(self.__class__)]
        self.number_of_results = 1
        self.number_fetched = 1

    def fetch_next(self):
        pass

    def transform_query(self, query):
        return query.capitalize()

    def get_by_id(self, identifier: str) -> Record:
        record = Record(self.__class__)
        record.identifier = identifier
        return record

class SimpleReaderNoIRIPrefix(SimpleReader):
    IRI_PREFIX = None


def test_catalog_to_graph():
    reader = SimpleReader()
    g = reader.catalog_to_graph()
    assert (reader.CATALOG_URIREF, RDF.type, EDPOPREC.Catalog) in g


def test_iri_to_identifier():
    iri = "http://example.com/records/reader/1"
    assert SimpleReader.iri_to_identifier(iri) == "1"

def test_iri_to_identifier_invalid():
    with pytest.raises(ReaderError):
        SimpleReader.iri_to_identifier("invalid/1")

def test_iri_to_identifier_and_vv_noprefixset():
    with pytest.raises(ReaderError):
        SimpleReaderNoIRIPrefix.iri_to_identifier(
            "http://example.com/records/reader/1"
        )
    with pytest.raises(ReaderError):
        SimpleReaderNoIRIPrefix.identifier_to_iri("1")

def test_identifier_to_iri():
    expected_iri = "http://example.com/records/reader/1"
    assert SimpleReader.identifier_to_iri("1") == expected_iri

