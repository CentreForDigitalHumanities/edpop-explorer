import sruthi
from typing import List, Dict, Optional

from edpop_explorer.apireader import APIReader, APIRecord, APIException

RECORDS_PER_PAGE = 10


class SRUReader(APIReader):
    sru_url: str = None
    sru_version: str = None
    query: str = None
    records: List[APIRecord]  # Move to superclass?
    fetching_exhausted: bool = False
    additional_params: Optional[Dict[str, str]] = None

    def transform_query(self, query: str) -> str:
        raise NotImplementedError('Should be implemented by subclass')

    def _convert_record(self, sruthirecord: dict) -> APIRecord:
        raise NotImplementedError('Should be implemented by subclass')

    def _perform_query(self, start_record: int) -> List[dict]:
        try:
            response = sruthi.searchretrieve(
                self.sru_url,
                self.prepared_query,
                start_record=start_record,
                maximum_records=RECORDS_PER_PAGE,
                sru_version=self.sru_version,
                additional_params=self.additional_params
            )
        except (
            sruthi.errors.SruError
        ) as err:
            raise APIException('Server returned error: ' + str(err))

        self.number_of_results = response.count

        records: List[APIRecord] = []
        for sruthirecord in response[0:RECORDS_PER_PAGE]:
            records.append(self._convert_record(sruthirecord))

        return records

    def prepare_query(self, query) -> None:
        self.prepared_query = self.transform_query(query)

    def fetch(self) -> None:
        self.records = []
        if self.prepared_query is None:
            raise APIException('First call prepare_query')
        results = self._perform_query(1)
        self.records.extend(results)
        self.number_fetched = len(self.records)
        if self.number_fetched == self.number_of_results:
            self.fetching_exhausted = True

    def fetch_next(self) -> None:
        # TODO: can be merged with fetch method
        if self.fetching_exhausted:
            return
        start_record = len(self.records) + 1
        results = self._perform_query(start_record)
        self.records.extend(results)
        self.number_fetched = len(self.records)
        if self.number_fetched == self.number_of_results:
            self.fetching_exhausted = True
