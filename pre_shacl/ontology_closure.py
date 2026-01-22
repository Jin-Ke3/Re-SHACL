"""
Ontology closure computation for property hierarchies.

This module provides functions to compute transitive closure of rdfs:subPropertyOf
relationships in ontologies, with support for owl:equivalentProperty.
"""

import hashlib
import logging
from typing import Dict, Set, Optional, Tuple
from rdflib import Graph, URIRef, RDFS, OWL

logger = logging.getLogger(__name__)

# Cache for closure computation - now stores tuple
_closure_cache: Dict[str, Tuple[Dict[URIRef, Set[URIRef]], Dict[URIRef, Set[URIRef]]]] = {}


def compute_subproperty_closure(
    ontology_graph: Graph,
    ontology_id: Optional[str] = None,
    inference: str = "rdfs"
) -> Tuple[Dict[URIRef, Set[URIRef]], Dict[URIRef, Set[URIRef]]]:
    """
    Precompute transitive closure of rdfs:subPropertyOf and track equivalences.
    
    Returns:
        Tuple of (subprop_closure, equivalent_props) where:
        - subprop_closure[p] = {q | q rdfs:subPropertyOf* p} (transitive, includes equivalences if OWL)
        - equivalent_props[p] = {q | p owl:equivalentProperty q OR p owl:sameAs q} (direct only, OWL only)
    
    Implementation:
    1. Collect rdfs:subPropertyOf edges
    2. Collect owl:equivalentProperty and owl:sameAs ONLY if inference is OWL-based (store separately)
    3. Add equivalences as bidirectional subPropertyOf for closure computation (OWL only)
    4. Compute transitive closure using fixpoint iteration
    5. Cache result by ontology hash + inference level for reuse
    
    IMPORTANT: The ontology graph is NOT mutated. We build a derived internal
    adjacency structure (dict of sets) with bidirectional edges for equivalence.
    
    Algorithm: Fixpoint propagation until no new edges added.
    Complexity: O(n*e) where n=nodes, e=edges; typically fast for sparse ontologies.
    
    Args:
        ontology_graph: The ontology graph (not modified)
        ontology_id: Optional stable ID for caching (e.g., filepath + mtime)
        inference: Inference level ("rdfs" or "owl-ld", etc.) - OWL constructs only processed for OWL levels
    
    Returns:
        Dictionary mapping each property to its set of sub-properties (including transitive)
    """
    # Compute stable hash of ontology + inference for caching
    if ontology_id is None:
        # Hash sorted triples (stable for same content)
        triples_sorted = sorted((str(s), str(p), str(o)) for s, p, o in ontology_graph)
        triple_str = '\n'.join(f"{s} {p} {o}" for s, p, o in triples_sorted)
        ont_hash = hashlib.sha256(triple_str.encode()).hexdigest()
    else:
        # Use caller-provided ID
        ont_hash = ontology_id
    
    # Include inference level in cache key
    cache_key = f"{ont_hash}:{inference}"
    
    # Check cache
    if cache_key in _closure_cache:
        logger.debug(f"Using cached closure for ontology {ont_hash[:8]} with inference={inference}")
        return _closure_cache[cache_key]
    
    logger.info(f"Computing subproperty closure for ontology {ont_hash[:8]} with inference={inference}")
    
    # Compute closure and equivalences
    closure, equivalent_props = _compute_closure_impl(ontology_graph, inference=inference)
    
    # Cache result
    _closure_cache[cache_key] = (closure, equivalent_props)
    logger.info(f"Cached closure for ontology {ont_hash[:8]} with {len(closure)} properties (inference={inference})")
    
    return closure, equivalent_props


def _compute_closure_impl(ontology_graph: Graph, inference: str = "rdfs") -> Tuple[Dict[URIRef, Set[URIRef]], Dict[URIRef, Set[URIRef]]]:
    """
    Internal implementation of closure computation.
    
    Args:
        ontology_graph: The ontology graph
        inference: Inference level - OWL constructs only processed for OWL-based levels
    
    Returns:
        Tuple of (subprop_closure, equivalent_props)
    """
    # Build internal adjacency structure: subprop_edges[parent] = {children}
    # This represents the "q is a subproperty of p" relationship
    subprop_edges: Dict[URIRef, Set[URIRef]] = {}
    equivalent_props: Dict[URIRef, Set[URIRef]] = {}
    all_properties: Set[URIRef] = set()
    
    # Step 1: Add direct rdfs:subPropertyOf edges
    for sub, pred, sup in ontology_graph.triples((None, RDFS.subPropertyOf, None)):
        if isinstance(sub, URIRef) and isinstance(sup, URIRef):
            all_properties.add(sub)
            all_properties.add(sup)
            
            if sup not in subprop_edges:
                subprop_edges[sup] = set()
            subprop_edges[sup].add(sub)
    
    # Step 2: Collect owl:equivalentProperty (for copying AND for closure) - OWL only
    is_owl = inference.startswith("owl")
    if is_owl:
        for p, pred, q in ontology_graph.triples((None, OWL.equivalentProperty, None)):
            if isinstance(p, URIRef) and isinstance(q, URIRef):
                all_properties.add(p)
                all_properties.add(q)
                
                # Store in equivalent_props (for full shape copying)
                if p not in equivalent_props:
                    equivalent_props[p] = set()
                if q not in equivalent_props:
                    equivalent_props[q] = set()
                equivalent_props[p].add(q)
                equivalent_props[q].add(p)
                
                # ALSO add as bidirectional subPropertyOf (for transitive closure)
                if q not in subprop_edges:
                    subprop_edges[q] = set()
                if p not in subprop_edges:
                    subprop_edges[p] = set()
                subprop_edges[q].add(p)
                subprop_edges[p].add(q)
    
    # Step 3: Collect owl:sameAs between properties (same treatment as equivalentProperty) - OWL only
    if is_owl:
        for p, pred, q in ontology_graph.triples((None, OWL.sameAs, None)):
            if isinstance(p, URIRef) and isinstance(q, URIRef):
                all_properties.add(p)
                all_properties.add(q)
                
                # Store in equivalent_props
                if p not in equivalent_props:
                    equivalent_props[p] = set()
                if q not in equivalent_props:
                    equivalent_props[q] = set()
                equivalent_props[p].add(q)
                equivalent_props[q].add(p)
                
                # ALSO add as bidirectional subPropertyOf
                if q not in subprop_edges:
                    subprop_edges[q] = set()
                if p not in subprop_edges:
                    subprop_edges[p] = set()
                subprop_edges[q].add(p)
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
    logger.debug(f"Found {len(equivalent_props)} properties with equivalences")
    
    return closure, equivalent_props


def clear_closure_cache() -> None:
    """
    Clear the closure cache.
    
    Useful for testing or when ontology changes.
    """
    global _closure_cache
    _closure_cache.clear()
    logger.debug("Cleared closure cache")
