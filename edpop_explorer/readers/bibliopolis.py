from dataclasses import dataclass, field as dataclass_field
import yaml

from edpop_explorer.apireader import APIRecord
from edpop_explorer.srureader import SRUReader


@dataclass
class BibliopolisRecord(APIRecord):
    data: dict = dataclass_field(default_factory=dict)
    TITLE_FIELDS = \
        ['http://krait.kb.nl/coop/tel/handbook/telterms.html:mainEntry',
         'title']

    def get_title(self) -> str:
        '''Convenience method to retrieve the title of a record in a standard
        way'''
        for field in self.TITLE_FIELDS:
            if field in self.data:
                return self.data[field]
        return '(unknown title)'

    def show_record(self) -> str:
        return yaml.safe_dump(self.data)


class BibliopolisReader(SRUReader):
    sru_url = 'http://jsru.kb.nl/sru/sru'
    sru_version = '1.2'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'

    def __init__(self):
        super().__init__()
        self.additional_params = {
            'x-collection': 'Bibliopolis'
        }

    def _convert_record(self, sruthirecord: dict) -> BibliopolisRecord:
        record = BibliopolisRecord(data=sruthirecord)
        return record

    def transform_query(self, query: str) -> str:
        return query
