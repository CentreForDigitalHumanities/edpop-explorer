from typing import Optional, List

from rdflib import URIRef

from edpop_explorer import SRUMarc21BibliographicalReader, Marc21Data, Field


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
    # BnF has its information in different fields than normally in Marc21
    _title_field_subfield = ('200', 'a')
    _alternative_title_field_subfield = ('500', 'a')
    _publisher_field_subfield = ('210', 'c')
    _place_field_subfield = ('210', 'a')
    _dating_field_subfield = ('210', 'd')
    _language_field_subfield = ('101', 'a')
    # Note that the physical description field normally also (or only)
    # contains the extent, but still physical description is more accurate
    _physical_description_field_subfield = ('215', 'a')
    _size_description_field_subfield = ('215', 'd')
    _extent_field_subfield = ('xxx', 'x')  # Not available

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

    @classmethod
    def _get_contributors(cls, data: Marc21Data) -> List[Field]:
        contributors: List[Field] = []
        contributor_fields = data.get_fields('700')
        for field in contributor_fields:
            surname = field.subfields.get('a')
            givenname = field.subfields.get('b')
            if surname and givenname:
                contributors.append(Field(f"{givenname} {surname}"))
            elif surname or givenname:
                contributors.append(Field(surname or givenname))
        return contributors
