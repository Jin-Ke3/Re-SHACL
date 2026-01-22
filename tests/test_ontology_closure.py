"""Unit tests for ontology closure computation.

Tests the transitive closure computation for rdfs:subPropertyOf relationships,
including owl:equivalentProperty handling and determinism.
"""

import pytest
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDFS, OWL
from pre_shacl.ontology_closure import (
    compute_subproperty_closure,
    clear_closure_cache
)

# Test namespaces
EX = Namespace("http://example.org/")


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test to ensure test isolation."""
    clear_closure_cache()
    yield
    clear_closure_cache()


def test_empty_ontology():
    """Test closure computation with empty ontology."""
    ont = Graph()
    closure = compute_subproperty_closure(ont)
    assert closure == {}


def test_single_subproperty():
    """Test simple single-level subPropertyOf relationship."""
    ont = Graph()
    p1 = EX.writes
    p2 = EX.authors
    
    ont.add((p1, RDFS.subPropertyOf, p2))
    
    closure = compute_subproperty_closure(ont)
    
    assert p2 in closure
    assert p1 in closure[p2]
    assert len(closure[p2]) == 1


def test_transitive_subproperty():
    """Test transitive closure of rdfs:subPropertyOf."""
    ont = Graph()
    p1 = EX.pens
    p2 = EX.writes
    p3 = EX.authors
    
    # p1 subPropertyOf p2 subPropertyOf p3
    ont.add((p1, RDFS.subPropertyOf, p2))
    ont.add((p2, RDFS.subPropertyOf, p3))
    
    closure = compute_subproperty_closure(ont)
    
    # p3 should have both p2 and p1 as subproperties (transitive)
    assert p1 in closure[p3], "p1 should be a subproperty of p3 (transitive)"
    assert p2 in closure[p3], "p2 should be a subproperty of p3 (direct)"
    
    # p2 should have p1 as subproperty (direct)
    assert p1 in closure[p2], "p1 should be a subproperty of p2 (direct)"


def test_multiple_subproperties():
    """Test property with multiple direct sub-properties."""
    ont = Graph()
    p_super = EX.creates
    p1 = EX.writes
    p2 = EX.paints
    p3 = EX.composes
    
    ont.add((p1, RDFS.subPropertyOf, p_super))
    ont.add((p2, RDFS.subPropertyOf, p_super))
    ont.add((p3, RDFS.subPropertyOf, p_super))
    
    closure = compute_subproperty_closure(ont)
    
    assert p1 in closure[p_super]
    assert p2 in closure[p_super]
    assert p3 in closure[p_super]
    assert len(closure[p_super]) == 3


def test_equivalent_property_bidirectional():
    """Test owl:equivalentProperty creates bidirectional subPropertyOf."""
    ont = Graph()
    p1 = EX.author
    p2 = EX.creator
    
    ont.add((p1, OWL.equivalentProperty, p2))
    
    closure = compute_subproperty_closure(ont)
    
    # Both should be subproperties of each other
    assert p1 in closure[p2], "p1 should be subproperty of p2 (from equivalence)"
    assert p2 in closure[p1], "p2 should be subproperty of p1 (from equivalence)"


def test_equivalent_with_subproperty():
    """Test combination of equivalentProperty and subPropertyOf."""
    ont = Graph()
    p1 = EX.writes
    p2 = EX.authors
    p3 = EX.creates
    
    # p1 equivalent to p2, and p2 subPropertyOf p3
    ont.add((p1, OWL.equivalentProperty, p2))
    ont.add((p2, RDFS.subPropertyOf, p3))
    
    closure = compute_subproperty_closure(ont)
    
    # Due to equivalence, p1 should also be subproperty of p3
    assert p1 in closure[p3], "p1 should be subproperty of p3 (via equivalence)"
    assert p2 in closure[p3], "p2 should be subproperty of p3 (direct)"


def test_closure_determinism():
    """Test closure is deterministic regardless of triple order."""
    p1 = EX.p1
    p2 = EX.p2
    p3 = EX.p3
    
    # Create first ontology with one triple order
    ont1 = Graph()
    ont1.add((p1, RDFS.subPropertyOf, p2))
    ont1.add((p2, RDFS.subPropertyOf, p3))
    
    # Create second ontology with different triple order
    ont2 = Graph()
    ont2.add((p2, RDFS.subPropertyOf, p3))
    ont2.add((p1, RDFS.subPropertyOf, p2))
    
    closure1 = compute_subproperty_closure(ont1)
    closure2 = compute_subproperty_closure(ont2)
    
    # Results should be identical
    assert closure1 == closure2


def test_diamond_pattern():
    """Test diamond inheritance pattern."""
    ont = Graph()
    p_top = EX.top
    p_left = EX.left
    p_right = EX.right
    p_bottom = EX.bottom
    
    # Diamond: bottom -> left -> top, bottom -> right -> top
    ont.add((p_bottom, RDFS.subPropertyOf, p_left))
    ont.add((p_bottom, RDFS.subPropertyOf, p_right))
    ont.add((p_left, RDFS.subPropertyOf, p_top))
    ont.add((p_right, RDFS.subPropertyOf, p_top))
    
    closure = compute_subproperty_closure(ont)
    
    # p_top should have all three as subproperties
    assert p_bottom in closure[p_top]
    assert p_left in closure[p_top]
    assert p_right in closure[p_top]
    assert len(closure[p_top]) == 3


def test_self_loop():
    """Test handling of self-referential subPropertyOf (should be handled gracefully)."""
    ont = Graph()
    p = EX.property
    
    ont.add((p, RDFS.subPropertyOf, p))
    
    closure = compute_subproperty_closure(ont)
    
    # Self-loop should result in property being subproperty of itself
    assert p in closure[p]


def test_caching():
    """Test that closure results are cached."""
    ont = Graph()
    p1 = EX.p1
    p2 = EX.p2
    ont.add((p1, RDFS.subPropertyOf, p2))
    
    # First call - computes closure
    closure1 = compute_subproperty_closure(ont)
    
    # Second call - should use cache
    closure2 = compute_subproperty_closure(ont)
    
    # Results should be identical (same object from cache)
    assert closure1 is closure2


def test_cache_with_different_ontologies():
    """Test that different ontologies get different cache entries."""
    ont1 = Graph()
    ont1.add((EX.p1, RDFS.subPropertyOf, EX.p2))
    
    ont2 = Graph()
    ont2.add((EX.p3, RDFS.subPropertyOf, EX.p4))
    
    closure1 = compute_subproperty_closure(ont1)
    closure2 = compute_subproperty_closure(ont2)
    
    # Should be different results
    assert closure1 != closure2
    assert EX.p2 in closure1
    assert EX.p4 in closure2
    assert EX.p2 not in closure2
    assert EX.p4 not in closure1


def test_no_properties():
    """Test ontology with triples but no property hierarchies."""
    ont = Graph()
    # Add some data triples without subPropertyOf
    ont.add((EX.subject, EX.predicate, EX.object))
    
    closure = compute_subproperty_closure(ont)
    
    assert closure == {}


def test_complex_hierarchy():
    """Test a more complex property hierarchy."""
    ont = Graph()
    
    # Build hierarchy: p1 -> p2 -> p3 -> p4 -> p5
    ont.add((EX.p1, RDFS.subPropertyOf, EX.p2))
    ont.add((EX.p2, RDFS.subPropertyOf, EX.p3))
    ont.add((EX.p3, RDFS.subPropertyOf, EX.p4))
    ont.add((EX.p4, RDFS.subPropertyOf, EX.p5))
    
    # Add branch: p6 -> p3
    ont.add((EX.p6, RDFS.subPropertyOf, EX.p3))
    
    closure = compute_subproperty_closure(ont)
    
    # p5 should have all as subproperties
    assert EX.p1 in closure[EX.p5]
    assert EX.p2 in closure[EX.p5]
    assert EX.p3 in closure[EX.p5]
    assert EX.p4 in closure[EX.p5]
    assert EX.p6 in closure[EX.p5]
    
    # p3 should have p1, p2, and p6
    assert EX.p1 in closure[EX.p3]
    assert EX.p2 in closure[EX.p3]
    assert EX.p6 in closure[EX.p3]
