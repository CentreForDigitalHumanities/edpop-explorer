from pytest import fixture, raises
from rdflib import Literal, RDF
from rdflib.term import Node

from edpop_explorer import Field, FieldError
from edpop_explorer import EDPOPREC


@fixture
def basic_field() -> Field:
    return Field('Dit is een boektitel')


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
        # Test string from property
        basic_field.set_normalized_text('normalized')
        graph = basic_field.to_graph()
        assert (
            basic_field.subject_node,
            EDPOPREC.normalizedText,
            Literal(basic_field.normalized_text)
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

    def test_normalized_text(self, basic_field: Field):
        # If nothing is set, this should be None
        assert basic_field.normalized_text is None
        # Set normalized text by hand
        text = 'normalized'
        basic_field.set_normalized_text(text)
        assert basic_field.normalized_text == text
        # Now test a class with automatic normalized text creation

        class ComplexField(Field):
            def _create_normalized_text(self):
                return self.original_text.capitalize()
        title = 'title'
        complex_field = ComplexField(title)
        assert complex_field.normalized_text == title.capitalize()
        # A manual normalized text should override this
        complex_field.set_normalized_text(text)
        assert complex_field.normalized_text == text
