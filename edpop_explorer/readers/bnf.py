from typing import Optional

from rdflib import URIRef

from edpop_explorer import SRUMarc21BibliographicalReader, Marc21Data


class BnFReader(SRUMarc21BibliographicalReader):
    sru_url = 'http://catalogue.bnf.fr/api/SRU'
    sru_version = '1.2'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'
    marcxchange_prefix = 'info:lc/xmlns/marcxchange-v2:'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/bnf'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/bnf/"
    SHORT_NAME = "Bibliothèque nationale de France (BnF)"
    DESCRIPTION = "General catalogue of the French National Library"
    _title_field_subfield = ('200', 'a')
    _alternative_title_field_subfield = ('500', 'a')
    _publisher_field_subfield = ('201', 'c')
    _place_field_subfield = ('210', 'a')
    _dating_field_subfield = ('210', 'd')
    _language_field_subfield = ('101', 'a')
    # TODO: add format etc

    @classmethod
    def transform_query(cls, query: str) -> str:
        return 'bib.anywhere all ({})'.format(query)

    @classmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        # The link can be found in control field 003
        return data.controlfields.get('003', None)

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return f'bib.anywhere all ("{identifier}")'

    @classmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        return data.raw["id"]
