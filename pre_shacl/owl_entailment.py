"""OWL Entailment Engine

This module implements OWL (Web Ontology Language) entailment rules for RDF graphs.

Supported OWL rules:
- sameAs: Symmetric, transitive, and property copying
- equivalentProperty: Conversion to subPropertyOf relations
- subPropertyOf: Transitive closure and equivalence detection
- domain: Type inference and inheritance
- range: Type inference and inheritance
- subClassOf: Transitive closure and equivalence detection
- equivalentClass: Conversion to subClassOf relations
- Class inheritance: Type propagation through class hierarchy
"""

import logging
from typing import Set, Tuple
from rdflib import RDF, RDFS, OWL, Graph
from .entailment_base import run_fixpoint_entailment

logger = logging.getLogger(__name__)


def apply_owl_rules(data_graph: Graph, inferred_triples: Set[Tuple]) -> None:
    """
    Apply OWL entailment rules to discover new triples.
    
    This function implements the core OWL reasoning rules. It examines the current
    state of the data graph and adds newly inferred triples to the inferred_triples set.
    
    Args:
        data_graph: The RDF graph to analyze.
        inferred_triples: Set to accumulate newly inferred triples.
    """
    for s, _, o in data_graph.triples((None, OWL.sameAs, None)):
        # Symmetric sameAs
        if not o == s:
            inferred_triples.add((o, OWL.sameAs, s))

        # Transitive sameAs
        for _, _, super_o in data_graph.triples((o, OWL.sameAs, None)):
            inferred_triples.add((s, OWL.sameAs, super_o))
        # SameAs copy subject triples
        for _, pred, obj in data_graph.triples((s, None, None)):
            inferred_triples.add((o, pred, obj))
        # SameAs copy predicate triples
        for subj, _, obj in data_graph.triples((None, s, None)):
            inferred_triples.add((subj, o, obj))
        # SameAs copy object triples
        for subj, pred, _ in data_graph.triples((None, None, s)):
            inferred_triples.add((subj, pred, o))

    # Equivalence relation to sub property conversion
    for s, _, o in data_graph.triples((None, OWL.equivalentProperty, None)):
        inferred_triples.add((s, RDFS.subPropertyOf, o))
        inferred_triples.add((o, RDFS.subPropertyOf, s))

    for sub_property_name, _, super_property_name in data_graph.triples((None, RDFS.subPropertyOf, None)):
        for _, _, super_property in data_graph.triples((super_property_name, RDFS.subPropertyOf, None)):
            # Equivalent property relation
            if super_property == sub_property_name:
                inferred_triples.add((sub_property_name, OWL.equivalentProperty, super_property_name))
            # Transitive property relation
            else:
                inferred_triples.add((sub_property_name, RDFS.subPropertyOf, super_property))

    # RDFS domain
    for property_name, _, class_name in data_graph.triples((None, RDFS.domain, None)):
        # Type entailment for entity
        for entity_name, _, _ in data_graph.triples((None, property_name, None)):
            inferred_triples.add((entity_name, RDF.type, class_name))

        # Superclass entailment for domain expression
        for _, _, superclass_name in data_graph.triples((class_name, RDFS.subClassOf, None)):
            inferred_triples.add((property_name, RDFS.domain, superclass_name))

        # Super property entailment for domain expression
        for _, _, super_property_name in data_graph.triples((property_name, RDFS.subPropertyOf, None)):
            inferred_triples.add((super_property_name, RDFS.domain, class_name))

    # # RDFS range
    for property_name, _, class_name in data_graph.triples((None, RDFS.range, None)):
        # Type entailment for entity
        for _, _, entity_name in data_graph.triples((None, property_name, None)):
            inferred_triples.add((entity_name, RDF.type, class_name))

        # Superclass entailment for range expression
        for _, _, superclass_name in data_graph.triples((class_name, RDFS.subClassOf, None)):
            inferred_triples.add((property_name, RDFS.range, superclass_name))

        # Super property entailment for range expression
        for _, _, super_property_name in data_graph.triples((property_name, RDFS.subPropertyOf, None)):
            inferred_triples.add((super_property_name, RDFS.range, class_name))

    for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
        for _, _, super_class in data_graph.triples((superclass_name, RDFS.subClassOf, None)):
            # Transitive classes
            inferred_triples.add((subclass_name, RDFS.subClassOf, super_class))

            # Equivalent class relation
            if super_class == subclass_name:
                inferred_triples.add((subclass_name, OWL.equivalentClass, superclass_name))

    # Class inheritance
    for subclass_name, _, superclass_name in data_graph.triples((None, RDFS.subClassOf, None)):
        for entity_name, _, _ in data_graph.triples((None, RDF.type, subclass_name)):
            inferred_triples.add((entity_name, RDF.type, superclass_name))

    # Equivalence relation to subclass conversion
    for s, p, o in data_graph.triples((None, OWL.equivalentClass, None)):
        inferred_triples.add((s, RDFS.subClassOf, o))
        inferred_triples.add((o, RDFS.subClassOf, s))


def entail(data_graph: Graph, max_iterations: int = 1000) -> None:
    """
    Apply OWL entailment rules to an RDF graph in place.
    
    This function iteratively applies OWL inference rules until a fixpoint
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
    run_fixpoint_entailment(data_graph, apply_owl_rules, max_iterations, "OWL")