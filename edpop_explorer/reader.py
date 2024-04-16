from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Union
from rdflib import Graph, RDF, URIRef
from urllib.parse import quote, unquote

from edpop_explorer import (
    EDPOPREC, BIBLIOGRAPHICAL, BIOGRAPHICAL, bind_common_namespaces
)
from .record import Record


@dataclass
class BasePreparedQuery:
    """Empty base dataclass for prepared queries. For prepared queries that
    can be represented by a single string, do not inherit from this class
    but use a simple string instead."""
    pass


PreparedQueryType = Union[str, BasePreparedQuery]


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
    number_fetched: int = 0
    '''The number of results that has been fetched so far, or 0 if
    no fetch has been performed yet.'''
    records: List[Optional[Record]]
    '''The records that have been fetched as instances of
    (a subclass of) ``Record``.'''
    prepared_query: Optional[PreparedQueryType] = None
    '''A transformed version of the query, available after
    calling ``prepare_query()`` or ``set_query``.'''
    READERTYPE: Optional[str] = None
    '''The type of the reader, out of ``BIOGRAPHICAL`` and
    ``BIBLIOGRAPHICAL`` (defined in the ``edpop_explorer`` package).'''
    CATALOG_URIREF: Optional[URIRef] = None
    IRI_PREFIX: Optional[str] = None
    '''The prefix to use to create an IRI out of a record identifier.
    If an IRI cannot be created with a simple prefix, the 
    `identifier_to_iri` and `iri_to_identifier` methods have to be
    overridden.'''
    FETCH_ALL_AT_ONCE = False
    '''True if the reader is configured to fetch all records at once,
    even if the user only needs a subset. If so, it may be economic to
    save the state (by pickling) if the results are needed in a future 
    session.'''
    _graph: Optional[Graph] = None

    def __init__(self):
        self.records = []

    @classmethod
    @abstractmethod
    def transform_query(cls, query: str) -> PreparedQueryType:
        '''Return a version of the query that is prepared for use in the
        API.

        This method does not have to be called directly; instead 
        ``prepare_query()`` can be used.'''
        pass

    def prepare_query(self, query: str) -> None:
        '''Prepare a query for use by the reader's API. Updates the 
        ``prepared_query`` attribute.'''
        self.prepared_query = self.transform_query(query)

    def set_query(self, query: PreparedQueryType) -> None:
        '''Set an exact query. Updates the ``prepared_query``
        attribute.'''
        self.prepared_query = query

    def adjust_start_record(self, start_number: int) -> None:
        """Skip the given number of first records and start fetching 
        afterwards. Should be calling before the first time calling
        ``fetch()``. The missing records in the ``records`` attribute
        will be filled by ``None``s. The ``number_fetched`` attribute
        will be adjusted as if the first records have been fetched.
        This is mainly useful if the skipped records have already been 
        fetched but the original ``Reader`` object is not available anymore. 
        This functionality may be ignored by readers that can only load 
        all records at once; generally these are readers that return lazy 
        records."""
        if self.number_of_results is not None:
            raise ReaderError(
                "adjust_start_record should not be called after fetching."
            )
        self.number_fetched = start_number
        self.records = [None for _ in range(start_number)]

    @abstractmethod
    def fetch(
            self, number: Optional[int] = None
    ):
        '''Perform an initial or subsequent query. Most readers fetch
        a limited number of records at once -- this number depends on
        the reader but it may be adjusted using the ``number`` argument.
        Other readers fetch all records at once and ignore the ``number``
        argument. After fetching, the ``records`` and ``number_fetched``
        attributes are adjusted and the ``number_of_results`` attribute
        will be available.'''
        pass

    @classmethod
    @abstractmethod
    def get_by_id(cls, identifier: str) -> Record:
        '''Get a single record by its identifier.'''
        pass

    @classmethod
    def get_by_iri(cls, iri: str) -> Record:
        '''Get a single records by its IRI.'''
        identifier = cls.iri_to_identifier(iri)
        return cls.get_by_id(identifier)

    @classmethod
    def identifier_to_iri(cls, identifier: str) -> str:
        if not isinstance(cls.IRI_PREFIX, str):
            raise ReaderError(
                f"Cannot convert identifier to IRI: {__class__}.IRI_PREFIX "
                "not a string."
            )
        return cls.IRI_PREFIX + quote(identifier)

    @classmethod
    def iri_to_identifier(cls, iri: str) -> str:
        if not isinstance(cls.IRI_PREFIX, str):
            raise ReaderError(
                f"Cannot convert IRI to identifier: {__class__}.IRI_PREFIX "
                "not a string."
            )
        if iri.startswith(cls.IRI_PREFIX):
            return unquote(iri[len(cls.IRI_PREFIX):])
        else:
            raise ReaderError(
                f"Cannot convert IRI {iri} to identifier: IRI does not start "
                "with {cls.IRI_PREFIX}."
            )

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

    @property
    def fetching_exhausted(self) -> bool:
        """Return ``True`` if all results have been fetched. This is currently
        implemented by simply checking if the ``number_of_results`` and
        ``number_fetched`` attributes are equal."""
        return self.number_fetched == self.number_of_results
    
    def generate_identifier(self) -> str:
        """Generate an identifier for this reader that is unique for the
        combination of reader type and prepared query. This identifier can
        be used when the reader has to be reused across sessions by
        pickling and unpickling.
        
        Note: while the identifier is guaranteed to be unique, there
        is no guarantee that the generated identifier is the same for
        every combination of reader type and prepared query."""
        if self.prepared_query is None:
            raise RuntimeError("A prepared query should be set first")
        # Create identifier based on reader class name and prepared query.
        readertype = self.__class__
        # self.prepared_query is either a string or a dataclass instance,
        # which means that it has a __str__ method that gives a unique
        # string representation of its contents (at least as long as
        # it does not contain a very complex data structure, which should
        # not be the case). For dataclasses, it is not guaranteed 
        prepared_query = str(self.prepared_query)
        return f"{readertype} | {prepared_query}"


class GetByIdBasedOnQueryMixin(ABC):
    """Mixin for readers that are based on an API that has no special
    way of retrieving single records -- instead, these readers fetch
    single records using a list query. To use, make sure to override
    the ``_prepare_get_by_id_query`` method, which defines the list
    query that should be used."""

    @classmethod
    def get_by_id(cls, identifier: str) -> Record:
        reader = cls()
        assert isinstance(reader, Reader), \
            "GetByIdBasedOnQueryMixin should be used on Reader subclass"
        reader.set_query(cls._prepare_get_by_id_query(identifier))
        reader.fetch()
        if reader.number_of_results == 0:
            raise ReaderError("No results returned")
        for record in reader.records:
            assert record is not None
            if record.identifier == identifier:
                return record
        # Record with correct ID was not returned in first fetch -
        # give up.
        raise ReaderError(
            f"Record with identifier {identifier} not present among "
            f"{reader.number_of_results} returned results."
        )

    @classmethod
    @abstractmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> PreparedQueryType:
        pass


class ReaderError(Exception):
    pass


class NotFoundError(ReaderError):
    pass
