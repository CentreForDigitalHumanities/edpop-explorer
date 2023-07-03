from edpop_explorer.srureader import SRUReader
from edpop_explorer.apireader import APIRecord
from dataclasses import dataclass, field as dataclass_field
from typing import Optional
import pandas as pd


@dataclass
class GallicaRecord(APIRecord):
    data: dict = dataclass_field(default_factory=dict)
    identifier: Optional[str] = None

    def get_title(self) -> str:
        if 'title' in self.data:
            return self.data['title']
        else:
            return '(no title defined)'

    def show_record(self) -> str:
        field_strings = []
        for key in self.data:
            value = self.data[key]
            if type(value) == dict:
                value = '\n' + pd.DataFrame(value.items()).to_string(
                    index=False, header=False
                )
            elif type(value) == list:
                value = ''.join(['\n- ' + x for x in value])
            field_strings.append('{}: {}'.format(key, value))
        return '\n'.join(field_strings)


class GallicaReader(SRUReader):
    sru_url = 'https://gallica.bnf.fr/SRU'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'

    def _convert_record(self, sruthirecord: dict) -> GallicaRecord:
        record = GallicaRecord()
        # identifier field contains visitable Gallica URL and possibly
        # also other types of identifier. In the first case we get it as a
        # string from sruthi, in the latter case as a list of strings.
        # Take the first string starting with https:// as the identifier
        # and as the link.
        if type(sruthirecord['identifier']) == list:
            identifiers = sruthirecord['identifier']
        elif type(sruthirecord['identifier']) == str:
            identifiers = [sruthirecord['identifier']]
        else:
            identifiers = []
        for identifier in identifiers:
            if identifier.startswith('https://'):
                record.identifier = identifier
                record.link = identifier
        record.link = record.identifier
        for key in sruthirecord:
            if key in ['schema', 'id']:
                continue
            showkey: str = key.replace(self.CTAS_PREFIX, 'ctas:')
            record.data[showkey] = sruthirecord[key]
        return record

    def transform_query(self, query: str) -> str:
        return 'gallica all {}'.format(query)
