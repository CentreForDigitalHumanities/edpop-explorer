import requests
from dataclasses import dataclass, field as dataclass_field
from typing import List, Dict, Optional
import json

from edpop_explorer.apireader import APIReader, APIRecord, APIException

RECORDS_PER_PAGE = 10


@dataclass
class SBTIRecord(APIRecord):
    data: Optional[Dict] = dataclass_field(default_factory=dict)
    identifier: Optional[str] = None

    def show_record(self) -> str:
        contents = json.dumps(self.data, indent=2)
        if self.link:
            contents = self.link + '\n' + contents
        return contents

    def get_title(self) -> str:
        try:
            heading = self.data['heading'][0]
            name = '{} {} ({})'.format(
                heading['firstname'],
                heading['name'],
                heading['headingOf'][0]
            )
        except (KeyError, IndexError, TypeError):
            name = '(unknown title)'
        return name


class SBTIReader(APIReader):
    api_url = 'https://data.cerl.org/sbti/_search'
    link_base_url = 'https://data.cerl.org/sbti/'
    query: str = None
    records: List[APIRecord]  # Move to superclass?
    fetching_exhausted: bool = False
    additional_params: Optional[Dict[str, str]] = None

    def _perform_query(self, start_record: int) -> List[dict]:
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
            raise APIException('Error during server request: ' + str(err))

        # TODO: check for error responses
        try:
            if response['hits'] is None:
                self.number_of_results = 0
            else:
                self.number_of_results = response['hits']['value']
        except KeyError:
            raise APIException('Number of hits not given in server response')

        if 'rows' not in response:
            # There are no rows in the response, so stop here
            return []

        records: List[APIRecord] = []
        for rawrecord in response['rows']:
            record = SBTIRecord()
            record.data = rawrecord
            record.identifier = rawrecord['id']
            record.link = self.link_base_url + record.identifier
            records.append(record)

        return records

    def prepare_query(self, query) -> None:
        # No transformation needed
        self.prepared_query = query

    def fetch(self) -> None:
        self.records = []
        if self.prepared_query is None:
            raise APIException('First call prepare_query')
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
