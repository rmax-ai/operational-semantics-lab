"""RDF namespace definitions for the Operational Semantics ontology."""

import rdflib

# Core namespace
OS_NAMESPACE = "http://rmax.ai/ontology/operational-semantics/"
OS = rdflib.Namespace(OS_NAMESPACE)

# Standard prefixes
RDF = rdflib.RDF
RDFS = rdflib.RDFS
OWL = rdflib.OWL
XSD = rdflib.XSD
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")

# Convenience mapping for serialization
PREFIX_MAP = {
    "os": OS,
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    "xsd": XSD,
    "sh": SH,
    "dcterms": DCTERMS,
}
