from pathlib import Path
import sqlite3
from appdirs import AppDirs
from rdflib import URIRef

from edpop_explorer import (
    Reader, BibliographicalRecord, ReaderError, Field, BIBLIOGRAPHICAL
)


class USTCReader(Reader):
    DATABASE_FILENAME = 'ustc.sqlite3'
    USTC_LINK = 'https://www.ustc.ac.uk/editions/{}'
    READERTYPE = BIBLIOGRAPHICAL
    CATALOG_URIREF = URIRef(
        'https://dhstatic.hum.uu.nl/edpop-explorer/catalogs/ustc'
    )

    def __init__(self):
        self.database_file = Path(
            AppDirs('edpop-explorer', 'cdh').user_data_dir
        ) / self.DATABASE_FILENAME
        if not self.database_file.exists():
            # Find database dir with .resolve() because on Windows it is
            # some sort of hidden symlink if Python was installed using
            # the Windows Store...
            db_dir = self.database_file.parent.resolve()
            print(f'USTC database not found. Please obtain the file '
                  f'{self.DATABASE_FILENAME} from the project team and add it '
                  f'to the following directory: {db_dir}')
            raise ReaderError('Database file not found')
        self.con = sqlite3.connect(str(self.database_file))

    def transform_query(self, query: str) -> str:
        return '%' + query + '%'

    def fetch(self) -> None:
        # This method fetches all records immediately, because the data is
        # locally stored.

        if not self.prepared_query:
            raise ReaderError('No query has been set')

        cur = self.con.cursor()
        columns = [x[1] for x in cur.execute('PRAGMA table_info(editions)')]
        # This kind of query is far from ideal, but the alternative is to
        # implement SQLite full text search which is probably too much work
        # for our current goal (i.e. getting insight in the data structures)
        res = cur.execute(
            'SELECT E.* FROM editions E '
            'WHERE E.std_title LIKE ? '
            'OR E.author_name_1 LIKE ? '
            'OR E.author_name_2 LIKE ? '
            'OR E.author_name_3 LIKE ? '
            'OR E.author_name_4 LIKE ? '
            'OR E.author_name_5 LIKE ? '
            'OR E.author_name_6 LIKE ? '
            'OR E.author_name_7 LIKE ? '
            'OR E.author_name_8 LIKE ? '
            'ORDER BY E.id',
            [self.prepared_query for _ in range(9)],
        )
        self.records = []
        for row in res:
            data = {}
            for i in range(len(columns)):
                data[columns[i]] = row[i]
            record = self._convert_record(data)
            self.records.append(record)
        self.number_of_results = len(self.records)
        self.number_fetched = self.number_of_results
        self.fetching_exhausted = True

    def fetch_next(self):
        pass

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

