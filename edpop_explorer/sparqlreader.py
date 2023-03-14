from typing import Dict, List, Optional
from dataclasses import dataclass, field as dataclass_field
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions

from edpop_explorer.apireader import APIReader, APIRecord, APIException


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
        wrapper.setQuery(f"""
prefix schema: <http://schema.org/>
select ?p ?o
{{
    <{self.identifier}> ?p ?o
}}
        """)
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
            field_strings.append('{}: {}'.format(field, self.fields[field]))
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
        self.prepared_query = f"""
prefix schema: <http://schema.org/>
select ?s ?name where
{{
  ?s ?p ?o .
  ?s {self.name_predicate} ?name .
  {self.filter}
  FILTER (regex(?o, "{query}","i"))
}}
order by ?s
        """

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
