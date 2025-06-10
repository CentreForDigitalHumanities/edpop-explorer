from abc import ABC, abstractmethod
from typing import Type, Tuple, Union, Optional, List, TYPE_CHECKING
from rdflib.term import Node
from rdflib import URIRef, Graph, BNode, RDF, Literal

from edpop_explorer import (
    EDPOPREC, Field, BIBLIOGRAPHICAL, BIOGRAPHICAL, bind_common_namespaces,
    DigitizationField
)

if TYPE_CHECKING:
    from edpop_explorer import Reader


class RawData(ABC):
    """Base class to store raw original data of a record. Only defines
    an abstract method ``to_dict``.
    """

    @abstractmethod
    def to_dict(self) -> dict:
        """Give a ``dict`` representation of the raw data."""
        pass


class RecordError(Exception):
    pass


class Record:
    """Python representation of edpoprec:Record.

    This base class provides some basic attributes, an infrastructure
    to define fields and a method to convert the record to RDF.
    While this is a non-abstract base class, no fields are
    defined here -- these should be added in subclasses. ``Record``
    and its subclasses should be created by calling the constructor
    with the ``Reader`` class as the ``from_reader`` parameter
    and by setting the ``data``, ``link``, ``identifier`` and
    ``subject_node`` attributes (all are optional but recommended),
    as well as the fields that are defined by the subclass.
    fields are set using the attribute with the same name:
    set them to an instance of ``Field`` or to ``None``. The
    basic attributes and the fields are ``None`` by default.

    Subclasses should override the ``_rdf_class`` attribute to
    the corresponding RDF class. They should define additional 
    fields by adding additional public attributes defaulting
    to ``None`` and by registring them in the ``_fields`` attribute.
    For registring, a constructor ``__init__`` should be defined
    that first calls the parent's constructor and then adds the
    fields by adding tuples to ``_fields`` in the form
    ``('<attribute-name>', EDPOPREC.<rdf-property-name>,
    <Field class name>)``.
    """
    #: The raw original data of a record.
    data: Union[None, dict, RawData] = None
    _fields: List[Tuple[str, URIRef, Type[Field]]]
    _rdf_class: Node = EDPOPREC.Record
    link: Optional[str] = None
    '''A user-friendly link where the user can find the record.'''
    identifier: Optional[str] = None
    '''Unique identifier used by the source catalog.'''
    from_reader: Type["Reader"]
    '''The subject node, which will be used to convert the record to 
    RDF. This is a blank node by default.'''
    _graph: Optional[Graph] = None
    _bnode: Optional[BNode] = None

    def __init__(self, from_reader: Type["Reader"]):
        self._fields = []
        self.from_reader = from_reader

    def to_graph(self) -> Graph:
        '''Return an RDF graph for this record.'''
        self.fetch()
        g = Graph()
        
        # Set basic properties
        rdfclass = EDPOPREC.Record
        if self.from_reader:
            if self.from_reader.READERTYPE == BIOGRAPHICAL:
                rdfclass = EDPOPREC.BiographicalRecord
            elif self.from_reader.READERTYPE == BIBLIOGRAPHICAL:
                rdfclass = EDPOPREC.BibliographicalRecord
        g.add((
            self.subject_node,
            RDF.type,
            rdfclass
        ))
        if self.from_reader is not None and \
                self.from_reader.CATALOG_URIREF is not None:
            g.add((
                self.subject_node,
                EDPOPREC.fromCatalog,
                self.from_reader.CATALOG_URIREF
            ))
        if self.identifier:
            g.add((
                self.subject_node,
                EDPOPREC.identifier,
                Literal(self.identifier)
            ))
        if self.link:
            g.add((
                self.subject_node,
                EDPOPREC.publicURL,
                Literal(self.link)
            ))
        original_data = self.get_data_dict()
        if original_data is not None:
            g.add((
                self.subject_node,
                EDPOPREC.originalData,
                Literal(original_data, datatype=RDF.JSON)
            ))

        # Put all fields from self.FIELDS in the graph by accessing
        # the associated attributes or properties. If they contain a
        # list of Fields, repeat them in RDF.
        assert isinstance(self._fields, list)
        for field in self._fields:
            attrname, propref, fieldclass = field
            if not issubclass(fieldclass, Field):
                raise RecordError(
                    f"{attrname} in {self.__class__}.FIELDS is defined as being "
                    "of type {fieldclass}, but this type does not inherit from "
                    "Field."
                )
            value_or_values = getattr(self, attrname, None)
            if isinstance(value_or_values, list):
                values = value_or_values
            else:
                values = [value_or_values]
            for value in values:
                if value is None:
                    # self does not have the attribute or the attribute's value
                    # is None; ignore
                    continue
                if not isinstance(value, fieldclass):
                    raise RecordError(
                        f"{attrname} attribute is of type {type(value)} while an "
                        "instance of {fieldclass} was expected."
                    )
                partial_graph = value.to_graph()
                g.add((self.subject_node, propref, value.subject_node))
                g += partial_graph

        # Set namespace prefixes
        bind_common_namespaces(g)

        return g

    def get_data_dict(self) -> Optional[dict]:
        """Convenience function to get the record's raw data as a ``dict``,
        or ``None`` if it is not available."""
        self.fetch()
        if isinstance(self.data, RawData):
            return self.data.to_dict()
        else:
            # self.data should be dict or None
            return self.data

    def __str__(self):
        if self.identifier:
            return f'{self.__class__} object ({self.identifier})'
        else:
            return f'{self.__class__} object'

    def fetch(self) -> None:
        '''Fetch the full contents of the record if this record works with
        lazy loading (i.e., if the record's class derives from
        ``RDFRecordMixin``). If the record is not lazy, this method does
        nothing.'''
        pass

    @property
    def iri(self) -> Optional[str]:
        '''A stable IRI based on the `identifier` attribute. `None` if
        the `identifier` attribute is not set.'''
        if self.identifier:
            return self.from_reader.identifier_to_iri(self.identifier)
        else:
            return None

    @property
    def subject_node(self) -> Node:
        '''A subject node based on the `identifier` attribute. If the 
        `identifier` attribute is not set, a blank node.'''
        iri = self.iri
        if iri is not None:
            return URIRef(iri)
        else:
            # IRI is not available; return a consistent blank node
            if not self._bnode:
                self._bnode = BNode()
            return self._bnode


class BibliographicalRecord(Record):
    '''Python representation of edpoprec:BibliographicalRecord.

    This subclass adds fields that are specific for bibliographical
    records.
    '''
    _rdf_class = EDPOPREC.BibliographicalRecord
    title: Optional[Field] = None
    alternative_title: Optional[Field] = None
    contributors: Optional[List[Field]] = None
    publisher_or_printer: Optional[Field] = None
    place_of_publication: Optional[Field] = None
    dating: Optional[Field] = None
    languages: Optional[List[Field]] = None
    extent: Optional[Field] = None
    size: Optional[Field] = None
    physical_description: Optional[Field] = None
    bookseller: Optional[Field] = None
    bibliographical_format: Optional[Field] = None
    fingerprint: Optional[Field] = None
    collation_formula: Optional[Field] = None
    genres: Optional[List[Field]] = None
    holdings: Optional[List[Field]] = None
    typographical_features: Optional[List[Field]] = None
    digitization: Optional[List[Field]] = None

    def __init__(self, from_reader: Type["Reader"]):
        super().__init__(from_reader)
        assert isinstance(self._fields, list)
        self._fields += [
            ('title', EDPOPREC.title, Field),
            ('alternative_title', EDPOPREC.alternativeTitle, Field),
            ('contributors', EDPOPREC.contributor, Field),
            ('publisher_or_printer', EDPOPREC.publisherOrPrinter, Field),
            ('place_of_publication', EDPOPREC.placeOfPublication, Field),
            ('dating', EDPOPREC.dating, Field),
            ('languages', EDPOPREC.language, Field),
            ('extent', EDPOPREC.extent, Field),
            ('size', EDPOPREC.size, Field),
            ('physical_description', EDPOPREC.physicalDescription, Field),
            ('bookseller', EDPOPREC.bookseller, Field),
            ('bibliographical_format', EDPOPREC.bibliographicalFormat, Field),
            ('fingerprint', EDPOPREC.fingerprint, Field),
            ('collation_formula', EDPOPREC.collationFormula, Field),
            ('genres', EDPOPREC.genre, Field),
            ('holdings', EDPOPREC.holdings, Field),
            ('typographical_features', EDPOPREC.typographicalFeatures, Field),
            ('digitization', EDPOPREC.digitization, DigitizationField),
        ]

    def __str__(self) -> str:
        if self.title:
            return str(self.title)
        else:
            return super().__str__()


class BiographicalRecord(Record):
    '''Python representation of edpoprec:BiographicalRecord.

    This subclass adds fields that are specific for biographical records.
    '''
    _rdf_class = EDPOPREC.BiographicalRecord
    name: Optional[Field] = None
    variant_names: Optional[List[Field]] = None
    place_of_birth: Optional[Field] = None
    place_of_death: Optional[Field] = None
    places_of_activity: Optional[List[Field]] = None
    activity_timespan: Optional[Field] = None
    activities: Optional[List[Field]] = None
    gender: Optional[Field] = None
    timespan: Optional[Field] = None

    def __init__(self, from_reader: Type["Reader"]):
        super().__init__(from_reader)
        assert isinstance(self._fields, list)
        self._fields += [
            ('name', EDPOPREC.name, Field),
            ('variant_names', EDPOPREC.variantName, Field),
            ('place_of_birth', EDPOPREC.placeOfBirth, Field),
            ('place_of_death', EDPOPREC.placeOfDeath, Field),
            ('places_of_activity', EDPOPREC.placeOfActivity, Field),
            ('activity_timespan', EDPOPREC.activityTimespan, Field),
            ('activities', EDPOPREC.activity, Field),
            ('gender', EDPOPREC.gender, Field),
            ('timespan', EDPOPREC.timespan, Field),
        ]

    def __str__(self) -> str:
        if self.name:
            return str(self.name)
        else:
            return super().__str__()


class LazyRecordMixin(ABC):
    '''Abstract mixin that adds an interface for lazy loading to a Record.

    To use, implement the ``fetch()`` method and make sure that it fills
    the record's ``data`` attributes and its Fields and that the 
    ``fetched`` attribute is set to ``True``.'''
    fetched: bool = False
    
    @abstractmethod
    def fetch(self) -> None:
        pass
