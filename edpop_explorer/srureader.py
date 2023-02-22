import sruthi
import csv
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field as dataclass_field

from edpop_explorer.apireader import APIReader


READABLE_FIELDS_FILE = Path(__file__).parent / 'M21_fields.csv'
translation_dictionary = {}
with open(READABLE_FIELDS_FILE) as dictionary_file:
    reader = csv.DictReader(dictionary_file)
    for row in reader:
        translation_dictionary[row['Tag number']] = \
            row[' Tag description'].strip()


@dataclass
class SRURecordField:
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
class SRURecord:
    # We use a list for the fields and not a dictionary because they may
    # appear more than once
    fields: List[SRURecordField] = dataclass_field(default_factory=list)
    url: Optional[str] = None

    def get_first_field(self, fieldnumber: str) -> SRURecordField:
        '''Return the first occurance of a field with a given field number.
        May be useful for fields that appear only once, such as 245.
        Return None if field is not found.'''
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                return field
        return None

    def get_fields(self, fieldnumber: str) -> List[SRURecordField]:
        '''Return a list of fields with a given field number. May return an
        empty list if field does not occur.'''
        returned_fields = []
        for field in self.fields:
            if field.fieldnumber == fieldnumber:
                returned_fields.append(field)
        return returned_fields

    def get_title(self):
        field_245 = self.get_first_field('245')
        if field_245:
            return field_245.subfields.get('a', '(unknown title)')
        else:
            return '(unknown title)'

    def show_record(self) -> str:
        field_strings = []
        for field in self.fields:
            field_strings.append(str(field))
        return '\n'.join(field_strings)

    def __repr__(self):
        return self.get_title()


RECORDS_PER_PAGE = 10


class SRUReader(APIReader):
    sru_url: str = None
    sru_version: str = None
    query: str = None
    records: List[SRURecord]
    fetching_exhausted: bool = False

    def _perform_query(self, query: str, start_record: int) -> List[SRURecord]:
        try:
            response = sruthi.searchretrieve(
                self.sru_url,
                query,
                start_record=start_record,
                maximum_records=RECORDS_PER_PAGE,
                sru_version=self.sru_version
            )
        except (
            sruthi.errors.SruError, sruthi.errors.SruthiError
        ):
            raise

        records: List[SRURecord] = []
        self.number_of_results = response.count

        for sruthirecord in response[0:RECORDS_PER_PAGE]:
            record = SRURecord()
            for sruthifield in sruthirecord['datafield']:
                fieldnumber = sruthifield['tag']
                field = SRURecordField(
                    fieldnumber=fieldnumber,
                    indicator1=sruthifield['ind1'],
                    indicator2=sruthifield['ind2'],
                    subfields={}
                )
                if fieldnumber in translation_dictionary:
                    field.description = translation_dictionary[fieldnumber]
                # If there are multiple subfields, sruthi puts it directly in
                # a dict, otherwise it uses a list of dicts
                if type(sruthifield['subfield']) == dict:
                    sruthisubfields = [sruthifield['subfield']]
                else:
                    sruthisubfields = sruthifield['subfield']
                assert type(sruthisubfields) == list
                for sruthisubfield in sruthisubfields:
                    field.subfields[sruthisubfield['code']] = \
                        sruthisubfield['text']
                record.fields.append(field)
            records.append(record)
        return records

    def fetch(self, query) -> List[SRURecord]:
        self.records = []
        self.query = query
        results = self._perform_query(query, 1)
        self.records.extend(results)
        return results

    def fetch_next(self) -> List[SRURecord]:
        start_record = len(self.records) + 1
        results = self._perform_query(self.query, start_record)
        self.records.extend(results)
        return results
