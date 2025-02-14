from typing import Optional, List
from rdflib import URIRef
from edpop_explorer import SRUReader, BibliographicalRecord, BIBLIOGRAPHICAL
from edpop_explorer import Field
from edpop_explorer.fields import LanguageField, ContributorField


class KBReader(SRUReader):
    sru_url = 'http://jsru.kb.nl/sru'
    sru_version = '1.2'
    KB_LINK = 'https://webggc.oclc.org/cbs/DB=2.37/PPN?PPN={}'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/kb'
    )
    READERTYPE = BIBLIOGRAPHICAL
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/kb/"
    SHORT_NAME = "Koninklijke Bibliotheek (KB)"
    DESCRIPTION = "General catalogue of KB, national library of The Netherlands."
    _EXTENT_LOCATION = "http://purl.org/dc/terms/:extent"

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
        # This seems to work fine; not thoroughly tested.
        oai_pmh_identifier = data.get('OaiPmhIdentifier', None)
        if not isinstance(oai_pmh_identifier, str):
            return None
        PREFIX = 'GGC:AC:'
        if oai_pmh_identifier and oai_pmh_identifier.startswith(PREFIX):
            return oai_pmh_identifier[len(PREFIX):]
        return None

    def _convert_record(self, sruthirecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=type(self))
        record.data = sruthirecord
        record.identifier = self._find_ppn(record.data)
        if record.identifier:
            # Also here: it seems to work, but there may be records where
            # it doesn't work...
            # NOTE: there is often a URL in the `identifier' field as well,
            # but not always, and it uses a `resolver', which is slower.
            # But if we find records for which no link can be found this may
            # be an alternative.
            record.link = self.KB_LINK.format(record.identifier)
        record.title = self._get_title(sruthirecord)
        record.languages = self._get_languages(sruthirecord)
        record.extent = self._get_extent(sruthirecord)
        record.size = self._get_size(sruthirecord)
        record.publisher_or_printer = self._get_publisher(sruthirecord)
        record.contributors = self._get_contributors(sruthirecord)
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

    def _get_extent(self, data) -> Optional[Field]:
        if self._EXTENT_LOCATION in data:
            return Field(data[self._EXTENT_LOCATION][0])

    def _get_size(self, data) -> Optional[Field]:
        if self._EXTENT_LOCATION in data:
            return Field(data[self._EXTENT_LOCATION][1])

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
