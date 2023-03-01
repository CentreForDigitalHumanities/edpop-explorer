from edpop_explorer.srureader import SRUReader, SRURecord


class HPBReader(SRUReader):
    sru_url = 'http://sru.k10plus.de/hpb'
    sru_version = '1.1'
    HPB_LINK = 'http://hpb.cerl.org/record/{}'

    def transform_query(self, query: str) -> str:
        return query

    def get_link(self, record: SRURecord):
        # The record id can be found in field 035 in subfield a starting
        # with (CERL), like this: (CERL)HU-SzSEK.01.bibJAT603188.
        # The URI can then be created using HPB_URI.
        # HPB records have field 035 two times.
        fields035 = record.get_fields('035')
        for field in fields035:
            if 'a' in field.subfields and \
                    field.subfields['a'].startswith('(CERL)'):
                return self.HPB_LINK.format(
                    field.subfields['a'][len('(CERL)'):]
                )
        return None
