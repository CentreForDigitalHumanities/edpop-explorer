from edpop_explorer.srureader import SRUReader
from edpop_explorer.apireader import APIRecord
from dataclasses import dataclass, field as dataclass_field
from typing import Optional, Dict, List
from termcolor import colored


@dataclass
class CERLThesaurusRecord(APIRecord):
    data: dict = dataclass_field(default_factory=dict)
    identifier: Optional[str] = None

    def get_title(self) -> str:
        if 'ctas:display' in self.data:
            return self.data['ctas:display']
        else:
            return '(no display name defined)'

    def show_dictlist(self, data: List[Dict[str, str]]) -> str:
        '''Prepare complex data from the SRU response from CERL
        Thesaurus for display in a table. This data comes as a list of
        dictionaries where the keys are the table columns.'''
        # Get all columns by getting lists of all keys and flattening this list
        columns = set(sum([list(x.keys()) for x in data], []))
        # Determine the maximum size for all fields; this will be column size
        columns_size = {}
        for row in data:
            for column in row:
                value = row.get(column, '')
                current_size = columns_size.get(column, -1)
                if len(value) > current_size:
                    columns_size[column] = len(value)
        tablestring = ''
        # Add columns to the data to show them too
        columnsrow = {column: column + ':' for column in columns}
        data.insert(0, columnsrow)
        # Make a table of all rows
        for row in data:
            rowstring = ''
            for column in columns:
                value = row.get(column, '')
                cellstring = f'  {value:{columns_size[column]}}'
                rowstring += cellstring
            tablestring += rowstring + '\n'
        return tablestring

    def show_record(self) -> str:
        field_strings = []
        if self.link:
            field_strings.append('URL: ' + self.link)
        for key in self.data:
            value = self.data[key]
            if type(value) == list:
                value = '\n' + self.show_dictlist(value)
            field_strings.append('{}: {}'.format(key, value))
        return '\n'.join(field_strings)


class CERLThesaurusReader(SRUReader):
    sru_url = 'https://data.cerl.org/thesaurus/_sru'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'

    def _convert_record(self, sruthirecord: dict) -> CERLThesaurusRecord:
        record = CERLThesaurusRecord()
        record.identifier = sruthirecord['id']
        record.link = self.CERL_LINK.format(record.identifier)
        for key in sruthirecord:
            if key in ['schema', 'id']:
                continue
            showkey: str = key.replace(self.CTAS_PREFIX, 'ctas:')
            record.data[showkey] = sruthirecord[key]
        return record

    def transform_query(self, query: str) -> str:
        return query
