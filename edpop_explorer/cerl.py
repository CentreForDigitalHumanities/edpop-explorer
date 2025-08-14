from abc import abstractmethod

import requests
from typing import List, Dict, Optional

from edpop_explorer import (
    Reader, Record, ReaderError, GetByIdBasedOnQueryMixin
)


class CERLReader(GetByIdBasedOnQueryMixin, Reader):
    """A generic reader class for the CERL databases on the ``data.cerl.org``
    platform.

    This is an abstract class -- to use, derive from this class, set the
    ``API_URL``, ``API_BY_ID_BASE_URL`` and ``LINK_BASE_URL`` constant
    attributes, and implement the ``_convert_record`` class method."""

    API_URL: str
    """The base URL of the search API, of the form ``https://data.cerl.org/<CATALOGUE>/_search``."""
    API_BY_ID_BASE_URL: str
    """The base URL of the API for retrieving single records, of the form ``https://data.cerl.org/<CATALOGUE>/``."""
    LINK_BASE_URL: str
    """The base URL for userfriendly representations of single records."""
    additional_params: Optional[Dict[str, str]] = None
    DEFAULT_RECORDS_PER_PAGE = 10

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return f"{identifier}"

    @classmethod
    @abstractmethod
    def _convert_record(cls, rawrecord: dict) -> Record:
        pass

    def _perform_query(self, start_record: int, maximum_records: Optional[int]) -> List[Record]:
        assert isinstance(self.prepared_query, str)
        if maximum_records is None:
            maximum_records = self.DEFAULT_RECORDS_PER_PAGE
        try:
            response = requests.get(
                self.API_URL,
                params={
                    'query': self.prepared_query,
                    'from': start_record,
                    'size': maximum_records,
                    'mode': 'default',
                    'sort': 'default'
                },
                headers={
                    'Accept': 'application/json'
                }
            ).json()
        except requests.exceptions.RequestException as err:
            raise ReaderError('Error during server request: ' + str(err))

        # TODO: check for error responses
        try:
            if response['hits'] is None:
                self.number_of_results = 0
            else:
                self.number_of_results = response['hits']['value']
        except KeyError:
            raise ReaderError('Number of hits not given in server response')

        return [self._convert_record(x) for x in response['rows']] if 'rows' in response else []

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

    def fetch_range(self, range_to_fetch: range) -> range:
        if self.prepared_query is None:
            raise ReaderError('First call prepare_query')
        start_record = range_to_fetch.start
        number_to_fetch = range_to_fetch.stop - start_record
        results = self._perform_query(start_record, number_to_fetch)
        for i, result in enumerate(results):
            self.records[i + range_to_fetch.start] = result
        return range(start_record, start_record + len(results))

