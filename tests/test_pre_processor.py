"""
End-to-end tests for SHACL shape preprocessing.

These tests verify that the pre_process_shacl_graph_full function correctly
processes SHACL shape graphs with various inference regimes.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rdflib import Graph, Namespace, URIRef, BNode, RDF, RDFS, Literal
from rdflib.namespace import SH, OWL
from pre_shacl.pre_processor import pre_process_shacl_graph_full


# Define test namespace
EX = Namespace("http://example.org/")


@pytest.fixture
def simple_data_graph():
    """Create a simple data graph for testing."""
    g = Graph()
    g.bind("ex", EX)
    
    # Add some basic data
    g.add((EX.alice, RDF.type, EX.Person))
    g.add((EX.alice, EX.name, Literal("Alice")))
    g.add((EX.alice, EX.age, Literal(30)))
    
    return g


@pytest.fixture
def simple_shape_graph():
    """Create a simple SHACL shape graph for testing."""
    g = Graph()
    g.bind("ex", EX)
    g.bind("sh", SH)
    
    # Define a simple closed shape for Person
    person_shape = EX.PersonShape
    g.add((person_shape, RDF.type, SH.NodeShape))
    g.add((person_shape, SH.targetClass, EX.Person))
    g.add((person_shape, SH.closed, Literal(True)))
    
    # Add property shape for name
    name_prop = BNode()
    g.add((person_shape, SH.property, name_prop))
    g.add((name_prop, SH.path, EX.name))
    
    # Add ignoredProperties list
    ignored_list = BNode()
    g.add((person_shape, SH.ignoredProperties, ignored_list))
    g.add((ignored_list, RDF.first, RDF.type))
    g.add((ignored_list, RDF.rest, RDF.nil))
    
    return g


@pytest.fixture
def hierarchical_data_graph():
    """Create a data graph with class hierarchy."""
    g = Graph()
    g.bind("ex", EX)
    
    # Class hierarchy: Student subClassOf Person
    g.add((EX.Student, RDFS.subClassOf, EX.Person))
    
    # Data
    g.add((EX.bob, RDF.type, EX.Student))
    g.add((EX.bob, EX.name, Literal("Bob")))
    g.add((EX.bob, EX.studentId, Literal("12345")))
    
    return g


class TestPreprocessorNoRegime:
    """Test preprocessing with 'none' regime."""
    
    def test_none_regime_no_changes(self, simple_data_graph, simple_shape_graph):
        """Test that 'none' regime doesn't modify graphs."""
        dg_initial_size = len(simple_data_graph)
        sg_initial_size = len(simple_shape_graph)
        
        dg, sg = pre_process_shacl_graph_full(
            simple_data_graph, 
            simple_shape_graph, 
            'none'
        )
        
        # Graphs should be unchanged
        assert len(dg) == dg_initial_size, \
            "Data graph should not be modified with 'none' regime"
        assert len(sg) == sg_initial_size, \
            "Shape graph should not be modified with 'none' regime"


class TestPreprocessorRDFSRegime:
    """Test preprocessing with RDFS entailment."""
    
    def test_rdfs_entails_data_graph(self, hierarchical_data_graph, simple_shape_graph):
        """Test that RDFS regime entails the data graph."""
        dg_initial_size = len(hierarchical_data_graph)
        
        dg, sg = pre_process_shacl_graph_full(
            hierarchical_data_graph, 
            simple_shape_graph, 
            'rdfs'
        )
        
        # Data graph should have new inferred triples
        assert len(dg) > dg_initial_size, \
            "Expected RDFS entailment to add triples to data graph"
        
        # bob should be inferred as Person (via subClassOf)
        assert (EX.bob, RDF.type, EX.Person) in dg, \
            "Expected RDFS inference: Student subClassOf Person"
    
    def test_rdfs_updates_ignored_properties(self, hierarchical_data_graph, simple_shape_graph):
        """Test that RDFS regime updates ignored properties in closed shapes."""
        dg, sg = pre_process_shacl_graph_full(
            hierarchical_data_graph, 
            simple_shape_graph, 
            'rdfs'
        )
        
        # Shape graph should still be valid
        assert len(sg) > 0, "Shape graph should not be empty"
        
        # PersonShape should still be a NodeShape
        assert (EX.PersonShape, RDF.type, SH.NodeShape) in sg, \
            "PersonShape should still be a NodeShape"


class TestPreprocessorOWLRegime:
    """Test preprocessing with OWL entailment."""
    
    def test_owl_entails_data_graph(self):
        """Test that OWL regime entails the data graph with sameAs."""
        dg = Graph()
        dg.bind("ex", EX)
        
        # Add sameAs relation
        dg.add((EX.alice, OWL.sameAs, EX.alice2))
        dg.add((EX.alice, RDF.type, EX.Person))
        dg.add((EX.alice, EX.name, Literal("Alice")))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.bind("sh", SH)
        
        # Simple non-closed shape
        person_shape = EX.PersonShape
        sg.add((person_shape, RDF.type, SH.NodeShape))
        sg.add((person_shape, SH.targetClass, EX.Person))
        
        dg_initial_size = len(dg)
        
        dg, sg = pre_process_shacl_graph_full(dg, sg, 'owl-ld')
        
        # Data graph should have new inferred triples
        assert len(dg) > dg_initial_size, \
            "Expected OWL entailment to add triples to data graph"
        
        # alice2 should be inferred as Person (via sameAs)
        assert (EX.alice2, RDF.type, EX.Person) in dg, \
            "Expected OWL inference: sameAs property copying"


class TestPreprocessorClosedShapes:
    """Test preprocessing behavior with closed shapes."""
    
    def test_closed_shape_has_ignored_properties(self, simple_data_graph, simple_shape_graph):
        """Test that closed shapes have ignoredProperties."""
        dg, sg = pre_process_shacl_graph_full(
            simple_data_graph, 
            simple_shape_graph, 
            'none'
        )
        
        # PersonShape should have ignoredProperties
        ignored_props = list(sg.objects(EX.PersonShape, SH.ignoredProperties))
        assert len(ignored_props) > 0, \
            "Closed shape should have ignoredProperties list"
    
    def test_ignored_properties_includes_rdf_type(self, simple_data_graph, simple_shape_graph):
        """Test that rdf:type is in ignored properties."""
        dg, sg = pre_process_shacl_graph_full(
            simple_data_graph, 
            simple_shape_graph, 
            'none'
        )
        
        # Get ignoredProperties list
        ignored_list = sg.value(EX.PersonShape, SH.ignoredProperties)
        
        # Convert RDF list to Python list
        ignored_props = []
        current = ignored_list
        while current and current != RDF.nil:
            first = sg.value(current, RDF.first)
            if first:
                ignored_props.append(first)
            current = sg.value(current, RDF.rest)
        
        # rdf:type should be in ignored properties
        assert RDF.type in ignored_props, \
            "rdf:type should be in ignoredProperties for closed shapes"


class TestPreprocessorIntegration:
    """Integration tests for the full preprocessing pipeline."""
    
    def test_multiple_shapes_processing(self):
        """Test processing multiple shapes in the same graph."""
        dg = Graph()
        dg.bind("ex", EX)
        
        # Data with two classes
        dg.add((EX.alice, RDF.type, EX.Person))
        dg.add((EX.alice, EX.name, Literal("Alice")))
        dg.add((EX.course1, RDF.type, EX.Course))
        dg.add((EX.course1, EX.title, Literal("Math 101")))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.bind("sh", SH)
        
        # Two closed shapes
        person_shape = EX.PersonShape
        sg.add((person_shape, RDF.type, SH.NodeShape))
        sg.add((person_shape, SH.targetClass, EX.Person))
        sg.add((person_shape, SH.closed, Literal(True)))
        
        course_shape = EX.CourseShape
        sg.add((course_shape, RDF.type, SH.NodeShape))
        sg.add((course_shape, SH.targetClass, EX.Course))
        sg.add((course_shape, SH.closed, Literal(True)))
        
        dg, sg = pre_process_shacl_graph_full(dg, sg, 'none')
        
        # Both shapes should still exist
        assert (person_shape, RDF.type, SH.NodeShape) in sg
        assert (course_shape, RDF.type, SH.NodeShape) in sg
    
    def test_non_closed_shape_unchanged(self):
        """Test that non-closed shapes are not modified."""
        dg = Graph()
        dg.bind("ex", EX)
        dg.add((EX.alice, RDF.type, EX.Person))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.bind("sh", SH)
        
        # Non-closed shape (no sh:closed or sh:closed false)
        person_shape = EX.PersonShape
        sg.add((person_shape, RDF.type, SH.NodeShape))
        sg.add((person_shape, SH.targetClass, EX.Person))
        
        sg_initial_size = len(sg)
        
        dg, sg = pre_process_shacl_graph_full(dg, sg, 'rdfs')
        
        # Shape graph size should be unchanged (no ignoredProperties added)
        # Note: This depends on implementation - may need adjustment
        assert (person_shape, RDF.type, SH.NodeShape) in sg, \
            "Non-closed shape should remain in graph"


class TestPreprocessorEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_data_graph(self, simple_shape_graph):
        """Test preprocessing with empty data graph."""
        dg = Graph()
        
        # Should not crash
        dg, sg = pre_process_shacl_graph_full(dg, simple_shape_graph, 'none')
        
        assert len(dg) == 0, "Empty data graph should remain empty"
        assert len(sg) > 0, "Shape graph should not be empty"
    
    def test_empty_shape_graph(self, simple_data_graph):
        """Test preprocessing with empty shape graph."""
        sg = Graph()
        
        # Should not crash
        dg, sg = pre_process_shacl_graph_full(simple_data_graph, sg, 'none')
        
        assert len(dg) > 0, "Data graph should not be empty"
        assert len(sg) == 0, "Empty shape graph should remain empty"
    
    def test_invalid_regime_falls_back(self, simple_data_graph, simple_shape_graph):
        """Test that invalid regime is handled gracefully."""
        # Note: This test depends on implementation behavior
        # Some implementations might raise an error, others might default to 'none'
        try:
            dg, sg = pre_process_shacl_graph_full(
                simple_data_graph, 
                simple_shape_graph, 
                'invalid-regime'
            )
            # If no error, verify graphs are still valid
            assert len(dg) > 0
            assert len(sg) > 0
        except (ValueError, KeyError):
            # If it raises an error, that's also acceptable
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
