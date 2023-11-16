'''Test all readers for basic sanity, without invoking methods that could
access the internet or manipulate files.'''

import pytest
from typing import Type

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
    assert isinstance(readercls.transform_query("testquery"), str)


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
