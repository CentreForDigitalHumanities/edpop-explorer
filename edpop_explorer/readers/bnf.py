from typing import Optional

from edpop_explorer.srumarc21reader import SRUMarc21Reader, Marc21Record


class BnFReader(SRUMarc21Reader):
    sru_url = 'http://catalogue.bnf.fr/api/SRU'
    sru_version = '1.2'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'
    marcxchange_prefix = 'info:lc/xmlns/marcxchange-v2:'

    def transform_query(self, query: str) -> str:
        return 'bib.anywhere all ({})'.format(query)

    def _convert_record(self, sruthirecord: dict) -> Marc21Record:
        # Call inherited method, but change the title field
        record = super()._convert_record(sruthirecord)
        # For some reason BnF holds the main title in field 200, which
        # normally does not exist in marc21.
        record.title_field_subfield = ['200', 'a']
        return record

    def get_link(self, record: Marc21Record) -> Optional[str]:
        # The link can be found in control field 003
        return record.controlfields.get('003', None)
