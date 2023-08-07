from dataclasses import dataclass
from typing import Optional, List
from rdflib import Graph, RDF, RDFS

from edpop_explorer import EDPOPREC


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
    number_of_results: Optional[int] = None
    number_fetched: Optional[int] = None
    records: List[APIRecord]
    prepared_query: Optional[str] = None
    READERTYPE: Optional[str] = None
    CATALOG_URIREF: Optional[str] = None

    BIOGRAPHICAL = 'biographical'
    BIBLIOGRAPHICAL = 'bibliographical'

    def prepare_query(self, query: str) -> None:
        raise NotImplementedError('Should be implemented by subclass')

    def set_query(self, query: str) -> None:
        '''Set an exact query'''
        self.prepared_query = query

    def fetch(self):
        raise NotImplementedError('Should be implemented by subclass')

    def fetch_next(self):
        raise NotImplementedError('Should be implemented by subclass')

    def create_rdf(self) -> None:
        '''Create an RDF graph for this reader and put it in the rdf
        attribute. Subclasses should override this and first call
        super.create_rdf().'''
        g = Graph()
        if not self.CATALOG_URIREF:
            raise APIException(
                'Cannot create graph because catalog IRI has not been set. '
                'This should have been done on class level.'
            )

        # Set reader class
        rdfclass = EDPOPREC.Catalog
        if self.READERTYPE == self.BIOGRAPHICAL:
            rdfclass = EDPOPREC.BiographicalCatalog
        elif self.READERTYPE == self.BIBLIOGRAPHICAL:
            rdfclass = EDPOPREC.BibliographicalCatalog
        g.add((self.CATALOG_URIREF, RDF.type, rdfclass))

        # Set namespace prefixes
        g.bind('rdf', RDF)
        g.bind('rdfs', RDFS)
        g.bind('edpoprec', EDPOPREC)

        self.graph = g


class APIException(Exception):
    pass
