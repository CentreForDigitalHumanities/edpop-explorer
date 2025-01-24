import sqlite3
from rdflib import URIRef
from typing import Optional

from edpop_explorer import (
    Reader, BibliographicalRecord, ReaderError, Field, BIBLIOGRAPHICAL, DatabaseFileMixin
)
from edpop_explorer.fields import LanguageField
from edpop_explorer.reader import GetByIdBasedOnQueryMixin
from edpop_explorer.sql import SQLPreparedQuery


class FBTEEReader(DatabaseFileMixin, GetByIdBasedOnQueryMixin, Reader):
    DATABASE_URL = 'https://dhstatic.hum.uu.nl/edpop/cl.sqlite3'
    DATABASE_FILENAME = 'cl.sqlite3'
    DATABASE_LICENSE = 'https://dhstatic.hum.uu.nl/edpop/LICENSE.txt'
    FBTEE_LINK = 'http://fbtee.uws.edu.au/stn/interface/browse.php?t=book&' \
        'id={}'
    READERTYPE = BIBLIOGRAPHICAL
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/fbtee'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/fbtee/"
    prepared_query: Optional[SQLPreparedQuery] = None
    FETCH_ALL_AT_ONCE = True
    SHORT_NAME = "French Book Trade in Enlightenment Europe (FBTEE)"
    DESCRIPTION = "Mapping the Trade of the Société Typographique de " \
        "Neuchâtel, 1769-1794"

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> SQLPreparedQuery:
        return SQLPreparedQuery(
            where_statement="WHERE book_code = ?",
            arguments=[identifier]
        )

    @classmethod
    def transform_query(cls, query: str) -> SQLPreparedQuery:
        return SQLPreparedQuery(
            where_statement='WHERE full_book_title LIKE ?',
            arguments=[f'%{query}%']
        )

    @classmethod
    def _add_fields(cls, record: BibliographicalRecord) -> None:
        assert isinstance(record.data, dict)
        record.title = Field(record.data['full_book_title'])
        if record.data['languages']:
            languages = record.data['languages'].split(sep=', ')
            record.languages = [LanguageField(x) for x in languages]
            [x.normalize() for x in record.languages]
        pages = record.data['pages']
        if pages:
            record.extent = Field(pages)
        place = record.data['stated_publication_places']
        if place:
            record.place_of_publication = Field(place)
        year = record.data['stated_publication_years']
        if year:
            record.dating = Field(year)
        publisher = record.data['stated_publishers']
        if publisher:
            record.publisher_or_printer = Field(publisher)
        record.contributors = []
        for author in record.data['authors']:
            # author is tuple of author code and author name
            record.contributors.append(Field(author[1]))

    def fetch_range(self, range_to_fetch: range) -> range:
        # This method always fetches all data at once. This could be avoided,
        # but it is inexpensive because the data is locally available and
        # the dataset is small.
        self.prepare_data()
        if not self.prepared_query:
            raise ReaderError('First call prepare_query method')
        if self.fetching_exhausted:
            return range(0)
        with sqlite3.connect(str(self.database_path)) as con:
            cur = con.cursor()
            columns = [x[1] for x in cur.execute('PRAGMA table_info(books)')]
            res = cur.execute(
                'SELECT B.*, BA.author_code, A.author_name FROM books B '
                'LEFT OUTER JOIN books_authors BA on B.book_code=BA.book_code '
                'JOIN authors A on BA.author_code=A.author_code '
                f'{self.prepared_query.where_statement} '
                'ORDER BY B.book_code',
                self.prepared_query.arguments
            )
            last_book_code = ''
            i = -1
            for row in res:
                # Since we are joining with another table, a book may be repeated,
                # so check if this is a new item
                book_code: str = row[columns.index('book_code')]
                if last_book_code != book_code:
                    # We have a new book, so update i
                    i += 1
                    record = BibliographicalRecord(self.__class__)
                    record.data = {}
                    for j in range(len(columns)):
                        record.data[columns[j]] = row[j]
                    record.identifier = book_code
                    # The public web interface has pages for "super books"
                    # rather than individual editions, so link to these.
                    super_book_code = record.data['super_book_code']
                    record.link = self.FBTEE_LINK.format(super_book_code)
                    record.data['authors'] = []
                    self.records[i] = record
                    last_book_code = book_code
                # Add author_code and author_name to the last record
                assert len(self.records) > 0
                author_code = row[len(columns)]
                author_name = row[len(columns) + 1]
                assert isinstance(self.records[i].data, dict)
                self.records[i].data['authors'].append((author_code, author_name))
            for record_number in self.records:
                record = self.records[record_number]
                assert isinstance(record, BibliographicalRecord)
                self._add_fields(record)
            self.number_of_results = len(self.records)
        return range(0, len(self.records))
