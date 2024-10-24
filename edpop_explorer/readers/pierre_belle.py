import csv
from typing import List
from edpop_explorer import Reader, ReaderError, BibliographicalRecord, Field, DatabaseFileMixin, BIBLIOGRAPHICAL
from rdflib import URIRef

from edpop_explorer.fields import LanguageField


class PierreBelleReader(DatabaseFileMixin, Reader):
    """ Pierre-Belle database reader. Access with command 'pb'."""
    DATABASE_URL = 'https://dhstatic.hum.uu.nl/edpop/biblio_pierrebelle.csv'
    DATABASE_FILENAME = 'biblio_pierrebelle.csv'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/pierre_belle'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/pierre_belle/"
    FETCH_ALL_AT_ONCE = True
    READERTYPE = BIBLIOGRAPHICAL
    SHORT_NAME = "Pierre and Belle"
    DESCRIPTION = "Bibliography of early modern editions of Pierre de " \
        "Provence et la Belle Maguelonne (ca. 1470-ca. 1800)"

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord['ID']
        record.title = Field(rawrecord['Shortened title'])
        record.languages = [LanguageField(rawrecord['Language'])]
        [x.normalize() for x in record.languages]
        record.publisher_or_printer = Field(rawrecord['Publisher'])
        record.place_of_publication = Field(rawrecord['Place of publication'])
        record.dating = Field(rawrecord['Date'])
        return record

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

    @classmethod
    def get_by_id(cls, identifier: str) -> BibliographicalRecord:
        reader = cls()
        reader.prepare_data()
        with open(reader.database_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['ID'] == identifier:
                    return cls._convert_record(row)
        raise ReaderError(f"Item with id {identifier} does not exist.")
    
    def _perform_query(self) -> List[BibliographicalRecord]:
        assert isinstance(self.prepared_query, str)
        self.prepare_data()
        
        # Search query in all columns, and fetch results based on query
        results = []
        with open(self.database_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                for key in row.keys():
                    if self.prepared_query in row[key]:
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