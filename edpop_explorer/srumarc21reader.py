from dataclasses import dataclass, field as dataclass_field
from typing import Dict, List, Optional
import csv
from pathlib import Path

from edpop_explorer.apireader import APIRecord
from edpop_explorer.srureader import SRUReader


READABLE_FIELDS_FILE = Path(__file__).parent / 'M21_fields.csv'
translation_dictionary = {}
with open(READABLE_FIELDS_FILE) as dictionary_file:
    reader = csv.DictReader(dictionary_file)
    for row in reader:
        translation_dictionary[row['Tag number']] = \
            row[' Tag description'].strip()


@dataclass
class Marc21RecordField:
    fieldnumber: str
    indicator1: str
    indicator2: str
    subfields: Dict[str, str] = dataclass_field(default_factory=list)
    description: Optional[str] = None

    def __repr__(self):
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
class Marc21Record(APIRecord):
    # We use a list for the fields and not a dictionary because they may
    # appear more than once
    fields: List[Marc21RecordField] = dataclass_field(default_factory=list)
    controlfields: Dict[str, str] = dataclass_field(default_factory=dict)
    link: Optional[str] = None
    title_field_subfield = ['245', 'a']

    def get_first_field(self, fieldnumber: str) -> Marc21RecordField:
        '''Return the first occurance of a field with a given field number.
        May be useful for fields that appear only once, such as 245.
        Return None if field is not found.'''
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                return field
        return None

    def get_fields(self, fieldnumber: str) -> List[Marc21RecordField]:
        '''Return a list of fields with a given field number. May return an
        empty list if field does not occur.'''
        returned_fields = []
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                returned_fields.append(field)
        return returned_fields

    def get_title(self):
        title_field = self.get_first_field(self.title_field_subfield[0])
        if title_field:
            return title_field.subfields.get(
                self.title_field_subfield[1],
                '(unknown title)'
            )
        else:
            return '(unknown title)'

    def show_record(self) -> str:
        field_strings = []
        for field in self.fields:
            field_strings.append(str(field))
        return '\n'.join(field_strings)

    def __repr__(self):
        return self.get_title()


class SRUMarc21Reader(SRUReader):
    marcxchange_prefix = ''
    records: List[Marc21Record]

    def _get_subfields(self, sruthifield) -> list:
        # If there is only one subfield, sruthi puts it directly in
        # a dict, otherwise it uses a list of dicts. Make sure that
        # we always have a list.
        subfielddata = sruthifield[f'{self.marcxchange_prefix}subfield']
        if type(subfielddata) == dict:
            sruthisubfields = [subfielddata]
        else:
            sruthisubfields = subfielddata
        assert type(sruthisubfields) == list
        return sruthisubfields

    def _convert_record(self, sruthirecord: dict) -> Marc21Record:
        record = Marc21Record()
        # marcxml (marc21 in xml) consists of a controlfield and a datafield.
        # The controlfield and the datafield contain multiple fields.
        # The controlfield consists of simple pairs of tags (field numbers)
        # and texts (field values).
        for sruthicontrolfield in \
                sruthirecord[f'{self.marcxchange_prefix}controlfield']:
            tag = sruthicontrolfield['tag']
            text = sruthicontrolfield['text']
            record.controlfields[tag] = text
        # The datafield is more complex; these fields also have two indicators,
        # one-digit numbers that carry special meanings, and multiple subfields
        # that each have a one-character code.
        for sruthifield in sruthirecord[f'{self.marcxchange_prefix}datafield']:
            fieldnumber = sruthifield['tag']
            field = Marc21RecordField(
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
            sruthisubfields = self._get_subfields(sruthifield)

            for sruthisubfield in sruthisubfields:
                field.subfields[sruthisubfield['code']] = \
                    sruthisubfield['text']
            record.fields.append(field)
        record.link = self.get_link(record)
        return record

    def get_link(self, record: APIRecord) -> Optional[str]:
        raise NotImplementedError('Should be implemented by subclass')
