from edpop_explorer.srureader import SRUReader, SRURecord


class VD16Reader(SRUReader):
    sru_url = 'http://bvbr.bib-bvb.de:5661/bvb01sru'
    sru_version = '1.1'
    VD16_LINK = 'http://gateway-bayern.de/{}'  # Spaces should be replaced by +

    def transform_query(self, query: str) -> str:
        # This SRU URL combines multiple databases, so make sure only VD16 is
        # queried
        return 'VD16 and ({})'.format(query)

    def get_link(self, record: SRURecord):
        try:
            identifier = record.get_first_field('024').subfields['a']
        except KeyError:
            return None
        return self.VD16_LINK.format(identifier).replace(' ', '+')


class VD17Reader(SRUReader):
    sru_url = 'http://sru.k10plus.de/vd17'
    sru_version = '1.1'
    VD17_LINK = \
        'https://kxp.k10plus.de/DB=1.28/CMD?ACT=SRCHA&IKT=8079&TRM=%27{}%27'

    def transform_query(self, query: str) -> str:
        return query

    def get_link(self, record: SRURecord):
        try:
            identifier = record.get_first_field('024').subfields['a']
        except KeyError:
            return None
        return self.VD17_LINK.format(identifier)


class VD18Reader(SRUReader):
    sru_url = 'http://sru.k10plus.de/vd18'
    sru_version = '1.1'
    VD18_LINK = 'https://kxp.k10plus.de/DB=1.65/SET=1/TTL=1/CMD?ACT=SRCHA&' \
        'IKT=1016&SRT=YOP&TRM={}&ADI_MAT=B&MATCFILTER=Y&MATCSET=Y&ADI_MAT=T&' \
        'REC=*'

    def transform_query(self, query: str) -> str:
        return query

    def get_link(self, record: SRURecord):
        # The record id is in field 024 for which subfield 2 is vd18. There
        # may be more than one occurance of field 024.
        fields024 = record.get_fields('024')
        for field in fields024:
            if '2' in field.subfields and \
                    'a' in field.subfields and \
                    field.subfields['2'] == 'vd18':
                return self.VD18_LINK.format(
                    field.subfields['a'][5:]
                )
        return None
