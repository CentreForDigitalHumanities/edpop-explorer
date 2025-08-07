from dataclasses import dataclass, field as dataclass_field
from typing import Dict, List, Optional, Union
import csv
from pathlib import Path
from abc import abstractmethod, ABC

from edpop_explorer import BibliographicalRecord, RawData, Field, Reader
from edpop_explorer.fields import LanguageField

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
    indicator1: Optional[str] = None
    indicator2: Optional[str] = None
    subfields: Dict[str, str] = dataclass_field(default_factory=dict)
    description: Optional[str] = None

    def __str__(self):
        '''
        Return the usual marc21 representation
        '''
        sf = []
        ind1 = self.indicator1 if self.indicator1 and self.indicator1.rstrip() != '' else '#'
        ind2 = self.indicator1 if self.indicator2 and self.indicator2.rstrip() != '' else '#'
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
    picafields: List[Marc21Field] = dataclass_field(default_factory=list)
    raw: dict = dataclass_field(default_factory=dict)

    def get_first_field(self, fieldnumber: str, picaxml=False) -> Optional[Marc21Field]:
        '''Return the first occurance of a field with a given field number.
        May be useful for fields that appear only once, such as 245.
        Return None if field is not found.'''
        for field in (self.fields if not picaxml else self.picafields):
            if field.fieldnumber == fieldnumber:
                return field
        return None

    def get_first_subfield(self, fieldnumber: str, subfield: Union[str, tuple[str]], picaxml=False) -> Optional[str]:
        '''Return the requested subfield of the first occurance of a field with
        the given field number. Return None if field is not found or if the
        subfield is not present on the first occurance of the field.
        ``subfield`` may be a tuple, in that case a concatenation of all
        given subfields is returned.'''
        field = self.get_first_field(fieldnumber, picaxml=picaxml)
        if field is not None:
            if isinstance(subfield, tuple):
                return ' '.join(field.subfields.get(x, '') for x in subfield)
            else:
                return field.subfields.get(subfield, None)
        else:
            return None

    def get_fields(self, fieldnumber: str, picaxml=False) -> List[Marc21Field]:
        '''Return a list of fields with a given field number. May return an
        empty list if field does not occur.'''
        returned_fields: List[Marc21Field] = []
        for field in (self.fields if not picaxml else self.picafields):
            if field.fieldnumber == fieldnumber:
                returned_fields.append(field)
        return returned_fields

    def get_all_subfields(self, fieldnumber: str, subfield: str, picaxml=False) -> List[str]:
        '''Return a list of subfields that matches the requested field number
        and subfield. May return an empty list if the field and subfield do not
        occur.'''
        fields = self.get_fields(fieldnumber, picaxml)
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
        field_strings = list(map(str, self.data.fields))
        return '\n'.join(field_strings)


class Marc21BibliographicalRecord(Marc21DataMixin, BibliographicalRecord):
    '''A combination of ``BibliographicalRecord`` and ``Marc21DataMixin``.'''
    pass


class Marc21BibliographicalReaderMixin(Reader, ABC):
    _title_field_subfield = ('245', 'a')
    _alternative_title_field_subfield = ('246', 'a')
    _publisher_field_subfield = ('264', 'b')
    _language_field_subfield = ('041', 'a')
    _place_field_subfield = ('264', 'a')
    _dating_field_subfield = ('264', 'c')
    _extent_field_subfield = ('300', 'a')
    _physical_description_field_subfield = ('300', 'b')
    _size_field_subfield = ('300', 'c')
    _fingerprint_field_subfield = ('026', 'e')

    @classmethod
    @abstractmethod
    def _get_link(cls, data: Marc21Data) -> Optional[str]:
        pass

    @classmethod
    @abstractmethod
    def _get_identifier(cls, data: Marc21Data) -> Optional[str]:
        pass

    @classmethod
    def _marc21data_to_record(cls, data: Marc21Data) -> Marc21BibliographicalRecord:
        record = Marc21BibliographicalRecord(from_reader=cls)
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
            language_field = LanguageField(language)
            language_field.normalize()
            record.languages = [language_field]
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
        fingerprint = data.get_first_subfield(*cls._fingerprint_field_subfield)
        if fingerprint:
            record.fingerprint = Field(fingerprint)

        # Add the contributors
        record.contributors = cls._get_contributors(data)

        # Add the holdings
        record.holdings = cls._get_holdings(data)

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

    @classmethod
    def _get_holdings(cls, data: Marc21Data) -> List[Field]:
        # There is no default place where the holdings can be found, so
        # leave this to readers.
        return []
