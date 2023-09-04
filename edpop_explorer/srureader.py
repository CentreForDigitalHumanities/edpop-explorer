import sruthi
import requests
from abc import abstractmethod
from typing import List, Optional

from edpop_explorer import Reader, Record, ReaderError

RECORDS_PER_PAGE = 10


class SRUReader(Reader):
    '''Subclass of ``Reader`` that adds basic SRU functionality
    using the ``sruthi`` library.

    This class is still abstract and subclasses should implement
    the ``transform_query()`` and ``_convert_record()`` methods,
    and set the attributes ``sru_url`` and ``sru_version``.

    .. automethod:: _convert_record'''
    sru_url: str
    '''URL of the SRU API.'''
    sru_version: str
    '''Version of the SRU protocol. Can be '1.1' or '1.2'.'''
    query: Optional[str] = None
    records: List[Record]  # Move to superclass?
    session: requests.Session
    '''The ``Session`` object of the ``requests`` library.'''

    def __init__(self):
        # Set a session to allow reuse of HTTP sessions and to set additional
        # parameters and settings, which some SRU APIs require -
        # see https://github.com/metaodi/sruthi#custom-parameters-and-settings
        self.session = requests.Session()

    @abstractmethod
    def transform_query(self, query: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def _convert_record(cls, sruthirecord: dict) -> Record:
        '''Convert the output of ``sruthi`` into an instance of
        (a subclass of) ``Record``.'''
        pass

    def _perform_query(self, start_record: int) -> List[Record]:
        try:
            response = sruthi.searchretrieve(
                self.sru_url,
                self.prepared_query,
                start_record=start_record,
                maximum_records=RECORDS_PER_PAGE,
                sru_version=self.sru_version,
                session=self.session
            )
        except (
            sruthi.errors.SruError
        ) as err:
            raise ReaderError('Server returned error: ' + str(err))

        self.number_of_results = response.count

        records: List[Record] = []
        for sruthirecord in response[0:RECORDS_PER_PAGE]:
            records.append(self._convert_record(sruthirecord))

        return records

    def prepare_query(self, query) -> None:
        self.prepared_query = self.transform_query(query)

    def fetch(self) -> None:
        self.records = []
        if self.prepared_query is None:
            raise ReaderError('First call prepare_query')
        results = self._perform_query(1)
        self.records.extend(results)
        self.number_fetched = len(self.records)

    def fetch_next(self) -> None:
        # TODO: can be merged with fetch method
        if self.number_of_results == self.number_fetched:
            return
        start_record = len(self.records) + 1
        results = self._perform_query(start_record)
        self.records.extend(results)
        self.number_fetched = len(self.records)
