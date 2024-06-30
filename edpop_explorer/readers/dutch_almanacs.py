import csv
from pathlib import Path
from typing import List
from edpop_explorer import Reader, ReaderError, BibliographicalRecord
from rdflib import URIRef


class DutchAlmanacsReader(Reader):
    """ Dutch Almanacs database reader. Access with command 'dutalm'."""
    FILENAME = Path(__file__).parent / 'data' / 'biblio_dutchalmanacs.csv'
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/dutch_almanacs'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/dutch_almanacs/"
    FETCH_ALL_AT_ONCE = True
    SHORT_NAME = "Dutch Almanacs"
    DESCRIPTION = "Bibliography of Dutch Almanacs 1570-1710"

    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BibliographicalRecord:
        record = BibliographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord['ID']
        record.dating = rawrecord['Jaar']
        record.place_of_publication = rawrecord['Plaats uitgave']
        record.bookseller = rawrecord['Boekverkoper']
        record.contributors = rawrecord['Auteur']
        record.title = rawrecord['Titel']
        record.physical_description = rawrecord['Formaat']
        record.location = rawrecord['Vindplaats']
        record.update = rawrecord['Bijwerk']
        record.image = rawrecord['Figure']
        record.place_of_printing = rawrecord['Plaats druk']
        record.publisher_or_printer = rawrecord['Drukker']
        record.style = rawrecord['Stijl']
        return record

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

    @classmethod
    def get_by_id(cls, identifier: str) -> BibliographicalRecord:
        with open(cls.FILENAME, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['ID'] == identifier:
                    return cls._convert_record(row)
        raise ReaderError(f"Item with id {identifier} does not exist.")

    def _perform_query(self) -> List[BibliographicalRecord]:
        assert isinstance(self.prepared_query, str)

        # Search query in all columns, and fetch results based on query
        results = []
        with open(self.__class__.FILENAME, 'r', encoding='utf-8-sig') as file:
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