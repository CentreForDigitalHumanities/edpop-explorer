
from typing_extensions import override

import pytest

from rdflib import URIRef, RDF

from edpop_explorer import (
    Record,
    Reader,
    ReaderError,
    EDPOPREC,
    GetByIdBasedOnQueryMixin,
    NotFoundError,
)


class SimpleReader(Reader):
    """A simple reader which always yields 20 items which have as their
    ID the index number."""

    CATALOG_URIREF = URIRef("http://example.com/reader")
    IRI_PREFIX = "http://example.com/records/reader/"
    NUMBER_OF_ITEMS = 20

    @override
    def fetch_range(self, range_to_fetch: range) -> range:
        if range_to_fetch.stop > self.NUMBER_OF_ITEMS:
            range_to_fetch = range(range_to_fetch.start, self.NUMBER_OF_ITEMS)
        for i in range_to_fetch:
            self.records[i] = self.get_by_id(str(i))
        self.number_of_results = self.NUMBER_OF_ITEMS
        return range_to_fetch

    @classmethod
    @override
    def transform_query(cls, query):
        return query.capitalize()

    @classmethod
    @override
    def get_by_id(cls, identifier: str) -> Record:
        if int(identifier) not in range(cls.NUMBER_OF_ITEMS):
            raise NotFoundError
        record = Record(cls)
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


def test_fetch():
    reader = SimpleReader()
    reader.set_query("test")  # Ignored by SimpleReader
    to_fetch = 8
    reader.fetch(to_fetch)
    assert reader.number_of_results == 20
    assert reader.number_fetched == to_fetch
    record = reader.get(5, False)
    assert isinstance(record, Record)
    # Fetch the next 8
    reader.fetch(to_fetch)
    record = reader.get(12, False)
    assert isinstance(record, Record)
    # Fetch the rest
    reader.fetch(to_fetch)
    assert reader.fetching_exhausted
    assert reader.number_fetched == reader.number_of_results
    with pytest.raises(NotFoundError):
        # Number 20 should not exist
        record = reader.get(20, False)


def test_get_allow_fetching():
    reader = SimpleReader()
    reader.set_query("test")
    record = reader.get(5, True)
    assert isinstance(record, Record)


def test_get_no_fetching():
    reader = SimpleReader()
    reader.set_query("test")
    with pytest.raises(NotFoundError):
        reader.get(5, False)


class SimpleReaderGetByIdBasedOnQuery(GetByIdBasedOnQueryMixin, SimpleReader):
    FETCH_ALL_AT_ONCE = True

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return f"get {identifier}"

    @override
    def fetch_range(self, range_to_fetch: range) -> range:
        # To simplify, fetch all records at once
        if self.prepared_query == "get manymatching":
            self.records = {
                0: Record(self.__class__),
                1: Record(self.__class__),
            }
            self.number_of_results = 2
            return range(0, 2)
        elif self.prepared_query == "get nonematching":
            self.records = {}
            self.number_of_results = 0
            return range(0, 0)
        elif self.prepared_query.startswith("get "):
            record = Record(self.__class__)
            record.identifier = self.prepared_query[4:]
            self.records = {
                0: record,
            }
            self.number_of_results = 1
            return range(0, 1)


def test_getbyidbasedonquerymixin():
    record = SimpleReaderGetByIdBasedOnQuery.get_by_id("10")
    assert record.identifier == "10"


def test_getbyidbasedonquerymixin_multiplereturned():
    with pytest.raises(ReaderError):
        SimpleReaderGetByIdBasedOnQuery.get_by_id("manymatching")


def test_getbyidbasedonquerymixin_nonereturned():
    with pytest.raises(ReaderError):
        SimpleReaderGetByIdBasedOnQuery.get_by_id("nonematching")


def test_generate_identifier():
    reader = SimpleReader()
    reader.prepare_query("Hoi")
    identifier = reader.generate_identifier()
    # A new reader with the same query should have the same identifier. Now,
    # also perform a fetch.
    reader2 = SimpleReader()
    reader2.prepare_query("Hoi")
    reader2.fetch()
    identifier2 = reader2.generate_identifier()
    assert identifier == identifier2
