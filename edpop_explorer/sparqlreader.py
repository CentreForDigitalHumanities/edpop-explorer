from typing import Optional, Type
from rdflib import Graph
import json
from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON as JSONFormat
from abc import abstractmethod

from edpop_explorer import (
    Reader, Record, BibliographicalRecord, ReaderError, RecordError,
    LazyRecordMixin
)

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


class RDFRecordMixin(LazyRecordMixin):
    '''Mixin that adds lazy RDF fetching functionality to a Record.'''
    identifier: Optional[str] = None
    fetched: bool = False
    data: Optional[dict] = None
    original_graph: Optional[Graph] = None
    from_reader: Type["SparqlReader"]

    def fetch(self) -> None:
        # TODO: at the moment this mixin only supports fetching RDF data
        # if the IRI in the identifier attribute is available via HTTP
        # as data that rdflib can process. We might need to support
        # IRIs that can only be accessed via an endpoint as well.
        if not self.identifier:
            raise RecordError(
                'identifier (subject IRI) has not been set'
            )
        if self.fetched:
            return
        try:
            self.original_graph = Graph()
            self.original_graph.parse(self.identifier)
        except Exception as err:
            # URLLib does not catch errors of underlying libraries, hence
            # the use of except Exception
            raise RecordError(
                f"Error while loading record's contents from IRI "
                f"{self.identifier}: {err}"
            )
        # Convert to JSON for raw data attribute
        self.data = json.loads(
            self.original_graph.serialize(format="json-ld")
        )
        # Call Reader's data conversion method to fill the record's Fields
        assert isinstance(self, Record)
        self.from_reader._convert_record(self.original_graph, self)

        self.fetched = True


class BibliographicalRDFRecord(RDFRecordMixin, BibliographicalRecord):
    pass


class SparqlReader(Reader):
    endpoint: str
    name_predicate: str
    filter: Optional[str] = None

    def transform_query(self, query: str):
        return prepare_listing_query(
            name_predicate=self.name_predicate,
            filter=self.filter,
            query=query
        )

    def fetch(self):
        if not self.prepared_query:
            raise ReaderError('First call prepare_query method')
        wrapper = SPARQLWrapper(self.endpoint)
        wrapper.setReturnFormat(JSONFormat)
        wrapper.setQuery(self.prepared_query)
        try:
            response = wrapper.queryAndConvert()
        except SPARQLExceptions.QueryBadFormed as err:
            raise ReaderError(
                'Malformed SPARQL query: {}'.format(err)
            )
        assert isinstance(response, dict)
        results = response['results']['bindings']
        self.records = []
        self.number_of_results = len(results)
        for result in results:
            iri = result['s']['value']
            name = result['name']['value']
            self.records.append(self._create_lazy_record(iri, name))
        self.number_fetched = self.number_of_results

    def fetch_next(self):
        pass

    @classmethod
    @abstractmethod
    def _convert_record(cls, graph: Graph, record: Record) -> None:
        '''Convert data from an RDF graph to Fields in a Record. The 
        Record is changed in-place.'''
        pass

    @classmethod
    @abstractmethod
    def _create_lazy_record(cls, iri: str, name: str) -> Record:
        """Create a Record/LazyRecordMixin record object.

        This is the lazy record that is created after running the SPARQL
        query. The record initially only gets the IRI attached as well
        as a single property (``name``, used for quick identification), while
        the rest will be loaded when Record.fetch() is called.
        """
        pass
