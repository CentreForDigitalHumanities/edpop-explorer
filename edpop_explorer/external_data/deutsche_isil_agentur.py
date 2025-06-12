from functools import cache
from typing import Optional
from urllib.error import HTTPError

from rdflib import Graph, URIRef, Namespace

DBP = Namespace("http://dbpedia.org/property/")


def get_isil_uri(code: str) -> str:
    return f"https://ld.zdb-services.de/resource/organisations/{code}"


@cache
def get_isil_name_by_code(code: str) -> Optional[str]:
    """Get the short name of an institution from the data of Deutsche ISIL
    Agentur. Return ``None`` if the code is not found. May raise
    ``HTTPError`` in case of a network error."""
    uri = get_isil_uri(code)
    graph = Graph()
    graph.parse(uri)
    value = graph.value(URIRef(uri), DBP.shortName)
    if not value:
        return None
    name = str(value)
    return name
