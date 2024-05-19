import csv
from pathlib import Path
from typing import List, Dict, Optional
from edpop_explorer import Reader, ReaderError, BibliographicalRecord

class PierreBelleReader(Reader):
    filename = Path(__file__).parent /'data'/'biblio_pierrebelle.csv'

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord['ID']
        record.title = rawrecord['Shortened title']
        record.languages = [rawrecord['Language']]
        record.publisher_or_printer = rawrecord['Publisher']
        record.place_of_publication = rawrecord['Place of publication']
        record.dating = rawrecord['Date']
        return record

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

    @classmethod
    def get_by_id(cls, identifier: str) -> BibliographicalRecord:
        with open(cls.filename, 'r',encoding='utf-8-sig') as file:
            reader = csv.DictReader(file,delimiter=';')
            for row in reader:
                if row['ID'] == identifier:
                    return cls._convert_record(row)
        raise ReaderError(f"Item with id {identifier} does not exist.")
    

    def _perform_query(self, start_record: int, maximum_records: Optional[int]) -> List[BibliographicalRecord]:
        assert isinstance(self.prepared_query, str)
        if maximum_records is None:
            maximum_records = self.DEFAULT_RECORDS_PER_PAGE
        
        # Fetch results based on query
        results = []
        with open(self.__class__.filename, 'r',encoding='utf-8-sig') as file:
            reader = csv.DictReader(file,delimiter=';')
            for row in reader:
                found = False
                for key in row.keys():
                    if self.prepared_query in row[key]:
                        results.append(row)
                        found = True
                    if found:
                        break
        
        self.number_of_results = len(results)
        records = []
        for result in results:
            record = self._convert_record(result)
            records.append(record)

        return records


    def fetch_range(self, range_to_fetch: range) -> range:
        if self.prepared_query is None:
            raise ReaderError('First call prepare_query')
        if self.fetching_exhausted:
            return range(0)
        start_record = range_to_fetch.start
        number_to_fetch = range_to_fetch.stop - start_record
        results = self._perform_query(start_record, number_to_fetch)
        for i, result in enumerate(results):
            self.records[i] = result
        return range(start_record, start_record + len(results))