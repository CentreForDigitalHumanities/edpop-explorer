from edpop_explorer import SRUReader, Record


class CERLThesaurusReader(SRUReader):
    sru_url = 'https://data.cerl.org/thesaurus/_sru'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'

    def _convert_record(self, sruthirecord: dict) -> Record:
        record = Record(from_reader=self.__class__)
        record.identifier = sruthirecord['id']
        record.link = self.CERL_LINK.format(record.identifier)
        record.data = sruthirecord
        return record

    def transform_query(self, query: str) -> str:
        return query
