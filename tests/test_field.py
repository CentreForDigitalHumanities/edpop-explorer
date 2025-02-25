from pytest import fixture, raises
from rdflib import Literal, RDF
from rdflib.term import Node

from edpop_explorer import Field, FieldError, LocationField
from edpop_explorer import EDPOPREC
from tests.test_reader import SimpleReader


@fixture
def basic_field() -> Field:
    return Field('Dit is een boektitel')


@fixture
def basic_location_field() -> LocationField:
    field = LocationField('Voorschoten')
    return field


class TestField:
    def test_init(self, basic_field: Field):
        assert basic_field.original_text == 'Dit is een boektitel'
        assert isinstance(basic_field.subject_node, Node)

    def test_to_graph(self, basic_field: Field):
        graph = basic_field.to_graph()
        assert (basic_field.subject_node, RDF.type, EDPOPREC.Field) in graph
        # Test simple string
        assert (
            basic_field.subject_node,
            EDPOPREC.originalText,
            Literal(basic_field.original_text)
        ) in graph
        # Test boolean
        basic_field.unknown = True
        graph = basic_field.to_graph()
        assert (
            basic_field.subject_node,
            EDPOPREC.unknown,
            Literal(True)
        ) in graph
        # Invalid type on object should give exception
        basic_field.unknown = 'other value'  # type: ignore
        with raises(FieldError):
            basic_field.to_graph()
        # Nonexisting datatype defined in class on SUBFIELDS should give
        # exception
        basic_field._subfields = basic_field._subfields.copy()
        basic_field._subfields.append(
            ('other', EDPOPREC.other, 'othertype')
        )
        basic_field.other = 'text'  # type: ignore
        with raises(FieldError):
            basic_field.to_graph()

    def test_iri_absent(self, basic_field: Field):
        # If a field is not bound to a record, the IRI cannot be generated
        assert basic_field.iri is None

    def test_iri_basic(self):
        record = SimpleReader.get_by_id("0")
        field = record.get_first_field("title")
        assert field.iri is None  # Field is not yet bound, so IRI should be None
        record.bind_all_fields()
        assert isinstance(field.iri, str)  # Now IRI should be available

    def test_iri_different_records(self):
        # Assert that the same field on a different record has a different IRI
        record1 = SimpleReader.get_by_id("0")
        record2 = SimpleReader.get_by_id("1")
        record1.bind_all_fields()
        record2.bind_all_fields()
        assert record1.get_first_field("title").iri != record2.get_first_field("title").iri

    def test_iri_different_value(self):
        # Assert that a field with different contents has a different IRI
        record = SimpleReader.get_by_id("0")
        record.bind_all_fields()
        field = record.get_first_field("title")
        iri1 = field.iri
        record.title = None
        record.add_field("title", Field("Andere titel"))  # Add a different title field
        record.bind_all_fields()
        field = record.get_first_field("title")
        iri2 = field.iri
        assert iri1 != iri2

    def test_iri_different_field(self):
        # Assert that a field with different contents has a different IRI
        record = SimpleReader.get_by_id("0")
        record.bind_all_fields()
        field1 = record.get_first_field("title")
        iri1 = field1.iri
        record.add_field("alternative_title", Field(field1.original_text))  # Add a different title field
        record.bind_all_fields()
        field2 = record.get_first_field("alternative_title")
        iri2 = field2.iri
        assert iri1 != iri2

class TestLocationField:
    def test_basic_form(self, basic_location_field: LocationField):
        field = basic_location_field
        graph = field.to_graph()
        assert (
            field.subject_node,
            EDPOPREC.locationType,
            None
        ) not in graph

    def test_location_type(self, basic_location_field: LocationField):
        field = basic_location_field
        field.location_type = LocationField.LOCALITY
        graph = field.to_graph()
        assert (
            field.subject_node,
            EDPOPREC.locationType,
            EDPOPREC.locality
        ) in graph
