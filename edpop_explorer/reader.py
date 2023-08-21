from abc import ABC, abstractmethod
from typing import Optional, List, Type, Tuple, ClassVar, Union
from rdflib import Graph, RDF, RDFS, URIRef, BNode, Literal

from edpop_explorer import EDPOPREC
from .record import Record



class Reader(ABC):
    number_of_results: Optional[int] = None
    number_fetched: Optional[int] = None
    records: List[Record]
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
            raise ReaderError(
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


class ReaderError(Exception):
    pass
