from typing import Optional, List, Type, Tuple, ClassVar, Union
from rdflib import Graph, RDF, RDFS, URIRef, BNode, Literal
from rdflib.term import Node
from abc import ABC, abstractmethod

from edpop_explorer import EDPOPREC
from edpop_explorer.fields import Field


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


class APIRecord:
    #: The raw original data of a record
    data: Union[None, dict, RawData]
    _fields: List[Tuple[str, URIRef, Type[Field]]]
    _rdf_class: Node = EDPOPREC.Record
    link: Optional[str] = None
    '''A user-friendly link where the user can find the record'''
    identifier: Optional[str] = None
    '''Unique identifier used by the source catalog'''
    from_catalog: Optional[Type["APIReader"]]
    subject_node: Node
    _graph: Optional[Graph] = None

    def __init__(self, from_catalog: Type["APIReader"]):
        self._fields = []
        self.from_catalog = from_catalog
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
        if self.from_catalog:
            if self.from_catalog.READERTYPE == APIReader.BIOGRAPHICAL:
                rdfclass = EDPOPREC.BiographicalRecord
            elif self.from_catalog.READERTYPE == APIReader.BIBLIOGRAPHICAL:
                rdfclass = EDPOPREC.BibliographicalRecord
        g.add((
            self.subject_node,
            RDF.type,
            rdfclass
        ))
        if self.from_catalog is not None and \
                self.from_catalog.CATALOG_URIREF is not None:
            g.add((
                self.subject_node,
                EDPOPREC.fromCatalog,
                self.from_catalog.CATALOG_URIREF
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


class BibliographicalRecord(APIRecord):
    _rdf_class = EDPOPREC.BibliographicalRecord
    title: Optional[Field] = None
    alternative_title: Optional[Field] = None
    contributor: Optional[Field] = None
    publisher_or_printer: Optional[Field] = None
    place_of_publication: Optional[Field] = None
    dating: Optional[Field] = None
    languages: Optional[List[Field]] = None
    extent: Optional[Field] = None
    size: Optional[Field] = None
    physical_description: Optional[Field] = None

    def __init__(self, from_reader: Type["APIReader"]):
        super().__init__(from_reader)
        assert isinstance(self._fields, list)
        self._fields += [
            ('title', EDPOPREC.title, Field),
            ('alternative_title', EDPOPREC.alternativeTitle, Field),
            ('contributor', EDPOPREC.contributor, Field),
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


class APIReader(ABC):
    number_of_results: Optional[int] = None
    number_fetched: Optional[int] = None
    records: List[APIRecord]
    prepared_query: Optional[str] = None
    READERTYPE: Optional[str] = None
    CATALOG_URIREF: Optional[URIRef] = None
    _graph: Optional[Graph] = None

    BIOGRAPHICAL: ClassVar[str] = 'biographical'
    BIBLIOGRAPHICAL: ClassVar[str] = 'bibliographical'

    @abstractmethod
    def transform_query(self, query: str) -> str:
        pass

    def prepare_query(self, query: str) -> None:
        self.prepared_query = self.transform_query(query)

    def set_query(self, query: str) -> None:
        '''Set an exact query'''
        self.prepared_query = query

    @abstractmethod
    def fetch(self):
        raise NotImplementedError('Should be implemented by subclass')

    @abstractmethod
    def fetch_next(self):
        raise NotImplementedError('Should be implemented by subclass')

    def catalog_to_graph(self) -> Graph:
        '''Create an RDF representation of the catalog that this reader
        supports as an instance of EDPOPREC:Catalog.'''
        g = Graph()
        if not self.CATALOG_URIREF:
            raise APIException(
                'Cannot create graph because catalog IRI has not been set. '
                'This should have been done on class level.'
            )

        # Set reader class
        rdfclass = EDPOPREC.Catalog
        if self.READERTYPE == self.BIOGRAPHICAL:
            rdfclass = EDPOPREC.BiographicalCatalog
        elif self.READERTYPE == self.BIBLIOGRAPHICAL:
            rdfclass = EDPOPREC.BibliographicalCatalog
        g.add((self.CATALOG_URIREF, RDF.type, rdfclass))

        # Set namespace prefixes
        g.bind('rdf', RDF)
        g.bind('rdfs', RDFS)
        g.bind('edpoprec', EDPOPREC)

        return g


class APIException(Exception):
    pass
