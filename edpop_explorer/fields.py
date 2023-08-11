"""This module defines Field and a number of subclasses.

A Field (edpoprec:Field) in 
"""

from typing import Optional, Callable, List, Tuple
from rdflib import Graph, Literal, BNode, RDF, URIRef
from rdflib.term import Node
from dataclasses import dataclass

from edpop_explorer import EDPOPREC


DATATYPES = {
    'string': {
        'input_type': str,
        'converter': (lambda x: Literal(x)),
    },
    'boolean': {
        'input_type': bool,
        'converter': (lambda x: Literal(x)),
    },
}


class FieldError(Exception):
    pass


@dataclass
class Field:
    """Python representation of edpoprec:Field.

    Instantiate with the original text, which is the only required attribute.
    Use to_graph() to obtain an RDF graph. The subject node is by default 
    a blank node, but this may be overridden by setting the subject_node 
    attribute. This base class does not provide any normalization.

    Subclasses should override the RDF_CLASS attribute to the corresponding
    RDF class.
    Subclasses of Field define more specific kinds of fields that offer more
    complexity, as well as a default way of """
    original_text: str
    __doc_original_text__ = "The text as it was directly taken from the original record"
    subject_node: Node
    SUBFIELDS: List[Tuple[str, URIRef, str]]
    _normalized_text: Optional[str] = None
    unknown: Optional[bool] = None
    _create_normalized_text: Optional[Callable] = None
    RDF_CLASS: Node = EDPOPREC.Field
    
    def __init__(self, original_text: str) -> None:
        self.subject_node = BNode()
        self.original_text = original_text
        self.SUBFIELDS = [
            ('original_text', EDPOPREC.originalText, 'string'),
            ('normalized_text', EDPOPREC.normalizedText, 'string'),
            ('unknown', EDPOPREC.unknown, 'boolean'),
        ]

    def set_normalized_text(self, text: Optional[str]):
        """Manually set the normalized text.

        In case of subclasses that support automatic creation of the 
        normalized text, this method will override the automatic version. 
        Give None as an argument to reset the normalized text."""
        self._normalized_text = text

    @property
    def normalized_text(self) -> Optional[str]:
        """A human-readable string representation of the normalized field.

        Should be set manually in the basic Field class with set_normalized_text
        or is automatically created in more complex subclasses. Contains None in
        case there is no normalization."""
        if self._normalized_text is not None:
            return self._normalized_text
        if callable(self._create_normalized_text):
            text = self._create_normalized_text()
            assert type(text) == str
            return text
        else:
            return None

    def to_graph(self) -> Graph:
        assert isinstance(self.subject_node, Node)
        graph = Graph()
        graph.add((
            self.subject_node,
            RDF.type,
            self.RDF_CLASS
        ))
        for subfield in self.SUBFIELDS:
            attrname, propref, datatype = subfield
            value = getattr(self, attrname, None)
            if value is None:
                # self does not have the attribute or the attribute is None;
                # ignore.
                continue
            try:
                typedef = DATATYPES[datatype]
            except ValueError:
                raise FieldError(
                    f"Datatype '{datatype}' was defined in subfield list on {self.__class__}"
                    "but it does not exist"
                )
            else:
                input_type = typedef['input_type']
                if type(value) != input_type:
                    raise FieldError(
                        f"Subfield {attrname} should be of type {str(input_type)} but "
                        "it is {str(type(value))}"
                    )
                else:
                    converter = typedef['converter']
                    converted = converter(value)
                    assert isinstance(converted, Node)
                    graph.add((
                        self.subject_node,
                        propref,
                        converted
                    ))
        return graph

    def __str__(self) -> str:
        if self.normalized_text is not None:
            return self.normalized_text
        else:
            return self.original_text

