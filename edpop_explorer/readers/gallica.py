from edpop_explorer import SRUReader, BibliographicalRecord, Field
from typing import Optional
import re


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
            if identifier.startswith('https://'):
                record.identifier = identifier
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
        record.languages = [Field(x) for x in languages]
        publisher = _force_string(sruthirecord.get('publisher', None))
        if publisher:
            record.publisher_or_printer = Field(publisher)

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

    def transform_query(self, query: str) -> str:
        return 'gallica all {}'.format(query)
