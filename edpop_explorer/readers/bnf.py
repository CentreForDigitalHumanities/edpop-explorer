from typing import Optional

from edpop_explorer import SRUMarc21BibliographicalReader, Marc21Data


class BnFReader(SRUMarc21BibliographicalReader):
    sru_url = 'http://catalogue.bnf.fr/api/SRU'
    sru_version = '1.2'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'
    marcxchange_prefix = 'info:lc/xmlns/marcxchange-v2:'
    _title_field_subfield = ('200', 'a')
    _alternative_title_field_subfield = ('500', 'a')
    _publisher_field_subfield = ('201', 'c')
    _place_field_subfield = ('210', 'a')
    _dating_field_subfield = ('210', 'd')
    _language_field_subfield = ('101', 'a')
    # TODO: add format etc

    def transform_query(self, query: str) -> str:
        return 'bib.anywhere all ({})'.format(query)

    @classmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        # The link can be found in control field 003
        return data.controlfields.get('003', None)

    @classmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        # TODO
        return None
