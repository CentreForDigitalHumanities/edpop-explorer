from typing import Dict, List

from rdflib import URIRef
from edpop_explorer import SRUReader, Record, BiographicalRecord, Field, BIOGRAPHICAL
from edpop_explorer.fields import LocationField


class CERLThesaurusReader(SRUReader):
    sru_url = 'https://data.cerl.org/thesaurus/_sru'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/cerlthesaurus'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/cerlthesaurus/"
    READERTYPE = BIOGRAPHICAL
    SHORT_NAME = "CERL Thesaurus"
    DESCRIPTION = "The CERL Thesaurus file contains forms of imprint " \
        "places, imprint names, personal names and corporate names as "\
        "found in material printed before the middle of the nineteenth "\
        "century - including variant spellings, forms in Latin and "\
        "other languages, and fictitious names."

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

        # Add activityNote. This field can have only one value in CT.
        # NB: this data is very inconsistent and often includes other information
        # than somebody's activity - consider ignoring
        activitynote = sruthirecord.get(PREFIX + 'activityNote')
        if activitynote:
            record.activities = [Field(activitynote)]
        # Add biographicalData, which appears to be in all cases the years
        # that somebody was alive or that an entity existed
        biographicaldata = sruthirecord.get(PREFIX + 'biographicalData')
        if biographicaldata:
            record.timespan = Field(biographicaldata)
        # Add geographicalNote, which appears to be a country in all cases.
        # Add it to places of activity.
        geographicalnote = sruthirecord.get(PREFIX + 'geographicalNote')
        if geographicalnote:
            field = LocationField(geographicalnote)
            field.location_type = LocationField.COUNTRY
            record.places_of_activity = [field]

        return record

    @classmethod
    def transform_query(cls, query: str) -> str:
        return query
