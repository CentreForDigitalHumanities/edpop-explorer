from rdflib import URIRef
from typing import Optional

from edpop_explorer import (
    SRUMarc21BibliographicalReader, Marc21Data, BIBLIOGRAPHICAL
)


class HPBReader(SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/hpb'
    sru_version = '1.1'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/hpb'
    )
    READERTYPE = BIBLIOGRAPHICAL
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/hpb/"

    @classmethod
    def transform_query(cls, query: str) -> str:
        return query

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return f"pica.cid={identifier}"

    @classmethod
    def _get_identifier(cls, data:Marc21Data) -> Optional[str]:
        # The record id can be found in field 035 in subfield a starting
        # with (CERL), like this: (CERL)HU-SzSEK.01.bibJAT603188.
        # The URI can then be created using HPB_URI.
        # HPB records have field 035 two times.
        fields035 = data.get_fields('035')
        for field in fields035:
            if 'a' in field.subfields and \
                    field.subfields['a'].startswith('(CERL)'):
                return field.subfields['a'][len('(CERL)'):]


    @classmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        identifier = cls._get_identifier(data)
        if identifier is not None:
            return cls.HPB_LINK.format(identifier)
        else:
            return None
