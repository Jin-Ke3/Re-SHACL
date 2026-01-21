"""RDFS Entailment Engine

This module implements RDFS (RDF Schema) entailment rules as defined in
the W3C RDF Semantics specification.

Supported RDFS rules:
- subPropertyOf: Transitive closure of property hierarchies
- subClassOf: Transitive closure of class hierarchies
- Class inheritance: Type propagation through class hierarchy (rdf:type)
- domain: Type inference for subjects of properties with domain constraints
- range: Type inference for objects of properties with range constraints
"""

import logging
from rdflib import RDF, RDFS, Graph
from typing import Set, Tuple
from pre_shacl.entailment_base import run_fixpoint_entailment

logger = logging.getLogger(__name__)


def apply_rdfs_rules(data_graph: Graph, inferred_triples: Set[Tuple]) -> None:
    """
    Apply all RDFS entailment rules to the data graph.
    
    Args:
        data_graph: The RDF graph being entailed
        inferred_triples: Set to collect newly inferred triples
    """
    # Transitive properties
    for sub_property_name, _, super_property_name in data_graph.triples((None, RDFS.subPropertyOf, None)):
        for _, _, super_property in data_graph.triples((super_property_name, RDFS.subPropertyOf, None)):
            inferred_triples.add((sub_property_name, RDFS.subPropertyOf, super_property))

    # Property hierarchy: if P subPropertyOf Q and (x P y), then (x Q y)
    for sub_property, _, super_property in data_graph.triples((None, RDFS.subPropertyOf, None)):
        for subject, _, obj in data_graph.triples((None, sub_property, None)):
            inferred_triples.add((subject, super_property, obj))

    for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
        # Transitive classes
        for _, _, super_class in data_graph.triples((superclass_name, RDFS.subClassOf, None)):
            inferred_triples.add((subclass_name, RDFS.subClassOf, super_class))
        # Class inheritance
        for entity_name, _, _ in data_graph.triples((None, RDF.type, subclass_name)):
            inferred_triples.add((entity_name, RDF.type, superclass_name))

    # RDFS domain
    for property_name, _, class_name in data_graph.triples((None, RDFS.domain, None)):
        for entity_name, _, _ in data_graph.triples((None, property_name, None)):
            inferred_triples.add((entity_name, RDF.type, class_name))

    # RDFS range
    for property_name, _, class_name in data_graph.triples((None, RDFS.range, None)):
        for _, _, entity_name in data_graph.triples((None, property_name, None)):
            inferred_triples.add((entity_name, RDF.type, class_name))


def entail(data_graph: Graph, max_iterations: int = 1000) -> None:
    """
    Apply RDFS entailment rules to an RDF graph in place.
    
    This function iteratively applies RDFS inference rules until a fixpoint
    is reached (no new triples can be inferred). The graph is modified in place.
    
    Args:
        data_graph: An rdflib Graph to be entailed. Modified in place.
        max_iterations: Maximum number of iterations to prevent infinite loops (default: 1000).
    
    Raises:
        RuntimeWarning: If max_iterations is reached before fixpoint.
    
    Example:
        >>> from rdflib import Graph
        >>> g = Graph()
        >>> g.parse("data.ttl")
        >>> entail(g)
        >>> print(f"Inferred {len(g)} total triples")
    """
    run_fixpoint_entailment(data_graph, apply_rdfs_rules, max_iterations, "RDFS")
