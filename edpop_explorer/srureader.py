import sruthi
from typing import List
import json

from edpop_explorer.apireader import APIReader, APIRecord

RECORDS_PER_PAGE = 10


class SRUReader(APIReader):
    sru_url: str = None
    sru_version: str = None
    query: str = None
    records: List[APIRecord]  # Move to superclass?
    fetching_exhausted: bool = False

    def transform_query(self, query: str) -> str:
        raise NotImplementedError('Should be implemented by subclass')

    def get_link(self, record: APIRecord) -> str:
        raise NotImplementedError('Should be implemented by subclass')

    def _convert_record(self, sruthirecord: dict) -> APIRecord:
        raise NotImplementedError('Should be implemented by subclass')

    def _perform_query(self, query: str, start_record: int) -> List[dict]:
        try:
            response = sruthi.searchretrieve(
                self.sru_url,
                self.transform_query(query),
                start_record=start_record,
                maximum_records=RECORDS_PER_PAGE,
                sru_version=self.sru_version
            )
        except (
            sruthi.errors.SruError, sruthi.errors.SruthiError
        ):
            raise

        self.number_of_results = response.count

        records: List[APIRecord] = []
        for sruthirecord in response[0:RECORDS_PER_PAGE]:
            records.append(self._convert_record(sruthirecord))

        return records

    def fetch(self, query: str) -> None:
        self.records = []
        self.query = query
        results = self._perform_query(query, 1)
        self.records.extend(results)
        self.number_fetched = len(self.records)
        if self.number_fetched == self.number_of_results:
            self.fetching_exhausted = True

    def fetch_next(self) -> None:
        if self.fetching_exhausted:
            return
        start_record = len(self.records) + 1
        results = self._perform_query(self.query, start_record)
        self.records.extend(results)
        self.number_fetched = len(self.records)
        if self.number_fetched == self.number_of_results:
            self.fetching_exhausted = True
