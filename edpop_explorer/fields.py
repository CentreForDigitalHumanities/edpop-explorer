"""This module defines ``Field`` and a number of subclasses for specialized
fields. 
"""

from typing import Optional, Callable, List, Tuple
from rdflib import Graph, Literal, BNode, RDF, URIRef
from rdflib.term import Node

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
    'edtf': {
        'input_type': str,
        'converter': (
            lambda x: Literal(
                x, datatype=URIRef("http://id.loc.gov/datatypes/edtf")
            )
        )
    }
}


class FieldError(Exception):
    pass


class Field:
    """Python representation of edpoprec:Field.

    This base class has two user-defined subfields: ``original_text`` (which is
    required and should be passed to the constructor), and ``unknown``.
    User-defined subfields are simple object attributes and can be accessed
    directly. In addition, this base class defines an automatic
    subfield ``normalized_text``, which is a read-only property that is only
    available if normalization is supported by the field -- this is
    not the case for this base class. In those cases, it is still possible to
    set this field using the ``set_normalized_text`` method.
    Except ``original_text``, all subfields are optional and are None by default.
    Use ``to_graph()`` to obtain an RDF graph. The subject node is by default 
    a blank node, but this may be overridden by setting the subject_node 
    attribute.

    Subclasses should override the ``_rdf_class`` attribute to the corresponding
    RDF class. Subclasses can define additional subfields by adding additional
    public attributes and by registring them in the ``SUBFIELDS`` constant
    attribute. For registring, a constructor ``__init__`` should be defined that
    first calls the parent's constructor and then adds the subfields one
    by one using ``self.SUBFIELDS.append(('<attribute-name>',
    EDPOPREC.<rdf-property-name>, '<datatype>'))``, where <datatype> is any
    of the datatypes defined in the ``DATATYPES`` constant of this module.
    Subclasses may furthermore define the ``_normalized_text`` private 
    method."""
    #: Subfield -- text of this field according to the original record.
    original_text: str
    #: This field's subject node if converted to RDF. This is a blank node
    #: by default.
    subject_node: Node
    _subfields: List[Tuple[str, URIRef, str]]
    _normalized_text: Optional[str] = None
    #: Subfield -- indicates whether the value of this field is explicitly
    #: marked as unknown in the original record.
    unknown: Optional[bool] = None
    _create_normalized_text: Optional[Callable] = None
    _rdf_class: Node = EDPOPREC.Field
    
    def __init__(self, original_text: str) -> None:
        if not isinstance(original_text, str):
            raise FieldError(
                f'original_text should be str, not {type(original_text)}'
            )
        self.subject_node = BNode()
        self.original_text = original_text
        self._subfields = [
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
        """Subfield -- a human-readable string representation of the normalized
        field.

        Should be set manually in the basic ``Field`` class with 
        ``set_normalized_text`` or is automatically created in more complex 
        subclasses. Contains ``None`` in case there is no normalization."""
        if self._normalized_text is not None:
            return self._normalized_text
        if callable(self._create_normalized_text):
            text = self._create_normalized_text()
            assert isinstance(text, str)
            return text
        else:
            return None

    def to_graph(self) -> Graph:
        '''Create an ``rdflib`` RDF graph according to the current data.'''
        assert isinstance(self.subject_node, Node)
        graph = Graph()
        graph.add((
            self.subject_node,
            RDF.type,
            self._rdf_class
        ))
        for subfield in self._subfields:
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
                    f"Datatype '{datatype}' was defined in subfield list on "
                    "{self.__class__} but it does not exist"
                )
            else:
                input_type = typedef['input_type']
                if not isinstance(value, input_type):
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

