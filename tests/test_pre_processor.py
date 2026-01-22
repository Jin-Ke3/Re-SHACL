"""
Tests for SHACL shape preprocessing with ontology-based extension.

These tests verify that the pre_process_shacl_graph_full function correctly
processes SHACL shape graphs using ontology information (TBox only, no data/ABox).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rdflib import Graph, Namespace, URIRef, BNode, RDF, RDFS, Literal
from rdflib.namespace import SH, OWL
from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pre_shacl.ontology_shape_entailer import extract_allowed_paths


# Define test namespace
EX = Namespace("http://example.org/")


@pytest.fixture
def simple_ontology():
    """Create a simple ontology for testing."""
    g = Graph()
    g.bind("ex", EX)
    
    # Add property hierarchy
    g.add((EX.nickname, RDFS.subPropertyOf, EX.name))
    g.add((EX.age, RDFS.subPropertyOf, EX.hasValue))
    
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


class TestPreprocessorNoRegime:
    """Test preprocessing with 'none' regime."""
    
    def test_none_regime_no_changes(self, simple_shape_graph):
        """Test that 'none' regime doesn't modify shapes."""
        ontology = Graph()
        sg_initial_size = len(simple_shape_graph)
        
        sg = pre_process_shacl_graph_full(
            simple_shape_graph,
            ontology,
            'none'
        )
        
        # Shape graph should be unchanged
        assert len(sg) == sg_initial_size, \
            "Shape graph should not be modified with 'none' regime"


class TestPreprocessorRDFSRegime:
    """Test preprocessing with RDFS entailment."""
    
    def test_rdfs_extends_shapes(self, simple_ontology, simple_shape_graph):
        """Test that RDFS regime extends closed shapes with sub-properties."""
        sg_initial_size = len(simple_shape_graph)
        
        sg = pre_process_shacl_graph_full(
            simple_shape_graph,
            simple_ontology,
            'rdfs'
        )
        
        # Shape graph should have new triples (sub-properties added)
        assert len(sg) > sg_initial_size, \
            "Expected shape extension to add triples"
        
        # Verify nickname was added as allowed property
        allowed = extract_allowed_paths(sg, EX.PersonShape)
        assert EX.name in allowed
        assert EX.nickname in allowed, "Sub-property should be added"
    
    def test_rdfs_updates_ignored_properties(self, simple_shape_graph):
        """Test that RDFS regime updates ignored properties in closed shapes."""
        ontology = Graph()
        
        sg = pre_process_shacl_graph_full(
            simple_shape_graph,
            ontology,
            'rdfs'
        )
        
        # Shape graph should still be valid
        assert len(sg) > 0, "Shape graph should not be empty"
        
        # PersonShape should still be a NodeShape
        assert (EX.PersonShape, RDF.type, SH.NodeShape) in sg
        
        # Should have rdf:type in ignored properties
        allowed = extract_allowed_paths(sg, EX.PersonShape)
        assert RDF.type in allowed, "rdf:type should be in allowed (via ignoredProperties)"


class TestPreprocessorOWLRegime:
    """Test preprocessing with OWL entailment."""
    
    def test_owl_extends_with_equivalent_properties(self):
        """Test that OWL regime handles equivalent properties."""
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.author, OWL.equivalentProperty, EX.creator))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.add((EX.BookShape, RDF.type, SH.NodeShape))
        sg.add((EX.BookShape, SH.targetClass, EX.Book))
        sg.add((EX.BookShape, SH.closed, Literal(True)))
        
        prop = BNode()
        sg.add((EX.BookShape, SH.property, prop))
        sg.add((prop, SH.path, EX.author))
        
        result = pre_process_shacl_graph_full(sg, ontology, 'rdfs')
        
        # Both properties should be allowed
        allowed = extract_allowed_paths(result, EX.BookShape)
        assert EX.author in allowed
        assert EX.creator in allowed, "Equivalent property should be added"


class TestClosedShapeExtension:
    """Test closed shape extension with ontology."""
    
    def test_transitive_subproperty_closure(self):
        """Test transitive closure of subPropertyOf."""
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.writes, RDFS.subPropertyOf, EX.authors))
        ontology.add((EX.pens, RDFS.subPropertyOf, EX.writes))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.add((EX.Shape1, RDF.type, SH.NodeShape))
        sg.add((EX.Shape1, SH.closed, Literal(True)))
        
        prop = BNode()
        sg.add((EX.Shape1, SH.property, prop))
        sg.add((prop, SH.path, EX.authors))
        
        result = pre_process_shacl_graph_full(sg, ontology, 'rdfs')
        
        # All properties in chain should be added
        allowed = extract_allowed_paths(result, EX.Shape1)
        assert EX.authors in allowed
        assert EX.writes in allowed, "Direct sub-property should be added"
        assert EX.pens in allowed, "Transitive sub-property should be added"
    
    def test_open_shape_not_extended(self):
        """Test that open shapes are not extended."""
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.nickname, RDFS.subPropertyOf, EX.name))
        
        sg = Graph()
        sg.bind("ex", EX)
        sg.add((EX.OpenShape, RDF.type, SH.NodeShape))
        # Note: sh:closed NOT set (open shape)
        
        prop = BNode()
        sg.add((EX.OpenShape, SH.property, prop))
        sg.add((prop, SH.path, EX.name))
        
        result = pre_process_shacl_graph_full(sg, ontology, 'rdfs')
        
        # Only original property should be present
        allowed = extract_allowed_paths(result, EX.OpenShape)
        assert EX.name in allowed
        assert EX.nickname not in allowed, "Open shapes should not be extended"


class TestErrorHandling:
    """Test error handling in the preprocessing pipeline."""
    
    def test_invalid_inference_level(self):
        """Test handling of invalid inference level."""
        ontology = Graph()
        shapes_graph = Graph()
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            pre_process_shacl_graph_full(
                shapes_graph, ontology, regime='invalid'
            )
    
    def test_empty_graphs(self):
        """Test preprocessing with empty graphs."""
        ontology = Graph()
        shapes_graph = Graph()
        
        # Should not crash
        sg = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='none'
        )
        
        assert isinstance(sg, Graph)
    
    def test_copy_on_write(self, simple_shape_graph, simple_ontology):
        """Test that preprocessing uses copy-on-write."""
        original_size = len(simple_shape_graph)
        
        result = pre_process_shacl_graph_full(
            simple_shape_graph, simple_ontology, 'rdfs'
        )
        
        # Original should be unchanged
        assert len(simple_shape_graph) == original_size, \
            "Original shape graph should not be modified (copy-on-write)"
        
        # Result should be larger (extended)
        assert len(result) > original_size, \
            "Result should have additional triples"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

