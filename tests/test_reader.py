import pytest

from rdflib import URIRef, RDF

from edpop_explorer import (
    Record, Reader, ReaderError, EDPOPREC, GetByIdBasedOnQueryMixin
)


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


class SimpleReaderGetByIdBasedOnQuery(GetByIdBasedOnQueryMixin, SimpleReader):
    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return f"get {identifier}"

    def fetch(self):
        if not self.prepared_query:
            return
        if self.prepared_query == "get manymatching":
            self.records = [Record(self.__class__), Record(self.__class__)]
            self.number_fetched = self.number_of_results = 2
        elif self.prepared_query == "get nonematching":
            self.records = []
            self.number_fetched = self.number_of_results = 0
        elif self.prepared_query.startswith("get "):
            record = Record(self.__class__)
            record.identifier = self.prepared_query[4:]
            self.records = [record]
            self.number_fetched = self.number_of_results = 1


def test_getbyidbasedonquerymixin():
    record = SimpleReaderGetByIdBasedOnQuery.get_by_id("10")
    assert record.identifier == "10"


def test_getbyidbasedonquerymixin_multiplereturned():
    with pytest.raises(ReaderError):
       SimpleReaderGetByIdBasedOnQuery.get_by_id("manymatching")


def test_getbyidbasedonquerymixin_nonereturned():
    with pytest.raises(ReaderError):
       SimpleReaderGetByIdBasedOnQuery.get_by_id("nonematching")
