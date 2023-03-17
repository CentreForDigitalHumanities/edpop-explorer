from typing import Dict, List, Optional
from dataclasses import dataclass, field as dataclass_field
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions

from edpop_explorer.apireader import APIReader, APIRecord, APIException


PREFIXES = {
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'schema': 'http://schema.org/',
    'owl': 'http://www.w3.org/2002/07/owl#',
}

PREFIXES_REVERSE_REPLACEMENT_TABLE = {
    PREFIXES[key]: (key + ':') for key in PREFIXES
}

PREFIX_DEFINITIONS = '\n'.join([
    f'prefix {key}: <{PREFIXES[key]}>' for key in PREFIXES
])

prepare_listing_query = (PREFIX_DEFINITIONS + """
select ?s ?name where
{{
  ?s ?p ?o .
  ?s {name_predicate} ?name .
  {filter}
  FILTER (regex(?o, "{query}","i"))
}}
order by ?s
""").format

prepare_lookup_query = """
prefix schema: <http://schema.org/>
select ?p ?o
{{
    <{identifier}> ?p ?o
}}
""".format


def replace_fqu_with_prefixed_uris(inputstring: str) -> str:
    '''Replace fully qualified URIs to prefixed URIs if they occur in
    the prefix table in the prefixes attribute'''
    for key in PREFIXES_REVERSE_REPLACEMENT_TABLE:
        inputstring = inputstring.replace(
            key, PREFIXES_REVERSE_REPLACEMENT_TABLE[key], 1
        )
    return inputstring


@dataclass
class SparqlRecord(APIRecord):
    name: str = None
    identifier: str = None
    sparql_endpoint: str = None
    fetched: bool = False
    fields: dict = dataclass_field(default_factory=dict)

    def fetch(self) -> None:
        if self.fetched:
            return
        wrapper = SPARQLWrapper(self.sparql_endpoint)
        wrapper.setReturnFormat(JSON)
        wrapper.setQuery(prepare_lookup_query(identifier=self.identifier))
        try:
            response = wrapper.queryAndConvert()
        except SPARQLExceptions.QueryBadFormed as err:
            raise APIException(
                'Malformed SPARQL query: {}'.format(err)
            )
        results = response['results']['bindings']
        for result in results:
            self.fields[result['p']['value']] = result['o']['value']
        self.fetched = True

    def get_title(self) -> str:
        return self.name

    def show_record(self) -> str:
        self.fetch()
        field_strings = []
        if self.link:
            field_strings.append('URL: ' + self.link)
        for field in self.fields:
            fieldstring = replace_fqu_with_prefixed_uris(field)
            field_strings.append(
                '{}: {}'.format(fieldstring, self.fields[field])
            )
        return '\n'.join(field_strings)

    def __repr__(self):
        return self.get_title()


class SparqlReader(APIReader):
    url: str = None
    filter: str = None
    wrapper: SPARQLWrapper
    records: List[SparqlRecord]
    name_predicate: str = None

    def __init__(self):
        self.wrapper = SPARQLWrapper(self.url)
        self.wrapper.setReturnFormat(JSON)

    def prepare_query(self, query: str):
        self.prepared_query = prepare_listing_query(
            name_predicate=self.name_predicate,
            filter=self.filter,
            query=query
        )

    def fetch(self) -> List[APIRecord]:
        if not self.prepared_query:
            raise APIException('First call prepare_query method')
        self.wrapper.setQuery(self.prepared_query)
        try:
            response = self.wrapper.queryAndConvert()
        except SPARQLExceptions.QueryBadFormed as err:
            raise APIException(
                'Malformed SPARQL query: {}'.format(err)
            )
        results = response['results']['bindings']
        self.records = []
        self.number_of_results = len(results)
        for result in results:
            record = SparqlRecord(
                identifier=result['s']['value'],
                sparql_endpoint=self.url,
                link=result['s']['value'],
                name=result['name']['value'],
            )
            self.records.append(record)
        self.number_fetched = self.number_of_results
