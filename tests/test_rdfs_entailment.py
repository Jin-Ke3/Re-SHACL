"""
Golden/snapshot tests for RDFS entailment.

These tests verify that RDFS entailment rules are correctly applied by checking
that expected triples are inferred from small test graphs.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rdflib import Graph, Namespace, RDF, RDFS, Literal
from pre_shacl.rdfs_entailment import entail


# Define test namespace
EX = Namespace("http://example.org/")


class TestRDFSSubPropertyOf:
    """Test RDFS subPropertyOf transitivity."""
    
    def test_transitive_subproperty(self):
        """Test that subPropertyOf is transitive."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: p1 subPropertyOf p2, p2 subPropertyOf p3
        g.add((EX.p1, RDFS.subPropertyOf, EX.p2))
        g.add((EX.p2, RDFS.subPropertyOf, EX.p3))
        
        # Apply entailment
        entail(g)
        
        # Assert: p1 should be subPropertyOf p3 (transitive)
        assert (EX.p1, RDFS.subPropertyOf, EX.p3) in g, \
            "Expected transitive subPropertyOf relation"


class TestRDFSSubClassOf:
    """Test RDFS subClassOf transitivity and type propagation."""
    
    def test_transitive_subclass(self):
        """Test that subClassOf is transitive."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: C1 subClassOf C2, C2 subClassOf C3
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        g.add((EX.C2, RDFS.subClassOf, EX.C3))
        
        # Apply entailment
        entail(g)
        
        # Assert: C1 should be subClassOf C3 (transitive)
        assert (EX.C1, RDFS.subClassOf, EX.C3) in g, \
            "Expected transitive subClassOf relation"
    
    def test_type_propagation_through_hierarchy(self):
        """Test that rdf:type propagates through class hierarchy."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: individual x is of type C1, C1 subClassOf C2
        g.add((EX.x, RDF.type, EX.C1))
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        
        # Apply entailment
        entail(g)
        
        # Assert: x should also be of type C2
        assert (EX.x, RDF.type, EX.C2) in g, \
            "Expected type to propagate through class hierarchy"
    
    def test_multi_level_type_propagation(self):
        """Test type propagation through multiple levels."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: x is C1, C1 subClassOf C2, C2 subClassOf C3
        g.add((EX.x, RDF.type, EX.C1))
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        g.add((EX.C2, RDFS.subClassOf, EX.C3))
        
        # Apply entailment
        entail(g)
        
        # Assert: x should be of all three types
        assert (EX.x, RDF.type, EX.C1) in g
        assert (EX.x, RDF.type, EX.C2) in g
        assert (EX.x, RDF.type, EX.C3) in g


class TestRDFSDomain:
    """Test RDFS domain inference."""
    
    def test_domain_type_inference(self):
        """Test that domain constraints infer types for subjects."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: property p has domain C, x has property p
        g.add((EX.p, RDFS.domain, EX.C))
        g.add((EX.x, EX.p, EX.y))
        
        # Apply entailment
        entail(g)
        
        # Assert: x should be inferred to be of type C
        assert (EX.x, RDF.type, EX.C) in g, \
            "Expected subject to be typed based on property domain"


class TestRDFSRange:
    """Test RDFS range inference."""
    
    def test_range_type_inference(self):
        """Test that range constraints infer types for objects."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: property p has range C, y is object of p
        g.add((EX.p, RDFS.range, EX.C))
        g.add((EX.x, EX.p, EX.y))
        
        # Apply entailment
        entail(g)
        
        # Assert: y should be inferred to be of type C
        assert (EX.y, RDF.type, EX.C) in g, \
            "Expected object to be typed based on property range"


class TestRDFSFixpoint:
    """Test that entailment reaches a fixpoint."""
    
    def test_fixpoint_reached(self):
        """Test that entailment completes without hitting max_iterations."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup a complex hierarchy
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        g.add((EX.C2, RDFS.subClassOf, EX.C3))
        g.add((EX.C3, RDFS.subClassOf, EX.C4))
        g.add((EX.x, RDF.type, EX.C1))
        
        # Apply entailment with low max_iterations to test guard
        initial_size = len(g)
        entail(g, max_iterations=100)
        
        # Should have inferred new triples
        assert len(g) > initial_size, "Expected new triples to be inferred"
        
        # Should have all expected types
        assert (EX.x, RDF.type, EX.C2) in g
        assert (EX.x, RDF.type, EX.C3) in g
        assert (EX.x, RDF.type, EX.C4) in g
    
    def test_max_iterations_guard(self):
        """Test that max_iterations prevents infinite loops."""
        g = Graph()
        g.bind("ex", EX)
        
        # Simple case that should complete quickly
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        
        # Apply with very low max_iterations
        entail(g, max_iterations=1)
        
        # Should not crash or hang
        assert len(g) >= 1


class TestRDFSIntegration:
    """Integration tests combining multiple RDFS rules."""
    
    def test_combined_rules(self):
        """Test multiple RDFS rules working together."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup complex scenario:
        # - Class hierarchy: Student subClassOf Person
        # - Property: enrolledIn has domain Student
        # - Individual: alice enrolledIn course1
        g.add((EX.Student, RDFS.subClassOf, EX.Person))
        g.add((EX.enrolledIn, RDFS.domain, EX.Student))
        g.add((EX.alice, EX.enrolledIn, EX.course1))
        
        # Apply entailment
        entail(g)
        
        # Assert: alice should be inferred as Student (from domain)
        assert (EX.alice, RDF.type, EX.Student) in g, \
            "Expected domain inference"
        
        # Assert: alice should also be inferred as Person (from class hierarchy)
        assert (EX.alice, RDF.type, EX.Person) in g, \
            "Expected type propagation through class hierarchy"
    
    def test_no_spurious_inferences(self):
        """Test that entailment doesn't create unexpected triples."""
        g = Graph()
        g.bind("ex", EX)
        
        # Simple case
        g.add((EX.x, RDF.type, EX.C))
        
        initial_size = len(g)
        entail(g)
        
        # Should not infer anything new (no rules apply)
        assert len(g) == initial_size, \
            "Expected no new inferences when no rules apply"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
