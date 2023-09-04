import requests
from typing import List, Dict, Optional

from edpop_explorer import Reader, Record, ReaderError

RECORDS_PER_PAGE = 10


class SBTIReader(Reader):
    api_url = 'https://data.cerl.org/sbti/_search'
    link_base_url = 'https://data.cerl.org/sbti/'
    fetching_exhausted: bool = False
    additional_params: Optional[Dict[str, str]] = None

    def _perform_query(self, start_record: int) -> List[Record]:
        try:
            response = requests.get(
                self.api_url,
                params={
                    'query': self.prepared_query,
                    'from': start_record,
                    'size': RECORDS_PER_PAGE,
                    'mode': 'default',
                    'sort': 'default'
                },
                headers={
                    'Accept': 'application/json'
                }
            ).json()
        except (
            requests.exceptions.RequestException
        ) as err:
            raise ReaderError('Error during server request: ' + str(err))

        # TODO: check for error responses
        try:
            if response['hits'] is None:
                self.number_of_results = 0
            else:
                self.number_of_results = response['hits']['value']
        except KeyError:
            raise ReaderError('Number of hits not given in server response')

        if 'rows' not in response:
            # There are no rows in the response, so stop here
            return []

        records: List[Record] = []
        for rawrecord in response['rows']:
            record = Record(from_reader=self.__class__)
            record.data = rawrecord
            record.identifier = rawrecord['id']
            record.link = self.link_base_url + record.identifier
            records.append(record)

        return records

    def transform_query(self, query) -> str:
        # No transformation needed
        return query

    def fetch(self) -> None:
        self.records = []
        if self.prepared_query is None:
            raise ReaderError('First call prepare_query')
        results = self._perform_query(0)
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
