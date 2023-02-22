from dataclasses import dataclass
from typing import Optional, List


@dataclass
class APIRecord:
    url: Optional[str] = None

    def get_title(self) -> str:
        '''Convenience method to retrieve the title of a record in a standard
        way'''
        raise NotImplementedError('Should be implemented by subclass')

    def show_record(self) -> str:
        raise NotImplementedError('Should be implemented by subclass')


class APIReader:
    number_of_results: int = None
    records: List[APIRecord]

    def fetch(self, query: str) -> List[APIRecord]:
        raise NotImplementedError('Should be implemented by subclass')

    def fetch_next(self) -> List[APIRecord]:
        raise NotImplementedError('Should be implemented by subclass')
