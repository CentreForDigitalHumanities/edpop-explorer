from dataclasses import dataclass, field as dataclass_field
from typing import Optional
import yaml
from edpop_explorer.srumarc21reader import SRUReader, APIRecord


@dataclass
class KBRecord(APIRecord):
    data: dict = dataclass_field(default_factory=dict)
    identifier: Optional[str] = None

    def get_title(self) -> str:
        if 'title' in self.data:
            title = self.data['title']
            if type(title) == list:
                # Title contains a list of strings if it consists of multiple
                # parts
                return ' : '.join(title)
            else:
                return title
        else:
            return '(no title defined)'

    def show_record(self) -> str:
        return_string = yaml.safe_dump(self.data, allow_unicode=True)
        if self.link:
            return_string = self.link + '\n' + return_string
        return return_string


class KBReader(SRUReader):
    sru_url = 'http://jsru.kb.nl/sru'
    sru_version = '1.2'
    KB_LINK = 'https://webggc.oclc.org/cbs/DB=2.37/PPN?PPN={}'

    def __init__(self):
        super().__init__()
        # Set in init method because dicts are mutable
        self.additional_params = {
            'x-collection': 'GGC'
        }

    def transform_query(self, query: str) -> str:
        return query

    def _find_ppn(self, data: dict):
        """Try to find the PPN given the data that comes from the SRU server"""
        # This seems to work fine; not thoroughly tested.
        oai_pmh_identifier = data.get('OaiPmhIdentifier', None)
        PREFIX = 'GGC:AC:'
        ppn = None
        if oai_pmh_identifier and oai_pmh_identifier.startswith(PREFIX):
            ppn = oai_pmh_identifier[len(PREFIX):]
        return ppn

    def _convert_record(self, sruthirecord: dict) -> KBRecord:
        record = KBRecord()
        record.data = sruthirecord
        record.identifier = self._find_ppn(record.data)
        if record.identifier:
            # Also here: it seems to work, but there may be records where
            # it doesn't work...
            # NOTE: there is often a URL in the `identifier' field as well,
            # but not always, and it uses a `resolver', which is slower.
            # But if we find records for which no link can be found this may
            # be an alternative.
            record.link = self.KB_LINK.format(record.identifier)
        return record
