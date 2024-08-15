import sqlite3
from typing import List, Optional, Union
from rdflib import URIRef

from edpop_explorer import (
    Reader, BibliographicalRecord, ReaderError, Field, BIBLIOGRAPHICAL,
    GetByIdBasedOnQueryMixin, DatabaseFileMixin
)
from edpop_explorer.sql import SQLPreparedQuery


class USTCReader(DatabaseFileMixin, GetByIdBasedOnQueryMixin, Reader):
    DATABASE_FILENAME = 'ustc.sqlite3'
    USTC_LINK = 'https://www.ustc.ac.uk/editions/{}'
    READERTYPE = BIBLIOGRAPHICAL
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/ustc'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/ustc/"
    prepared_query: Optional[SQLPreparedQuery] = None
    FETCH_ALL_AT_ONCE = True
    SHORT_NAME = "Universal Short Title Catalogue (USTC)"
    DESCRIPTION = "An open access bibliography of early modern print culture"

    @classmethod
    def transform_query(cls, query: str) -> SQLPreparedQuery:
        if len(query.strip()) < 3:
            # Do not allow very short USTC queries because they are very slow
            raise ReaderError('USTC query must have at least 3 characters.')
        where_statement = ( 
            'WHERE E.std_title LIKE ? '
            'OR E.author_name_1 LIKE ? '
            'OR E.author_name_2 LIKE ? '
            'OR E.author_name_3 LIKE ? '
            'OR E.author_name_4 LIKE ? '
            'OR E.author_name_5 LIKE ? '
            'OR E.author_name_6 LIKE ? '
            'OR E.author_name_7 LIKE ? '
            'OR E.author_name_8 LIKE ? '
        )
        like_argument = '%' + query + '%'
        arguments: List[Union[str, int]] = [like_argument for _ in range(9)]
        return SQLPreparedQuery(where_statement, arguments)

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> SQLPreparedQuery:
        try:
            identifier_int = int(identifier)
        except ValueError:
            raise ReaderError(f"Identifier {identifier} is not an integer")
        return SQLPreparedQuery(
            where_statement="WHERE E.sn = ?",
            arguments=[identifier_int]
        )

    def fetch_range(self, range_to_fetch: range) -> range:
        self.prepare_data()
        con = sqlite3.connect(str(self.database_path))

        # This method fetches all records immediately, because the data is
        # locally stored.

        if not self.prepared_query:
            raise ReaderError('No query has been set')
        if self.fetching_exhausted:
            return range(0)

        cur = con.cursor()
        columns = [x[1] for x in cur.execute('PRAGMA table_info(editions)')]
        # This kind of query is far from ideal, but the alternative is to
        # implement SQLite full text search which is probably too much work
        # for our current goal (i.e. getting insight in the data structures)
        res = cur.execute(
            'SELECT E.* FROM editions E '
            + self.prepared_query.where_statement
            + ' ORDER BY E.id',
            self.prepared_query.arguments,
        )
        for i, row in enumerate(res):
            data = {}
            for j in range(len(columns)):
                data[columns[j]] = row[j]
            record = self._convert_record(data)
            self.records[i] = record
        self.number_of_results = len(self.records)
        return range(0, len(self.records))

    def _convert_record(self, data: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=self.__class__)
        record.data = data
        record.identifier = data['sn']
        record.link = self.USTC_LINK.format(data['sn'])
        record.title = Field(data['std_title'])
        record.contributors = []
        for i in range(8):
            fieldname = f'author_name_{i + 1}'
            if data[fieldname]:
                record.contributors.append(Field(data[fieldname]))
        if data['printer_name_1']:
            # TODO: support for multiple printers
            record.publisher_or_printer = Field(data['printer_name_1'])
        if data['place']:
            record.place_of_publication = Field(data['place'])
        if data['year']:
            record.dating = Field(data['year'])
        record.languages = []
        for i in range(4):
            fieldname = f'language_{i + 1}'
            if data[fieldname]:
                record.languages.append(Field(data[fieldname]))
        if data['pagination']:
            record.extent = Field(data['pagination'])
        return record

