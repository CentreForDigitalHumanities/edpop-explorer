"""RDF-related common functionality."""

from rdflib.namespace import Namespace
from rdflib import Graph, RDF, RDFS

EDPOPREC = Namespace('https://dhstatic.hum.uu.nl/edpop-records/latest/')
"""EDPOP Record Ontology"""

RELATORS = Namespace('http://id.loc.gov/vocabulary/relators/')
"""Library of Congress relators. See: https://id.loc.gov/vocabulary/relators.html"""


def bind_common_namespaces(graph: Graph) -> None:
    """Bind the RDF namespaces that are in use across this package to the
    specified graph.

    These are: RDF, RDFS, EDPOPREC."""

    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("edpoprec", EDPOPREC)

