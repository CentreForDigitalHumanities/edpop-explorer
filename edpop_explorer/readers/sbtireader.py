from rdflib import URIRef
import requests
from typing import List, Dict, Optional

from edpop_explorer import (
    Reader, Record, ReaderError, BiographicalRecord, Field, BIOGRAPHICAL
)


class SBTIReader(Reader):
    api_url = 'https://data.cerl.org/sbti/_search'
    api_by_id_base_url = 'https://data.cerl.org/sbti/'
    link_base_url = 'https://data.cerl.org/sbti/'
    fetching_exhausted: bool = False
    additional_params: Optional[Dict[str, str]] = None
    CATALOG_URIREF = URIRef(
        'https://edpop.hum.uu.nl/readers/sbti'
    )
    IRI_PREFIX = "https://edpop.hum.uu.nl/readers/sbti/"
    DEFAULT_RECORDS_PER_PAGE = 10
    READERTYPE = BIOGRAPHICAL
    SHORT_NAME = "Scottish Book Trade Index (SBTI)"
    DESCRIPTION = "An index of the names, trades and addresses of people "\
        "involved in printing in Scotland up to 1850"

    @classmethod
    def _get_name_field(cls, data: dict) -> Optional[Field]:
        field = None
        firstname = data.get("firstname", None)
        name = data.get("name", None)
        if firstname and name:
            field = Field(f"{firstname} {name}")
        elif name:
            field = Field(f"{name}")
        return field

    @classmethod
    def get_by_id(cls, identifier: str) -> BiographicalRecord:
        try:
            response = requests.get(
                cls.api_by_id_base_url + identifier,
                headers={
                    'Accept': 'application/json'
                },
            ).json()
        except requests.exceptions.JSONDecodeError:
            raise ReaderError(f"Item with id {identifier} does not exist.")
        except requests.exceptions.RequestException as err:
            raise ReaderError(f"Error during server request: {err}")
        return cls._convert_record(response)


    @classmethod
    def _convert_record(cls, rawrecord: dict) -> BiographicalRecord:
        record = BiographicalRecord(from_reader=cls)
        record.data = rawrecord
        record.identifier = rawrecord.get('id', None)
        if not record.identifier:
            record.identifier = rawrecord.get('_id', None)
        if record.identifier:
            record.link = cls.link_base_url + record.identifier

        # Add fields
        heading = rawrecord.get("heading", None)
        if heading:
            name_field = cls._get_name_field(heading[0])
            record.name = name_field
        variant_name = rawrecord.get("variantName", None)
        if isinstance(variant_name, list):
            record.variant_names = []
            for name in variant_name:
                field = cls._get_name_field(name)
                if field:
                    record.variant_names.append(field)
        place_of_activity = rawrecord.get("placeOfActitivty", None)  # sic.
        if isinstance(place_of_activity, list):
            record.places_of_activity = []
            for place in place_of_activity:
                name = place.get("name", None)
                if name:
                    field = Field(name)
                    record.places_of_activity.append(field)

        return record

    def _perform_query(self, start_record: int, maximum_records: Optional[int]) -> List[Record]:
        assert isinstance(self.prepared_query, str)
        if maximum_records is None:
            maximum_records = self.DEFAULT_RECORDS_PER_PAGE
        print(f'The query is: {self.prepared_query}')
        try:
            response = requests.get(
                self.api_url,
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
            record = self._convert_record(rawrecord)
            records.append(record)

        return records

    @classmethod
    def transform_query(cls, query) -> str:
        # No transformation needed
        return query

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

