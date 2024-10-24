from rdflib import Graph, Namespace, URIRef
from rdflib.term import Node
from typing import List, Optional, Tuple

from edpop_explorer import Field, BIBLIOGRAPHICAL, BibliographicalRecord, LocationField
from edpop_explorer.cerl import CERLReader
from edpop_explorer.fields import LanguageField, ContributorField
from edpop_explorer.sparqlreader import (
    SparqlReader, BibliographicalRDFRecord
)


def _remove_markup(input_str: str) -> str:
    """Remove STCN-specific markup"""
    return input_str.replace('`IT`', '').replace('`LO`', '')


def safeget(dictionary: Optional[dict], attribute_chain: tuple, first: bool = False):
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


class STCNReader(CERLReader):
    API_URL = 'https://data.cerl.org/stcn/_search'
    API_BY_ID_BASE_URL = 'https://data.cerl.org/stcn/'
    LINK_BASE_URL = 'https://data.cerl.org/stcn/'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/stcn'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/stcn/"
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "Short-Title Catalogue Netherlands (STCN)"
    DESCRIPTION = "National biography of The Netherlands until 1801"

    @classmethod
    def _get_title(cls, rawrecord: dict) -> Optional[Field]:
        title = safeget(rawrecord, ("display", "title"))
        if isinstance(title, str):
            title = _remove_markup(title)
            return Field(title)

    @classmethod
    def _get_contributors(cls, rawrecord: dict) -> list[Field]:
        actors = safeget(rawrecord, ("data", "agent"))
        if not actors:
            return []
        contributors = []
        for actor in actors:
            name = actor.get("preferred", None)
            if name is None:
                continue
            contributor = ContributorField(name)
            contributor.name = name
            contributor.role = safeget(actor, ('role',), first=True)
            contributors.append(contributor)
        return contributors

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
    def _get_languages(cls, rawrecord: dict) -> list[Field]:
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
    def _get_genres(cls, rawrecord: dict) -> list[Field]:
        subjecttopics = safeget(rawrecord, ("data", "subjectTopic"))
        if subjecttopics is None:
            return []
        fields = [Field(x["preferred"]) for x in subjecttopics if "preferred" in x]
        return fields

    @classmethod
    def _get_holdings(cls, rawrecord: dict) -> list[Field]:
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
