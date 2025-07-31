from typing import Optional

from rdflib import URIRef

from edpop_explorer import CERLReader, BiographicalRecord, BIBLIOGRAPHICAL, Field
from edpop_explorer.fields import LanguageField
from edpop_explorer.readers.utils import format_holding
from edpop_explorer.srumarc21reader import Marc21BibliographicalReaderMixin, Marc21Data, Marc21BibliographicalRecord, \
    Marc21Field


class ESTCReader(CERLReader, Marc21BibliographicalReaderMixin):
    API_URL = 'https://datb.cerl.org/estc/_search'
    LINK_BASE_URL = 'https://datb.cerl.org/estc/'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/estc'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/estc/"
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "English Short Title Catalogue"

    _title_field_subfield = ('245', ('a', 'b'))
    _alternative_title_field_subfield = ('246', 'a')
    _publisher_field_subfield = ('260', ('a', 'b'))
    _place_field_subfield = ('752', 'd')
    _dating_field_subfield = ('260', 'c')  # NB: consider using the "dates" part out of the Marc21 data
    _extent_field_subfield = ('300', 'a')
    _physical_description_field_subfield = ('300', 'b')
    _size_field_subfield = ('300', 'c')

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> Marc21BibliographicalRecord:
        data = cls._convert_to_marc21data(rawrecord)
        record = cls._marc21data_to_record(data)

        # Some data is available outside the Marc21 data structure, so add it here.
        language: Optional[str] = rawrecord.get('language', None)
        if language is not None:
            language_field = LanguageField(language)
            language_field.normalize()
            record.languages = [language_field]

        holding_data: Optional[list] = rawrecord.get('holdings', None)
        holdings = []
        if holding_data:
            assert isinstance(holding_data, list)
            for holding in holding_data:
                data = holding.get('data', None)
                if data:
                    institution = data.get('institution', None)
                    shelf_mark = data.get('smk', None)
                    holdings.append(format_holding(institution, shelf_mark))
        record.holdings = holdings if holdings else None

        return record

    @classmethod
    def _convert_to_marc21data(cls, raw_data: dict) -> Marc21Data:
        data = Marc21Data()
        data.raw = raw_data
        marc_sections = raw_data['sections']
        assert isinstance(marc_sections, dict)
        for _, section_content in marc_sections.items():
            # The Marc21 fields are divided into sections, but these are irrelevant to us.
            assert isinstance(section_content, dict)
            for field_number, repeated_fields in section_content.items():
                # The field data may contain a list of fields, because fields may be repeated.
                # Ensure that it is a list.
                if not isinstance(repeated_fields, list):
                    repeated_fields = [repeated_fields]
                for field_data in repeated_fields:
                    if isinstance(field_data, dict):
                        # Data field; these have a complex structure
                        field = Marc21Field(field_number)
                        field.indicator1 = field_data.get('ind1', None)
                        field.indicator2 = field_data.get('ind2', None)
                        subfields = field_data.get('clean_subfields', None) or field_data.get('subfields', [])
                        for subfield_data in subfields:
                            for subfield_code, contents in subfield_data.items():
                                field.subfields[subfield_code] = contents
                        data.fields.append(field)
                    elif isinstance(field_data, str):
                        # Control field; these are simply pairs of numbers and data
                        data.controlfields[field_number] = field_data
        return data

    @classmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        identifier = cls._get_identifier(data)
        if identifier:
            return cls.LINK_BASE_URL + identifier
        return None

    @classmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        return data.raw.get('id', None)

    @classmethod
    def _get_contributors(cls, data: Marc21Data) -> list[Field]:
        contributors: list[Field] = []
        contributor_fields = data.get_fields('100')
        for field in contributor_fields:
            name = field.subfields.get('a', '').rstrip(',')  # Remove any trailing comma
            name2 = field.subfields.get('b', '').rstrip(',')
            full_name = (name + ' ' + name2).strip()
            if full_name:
                contributors.append(Field(full_name))
        return contributors
