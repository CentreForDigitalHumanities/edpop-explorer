from pytest import raises
from rdflib import Literal, URIRef
from typing import Optional, List

from edpop_explorer import Record, Reader, Field, RecordError
from edpop_explorer import EDPOPREC


class SimpleReader(Reader):
    CATALOG_URIREF = URIRef('http://example.com/reader')


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


class TestRecord:
    def test_to_graph(self):
        record = Record(SimpleReader)
        # Test if it works with an empty record
        g = record.to_graph()
        assert (
            record.subject_node, EDPOPREC.fromCatalog, SimpleReader.CATALOG_URIREF
        ) in g
        # Add basic attributes
        record.link = 'http://example.com'
        record.identifier = '123'
        g = record.to_graph()
        assert (
            record.subject_node, EDPOPREC.publicURL, Literal(record.link)
        ) in g
        assert (
            record.subject_node, EDPOPREC.identifier, Literal(record.identifier)
        ) in g
        # Now test a record with a field
        record = SimpleRecord(SimpleReader)
        # If testfield is None, it should be absent from the graph
        g = record.to_graph()
        assert (record.subject_node, EDPOPREC.testField, None) not in g
        # Now with a value for testfield
        record.testfield = Field('test')
        g = record.to_graph()
        assert (record.subject_node, EDPOPREC.testField, None) in g
        # Now try to assign a string to testfield instead of a Field
        record.testfield = 'test'  # type: ignore
        with raises(RecordError):
            g = record.to_graph()
        # Try a field that accepts multiple values
        record.testfield = None
        record.multiplefield = [
            Field('v1'), Field('v2')
        ]
        g = record.to_graph()
        assert len(list(
            g.objects(record.subject_node, EDPOPREC.multipleField)
        )) == 2
