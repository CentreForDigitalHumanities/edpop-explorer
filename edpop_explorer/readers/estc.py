from typing import Optional

from rdflib import URIRef

from edpop_explorer import CERLReader, BiographicalRecord, BIBLIOGRAPHICAL
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

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> Marc21BibliographicalRecord:
        data = cls._convert_to_marc21data(rawrecord)
        return cls._marc21data_to_record(data)

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
                        subfields = field_data.get('clean_subfields', None) or field_data.get('subfields', None)
                        for subfield_data in field_data['subfields']:
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
