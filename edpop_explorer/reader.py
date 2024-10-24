"""Base reader class and strongly related functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Dict

import requests
from appdirs import AppDirs
from rdflib import Graph, RDF, URIRef, SDO, Literal
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
    """Base reader class (abstract).

    This abstract base class provides a common interface for all readers.
    To use, instantiate a subclass, set a query using the
    ``prepare_query()`` or ``set_query()`` method, call ``fetch()``
    and subsequently ``fetch_next()`` until you have the number
    of results that you want. The attributes ``number_of_results``,
    ``number_fetched`` and ``records`` will be updated after
    fetching.

    To create a concrete reader, make a subclass that implements the
    ``fetch_range()`` and ``transform_query()`` methods
    and set the ``READERTYPE`` and ``CATALOG_URIREF`` attributes.
    ``fetch_range()`` should populate the ``records``, ``number_of_results``,
    ``number_fetched`` and ``range_fetched`` attributes.
    """
    number_of_results: Optional[int] = None
    """The total number of results for the query, or None if fetching
    has not yet started and the number is not yet known."""
    records: Dict[int, Record]
    """The records that have been fetched as instances of
    (a subclass of) ``Record``."""
    prepared_query: Optional[PreparedQueryType] = None
    """A transformed version of the query, available after
    calling ``prepare_query()`` or ``set_query``."""
    READERTYPE: Optional[str] = None
    """The type of the reader, out of ``BIOGRAPHICAL`` and
    ``BIBLIOGRAPHICAL`` (defined in the ``edpop_explorer`` package)."""
    CATALOG_URIREF: Optional[URIRef] = None
    IRI_PREFIX: Optional[str] = None
    """The prefix to use to create an IRI out of a record identifier.
    If an IRI cannot be created with a simple prefix, the 
    `identifier_to_iri` and `iri_to_identifier` methods have to be
    overridden."""
    SHORT_NAME: Optional[str] = None
    """Short name of the corresponding catalogue, to be used in
    user interfaces."""
    DESCRIPTION: Optional[str] = None
    """Information about the contents of the corresponding catalogue, 
    to be used in user interfaces."""
    FETCH_ALL_AT_ONCE = False
    """True if the reader is configured to fetch all records at once,
    even if the user only needs a subset."""
    DEFAULT_RECORDS_PER_PAGE: int = 10
    """The number of records to fetch at a time using the ``fetch()``
    method if not determined by user."""
    _fetch_position: int = 0
    """The index of the record that was fetched last. This is used by
    the ``fetch()`` method to decide where to continue fetching."""

    def __init__(self):
        self.records = {}

    @classmethod
    @abstractmethod
    def transform_query(cls, query: str) -> PreparedQueryType:
        """Return a version of the query that is prepared for use in the
        API.

        This method does not have to be called directly; instead
        ``prepare_query()`` can be used."""
        pass

    def prepare_query(self, query: str) -> None:
        """Prepare a query for use by the reader's API. Updates the
        ``prepared_query`` attribute."""
        self.prepared_query = self.transform_query(query)

    def set_query(self, query: PreparedQueryType) -> None:
        """Set an exact query. Updates the ``prepared_query``
        attribute."""
        self.prepared_query = query

    def adjust_start_record(self, start_number: int) -> None:
        """Skip the given number of first records and start fetching
        afterwards.

        This functionality may be ignored by readers that can only load
        all records at once; generally these are readers that return lazy
        records."""
        self._fetch_position = start_number

    def fetch(
            self, number: Optional[int] = None
    ) -> range:
        """Perform an initial or subsequent query. Most readers fetch
        a limited number of records at once -- this number depends on
        the reader but it may be adjusted using the ``number`` parameter.
        Other readers fetch all records at once and ignore the ``number``
        parameter. After fetching, the records are available in the
        ``records`` attribute and the ``number_of_results`` attribute
        will be available. Returns the range of record indexes that has
        been fetched."""
        if self.fetching_exhausted:
            return range(0)
        if number is None:
            number = self.DEFAULT_RECORDS_PER_PAGE
        resulting_range = self.fetch_range(range(self._fetch_position,
                                           self._fetch_position + number))
        self._fetch_position = resulting_range.stop
        return resulting_range

    @abstractmethod
    def fetch_range(self, range_to_fetch: range) -> range:
        """Fetch a specific range of records. After fetching, the records
        are available in the ``records`` attribute and the
        ``number_of_results`` attribute will be available. If not all records
        of the specified range exist, only the records that exist will be
        fetched.

        :param range_to_fetch: The range of records to fetch. ``step`` values
            of ranges other than 1 are not supported and may be ignored.
        :returns: The range of record indexes that has actually been fetched.
        """
        pass

    def get(self, index: int, allow_fetching: bool = True) -> Record:
        """Get a record with a specific index. If the record is not yet
        available, fetch additional records to make it available.

        :param index: The number of the record to get.
        :param allow_fetching: Allow fetching the record from an external
            source if it was not yet fetched.
        """
        try:
            return self.records[index]
        except KeyError:
            record = None
            # Try to fetch, if it is allowed, and if there is a chance that
            # it is successful (by verifying that index is not out of
            # available range, if known)
            if (allow_fetching and
                    (self.number_of_results is None
                     or self.number_of_results <= index)):
                # Fetch and try again
                self.fetch_range(range(index, index + 1))
                record = self.records.get(index)
            if record is not None:
                return record
            else:
                raise NotFoundError(f"Item with index {index} is not available.")

    @classmethod
    @abstractmethod
    def get_by_id(cls, identifier: str) -> Record:
        """Get a single record by its identifier."""
        pass

    @classmethod
    def get_by_iri(cls, iri: str) -> Record:
        """Get a single records by its IRI."""
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

        # Add name and description
        if cls.SHORT_NAME:
            g.add((cls.CATALOG_URIREF, SDO.name, Literal(cls.SHORT_NAME)))
        if cls.DESCRIPTION:
            g.add((cls.CATALOG_URIREF, SDO.description, Literal(cls.DESCRIPTION)))
        if (slug := cls.get_catalog_slug()) is not None:
            g.add((cls.CATALOG_URIREF, SDO.identifier, Literal(slug)))

        # Set namespace prefixes
        bind_common_namespaces(g)

        return g

    @property
    def fetching_exhausted(self) -> bool:
        """Return ``True`` if all results have been fetched."""
        return self.fetching_started and self.number_of_results == self.number_fetched

    @property
    def fetching_started(self) -> bool:
        """``True`` if fetching has started, otherwise ``False``. As soon
        as fetching has started, changing the query is not possible anymore."""
        return self.number_of_results is not None

    @property
    def number_fetched(self) -> int:
        """The number of results that has been fetched so far, or 0 if
        no fetch has been performed yet."""
        return len(self.records)

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

    @classmethod
    def get_catalog_slug(cls) -> Optional[str]:
        if cls.CATALOG_URIREF:
            return cls.CATALOG_URIREF.split("/")[-1]


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
            raise NotFoundError("No results returned")
        for record in reader.records.values():
            assert record is not None
            if record.identifier == identifier:
                return record
        # Record with correct ID was not returned in first fetch -
        # give up.
        raise NotFoundError(
            f"Record with identifier {identifier} not present among "
            f"{reader.number_of_results} returned results."
        )

    @classmethod
    @abstractmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> PreparedQueryType:
        pass


class DatabaseFileMixin:
    """Mixin that adds a method ``prepare_data`` to a ``Reader`` class,
    which will make the database file available in the ``database_path``
    attribute as a ``pathlib.Path`` object. If the constant attribute
    ``DATABASE_URL`` is given, the database will be downloaded from
    that URL if the data is not yet available. The database file will
    be (expected to be) stored in the application data directory
    using the filename specified in the constant attribute
    ``DATABASE_FILENAME``, which has to be specified by the user of
    this mixin."""
    DATABASE_URL: Optional[str] = None
    """The URL to download the database file from. If this attribute is
    ``None``, automatically downloading the database file is not supported."""
    DATABASE_FILENAME: str
    """The filename (not the full path) under which the database is expected
    to be stored."""
    DATABASE_LICENSE: Optional[str] = None
    """A URL that contains the license of the downloaded database file."""
    database_path: Optional[Path] = None
    """The path to the database file. Will be set by the ``prepare_data``
    method."""

    def prepare_data(self) -> None:
        """Prepare the database file by confirming that it is available,
        and if not, by attempting to download it."""
        self.database_path = Path(
            AppDirs('edpop-explorer', 'cdh').user_data_dir
        ) / self.DATABASE_FILENAME
        if not self.database_path.exists():
            if self.DATABASE_URL is None:
                # No database URL is given, so the user has to get the database
                # by themself.
                # Find database dir with .resolve() because on Windows it is
                # some sort of hidden symlink if Python was installed using
                # the Windows Store...
                db_dir = self.database_path.parent.resolve()
                error_message = (
                    f'{self.__class__.__name__} database not found. Please obtain the file '
                    f'{self.DATABASE_FILENAME} from the project team and add it '
                    f'to the following directory: {db_dir}'
                )
                raise ReaderError(error_message)
            else:
                self._download_database()

    def _download_database(self) -> None:
        print('Downloading database...')
        response = requests.get(self.DATABASE_URL)
        if response.ok:
            try:
                self.database_path.parent.mkdir(exist_ok=True, parents=True)
                with open(self.database_path, 'wb') as f:
                    f.write(response.content)
            except OSError as err:
                raise ReaderError(
                    f'Error writing database file to disk: {err}'
                )
        else:
            raise ReaderError(
                f'Error downloading database file from {self.DATABASE_URL}'
            )
        print(f'Successfully saved database to {self.database_path}.')
        print(f'See license: {self.DATABASE_LICENSE}')


class ReaderError(Exception):
    """Generic exception for failures in ``Reader`` class. More specific errors
    derive from this class."""
    pass


class NotFoundError(ReaderError):
    pass
