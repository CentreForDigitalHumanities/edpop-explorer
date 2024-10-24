import pytest
from rdflib import Literal, URIRef
from typing import Optional, List

from edpop_explorer import Record, Reader, Field, RecordError
from edpop_explorer import EDPOPREC
from edpop_explorer.record import BiographicalRecord


class SimpleReader(Reader):
    CATALOG_URIREF = URIRef('http://example.com/reader')
    IRI_PREFIX = "http://example.com/records/reader/"


class SimpleRecord(Record):
    _rdf_class = EDPOPREC.SimpleRecord
    testfield: Optional[Field] = None
    multiplefield: Optional[List[Field]] = None

    def __init__(self, from_reader):
        super().__init__(from_reader)
        self._fields.extend([
            ('testfield', EDPOPREC.testField, Field),
            ('multiplefield', EDPOPREC.multipleField, Field)
        ])


@pytest.fixture
def basic_record():
    record = SimpleRecord(SimpleReader)
    record.link = 'http://example.com'
    record.identifier = '123'
    return record


def test_iri(basic_record: SimpleRecord):
    assert basic_record.iri == "http://example.com/records/reader/123"


def test_iri_empty(basic_record: SimpleRecord):
    basic_record.identifier = None
    assert basic_record.iri is None


def test_subject_node(basic_record: SimpleRecord):
    assert basic_record.subject_node == \
            URIRef("http://example.com/records/reader/123")


def test_to_graph_empty():
    # Test if it works with an empty record
    record = Record(SimpleReader)
    g = record.to_graph()
    assert (
        record.subject_node, EDPOPREC.fromCatalog, SimpleReader.CATALOG_URIREF
    ) in g
    

def test_to_graph_basic_attributes(basic_record):
    g = basic_record.to_graph()
    assert (
        basic_record.subject_node, EDPOPREC.publicURL, Literal(basic_record.link)
    ) in g
    assert (
        basic_record.subject_node, EDPOPREC.identifier, Literal(basic_record.identifier)
    ) in g


def test_to_graph_empty_field(basic_record):
    # If testfield is None (the default), it should be absent from the graph
    g = basic_record.to_graph()
    assert (basic_record.subject_node, EDPOPREC.testField, None) not in g


def test_to_graph_field_normal_value(basic_record):
    basic_record.testfield = Field('test')
    g = basic_record.to_graph()
    assert (basic_record.subject_node, EDPOPREC.testField, None) in g
    

def test_to_graph_string_in_field(basic_record):
    basic_record.testfield = 'test'  # type: ignore
    with pytest.raises(RecordError):
        basic_record.to_graph()
    
def test_to_graph_field_multiple_values(basic_record):
    # Try a field that accepts multiple values
    basic_record.multiplefield = [
        Field('v1'), Field('v2')
    ]
    g = basic_record.to_graph()
    assert len(list(
        g.objects(basic_record.subject_node, EDPOPREC.multipleField)
    )) == 2

def test_biographicalrecord():
    # Basic test to check if class definition is sane; the logic should be
    # handled by super class
    record = BiographicalRecord(SimpleReader)
    record.to_graph()

def test_biographicalrecord_str():
    record = BiographicalRecord(SimpleReader)
    personname = "Person"
    record.name = Field(personname)
    assert str(record) == personname
