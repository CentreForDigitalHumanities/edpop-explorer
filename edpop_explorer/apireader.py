from dataclasses import dataclass
from typing import Optional, List


@dataclass
class APIRecord:
    # A user-friendly link where the user can find the record
    link: Optional[str] = None

    def get_title(self) -> str:
        '''Convenience method to retrieve the title of a record in a standard
        way'''
        raise NotImplementedError('Should be implemented by subclass')

    def show_record(self) -> str:
        raise NotImplementedError('Should be implemented by subclass')


class APIReader:
    number_of_results: int = None
    number_fetched: int = None
    records: List[APIRecord]

    def fetch(self, query: str):
        raise NotImplementedError('Should be implemented by subclass')

    def fetch_next(self):
        raise NotImplementedError('Should be implemented by subclass')


class APIException(Exception):
    pass
