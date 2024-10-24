"""Test all readers for basic sanity, without invoking methods that could
access the internet or manipulate files."""

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
    rng = reader.fetch(5)
    assert reader.number_of_results is not None
    assert reader.number_fetched == len(reader.records)
    assert rng == range(0, reader.number_fetched)
    if not reader.fetching_exhausted:
        # Assert that maximum number of results is respected if reader does
        # not fetch all results at once
        assert reader.number_fetched <= 5
    assert reader.number_of_results >= reader.number_fetched
    if reader.number_fetched > 0:
        record = reader.records[0]
        assert record is not None
        record.fetch()
        assert isinstance(record.to_graph(), Graph)
        # Take the IRI and check if searching by IRI gives
        # the same result
        iri = record.iri
        if iri is not None:
            samerecord = reader.get_by_iri(iri)
            assert samerecord.iri == iri
        else:
            warnings.warn(UserWarning(f"Record {record} has empty IRI"))
    # Perform a second fetch
    fetched_before = reader.number_fetched
    rng2 = reader.fetch()  # Do not pass number of results to test that as well
    # If not all records had been fetched already, more records
    # should be available now. Otherwise, nothing should have
    # changed.
    if fetched_before < reader.number_of_results:
        assert reader.number_fetched > fetched_before
        assert rng2.start == fetched_before
        assert rng2.stop == reader.number_fetched
        # Assert that the last record of the previous fetch is not the same as
        # the first record of the current fetch
        record1 = reader.records[fetched_before - 1]
        record2 = reader.records[fetched_before]
        assert record1 is not None and record2 is not None
        if record1.identifier is not None and record1.identifier == record2.identifier:
            # Both records have the same identifier, which could mean that
            # there was a mistake with the offsets. But just give a warning,
            # because there are APIs that (by mistake?) return duplicated
            # records.
            warnings.warn(UserWarning("Last record from first fetch is same as first record from second fetch"))
    else:
        assert reader.number_fetched == fetched_before
        assert rng2 == range(0)
