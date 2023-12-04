from dataclasses import dataclass
from typing import List, Union

from edpop_explorer import PreparedQuery


@dataclass
class SQLPreparedQuery(PreparedQuery):
    where_statement: str
    arguments: List[Union[str, int]]
