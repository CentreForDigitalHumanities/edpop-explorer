from edpop_explorer.srureader import SRUReader


class HPBReader(SRUReader):
    sru_url = 'http://sru.k10plus.de/hpb'
    sru_version = '1.1'

    def transform_query(self, query: str) -> str:
        return query
