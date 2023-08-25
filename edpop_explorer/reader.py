from abc import ABC, abstractmethod
from typing import Optional, List
from rdflib import Graph, RDF, URIRef

from edpop_explorer import (
    EDPOPREC, BIBLIOGRAPHICAL, BIOGRAPHICAL, bind_common_namespaces
)
from .record import Record



class Reader(ABC):
    '''Base reader class (abstract).

    This abstract base class provides a common interface for all readers.
    To use, instantiate a subclass, set a query using the 
    ``prepare_query()`` or ``set_query()`` method, call ``fetch()``
    and subsequently ``fetch_next()`` until you have the number
    of results that you want. The attributes ``number_of_results``,
    ``number_fetched`` and ``records`` will be updated after 
    fetching.

    To create a concrete reader, make a subclass that implements the 
    ``fetch()``, ``fetch_next()`` and ``transform_query()`` methods
    and set the ``READERTYPE`` and ``CATALOG_URIREF`` attributes.
    ``fetch()`` and ``fetch_next()`` should populate the 
    ``records``, ``number_of_results`` and ``number_fetched``
    attributes.
    '''
    number_of_results: Optional[int] = None
    '''The total number of results for the query, including those
    that have not been fetched yet.'''
    number_fetched: Optional[int] = None
    '''The number of results that has been fetched so far.'''
    records: List[Record]
    '''The records that have been fetched as instances of
    (a subclass of) ``Record``.'''
    prepared_query: Optional[str] = None
    '''A transformed version of the query, available after
    calling ``prepare_query()`` or ``set_query``.'''
    READERTYPE: Optional[str] = None
    '''The type of the reader, out of ``BIOGRAPHICAL`` and
    ``BIBLIOGRAPHICAL`` (defined in the ``edpop_explorer`` package).'''
    CATALOG_URIREF: Optional[URIRef] = None
    _graph: Optional[Graph] = None

    @abstractmethod
    def transform_query(self, query: str) -> str:
        '''Return a version of the query that is prepared for use in the
        API.

        This method does not have to be called directly; instead 
        ``prepare_query()`` can be used.'''
        pass

    def prepare_query(self, query: str) -> None:
        '''Prepare a query for use by the reader's API. Updates the 
        ``prepared_query`` attribute.'''
        self.prepared_query = self.transform_query(query)

    def set_query(self, query: str) -> None:
        '''Set an exact query. Updates the ``prepared_query``
        attribute.'''
        self.prepared_query = query

    @abstractmethod
    def fetch(self):
        '''Perform an initial query.'''

    @abstractmethod
    def fetch_next(self):
        '''Perform a subsequental query.'''
        pass

    @classmethod
    def catalog_to_graph(cls) -> Graph:
        '''Create an RDF representation of the catalog that this reader
        supports as an instance of EDPOPREC:Catalog.'''
        g = Graph()
        if not cls.CATALOG_URIREF:
            raise ReaderError(
                'Cannot create graph because catalog IRI has not been set. '
                'This should have been done on class level.'
            )

        # Set reader class
        rdfclass = EDPOPREC.Catalog
        if cls.READERTYPE == BIOGRAPHICAL:
            rdfclass = EDPOPREC.BiographicalCatalog
        elif cls.READERTYPE == BIBLIOGRAPHICAL:
            rdfclass = EDPOPREC.BibliographicalCatalog
        g.add((cls.CATALOG_URIREF, RDF.type, rdfclass))

        # Set namespace prefixes
        bind_common_namespaces(g)
        
        return g


class ReaderError(Exception):
    pass
