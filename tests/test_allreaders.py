'''Test all readers for basic sanity, without invoking methods that could
access the internet or manipulate files.'''

import pytest
import warnings
from typing import Type

from rdflib import Graph

from edpop_explorer import Reader, ReaderError
from edpop_explorer.readers import ALL_READERS


@pytest.mark.parametrize("readercls", ALL_READERS)
def test_instantiate(readercls: Type[Reader]):
    # Test if all concrete reader classes can be instantiated: all abstract
    # methods should have been overridden and there should be no errors
    # in the class definition.
    readercls()


@pytest.mark.parametrize("readercls", ALL_READERS)
def test_transform_query(readercls: Type[Reader]):
    readercls.transform_query("testquery")


@pytest.mark.parametrize("readercls", ALL_READERS)
def test_identifier_to_iri(readercls: Type[Reader]):
    # Converting an identifier to an IRI should always be possible
    assert isinstance(readercls.identifier_to_iri("123"), str)


@pytest.mark.parametrize("readercls", ALL_READERS)
def test_iri_to_identifier(readercls: Type[Reader]):
    # This is likely to fail, but if it fails it should raise a ReaderError
    # or derivative
    try:
        readercls.iri_to_identifier("http://example.com/record/1")
    except ReaderError:
        pass


@pytest.mark.parametrize("readercls", ALL_READERS)
def test_catalog_to_graph(readercls: Type[Reader]):
    assert isinstance(readercls.catalog_to_graph(), Graph)


@pytest.mark.parametrize("readercls", ALL_READERS)
@pytest.mark.requests
def test_realrequest(readercls: Type[Reader]):
    reader = readercls()
    reader.prepare_query("gruninger")
    reader.fetch()
    assert reader.number_fetched is not None
    assert reader.number_of_results is not None
    assert reader.number_fetched == len(reader.records)
    assert reader.number_of_results >= reader.number_fetched
    if reader.number_fetched > 0:
        record = reader.records[0]
        record.fetch()
        assert isinstance(record.to_graph(), Graph)
        # Take the IRI and check if searching by IRI gives
        # the same result
        iri = record.iri
        if iri is not None:
            samerecord = reader.get_by_iri(iri)
            assert samerecord.iri == iri
        else:
            warnings.warn(
                UserWarning(f"Record {record} has empty IRI")
            )
