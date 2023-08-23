from abc import ABC, abstractmethod
from typing import Type, Tuple, Union, Optional, List, TYPE_CHECKING
from rdflib.term import Node
from rdflib import URIRef, Graph, BNode, RDF, RDFS, Literal

from edpop_explorer import EDPOPREC, Field, BIBLIOGRAPHICAL, BIOGRAPHICAL

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
    #: The raw original data of a record
    data: Union[None, dict, RawData]
    _fields: List[Tuple[str, URIRef, Type[Field]]]
    _rdf_class: Node = EDPOPREC.Record
    link: Optional[str] = None
    '''A user-friendly link where the user can find the record'''
    identifier: Optional[str] = None
    '''Unique identifier used by the source catalog'''
    from_reader: Optional[Type["Reader"]]
    subject_node: Node
    _graph: Optional[Graph] = None

    def __init__(self, from_reader: Type["Reader"]):
        self._fields = []
        self.from_reader = from_reader
        self.subject_node = BNode()

    def get_title(self) -> Optional[str]:
        '''Convenience method to retrieve the title of a record in a standard
        way'''
        # Stays here for now for compatibility
        return self.__str__()

    def show_record(self) -> str:
        '''Give a multiline string representation of the record's contents'''
        raise NotImplementedError('Should be implemented by subclass')

    def to_graph(self) -> Graph:
        '''Create an RDF graph for this record and put it in the rdf
        attribute.'''
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
        g.bind('rdf', RDF)
        g.bind('rdfs', RDFS)
        g.bind('edpoprec', EDPOPREC)

        return g

    def get_data_dict(self) -> Optional[dict]:
        """Convenience function to get the record's raw data as a ``dict``,
        or ``None`` if it is not available."""
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


class BibliographicalRecord(Record):
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
        ]

    def __str__(self) -> str:
        if self.title:
            return str(self.title)
        else:
            return super().__str__()
