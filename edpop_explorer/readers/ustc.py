from typing import Dict, List
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
import sqlite3
import yaml
from appdirs import AppDirs

from edpop_explorer.apireader import APIReader, APIRecord, APIException


@dataclass
class USTCRecord(APIRecord):
    data: Dict[str, str] = dataclass_field(default_factory=dict)

    def get_title(self) -> str:
        return self.data.get('std_title', '(no title provided)')

    def show_record(self) -> str:
        return_string = yaml.safe_dump(self.data, allow_unicode=True)
        return return_string

    def __repr__(self):
        return self.get_title()


class USTCReader(APIReader):
    DATABASE_FILENAME = 'ustc.sqlite3'
    USTC_LINK = 'https://www.ustc.ac.uk/editions/{}'

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
            raise APIException('Database file not found')
        self.con = sqlite3.connect(str(self.database_file))

    def prepare_query(self, query: str):
        self.prepared_query = '%' + query + '%'

    def fetch(self) -> List[USTCRecord]:
        if not self.prepared_query:
            raise APIException('First call prepare_query method')

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
            record = USTCRecord()
            for i in range(len(columns)):
                record.data[columns[i]] = row[i]
            record.link = self.USTC_LINK.format(record.data['sn'])
            self.records.append(record)
        self.number_of_results = len(self.records)
        self.number_fetched = self.number_of_results
        self.fetching_exhausted = True

    def fetch_next(self):
        pass
