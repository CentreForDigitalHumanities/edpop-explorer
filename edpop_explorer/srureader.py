import sruthi
import requests
from abc import abstractmethod
from typing import List, Optional

from edpop_explorer import Reader, Record, ReaderError
from edpop_explorer.reader import GetByIdBasedOnQueryMixin


class SRUReader(GetByIdBasedOnQueryMixin, Reader):
    '''Subclass of ``Reader`` that adds basic SRU functionality
    using the ``sruthi`` library.

    This class is still abstract and subclasses should implement
    the ``transform_query()`` and ``_convert_record()`` methods
    and set the attributes ``sru_url`` and ``sru_version``.
    
    The ``_prepare_get_by_id_query()`` method by default returns
    the transformed version of the identifier as a query, which
    normally works, but this may be optimised by overriding it.

    .. automethod:: _convert_record'''
    sru_url: str
    '''URL of the SRU API.'''
    sru_version: str
    '''Version of the SRU protocol. Can be '1.1' or '1.2'.'''
    query: Optional[str] = None
    session: requests.Session
    '''The ``Session`` object of the ``requests`` library.'''

    def __init__(self):
        # Set a session to allow reuse of HTTP sessions and to set additional
        # parameters and settings, which some SRU APIs require -
        # see https://github.com/metaodi/sruthi#custom-parameters-and-settings
        super().__init__()
        self.session = requests.Session()

    @classmethod
    @abstractmethod
    def transform_query(cls, query: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def _convert_record(cls, sruthirecord: dict) -> Record:
        '''Convert the output of ``sruthi`` into an instance of
        (a subclass of) ``Record``.'''
        pass

    @classmethod
    def _prepare_get_by_id_query(cls, identifier: str) -> str:
        return cls.transform_query(identifier)

    def _perform_query(self, start_record: int, maximum_records: Optional[int]) -> List[Record]:
        if maximum_records is None:
            maximum_records = self.DEFAULT_RECORDS_PER_PAGE
        try:
            response = sruthi.searchretrieve(
                self.sru_url,
                self.prepared_query,
                start_record=start_record,
                maximum_records=maximum_records,
                sru_version=self.sru_version,
                session=self.session
            )
        except (
            sruthi.errors.SruError
        ) as err:
            raise ReaderError('Server returned error: ' + str(err))

        self.number_of_results = response.count

        records: List[Record] = []
        for sruthirecord in response[0:maximum_records]:
            records.append(self._convert_record(sruthirecord))

        return records

    def prepare_query(self, query) -> None:
        self.prepared_query = self.transform_query(query)

    def fetch_range(self, range_to_fetch: range) -> range:
        # SRU provides paged retrieve using a start record (that starts at
        # 1, while we start at 0) and a maximum number of results.
        if self.fetching_exhausted:
            return range(0, 0)
        if self.prepared_query is None:
            raise ReaderError('First call prepare_query')
        start_number = range_to_fetch.start
        start_number_sru = start_number + 1  # SRU starts at 1
        records_to_fetch = range_to_fetch.stop - range_to_fetch.start
        results = self._perform_query(start_number_sru, records_to_fetch)
        for i, result in enumerate(results):
            self.records[i + start_number] = result
        return range(start_number, start_number + len(results))
