"""Integration Tests for Pre-SHACL Preprocessing Pipeline

This module tests the complete preprocessing workflow from data/shapes loading
through entailment and shape extension to final SHACL validation.
"""

import pytest
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH, Literal, URIRef
from rdflib.namespace import XSD
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pre_shacl.EntailEngine import EntailEngine, InferenceLevel
import tempfile
import os


EX = Namespace("http://example.org/")


def load_turtle_graph(path):
    """Load an RDF graph from a Turtle file."""
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


class TestPreprocessingPipeline:
    """Test the full preprocessing pipeline end-to-end."""
    
    def test_simple_rdfs_preprocessing(self):
        """Test basic RDFS preprocessing with type inference."""
        # Create data graph with class hierarchy
        data_graph = Graph()
        data_graph.bind("ex", EX)
        data_graph.add((EX.Person, RDF.type, RDFS.Class))
        data_graph.add((EX.Student, RDFS.subClassOf, EX.Person))
        data_graph.add((EX.alice, RDF.type, EX.Student))
        data_graph.add((EX.alice, EX.name, Literal("Alice")))
        
        # Create simple shape
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        # Property shape for name
        prop_node = URIRef(EX.PersonShape_name)
        shapes_graph.add((EX.PersonShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.name))
        
        # Run preprocessing
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='rdfs'
        )
        
        # Verify type inference happened
        assert (EX.alice, RDF.type, EX.Person) in entailed_data
        assert (EX.alice, RDF.type, EX.Student) in entailed_data
    
    def test_owl_preprocessing_with_sameas(self):
        """Test OWL preprocessing with owl:sameAs inference."""
        # Create data with sameAs
        data_graph = Graph()
        data_graph.bind("ex", EX)
        data_graph.add((EX.alice, EX.name, Literal("Alice")))
        data_graph.add((EX.alice, OWL.sameAs, EX.aliceSmith))
        
        # Create shape
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        # Run OWL preprocessing
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='owl-ld'
        )
        
        # Verify sameAs inference
        assert (EX.aliceSmith, OWL.sameAs, EX.alice) in entailed_data  # symmetric
        assert (EX.aliceSmith, EX.name, Literal("Alice")) in entailed_data  # property copying
    
    def test_closed_shape_extension(self):
        """Test that closed shapes are extended with sub-properties."""
        # Create data with property hierarchy: nickname is a sub-property of name
        data_graph = Graph()
        data_graph.bind("ex", EX)
        data_graph.add((EX.nickname, RDFS.subPropertyOf, EX.name))
        data_graph.add((EX.alice, RDF.type, EX.Person))
        data_graph.add((EX.alice, EX.nickname, Literal("Ally")))
        
        # Create closed shape with property for 'name'
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        # Add sh:property for name (the super-property)
        prop_node = URIRef(EX.PersonShape_name)
        shapes_graph.add((EX.PersonShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.name))
        
        # Run preprocessing
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='rdfs'
        )
        
        # Verify data has inferred property (nickname -> name)
        assert (EX.alice, EX.name, Literal("Ally")) in entailed_data
        
        # Verify shape was extended with ex:nickname (the sub-property)
        shape_properties = set()
        for _, _, prop_shape in entailed_shapes.triples((EX.PersonShape, SH.property, None)):
            for _, _, path in entailed_shapes.triples((prop_shape, SH.path, None)):
                shape_properties.add(path)
        
        assert EX.name in shape_properties
        assert EX.nickname in shape_properties
    
    def test_ignored_properties_management(self):
        """Test that ignored properties are handled correctly per regime."""
        data_graph = Graph()
        data_graph.bind("ex", EX)
        data_graph.add((EX.alice, RDF.type, EX.Person))
        data_graph.add((EX.alice, EX.name, Literal("Alice")))
        data_graph.add((EX.alice, OWL.sameAs, EX.aliceSmith))
        
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        # Add name property
        prop_node = URIRef(EX.PersonShape_name)
        shapes_graph.add((EX.PersonShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.name))
        
        # Run preprocessing with OWL-LD
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='owl-ld'
        )
        
        # Verify shape has sh:ignoredProperties
        has_ignored = any(
            entailed_shapes.triples((EX.PersonShape, SH.ignoredProperties, None))
        )
        assert has_ignored, "Shape should have sh:ignoredProperties"
        
        # Check that owl:sameAs is in ignored list (OWL-LD only adds owl:sameAs, not rdf:type)
        for _, _, ignored_list in entailed_shapes.triples((EX.PersonShape, SH.ignoredProperties, None)):
            items = list(entailed_shapes.items(ignored_list))
            assert OWL.sameAs in items
            # OWL-LD does not add rdf:type to ignored properties
            assert RDF.type not in items


class TestEntailmentEngine:
    """Test the EntailEngine abstraction."""
    
    def test_rdfs_entailment_mode(self):
        """Test RDFS entailment via EntailEngine."""
        graph = Graph()
        graph.bind("ex", EX)
        graph.add((EX.Person, RDF.type, RDFS.Class))
        graph.add((EX.Student, RDFS.subClassOf, EX.Person))
        graph.add((EX.alice, RDF.type, EX.Student))
        
        engine = EntailEngine(graph, InferenceLevel.RDFS)
        engine.entail()
        
        # Verify subclass type propagation
        assert (EX.alice, RDF.type, EX.Person) in graph
    
    def test_owl_entailment_mode(self):
        """Test OWL entailment via EntailEngine."""
        graph = Graph()
        graph.bind("ex", EX)
        graph.add((EX.alice, OWL.sameAs, EX.aliceSmith))
        graph.add((EX.alice, EX.name, Literal("Alice")))
        
        engine = EntailEngine(graph, InferenceLevel.OWL_LD)
        engine.entail()
        
        # Verify sameAs symmetry
        assert (EX.aliceSmith, OWL.sameAs, EX.alice) in graph
        # Verify property copying
        assert (EX.aliceSmith, EX.name, Literal("Alice")) in graph
    
    def test_no_entailment_mode(self):
        """Test that NONE mode doesn't add triples."""
        graph = Graph()
        graph.bind("ex", EX)
        graph.add((EX.alice, RDF.type, EX.Student))
        graph.add((EX.Student, RDFS.subClassOf, EX.Person))
        
        initial_size = len(graph)
        
        engine = EntailEngine(graph, InferenceLevel.NONE)
        engine.entail()
        
        # Graph should not grow
        assert len(graph) == initial_size


class TestPreprocessingWithFiles:
    """Test preprocessing with actual fixture files."""
    
    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return os.path.join(os.path.dirname(__file__), "..", "PreSHACL", "fixtures")
    
    def test_person_closed_shape_fixture(self, fixtures_dir):
        """Test preprocessing with the person closed shape fixture."""
        shape_path = os.path.join(fixtures_dir, "person_shape_closed.ttl")
        data_path = os.path.join(fixtures_dir, "person_data_basic.ttl")
        
        if not os.path.exists(shape_path) or not os.path.exists(data_path):
            pytest.skip("Fixture files not found")
        
        data_graph = load_turtle_graph(data_path)
        shapes_graph = load_turtle_graph(shape_path)
        
        # Run preprocessing
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='rdfs'
        )
        
        # Basic sanity checks
        assert len(entailed_data) >= len(data_graph)
        assert len(entailed_shapes) >= len(shapes_graph)
    
    def test_preprocessing_preserves_original_data(self):
        """Test that preprocessing doesn't destroy original triples."""
        original_data = Graph()
        original_data.bind("ex", EX)
        original_data.add((EX.alice, EX.name, Literal("Alice")))
        original_data.add((EX.alice, RDF.type, EX.Person))
        
        original_triples = set(original_data)
        
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        
        entailed_data, _ = pre_process_shacl_graph_full(
            original_data, shapes_graph, regime='rdfs'
        )
        
        # All original triples should still be present
        for triple in original_triples:
            assert triple in entailed_data


class TestErrorHandling:
    """Test error handling in the preprocessing pipeline."""
    
    def test_invalid_inference_level(self):
        """Test handling of invalid inference level."""
        data_graph = Graph()
        shapes_graph = Graph()
        
        # Should handle gracefully or raise informative error
        with pytest.raises((ValueError, KeyError)):
            pre_process_shacl_graph_full(
                data_graph, shapes_graph, regime='invalid'
            )
    
    def test_empty_graphs(self):
        """Test preprocessing with empty graphs."""
        data_graph = Graph()
        shapes_graph = Graph()
        
        # Should not crash
        entailed_data, entailed_shapes = pre_process_shacl_graph_full(
            data_graph, shapes_graph, regime='none'
        )
        
        assert isinstance(entailed_data, Graph)
        assert isinstance(entailed_shapes, Graph)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
