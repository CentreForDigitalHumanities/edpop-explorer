from typing import Optional

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

    def transform_query(self, query: str) -> str:
        # This SRU URL combines multiple databases, so make sure only VD16 is
        # queried
        return 'VD16 and ({})'.format(query)



class VD17Reader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/vd17'
    sru_version = '1.1'
    LINK_FORMAT = \
        'https://kxp.k10plus.de/DB=1.28/CMD?ACT=SRCHA&IKT=8079&TRM=%27{}%27'

    def transform_query(self, query: str) -> str:
        return query


class VD18Reader(VDCommonMixin, SRUMarc21BibliographicalReader):
    sru_url = 'http://sru.k10plus.de/vd18'
    sru_version = '1.1'
    LINK_FORMAT = 'https://kxp.k10plus.de/DB=1.65/SET=1/TTL=1/CMD?ACT=SRCHA&' \
        'IKT=1016&SRT=YOP&TRM={}&ADI_MAT=B&MATCFILTER=Y&MATCSET=Y&ADI_MAT=T&' \
        'REC=*'

    def transform_query(self, query: str) -> str:
        return query

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

    def transform_query(self, query: str) -> str:
        return query

    @classmethod
    def _get_identifier(cls, record: Marc21Data) -> Optional[str]:
        return record.controlfields.get("001", None)
