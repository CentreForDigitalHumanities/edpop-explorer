from rdflib import URIRef
from typing import Dict, Optional

from edpop_explorer import (
    BiographicalRecord, Field, BIOGRAPHICAL
)
from edpop_explorer.cerl import CERLReader


class SBTIReader(CERLReader):
    API_URL = 'https://data.cerl.org/sbti/_search'
    API_BY_ID_BASE_URL = 'https://data.cerl.org/sbti/'
    LINK_BASE_URL = 'https://data.cerl.org/sbti/'
    additional_params: Optional[Dict[str, str]] = None
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/sbti'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/sbti/"
    DEFAULT_RECORDS_PER_PAGE = 10
    READERTYPE = BIOGRAPHICAL
    SHORT_NAME = "Scottish Book Trade Index (SBTI)"
    DESCRIPTION = "An index of the names, trades and addresses of people "\
        "involved in printing in Scotland up to 1850"

    @classmethod
    def _get_name_field(cls, data: dict) -> Optional[Field]:
        field = None
        firstname = data.get("firstname", None)
        name = data.get("name", None)
        if firstname and name:
            field = Field(f"{firstname} {name}")
        elif name:
            field = Field(f"{name}")
        return field

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BiographicalRecord:
        record = BiographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord.get('id', None)
        if not record.identifier:
            record.identifier = rawrecord.get('_id', None)
        if record.identifier:
            record.link = cls.LINK_BASE_URL + record.identifier

        # Add fields
        heading = rawrecord.get("heading", None)
        if heading:
            name_field = cls._get_name_field(heading[0])
            record.name = name_field
        variant_name = rawrecord.get("variantName", None)
        if isinstance(variant_name, list):
            record.variant_names = []
            for name in variant_name:
                field = cls._get_name_field(name)
                if field:
                    record.variant_names.append(field)
        place_of_activity = rawrecord.get("placeOfActitivty", None)  # sic.
        if isinstance(place_of_activity, list):
            record.places_of_activity = []
            for place in place_of_activity:
                name = place.get("name", None)
                if name:
                    field = Field(name)
                    record.places_of_activity.append(field)
        activity_dates = rawrecord.get("activityDates", None)
        if isinstance(activity_dates, list):
            record.activity_timespan = [Field(str(x['text'])) for x in activity_dates]
        activities = rawrecord.get("activity", None)
        if isinstance(activities, list):
            record.activities = [Field(x) for x in activities]

        return record

