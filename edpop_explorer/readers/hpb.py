from rdflib import URIRef
from typing import Optional, List

from edpop_explorer import (
    SRUMarc21BibliographicalReader, Marc21Data, BIBLIOGRAPHICAL, Field, Marc21Field
)
from edpop_explorer.readers.utils import format_holding


def holding_from_marc21(field: Marc21Field) -> Field:
    institution = field.subfields.get('c')
    shelf_mark = field.subfields.get('a')
    return format_holding(institution, shelf_mark)


class HPBReader(SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/hpb'
    sru_version = '1.1'
    sru_additional_schema = 'picaxml'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/hpb'
    )
    READERTYPE = BIBLIOGRAPHICAL
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/hpb/"
    SHORT_NAME = "Heritage of the Printed Book (HPB)"
    DESCRIPTION = (
        "The HPB Database (previously called the Hand Press Book Database) "
        "is a steadily growing collection of files of catalogue records from "
        "major European and North American research libraries covering items "
        "of European printing of the hand-press period (c.1455-c.1830) "
        "integrated into one file."
    )

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

    @classmethod
    def _get_holdings(cls, data: Marc21Data) -> List[Field]:
        holdings_fields = data.get_fields('009B', picaxml=True)
        return list(filter(None, map(holding_from_marc21, holdings_fields)))
