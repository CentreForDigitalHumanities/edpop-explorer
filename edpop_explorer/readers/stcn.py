from operator import methodcaller

from rdflib import URIRef
from typing import List, Optional, Tuple

from edpop_explorer import Field, BIBLIOGRAPHICAL, BibliographicalRecord, LocationField, BIOGRAPHICAL, \
    BiographicalRecord
from edpop_explorer.cerl import CERLReader
from edpop_explorer.fields import LanguageField, ContributorField


def _remove_markup(input_str: str) -> str:
    """Remove STCN-specific markup"""
    return input_str.replace('`IT`', '').replace('`LO`', '')


def safeget(dictionary: Optional[dict], attribute_chain: tuple, first: bool = False):
    """Safely get a (nested) attribute in a JSON-like structure. If the
    result is a list and ``first`` is ``True``, return the first item
    of the list."""
    if len(attribute_chain) == 0:
        raise ValueError("The attribute_chain argument cannot be empty")
    attribute = attribute_chain[0]
    if dictionary is None or attribute not in dictionary:
        return None
    value = dictionary[attribute]
    if first and isinstance(value, list):
        value = value[0]
    if len(attribute_chain) == 1:
        return value
    else:
        return safeget(value, attribute_chain[1:], first)


def _wrap_contributor(actor_data: dict) -> ContributorField:
    field = ContributorField(actor_data['preferred'])
    field.name = actor_data['preferred']
    field.role = safeget(actor_data, ('role',), first=True)
    return field


class STCNBaseReader(CERLReader):
    """STCN uses the same search API for its bibliographical records and
    its biographical records (persons and publishers/printers), but the
    data format as well as detail pages are different. This base class
    builds on CERLReader and adds the API URL."""
    API_URL = 'https://data.cerl.org/stcn/_search'


class STCNPersonsReader(STCNBaseReader):
    """STCN Persons reader. This reader does not include printers and
    publishers, because they are in a separate database."""
    API_BY_ID_BASE_URL = 'https://data.cerl.org/stcn_persons/'
    LINK_BASE_URL = 'https://data.cerl.org/stcn_persons/'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/stcn'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/stcn-persons/"
    READERTYPE = BIOGRAPHICAL
    SHORT_NAME = "STCN Persons"
    DESCRIPTION = "National bibliography of The Netherlands until 1801 – persons"

    @classmethod
    def transform_query(cls, query) -> str:
        # Only person records
        return f"({query}) AND data.type:pers"

    @classmethod
    def _get_names(cls, rawrecord: dict) -> Tuple[Optional[Field], Optional[List[Field]]]:
        preferred_name = safeget(rawrecord, ('shortDisplay',))
        namelist = safeget(rawrecord, ('data', 'agent'))
        alternative_names = None
        if namelist:
            alternative_names = [x["variants"] for x in namelist if x["variants"] != preferred_name]
        preferred_name_field = Field(preferred_name) if preferred_name else None
        alternative_names_field = [Field(x) for x in alternative_names] if alternative_names else None
        return preferred_name_field, alternative_names_field

    @classmethod
    def _get_timespan(cls, rawrecord: dict) -> Optional[Field]:
        timespan = safeget(rawrecord, ("dates",))
        if timespan:
            return Field(timespan)

    @classmethod
    def _get_activities(cls, rawrecord: dict) -> Optional[List[Field]]:
        profession_notes = safeget(rawrecord, ("data", "professionNote",))
        if not profession_notes:
            return None
        return [Field(x) for x in profession_notes]

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BiographicalRecord:
        record = BiographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord.get('id', None)
        if record.identifier:
            record.link = cls.LINK_BASE_URL + record.identifier
        record.name, record.variant_names = cls._get_names(rawrecord)
        record.timespan = cls._get_timespan(rawrecord)
        record.activities = cls._get_activities(rawrecord)
        return record


class STCNReader(STCNBaseReader):
    API_BY_ID_BASE_URL = 'https://data.cerl.org/stcn/'
    LINK_BASE_URL = 'https://data.cerl.org/stcn/'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/stcn'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/stcn/"
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "Short-Title Catalogue Netherlands (STCN)"
    DESCRIPTION = "National bibliography of The Netherlands until 1801"

    @classmethod
    def transform_query(cls, query) -> str:
        # Filter out bibliographical records
        return f"({query}) NOT data.type:pers NOT data.type:impr"

    @classmethod
    def _get_title(cls, rawrecord: dict) -> Optional[Field]:
        title = safeget(rawrecord, ("display", "title"))
        if isinstance(title, str):
            title = _remove_markup(title)
            return Field(title)

    @classmethod
    def _get_contributors(cls, rawrecord: dict) -> List[Field]:
        actors = safeget(rawrecord, ("data", "agent"))
        if not actors:
            return []
        return [_wrap_contributor(x) for x in actors if x.get('preferred')]

    @classmethod
    def _get_publisher_or_printer(cls, rawrecord: dict) -> Optional[Field]:
        # TODO: support multiple publishers/printers
        provision_agent = safeget(rawrecord, ("data", "provisionAgent"), first=True)
        if provision_agent is None:
            return None
        name = provision_agent.get("preferred", None)
        if name is None:
            return None
        field = Field(name)
        return field

    @classmethod
    def _get_place_of_publication(cls, rawrecord: dict) -> Optional[Field]:
        place = safeget(rawrecord, ("data", "provisionAgent", "place"), first=True)
        if place is None:
            return None
        else:
            field = LocationField(place)
            field.location_type = LocationField.LOCALITY
            return field

    @classmethod
    def _get_languages(cls, rawrecord: dict) -> List[Field]:
        languages = safeget(rawrecord, ("data", "language"))
        if languages is None:
            return []
        fields = []
        for language in languages:
            field = LanguageField(language)
            field.normalize()
            fields.append(field)
        return fields

    @classmethod
    def _get_dating(cls, rawrecord: dict) -> Optional[Field]:
        dating = safeget(rawrecord, ("data", "date"))
        if dating is not None:
            return Field(dating)

    @classmethod
    def _get_extent(cls, rawrecord: dict) -> Optional[Field]:
        sheets = safeget(rawrecord, ("data", "extent", "sheets"))
        if sheets is None:
            return None
        extent = f"{sheets} sheets"
        return Field(extent)

    @classmethod
    def _get_format(cls, rawrecord: dict) -> Optional[Field]:
        format_ = safeget(rawrecord, ("data", "format", "format"))
        if format_ is None:
            return None
        return Field(format_)

    @classmethod
    def _get_collation_formula(cls, rawrecord: dict) -> Optional[Field]:
        collations = safeget(rawrecord, ("data", "extent", "collation"))
        if not collations:
            return None
        # Multiple collation formulas are possible, but this seems to be rare.
        collation_string = ' ; '.join([x.get("value") for x in collations if "value" in x])
        return Field(collation_string)

    @classmethod
    def _get_fingerprint(cls, rawrecord: dict) -> Optional[Field]:
        fingerprints = safeget(rawrecord, ("data", "fingerprint"))
        if not fingerprints:
            return None
        # Multiple fingerprints are possible, but this seems to be rare
        fingerprint_string = ' ; '.join([x.get("fingerprint") for x in fingerprints if "fingerprint" in x])
        return Field(fingerprint_string)

    @classmethod
    def _get_genres(cls, rawrecord: dict) -> List[Field]:
        subjecttopics = safeget(rawrecord, ("data", "subjectTopic"))
        if subjecttopics is None:
            return []
        fields = [Field(x["preferred"]) for x in subjecttopics if "preferred" in x]
        return fields

    @classmethod
    def _get_holdings(cls, rawrecord: dict) -> List[Field]:
        holdings = safeget(rawrecord, ("data", "holdings"))
        if holdings is None:
            return []
        fields = []
        for holding in holdings:
            institution = safeget(holding, ("data", "institutionName"))
            shelfmark = safeget(holding, ("data", "shelfmark"))
            summary = f"{institution} - {shelfmark}"
            fields.append(Field(summary))
        return fields

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord.get('id', None)
        if record.identifier:
            record.link = cls.LINK_BASE_URL + record.identifier
        record.title = cls._get_title(rawrecord)
        record.contributors = cls._get_contributors(rawrecord)
        record.publisher_or_printer = cls._get_publisher_or_printer(rawrecord)
        record.place_of_publication = cls._get_place_of_publication(rawrecord)
        record.dating = cls._get_dating(rawrecord)
        record.languages = cls._get_languages(rawrecord)
        record.extent = cls._get_extent(rawrecord)
        record.bibliographical_format = cls._get_format(rawrecord)
        record.collation_formula = cls._get_collation_formula(rawrecord)
        record.fingerprint = cls._get_fingerprint(rawrecord)
        record.genres = cls._get_genres(rawrecord)
        record.holdings = cls._get_holdings(rawrecord)
        return record
