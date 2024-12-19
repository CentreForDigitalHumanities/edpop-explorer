from pytest import fixture, raises
from rdflib import Literal, RDF
from rdflib.term import Node

from edpop_explorer import Field, FieldError, LocationField
from edpop_explorer import EDPOPREC


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
