import csv
from typing import List
from edpop_explorer import Reader, ReaderError, Field, BibliographicalRecord, BIBLIOGRAPHICAL, DatabaseFileMixin
from rdflib import URIRef


class DutchAlmanacsReader(DatabaseFileMixin, Reader):
    """ Dutch Almanacs database reader. Access with command 'dutalm'."""
    DATABASE_URL = 'https://dhstatic.hum.uu.nl/edpop/biblio_dutchalmanacs.csv'
    DATABASE_FILENAME = 'biblio_dutchalmanacs.csv'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/dutch_almanacs'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/dutch_almanacs/"
    FETCH_ALL_AT_ONCE = True
    SHORT_NAME = "Dutch Almanacs"
    DESCRIPTION = "Bibliography of Dutch Almanacs 1570-1710"
    READERTYPE = BIBLIOGRAPHICAL

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord['ID']
        record.dating = Field(rawrecord['Jaar'])
        record.place_of_publication = Field(rawrecord['Plaats uitgave'])
        record.bookseller = Field(rawrecord['Boekverkoper'])
        record.contributors = [Field(author.strip()) for author in rawrecord['Auteur'].split('/')]
        record.title = Field(rawrecord['Titel'])
        record.physical_description = Field(rawrecord['Formaat'])
        record.holdings = [Field(rawrecord['Vindplaats'])]
        record.publisher_or_printer = Field(rawrecord['Drukker'])
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