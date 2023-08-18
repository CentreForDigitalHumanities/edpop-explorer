from edpop_explorer.srureader import SRUReader
from edpop_explorer.apireader import APIRecord
from dataclasses import dataclass, field as dataclass_field
from typing import Optional
import yaml


@dataclass
class CERLThesaurusRecord(APIRecord):
    data: dict = dataclass_field(default_factory=dict)
    identifier: Optional[str] = None

    def get_title(self) -> str:
        if 'ctas:display' in self.data:
            return self.data['ctas:display']
        else:
            return '(no display name defined)'

    def show_record(self) -> str:
        contents = yaml.safe_dump(self.data, allow_unicode=True)
        if self.link:
            contents = self.link + '\n' + contents
        return contents


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
