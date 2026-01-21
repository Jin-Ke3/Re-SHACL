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

logger = logging.getLogger(__name__)


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
    changes = True
    inferred_triples = set()
    num_inferred_triples = 0
    iteration = 0
    
    while changes and iteration < max_iterations:

        # Transitive properties
        for sub_property_name, _, super_property_name in data_graph.triples((None, RDFS.subPropertyOf, None)):
            for _, _, super_property in data_graph.triples((super_property_name, RDFS.subPropertyOf, None)):
                inferred_triples.add((sub_property_name, RDFS.subPropertyOf, super_property))

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

        # Track if there are any changes
        changes = len(inferred_triples) != num_inferred_triples
        num_inferred_triples = len(inferred_triples)

        for s, p, o in inferred_triples:
            data_graph.add((s, p, o))
        
        iteration += 1
    
    if iteration >= max_iterations:
        logger.warning(f"RDFS entailment reached max_iterations ({max_iterations}). "
                      f"Fixpoint may not have been reached.")
