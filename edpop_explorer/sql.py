from dataclasses import dataclass
from typing import List, Union

from edpop_explorer import BasePreparedQuery


@dataclass
class SQLPreparedQuery(BasePreparedQuery):
    where_statement: str
    arguments: List[Union[str, int]]
