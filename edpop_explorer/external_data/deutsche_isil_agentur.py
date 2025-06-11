from urllib.error import HTTPError

from rdflib import Graph, URIRef, Namespace

DBP = Namespace("http://dbpedia.org/property/")

_code_to_name = {}


def get_isil_uri(code: str) -> str:
    return f"https://ld.zdb-services.de/resource/organisations/{code}"


def get_isil_name_by_code(code: str) -> str | None:
    """Get the short name of an institution from the data of Deutsche ISIL
    Agentur. Return None if the code is not found."""
    if code in _code_to_name:
        return _code_to_name[code]
    uri = get_isil_uri(code)
    graph = Graph()
    try:
        graph.parse(uri)
    except HTTPError:
        return None
    value = graph.value(URIRef(uri), DBP.shortName)
    if not value:
        return None
    name = str(value)
    _code_to_name[code] = name
    return name
