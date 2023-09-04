from dataclasses import dataclass, field as dataclass_field
from typing import Dict, List, Optional
import csv
from pathlib import Path
from abc import abstractmethod

from edpop_explorer import (
    BibliographicalRecord, RawData, SRUReader, Field, BIBLIOGRAPHICAL
)


READABLE_FIELDS_FILE = Path(__file__).parent / 'M21_fields.csv'
translation_dictionary: Dict[str, str] = {}
with open(READABLE_FIELDS_FILE) as dictionary_file:
    reader = csv.DictReader(dictionary_file)
    for row in reader:
        translation_dictionary[row['Tag number']] = \
            row[' Tag description'].strip()


@dataclass
class Marc21Field:
    """Python representation of a single field in a Marc21 record"""
    fieldnumber: str
    indicator1: str
    indicator2: str
    subfields: Dict[str, str] = dataclass_field(default_factory=dict)
    description: Optional[str] = None

    def __str__(self):
        '''
        Return the usual marc21 representation
        '''
        sf = []
        ind1 = self.indicator1 if self.indicator1.rstrip() != '' else '#'
        ind2 = self.indicator1 if self.indicator2.rstrip() != '' else '#'
        description = ' ({})'.format(self.description) \
            if self.description else ''
        for subfield in self.subfields:
            sf.append('$${} {}'.format(subfield, self.subfields[subfield]))
        return '{}{}: {} {} {}'.format(
            self.fieldnumber,
            description,
            ind1,
            ind2,
            '  '.join(sf)
        )


@dataclass
class Marc21Data(RawData):
    """Python representation of the data inside a Marc21 record"""
    # We use a list for the fields and not a dictionary because they may
    # appear more than once
    fields: List[Marc21Field] = dataclass_field(default_factory=list)
    controlfields: Dict[str, str] = dataclass_field(default_factory=dict)
    raw: dict = dataclass_field(default_factory=dict)

    def get_first_field(self, fieldnumber: str) -> Optional[Marc21Field]:
        '''Return the first occurance of a field with a given field number.
        May be useful for fields that appear only once, such as 245.
        Return None if field is not found.'''
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                return field
        return None

    def get_first_subfield(self, fieldnumber: str, subfield: str) -> Optional[str]:
        '''Return the requested subfield of the first occurance of a field with
        the given field number. Return None if field is not found or if the
        subfield is not present on the first occurance of the field.'''
        field = self.get_first_field(fieldnumber)
        if field is not None:
            return field.subfields.get(subfield, None)
        else:
            return None

    def get_fields(self, fieldnumber: str) -> List[Marc21Field]:
        '''Return a list of fields with a given field number. May return an
        empty list if field does not occur.'''
        returned_fields: List[Marc21Field] = []
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                returned_fields.append(field)
        return returned_fields

    def get_all_subfields(self, fieldnumber: str, subfield: str) -> List[str]:
        '''Return a list of subfields that matches the requested field number
        and subfield. May return an empty list if the field and subfield do not
        occur.'''
        fields = self.get_fields(fieldnumber)
        returned_subfields: List[str] = []
        for field in fields:
            if subfield in field.subfields:
                returned_subfields.append(field.subfields[subfield])
        return returned_subfields

    def to_dict(self) -> dict:
        return self.raw


class Marc21DataMixin():
    """A mixin that adds a ``data`` attribute to a Record class to contain
    an instance of ``Marc21Data``.
    """
    data: Optional[Marc21Data] = None

    def show_record(self) -> str:
        if self.data is None:
            return "(no data)"
        field_strings = []
        for field in self.data.fields:
            field_strings.append(str(field))
        return '\n'.join(field_strings)

class SRUMarc21Reader(SRUReader):
    '''Subclass of ``SRUReader`` that adds Marc21 functionality.

    This class is still abstract and to create concrete readers
    the ``_get_link()``, ``_get_identifier()`` 
    and ``_convert_record`` methods should be implemented.

    .. automethod:: _convert_record
    .. automethod:: _get_link
    .. automethod:: _get_identifier'''
    marcxchange_prefix: str = ''

    @classmethod
    def _get_subfields(cls, sruthifield) -> list:
        # If there is only one subfield, sruthi puts it directly in
        # a dict, otherwise it uses a list of dicts. Make sure that
        # we always have a list.
        subfielddata = sruthifield[f'{cls.marcxchange_prefix}subfield']
        if isinstance(subfielddata, dict):
            sruthisubfields = [subfielddata]
        else:
            sruthisubfields = subfielddata
        assert isinstance(sruthisubfields, list)
        return sruthisubfields

    @classmethod
    def _convert_to_marc21data(cls, sruthirecord: dict) -> Marc21Data:
        data = Marc21Data()
        data.raw = sruthirecord
        # marcxml (marc21 in xml) consists of a controlfield and a datafield.
        # The controlfield and the datafield contain multiple fields.
        # The controlfield consists of simple pairs of tags (field numbers)
        # and texts (field values).
        for sruthicontrolfield in \
                sruthirecord[f'{cls.marcxchange_prefix}controlfield']:
            tag = sruthicontrolfield['tag']
            text = sruthicontrolfield['text']
            data.controlfields[tag] = text
        # The datafield is more complex; these fields also have two indicators,
        # one-digit numbers that carry special meanings, and multiple subfields
        # that each have a one-character code.
        for sruthifield in sruthirecord[f'{cls.marcxchange_prefix}datafield']:
            fieldnumber = sruthifield['tag']
            field = Marc21Field(
                fieldnumber=fieldnumber,
                indicator1=sruthifield['ind1'],
                indicator2=sruthifield['ind2'],
                subfields={}
            )
            # The translation_dictionary contains descriptions for a number
            # of important fields. Include them so that the user can more
            # easily understand the record.
            if fieldnumber in translation_dictionary:
                field.description = translation_dictionary[fieldnumber]
            sruthisubfields = cls._get_subfields(sruthifield)

            for sruthisubfield in sruthisubfields:
                field.subfields[sruthisubfield['code']] = \
                    sruthisubfield['text']
            data.fields.append(field)
        return data
    
    @classmethod
    @abstractmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        '''Get a public URL according to the Marc21 data or ``None`` if it
        is not available.'''
        pass

    @classmethod
    @abstractmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        '''Get the unique identifier from the Marc21 data or ``None`` if it
        is not available.'''
        pass


class Marc21BibliographicalRecord(Marc21DataMixin, BibliographicalRecord):
    '''A combination of ``BibliographicalRecord`` and ``Marc21DataMixin``.'''
    pass


class SRUMarc21BibliographicalReader(SRUMarc21Reader):
    '''Subclass of ``SRUMarc21Reader`` that adds functionality to create
    instances of ``BibliographicRecord``.

    This subclass assumes that the Marc21 data is according to the standard
    format of Marc21 for bibliographical data. See:
    https://www.loc.gov/marc/bibliographic/
    '''
    _title_field_subfield = ('245', 'a')
    _alternative_title_field_subfield = ('246', 'a')
    _publisher_field_subfield = ('264', 'b')
    _language_field_subfield = ('041', 'a')
    _place_field_subfield = ('264', 'a')
    _dating_field_subfield = ('264', 'c')
    _extent_field_subfield = ('300', 'a')
    _physical_description_field_subfield = ('300', 'b')
    _size_field_subfield = ('300', 'c')

    records: List[Marc21BibliographicalRecord]
    READERTYPE = BIBLIOGRAPHICAL
    
    @classmethod
    def _convert_record(cls, sruthirecord: dict) -> Marc21BibliographicalRecord:
        record = Marc21BibliographicalRecord(from_reader=cls)
        data = cls._convert_to_marc21data(sruthirecord)
        record.data = data
        record.link = cls._get_link(data)
        record.identifier = cls._get_identifier(data)
        # NOTE: it is probably better to outfactor the following logic to
        # other class methods, to offer more flexibility and because this
        # will become more complex as we add normalization.
        title = data.get_first_subfield(*cls._title_field_subfield)
        if title:
            record.title = Field(title)
        alternative_title = data.get_first_subfield(
            *cls._alternative_title_field_subfield
        )
        if alternative_title:
            record.alternative_title = Field(alternative_title)
        publisher = data.get_first_subfield(*cls._publisher_field_subfield)
        if publisher:
            record.publisher_or_printer = Field(publisher)
        place = data.get_first_subfield(*cls._place_field_subfield)
        if place:
            record.place_of_publication = Field(place)
        language = data.get_first_subfield(*cls._language_field_subfield)
        # TODO: look up if this field is repeatable - if so support multiple
        # languages
        if language:
            record.languages = [Field(language)]
        dating = data.get_first_subfield(*cls._dating_field_subfield)
        if dating:
            record.dating = Field(dating)
        extent = data.get_first_subfield(*cls._extent_field_subfield)
        if extent:
            record.extent = Field(extent)
        physical_description = data.get_first_subfield(
            *cls._physical_description_field_subfield
        )
        if physical_description:
            record.physical_description = Field(physical_description)
        size = data.get_first_subfield(*cls._size_field_subfield)
        if size:
            record.size = Field(size)

        # Add the contributors
        record.contributors = cls._get_contributors(data)

        return record

    @classmethod
    def _get_contributors(cls, data: Marc21Data) -> List[Field]:
        contributors: List[Field] = []
        contributor_fields = data.get_fields('100')
        for field in contributor_fields:
            name = field.subfields.get('a')
            if name:
                contributors.append(Field(name))
        return contributors

