"""This module defines ``Field`` and a number of subclasses for specialized
fields. 
"""

from typing import Optional, Callable, List, Tuple

from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
from rdflib import Graph, Literal, BNode, RDF, URIRef
from rdflib.term import Node

from edpop_explorer import EDPOPREC, normalizers
from edpop_explorer.normalizers import NormalizationResult
from edpop_explorer.normalization import relators

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
    },
    'uriref': {
        'input_type': str,
        'converter': lambda x: URIRef(x),
    },
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
    #: Subfield -- indicates whether the value of this field is explicitly
    #: marked as unknown in the original record.
    unknown: Optional[bool] = None
    #: Subfield -- may contain the URI of an authority record
    authority_record: Optional[str] = None
    normalizer: Optional[Callable] = None
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
            ('summary_text', EDPOPREC.summaryText, 'string'),
            ('unknown', EDPOPREC.unknown, 'boolean'),
            ('authority_record', EDPOPREC.authorityRecord, 'uriref'),
        ]

    def normalize(self) -> NormalizationResult:
        """Perform normalization on this field, based on the ``normalizer``
        attribute. Subclasses of ``Field`` may predefine a normalizer function,
        but this can always be overridden."""
        return self.normalizer()

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

    @property
    def summary_text(self) -> Optional[str]:
        return None

    def __str__(self) -> str:
        if self.summary_text is not None:
            return self.summary_text
        else:
            return self.original_text


class LocationField(Field):
    _rdf_class: Node = EDPOPREC.LocationField
    location_type: Optional[URIRef] = None
    LOCALITY = EDPOPREC.locality
    COUNTRY = EDPOPREC.country

    def __init__(self, original_text: str) -> None:
        super().__init__(original_text)
        self._subfields.append(
            ('location_type', EDPOPREC.locationType, 'uriref')
        )


class LanguageField(Field):
    _rdf_class = EDPOPREC.LanguageField
    language_code: Optional[str] = None
    normalizer = normalizers.normalize_by_language_code

    def __init__(self, original_text: str) -> None:
        super().__init__(original_text)
        self._subfields.append(
            ('language_code', EDPOPREC.languageCode, 'string')
        )

    @property
    def summary_text(self) -> Optional[str]:
        try:
            language = Lang(self.language_code)
            return language.name
        except InvalidLanguageValue:
            return None


class ContributorField(Field):
    _rdf_class = EDPOPREC.ContributorField
    role: Optional[str] = None
    name: Optional[str] = None

    def __init__(self, original_text: str) -> None:
        super().__init__(original_text)
        self._subfields.extend((
            ('name', EDPOPREC.name, 'string'),
            ('role', EDPOPREC.role, 'string'),
        ))

    @property
    def summary_text(self) -> Optional[str]:
        role = relators.relator_dict.get(self.role, self.role)
        name = self.name if self.name is not None else self.original_text
        if role is not None:
            return f"{name} ({role})"
        else:
            return name


class DigitizationField(Field):
    _rdf_class = EDPOPREC.DigitizationField
    description: Optional[str] = None
    url: Optional[str] = None
    iiif_manifest: Optional[str] = None
    preview_url: Optional[str] = None

    def __init__(self, original_text: str) -> None:
        super().__init__(original_text)
        self._subfields.extend((
            ('description', EDPOPREC.description, 'string'),
            ('url', EDPOPREC.url, 'string'),
            ('iiif_manifest', EDPOPREC.iiifManifest, 'string'),
            ('preview_url', EDPOPREC.previewURL, 'string'),
        ))

    @property
    def summary_text(self) -> Optional[str]:
        if self.description is not None:
            return self.description
        elif self.iiif_manifest is not None:
            return self.iiif_manifest
        elif self.url is not None:
            return self.url
        else:
            return self.original_text
