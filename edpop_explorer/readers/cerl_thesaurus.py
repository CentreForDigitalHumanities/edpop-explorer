from typing import Dict, List
from edpop_explorer import SRUReader, Record, BiographicalRecord, Field


class CERLThesaurusReader(SRUReader):
    sru_url = 'https://data.cerl.org/thesaurus/_sru'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'

    @classmethod
    def _get_acceptable_names(
            cls, namelist: List[Dict[str, str]]
    ) -> List[str]:
        names = []
        for name in namelist:
            if name['name'] in ['single', 'full']:
                names.append(name['text'])
        return names
    
    @classmethod
    def _convert_record(cls, sruthirecord: dict) -> Record:
        record = BiographicalRecord(from_reader=cls)
        record.identifier = sruthirecord['id']
        record.link = cls.CERL_LINK.format(record.identifier)
        record.data = sruthirecord

        # Add the names. Names are of different types: single, descriptive
        # (including the profession), full, inverted. inverted and
        # descriptive seem to be there always in addition to more
        # basic forms of the name. We will only choose the basic
        # forms for now. Names are both in headingForm (the default
        # display name) and variantForm (multiple variant names). We will
        # use these respectively for name and variantName.
        PREFIX = cls.CTAS_PREFIX
        headingform = sruthirecord.get(PREFIX + 'headingForm', None)
        if headingform and isinstance(headingform, list):
            names = cls._get_acceptable_names(headingform)
            if len(names):
                record.name = Field(names[0])
        # If no headingForm was defined, try display
        if not record.name:
            display = sruthirecord.get(PREFIX + 'display', None)
            if display:
                record.name = Field(display)

        variantform = sruthirecord.get(PREFIX + 'variantForm', None)
        if variantform and isinstance(variantform, list):
            names = cls._get_acceptable_names(variantform)
            record.variant_names = [Field(x) for x in names]

        return record

    def transform_query(self, query: str) -> str:
        return query
