"""
Golden/snapshot tests for OWL entailment.

These tests verify that OWL entailment rules are correctly applied by checking
that expected triples are inferred from small test graphs.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal
from pre_shacl.owl_entailment import entail


# Define test namespace
EX = Namespace("http://example.org/")


class TestOWLSameAs:
    """Test OWL sameAs property."""
    
    def test_sameas_symmetric(self):
        """Test that sameAs is symmetric."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: x sameAs y
        g.add((EX.x, OWL.sameAs, EX.y))
        
        # Apply entailment
        entail(g)
        
        # Assert: y should be sameAs x (symmetric)
        assert (EX.y, OWL.sameAs, EX.x) in g, \
            "Expected symmetric sameAs relation"
    
    def test_sameas_transitive(self):
        """Test that sameAs is transitive."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: x sameAs y, y sameAs z
        g.add((EX.x, OWL.sameAs, EX.y))
        g.add((EX.y, OWL.sameAs, EX.z))
        
        # Apply entailment
        entail(g)
        
        # Assert: x should be sameAs z (transitive)
        assert (EX.x, OWL.sameAs, EX.z) in g, \
            "Expected transitive sameAs relation"
    
    def test_sameas_property_copying_subject(self):
        """Test that properties are copied when subjects are sameAs."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: x sameAs y, x has property p with value v
        g.add((EX.x, OWL.sameAs, EX.y))
        g.add((EX.x, EX.p, EX.v))
        
        # Apply entailment
        entail(g)
        
        # Assert: y should also have property p with value v
        assert (EX.y, EX.p, EX.v) in g, \
            "Expected property to be copied to sameAs subject"
    
    def test_sameas_property_copying_object(self):
        """Test that properties are copied when objects are sameAs."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: x sameAs y, s has property p with value x
        g.add((EX.x, OWL.sameAs, EX.y))
        g.add((EX.s, EX.p, EX.x))
        
        # Apply entailment
        entail(g)
        
        # Assert: s should also have property p with value y
        assert (EX.s, EX.p, EX.y) in g, \
            "Expected property to be copied to sameAs object"


class TestOWLEquivalentProperty:
    """Test OWL equivalentProperty conversion."""
    
    def test_equivalent_property_to_subproperty(self):
        """Test that equivalentProperty is converted to subPropertyOf."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: p1 equivalentProperty p2
        g.add((EX.p1, OWL.equivalentProperty, EX.p2))
        
        # Apply entailment
        entail(g)
        
        # Assert: both directions of subPropertyOf should exist
        assert (EX.p1, RDFS.subPropertyOf, EX.p2) in g, \
            "Expected equivalentProperty to create subPropertyOf"
        assert (EX.p2, RDFS.subPropertyOf, EX.p1) in g, \
            "Expected equivalentProperty to create reverse subPropertyOf"


class TestOWLSubPropertyOf:
    """Test OWL subPropertyOf transitivity and equivalence detection."""
    
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
    
    def test_equivalent_property_detection_from_cycle(self):
        """Test that circular subPropertyOf creates equivalentProperty."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: p1 subPropertyOf p2, p2 subPropertyOf p1 (cycle)
        g.add((EX.p1, RDFS.subPropertyOf, EX.p2))
        g.add((EX.p2, RDFS.subPropertyOf, EX.p1))
        
        # Apply entailment
        entail(g)
        
        # Assert: equivalentProperty should be inferred
        assert (EX.p1, OWL.equivalentProperty, EX.p2) in g, \
            "Expected equivalentProperty from circular subPropertyOf"


class TestOWLDomainRange:
    """Test OWL domain and range inference."""
    
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
    
    def test_domain_superclass_propagation(self):
        """Test that domain constraints propagate to superclasses."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: p has domain C, C subClassOf D
        g.add((EX.p, RDFS.domain, EX.C))
        g.add((EX.C, RDFS.subClassOf, EX.D))
        
        # Apply entailment
        entail(g)
        
        # Assert: p should also have domain D
        assert (EX.p, RDFS.domain, EX.D) in g, \
            "Expected domain to propagate to superclass"
    
    def test_domain_superproperty_propagation(self):
        """Test that domain constraints propagate to superproperties."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: p1 has domain C, p1 subPropertyOf p2
        g.add((EX.p1, RDFS.domain, EX.C))
        g.add((EX.p1, RDFS.subPropertyOf, EX.p2))
        
        # Apply entailment
        entail(g)
        
        # Assert: p2 should also have domain C
        assert (EX.p2, RDFS.domain, EX.C) in g, \
            "Expected domain to propagate to superproperty"
    
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


class TestOWLSubClassOf:
    """Test OWL subClassOf transitivity and equivalence detection."""
    
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
    
    def test_equivalent_class_detection_from_cycle(self):
        """Test that circular subClassOf creates equivalentClass."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: C1 subClassOf C2, C2 subClassOf C1 (cycle)
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        g.add((EX.C2, RDFS.subClassOf, EX.C1))
        
        # Apply entailment
        entail(g)
        
        # Assert: equivalentClass should be inferred
        assert (EX.C1, OWL.equivalentClass, EX.C2) in g, \
            "Expected equivalentClass from circular subClassOf"
    
    def test_class_inheritance(self):
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


class TestOWLEquivalentClass:
    """Test OWL equivalentClass conversion."""
    
    def test_equivalent_class_to_subclass(self):
        """Test that equivalentClass is converted to subClassOf."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup: C1 equivalentClass C2
        g.add((EX.C1, OWL.equivalentClass, EX.C2))
        
        # Apply entailment
        entail(g)
        
        # Assert: both directions of subClassOf should exist
        assert (EX.C1, RDFS.subClassOf, EX.C2) in g, \
            "Expected equivalentClass to create subClassOf"
        assert (EX.C2, RDFS.subClassOf, EX.C1) in g, \
            "Expected equivalentClass to create reverse subClassOf"


class TestOWLFixpoint:
    """Test that entailment reaches a fixpoint."""
    
    def test_fixpoint_reached(self):
        """Test that entailment completes without hitting max_iterations."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup a complex scenario
        g.add((EX.x, OWL.sameAs, EX.y))
        g.add((EX.C1, RDFS.subClassOf, EX.C2))
        g.add((EX.x, RDF.type, EX.C1))
        
        # Apply entailment
        initial_size = len(g)
        entail(g, max_iterations=100)
        
        # Should have inferred new triples
        assert len(g) > initial_size, "Expected new triples to be inferred"
    
    def test_max_iterations_guard(self):
        """Test that max_iterations prevents infinite loops."""
        g = Graph()
        g.bind("ex", EX)
        
        # Simple case that should complete quickly
        g.add((EX.x, OWL.sameAs, EX.y))
        
        # Apply with very low max_iterations
        entail(g, max_iterations=1)
        
        # Should not crash or hang
        assert len(g) >= 1


class TestOWLIntegration:
    """Integration tests combining multiple OWL rules."""
    
    @pytest.mark.xfail(reason="Multi-pass inference requires optimization - see Phase 2")
    def test_combined_owl_and_rdfs_rules(self):
        """Test multiple OWL and RDFS rules working together."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup complex scenario:
        # - alice sameAs alice2
        # - alice is a Student
        # - Student subClassOf Person
        g.add((EX.alice, OWL.sameAs, EX.alice2))
        g.add((EX.alice, RDF.type, EX.Student))
        g.add((EX.Student, RDFS.subClassOf, EX.Person))
        
        # Apply entailment
        entail(g)
        
        # Assert: alice2 should also be Student (from sameAs)
        assert (EX.alice2, RDF.type, EX.Student) in g, \
            "Expected sameAs to copy type"
        
        # Assert: alice should be Person (from class hierarchy)
        assert (EX.alice, RDF.type, EX.Person) in g, \
            "Expected type propagation through class hierarchy"
        
        # Assert: alice2 should also be Person (combination)
        assert (EX.alice2, RDF.type, EX.Person) in g, \
            "Expected combined inference from sameAs and class hierarchy"
    
    @pytest.mark.xfail(reason="Multi-pass inference requires optimization - see Phase 2")
    def test_property_and_class_hierarchies(self):
        """Test interaction between property and class hierarchies."""
        g = Graph()
        g.bind("ex", EX)
        
        # Setup:
        # - teaches has domain Professor
        # - Professor subClassOf Person
        # - bob teaches course1
        g.add((EX.teaches, RDFS.domain, EX.Professor))
        g.add((EX.Professor, RDFS.subClassOf, EX.Person))
        g.add((EX.bob, EX.teaches, EX.course1))
        
        # Apply entailment
        entail(g)
        
        # Assert: bob should be Professor (from domain)
        assert (EX.bob, RDF.type, EX.Professor) in g, \
            "Expected domain inference"
        
        # Assert: bob should also be Person (from class hierarchy)
        assert (EX.bob, RDF.type, EX.Person) in g, \
            "Expected type propagation through class hierarchy"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
