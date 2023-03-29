from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
import sqlite3
import yaml

from edpop_explorer.apireader import APIReader, APIRecord, APIException


@dataclass
class FBTEERecord(APIRecord):
    data: Dict[str, str] = dataclass_field(default_factory=dict)
    authors: List[Tuple[str, str]] = dataclass_field(default_factory=list)

    def get_title(self) -> str:
        return self.data.get('full_book_title', '(no title provided)')

    def show_record(self) -> str:
        return_string = yaml.safe_dump(self.data, allow_unicode=True)
        if self.authors:
            authorstrings = [x[0] + ' - ' + x[1] for x in self.authors]
            return_string += '\nAuthors:\n' + '\n'.join(authorstrings)
        return return_string

    def __repr__(self):
        return self.get_title()


class FBTEEReader(APIReader):
    DATABASE_FILE = Path(__file__).parent.parent / 'cl.sqlite3'

    def __init__(self):
        self.con = sqlite3.connect(str(self.DATABASE_FILE))

    def prepare_query(self, query: str):
        self.prepared_query = '%' + query + '%'

    def fetch(self) -> List[FBTEERecord]:
        if not self.prepared_query:
            raise APIException('First call prepare_query method')

        cur = self.con.cursor()
        columns = [x[1] for x in cur.execute('PRAGMA table_info(books)')]
        res = cur.execute(
            'SELECT B.*, BA.author_code, A.author_name FROM books B '
            'JOIN books_authors BA on B.book_code=BA.book_code '
            'JOIN authors A on BA.author_code=A.author_code '
            'WHERE full_book_title LIKE ? '
            'ORDER BY B.book_code',
            (self.prepared_query,)
        )
        self.records = []
        last_book_code = ''
        for row in res:
            # Since we are joining with another table, a book may be repeated,
            # so check if this is a new item
            book_code: str = row[columns.index('book_code')]
            if last_book_code != book_code:
                record = FBTEERecord()
                record.data = {}
                for i in range(len(columns)):
                    record.data[columns[i]] = row[i]
                self.records.append(record)
                last_book_code = book_code
            # Add author_code and author_name to the last record
            assert len(self.records) > 0
            author_code = row[len(columns)]
            author_name = row[len(columns) + 1]
            self.records[-1].authors.append((author_code, author_name))
        self.number_of_results = len(self.records)
        self.number_fetched = self.number_of_results
        self.fetching_exhausted = True

    def fetch_next(self):
        pass
