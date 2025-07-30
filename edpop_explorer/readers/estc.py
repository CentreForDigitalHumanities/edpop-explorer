from rdflib import URIRef

from edpop_explorer import CERLReader, BiographicalRecord, BIBLIOGRAPHICAL


class ESTCReader(CERLReader):
    API_URL = 'https://datb.cerl.org/estc/_search'
    LINK_BASE_URL = 'https://datb.cerl.org/estc/'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/estc'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/estc/"
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "English Short Title Catalogue"

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BiographicalRecord:
        record = BiographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord.get('id', None)
        if record.identifier:
            record.link = cls.LINK_BASE_URL + record.identifier
        return record
