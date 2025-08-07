from rdflib import URIRef
from edpop_explorer import SRUReader, BibliographicalRecord, Field, BIBLIOGRAPHICAL
from typing import Optional
import re
import requests
import xmltodict

from edpop_explorer.fields import LanguageField, DigitizationField


def _force_list(data) -> list:
    if isinstance(data, list):
        return data
    elif data is None:
        return []
    else:
        return [data]


def _force_string(data) -> Optional[str]:
    '''Transform data into one string or None. Can be used if a single 
    string is expected, but if there is a possibility that it is a
    list.'''
    if isinstance(data, list):
        return ' ; '.join([str(x) for x in data])
    elif data is None:
        return None
    else:
        return str(data)


class GallicaReader(SRUReader):
    sru_url = 'https://gallica.bnf.fr/SRU'
    sru_version = '1.2'
    CERL_LINK = 'https://data.cerl.org/thesaurus/{}'
    CTAS_PREFIX = 'http://sru.cerl.org/ctas/dtd/1.1:'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/gallica'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/gallica/"
    DOCUMENT_API_URL = "https://gallica.bnf.fr/services/OAIRecord?ark={}"
    IDENTIFIER_PREFIX = "https://gallica.bnf.fr/"
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "Gallica"
    DESCRIPTION = "Digital library of the Bibliothèque nationale de France " \
        "and its partners"

    @classmethod
    def _get_digitization_field(cls, identifier: str, sruthirecord: dict) -> DigitizationField:
        # In Gallica, every record *is* a digitization, so we can just extract
        # the values from the record.

        # The IIIF manifest is not included in the record but can be distilled
        # from the identifier
        iiif_manifest = f"https://gallica.bnf.fr/iiif/{identifier}/manifest.json"
        extra = sruthirecord.get('extra', None)
        preview_url = None
        if isinstance(extra, dict):
            preview_url = extra.get('medres', None)

        field = DigitizationField(iiif_manifest)
        field.description = "IIIF digital object"
        field.iiif_manifest = iiif_manifest
        field.preview_url = preview_url
        return field

    @classmethod
    def _convert_record(cls, sruthirecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(cls)
        # identifier field contains visitable Gallica URL and possibly
        # also other types of identifier. In the first case we get it as a
        # string from sruthi, in the latter case as a list of strings.
        # Take the first string starting with https:// as the identifier
        # and as the link.
        identifiers = _force_list(sruthirecord.get('identifier', None))
        for identifier in identifiers:
            if identifier.startswith(cls.IDENTIFIER_PREFIX):
                record.identifier = identifier[len(cls.IDENTIFIER_PREFIX):]
                record.link = identifier
        record.data = {}
        for key in sruthirecord:
            if key in ['schema', 'id']:
                continue
            showkey: str = key.replace(cls.CTAS_PREFIX, 'ctas:')
            record.data[showkey] = sruthirecord[key]
        record.data = sruthirecord
        title = _force_string(sruthirecord.get('title', None))
        if title:
            record.title = Field(title)
        creators = _force_list(sruthirecord.get('creator', None))
        record.contributors = [Field(x) for x in creators]
        dating = _force_string(sruthirecord.get('date', None))
        if dating:
            record.dating = Field(dating)
        languages = _force_list(sruthirecord.get('language', None))
        record.languages = [LanguageField(x) for x in languages]
        [x.normalize() for x in record.languages]
        publisher = _force_string(sruthirecord.get('publisher', None))
        if publisher:
            record.publisher_or_printer = Field(publisher)
        record.digitization = [cls._get_digitization_field(record.identifier, sruthirecord)]

        # Format is more complicated: this is a list and generally contains
        # the number of views, the MIME type and the extent.
        # Try finding the extent by filtering out the other two.
        # This seems to work correctly.
        format_strings = _force_list(sruthirecord.get('format', None))
        for formatstr in format_strings:
            if not (formatstr.startswith('Nombre total de vues') or
                    re.match('$[a-z]+/[a-z]+^', formatstr)):
                record.extent = Field(formatstr)
                break

        return record

    @classmethod
    def get_by_id(cls, identifier: str) -> BibliographicalRecord:
        # Getting by id works via another interface (a simple XML API), but the 
        # returned data is the same in a slightly different format. Hence,
        # convert it to JSON just like sruthi does and extract the right piece
        # of data.
        url = cls.DOCUMENT_API_URL.format(identifier)
        res = requests.get(url, headers={"accept": "application/xml"})
        response_as_dict = xmltodict.parse(
            res.text,
            dict_constructor=dict,
            process_namespaces=True,
            namespaces={  # Remove these namespace prefixes
                "http://purl.org/dc/elements/1.1/": None,
                "http://www.openarchives.org/OAI/2.0/oai_dc/": None,
            },
            attr_prefix="",
            cdata_key="text",
        )
        data = response_as_dict["results"]["notice"]["record"]["metadata"]["dc"]
        # The returned XML has elements with attributes, while these attributes
        # are missing from the XML that is sent back by the SRU interface.
        # An attribute-less element is represented as a simple string by 
        # xmltodict, while an attribute with elements is represented as a 
        # dict where the contents is in the value of "text". Replace these
        # dicts with simple strings. (Not a very clean solution but refactoring
        # is not worth the time at this point.)
        for key in data:
            value = data[key]
            if isinstance(value, list):
                for index in range(len(value)):
                    item = value[index]
                    if isinstance(item, dict):
                        value[index] = item["text"]
        return cls._convert_record(data)

    @classmethod
    def transform_query(cls, query: str) -> str:
        return 'gallica all {}'.format(query)
