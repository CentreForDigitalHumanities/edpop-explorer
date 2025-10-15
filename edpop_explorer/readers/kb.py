import re
from typing import Optional, List, Literal
from rdflib import URIRef
from edpop_explorer import SRUReader, BibliographicalRecord, BIBLIOGRAPHICAL
from edpop_explorer import Field
from edpop_explorer.fields import LanguageField, ContributorField

ExtentType = Literal['extent', 'size', 'bibliographical-format']


def get_extent_type(input_string: str) -> ExtentType:
    # KB's 'extent' field is broader than ours: it may also contain the
    # bibliographical format or the size.
    # If it is of the format in-<number>, assume bibliographical format.
    if re.match(r'^in-\d+$', input_string):
        return 'bibliographical-format'
    elif input_string.endswith(' cm'):
        return 'size'
    else:
        return 'extent'


def get_extent_like_fields(data: dict, type_: ExtentType) -> List[Field]:
    if KBReader.EXTENT_LOCATION not in data:
        return []
    if isinstance(data[KBReader.EXTENT_LOCATION], list):
        extent = data[KBReader.EXTENT_LOCATION]
    else:
        extent = [data[KBReader.EXTENT_LOCATION]]
    return list(map(Field, filter(lambda x: get_extent_type(x) == type_, extent)))


class KBReader(SRUReader):
    sru_url = 'https://jsru.kb.nl/sru/sru'
    sru_version = '1.2'
    KB_LINK = 'https://webggc.oclc.org/cbs/DB=2.37/PPN?PPN={}'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/kb'
    )
    READERTYPE = BIBLIOGRAPHICAL
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/kb/"
    SHORT_NAME = "Koninklijke Bibliotheek (KB)"
    DESCRIPTION = "General catalogue of KB, national library of The Netherlands."
    EXTENT_LOCATION = "http://purl.org/dc/terms/:extent"

    def __init__(self):
        super().__init__()
        # The KB SRU requires 'x-collection' as an additional GET parameter
        self.session.params = {
            'x-collection': 'GGC'
        }

    @classmethod
    def transform_query(cls, query: str) -> str:
        return query

    def _find_ppn(self, data: dict):
        """Try to find the PPN given the data that comes from the SRU server;
        return None if PPN cannot be found"""
        # First try OAI-PMH identifier
        oai_pmh_identifier = data.get('OaiPmhIdentifier', None)
        prefix = 'GGC:AC:'
        if isinstance(oai_pmh_identifier, str) and oai_pmh_identifier.startswith(prefix):
            return oai_pmh_identifier[len(prefix):]
        # If not available, try recordIdentifier
        record_identifier = data.get('http://krait.kb.nl/coop/tel/handbook/telterms.html:recordIdentifier', None)
        if isinstance(record_identifier, str):
            # Record identifier is an URL that should end with PPN=<PPN>. The start of the URL is variable.
            match = re.match(r'^.*PPN=(\d+)$', record_identifier)
            if match:
                return match.group(1)
        return None

    def _convert_record(self, sruthirecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=type(self))
        record.data = sruthirecord
        record.identifier = self._find_ppn(record.data)
        if record.identifier:
            record.link = self.KB_LINK.format(record.identifier)
        record.title = self._get_title(sruthirecord)
        record.languages = self._get_languages(sruthirecord)
        record.extent = get_extent_like_fields(sruthirecord, 'extent')
        record.size = get_extent_like_fields(sruthirecord, 'size')
        record.bibliographical_format = get_extent_like_fields(sruthirecord, 'bibliographical-format')
        record.publisher_or_printer = self._get_publisher(sruthirecord)
        record.contributors = self._get_contributors(sruthirecord)
        record.dating = self._get_dating(sruthirecord)
        return record
    
    def _get_title(self, data) -> Optional[Field]:
        if 'title' in data:
            title = data['title']
            if isinstance(title, list):
                # Title contains a list of strings if it consists of multiple
                # parts
                return Field(' : '.join(title))
            else:
                return Field(title)
        else:
            return None

    def _get_languages(self, data) -> Optional[List[Field]]:
        # The 'language' field contains a list of languages, where every
        # language is repeated multiple times in different languages.
        # One of them is always a three-letter language code, so only
        # pass on these. NB: there is a possibility that not all entries
        # consisting of three characters are language codes.
        if 'language' not in data:
            return []
        fields = [
            LanguageField(x) for x in data['language']
            if isinstance(x, str) and len(x) == 3
        ]
        for field in fields:
            field.normalize()
        return fields

    def _get_publisher(self, data) -> Optional[List[Field]]:
        if "publisher" in data:
            pub = data["publisher"]
            if not isinstance(pub, list):
                pub = [pub]
            return [Field(x) for x in pub]

    def _get_contributors(self, data) -> Optional[List[Field]]:
        contributors = []
        for type_ in ['creator', 'contributor']:
            data_ = data.get(type_, None)
            if not data_:
                continue
            if isinstance(data_, str):
                # Wrap in a list if it is a single string
                data_ = [data_]
            assert isinstance(data_, list)
            for item in data_:
                field = ContributorField(item)
                field.role = type_
                contributors.append(field)
        return contributors

    def _get_dating(self, data) -> Optional[Field]:
        date = data.get('date', None)
        # Dates are such as 'Wed Jan 01 01:00:00 CET 1992' - only the year is relevant.
        if date:
            return Field(date.split()[-1])
