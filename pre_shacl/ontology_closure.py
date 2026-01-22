"""
Ontology closure computation for property hierarchies.

This module provides functions to compute transitive closure of rdfs:subPropertyOf
relationships in ontologies, with support for owl:equivalentProperty.
"""

import hashlib
import logging
from typing import Dict, Set, Optional
from rdflib import Graph, URIRef, RDFS, OWL

logger = logging.getLogger(__name__)

# Cache for closure computation
_closure_cache: Dict[str, Dict[URIRef, Set[URIRef]]] = {}


def compute_subproperty_closure(
    ontology_graph: Graph,
    ontology_id: Optional[str] = None
) -> Dict[URIRef, Set[URIRef]]:
    """
    Precompute transitive closure of rdfs:subPropertyOf.
    
    Returns:
        subprops[p] = {q | q rdfs:subPropertyOf* p}
        (All sub-properties of p, including transitive)
    
    Implementation:
    1. Build equivalence relation E where p~q iff (p owl:equivalentProperty q)
    2. For each (p owl:equivalentProperty q): add both (p rdfs:subPropertyOf q) 
       and (q rdfs:subPropertyOf p) edges to an INTERNAL adjacency structure
    3. Compute transitive closure using fixpoint iteration (graph reachability)
    4. Cache result by ontology hash for reuse
    
    IMPORTANT: The ontology graph is NOT mutated. We build a derived internal
    adjacency structure (dict of sets) with bidirectional edges for equivalence.
    
    Algorithm: Fixpoint propagation until no new edges added.
    Complexity: O(n*e) where n=nodes, e=edges; typically fast for sparse ontologies.
    
    Args:
        ontology_graph: The ontology graph (not modified)
        ontology_id: Optional stable ID for caching (e.g., filepath + mtime)
    
    Returns:
        Dictionary mapping each property to its set of sub-properties (including transitive)
    """
    # Compute stable hash of ontology for caching
    if ontology_id is None:
        # Hash sorted triples (stable for same content)
        triples_sorted = sorted((str(s), str(p), str(o)) for s, p, o in ontology_graph)
        triple_str = '\n'.join(f"{s} {p} {o}" for s, p, o in triples_sorted)
        ont_hash = hashlib.sha256(triple_str.encode()).hexdigest()
    else:
        # Use caller-provided ID
        ont_hash = ontology_id
    
    # Check cache
    if ont_hash in _closure_cache:
        logger.debug(f"Using cached closure for ontology {ont_hash[:8]}")
        return _closure_cache[ont_hash]
    
    logger.info(f"Computing subproperty closure for ontology {ont_hash[:8]}")
    
    # Compute closure
    closure = _compute_closure_impl(ontology_graph)
    
    # Cache result
    _closure_cache[ont_hash] = closure
    logger.info(f"Cached closure for ontology {ont_hash[:8]} with {len(closure)} properties")
    
    return closure


def _compute_closure_impl(ontology_graph: Graph) -> Dict[URIRef, Set[URIRef]]:
    """
    Internal implementation of closure computation.
    
    Args:
        ontology_graph: The ontology graph
    
    Returns:
        Dictionary mapping each property to its set of sub-properties
    """
    # Build internal adjacency structure: subprop_edges[parent] = {children}
    # This represents the "q is a subproperty of p" relationship
    subprop_edges: Dict[URIRef, Set[URIRef]] = {}
    all_properties: Set[URIRef] = set()
    
    # Step 1: Add direct rdfs:subPropertyOf edges
    for sub, pred, sup in ontology_graph.triples((None, RDFS.subPropertyOf, None)):
        if isinstance(sub, URIRef) and isinstance(sup, URIRef):
            all_properties.add(sub)
            all_properties.add(sup)
            
            if sup not in subprop_edges:
                subprop_edges[sup] = set()
            subprop_edges[sup].add(sub)
    
    # Step 2: Add bidirectional edges for owl:equivalentProperty
    # For each (p owl:equivalentProperty q), add both (p subPropertyOf q) and (q subPropertyOf p)
    for p, pred, q in ontology_graph.triples((None, OWL.equivalentProperty, None)):
        if isinstance(p, URIRef) and isinstance(q, URIRef):
            all_properties.add(p)
            all_properties.add(q)
            
            # Add p as subproperty of q
            if q not in subprop_edges:
                subprop_edges[q] = set()
            subprop_edges[q].add(p)
            
            # Add q as subproperty of p (bidirectional)
            if p not in subprop_edges:
                subprop_edges[p] = set()
            subprop_edges[p].add(q)
    
    # Step 3: Compute transitive closure using fixpoint iteration
    # closure[p] will contain all properties that are sub-properties of p (transitive)
    closure: Dict[URIRef, Set[URIRef]] = {}
    
    # Initialize: each property has its direct children
    for prop in all_properties:
        closure[prop] = subprop_edges.get(prop, set()).copy()
    
    # Fixpoint iteration: propagate until no changes
    changed = True
    iteration = 0
    while changed:
        changed = False
        iteration += 1
        
        for prop in all_properties:
            # For each direct child of prop, add all of child's children
            current_children = closure[prop].copy()
            for child in current_children:
                if child in closure:
                    # Add all grandchildren
                    for grandchild in closure[child]:
                        if grandchild not in closure[prop]:
                            closure[prop].add(grandchild)
                            changed = True
    
    logger.debug(f"Closure computation completed in {iteration} iterations")
    
    return closure


def clear_closure_cache() -> None:
    """
    Clear the closure cache.
    
    Useful for testing or when ontology changes.
    """
    global _closure_cache
    _closure_cache.clear()
    logger.debug("Cleared closure cache")
