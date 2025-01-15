import csv
from typing import List
from edpop_explorer import Reader, ReaderError, Field, BiographicalRecord, BIOGRAPHICAL, DatabaseFileMixin
from rdflib import URIRef


class KVCSReader(DatabaseFileMixin, Reader):
    """ KVCS database reader. Access with command 'kvcs'."""
    DATABASE_URL = 'https://dhstatic.hum.uu.nl/edpop/biblio_kvcs.csv'
    DATABASE_FILENAME = 'biblio_kvcs.csv'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/kvcs'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/kvcs/"
    FETCH_ALL_AT_ONCE = True
    SHORT_NAME = "KVCS"
    DESCRIPTION = "Drukkers & Uitgevers in KVCS"
    READERTYPE = BIOGRAPHICAL

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BiographicalRecord:
        record = BiographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord['ID']
        record.name = Field(rawrecord['Name'])
        record.gender = Field(rawrecord['Gender'])
        record.timespan = Field(rawrecord['Years of life'])
        record.places_of_activity = Field(rawrecord['City'])
        record.activity_timespan = Field(rawrecord['Years of activity'])
        record.activities = Field(rawrecord['Kind of print and sales activities'])
        return record

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

    @classmethod
    def get_by_id(cls, identifier: str) -> BiographicalRecord:
        reader = cls()
        reader.prepare_data()
        with open(reader.database_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['ID'] == identifier:
                    return cls._convert_record(row)
        raise ReaderError(f"Item with id {identifier} does not exist.")
    
    def _perform_query(self) -> List[BiographicalRecord]:
        assert isinstance(self.prepared_query, str)
        self.prepare_data()
        
        # Search query in all columns, and fetch results based on query
        results = []
        with open(self.database_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                for key in row.keys():
                    if self.prepared_query.lower() in row[key].lower():
                        results.append(row)
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
        results = self._perform_query()
        for i, result in enumerate(results):
            self.records[i] = result
        return range(start_record, start_record + len(results))