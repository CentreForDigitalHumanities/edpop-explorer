from typing import Optional

from rdflib import URIRef

from edpop_explorer import SRUMarc21BibliographicalReader, Marc21Data


class VDCommonMixin():
    LINK_FORMAT: str

    @classmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        field024 = data.get_first_field('024')
        if field024:
            return field024.subfields.get('a', None)
        else:
            return None

    @classmethod
    def _get_link(cls, record: Marc21Data) -> Optional[str]:
        identifier = cls._get_identifier(record)
        if identifier:
            return cls.LINK_FORMAT.format(identifier).replace(' ', '+')


class VD16Reader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://bvbr.bib-bvb.de:5661/bvb01sru'
    sru_version = '1.1'
    LINK_FORMAT = 'http://gateway-bayern.de/{}'  # Spaces should be replaced by +
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/vd16'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/vd16/"
    SHORT_NAME = "VD16"
    DESCRIPTION = "Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 16. Jahrhunderts"

    @classmethod
    def transform_query(cls, query: str) -> str:
        # This SRU URL combines multiple databases, so make sure only VD16 is
        # queried
        return 'VD16 and ({})'.format(query)


class VD17Reader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/vd17'
    sru_version = '1.1'
    LINK_FORMAT = \
        'https://kxp.k10plus.de/DB=1.28/CMD?ACT=SRCHA&IKT=8079&TRM=%27{}%27'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/vd17'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/vd17/"
    SHORT_NAME = "VD17"
    DESCRIPTION = "Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 17. Jahrhunderts"

    @classmethod
    def transform_query(cls, query: str) -> str:
        return query


class VD18Reader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/vd18'
    sru_version = '1.1'
    LINK_FORMAT = 'https://kxp.k10plus.de/DB=1.65/SET=1/TTL=1/CMD?ACT=SRCHA&' \
        'IKT=1016&SRT=YOP&TRM={}&ADI_MAT=B&MATCFILTER=Y&MATCSET=Y&ADI_MAT=T&' \
        'REC=*'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/vd18'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/vd18/"
    SHORT_NAME = "VD18"
    DESCRIPTION = "Verzeichnis der im deutschen Sprachbereich erschienenen Drucke des 18. Jahrhunderts"

    @classmethod
    def transform_query(cls, query: str) -> str:
        # Only return physical records, because the digital records are duplicates
        # of physical ones.
        # NB: the information from the digital records might be useful, but for
        # the moment we do not use anything from it and including them just
        # leads to duplicates in the results.
        return f"{query} and pica.bbg=A*"

    @classmethod
    def _get_identifier(cls, record: Marc21Data):
        # The record id is in field 024 for which subfield 2 is vd18. There
        # may be more than one occurance of field 024.
        fields024 = record.get_fields('024')
        for field in fields024:
            if '2' in field.subfields and \
                    'a' in field.subfields and \
                    field.subfields['2'] == 'vd18':
                return field.subfields['a'][5:]
        return None


class VDLiedReader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/vdlied'
    sru_version = '1.1'
    LINK_FORMAT = 'https://gso.gbv.de/DB=1.60/PPNSET?PPN={}'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/vdlied'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/vdlied/"
    SHORT_NAME = "VDLied"
    DESCRIPTION = "Das Verzeichnis der deutschsprachigen Liedflugschriften"

    @classmethod
    def transform_query(cls, query: str) -> str:
        return query

    @classmethod
    def _get_identifier(cls, record: Marc21Data) -> Optional[str]:
        return record.controlfields.get("001", None)
