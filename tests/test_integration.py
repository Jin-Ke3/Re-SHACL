"""Integration Tests for Pre-SHACL Preprocessing Pipeline

This module tests the complete preprocessing workflow using ontology-based
shape extension (no data graph entailment).
"""

import pytest
from rdflib import Graph, Namespace, RDF, RDFS, OWL, SH, Literal, URIRef
from rdflib.namespace import XSD
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pre_shacl.ontology_shape_entailer import extract_allowed_paths
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
    """Test the ontology-based shape preprocessing pipeline."""
    
    def test_simple_ontology_preprocessing(self):
        """Test basic ontology-based shape extension."""
        # Create ontology with property hierarchy
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.nickname, RDFS.subPropertyOf, EX.name))
        
        # Create closed shape
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        # Property shape for name
        prop_node = URIRef(EX.PersonShape_name)
        shapes_graph.add((EX.PersonShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.name))
        
        # Run preprocessing (shapes only, not data)
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='rdfs'
        )
        
        # Verify shape was extended with sub-property
        allowed = extract_allowed_paths(entailed_shapes, EX.PersonShape)
        assert EX.name in allowed
        assert EX.nickname in allowed, "Sub-property should be added to closed shape"
    
    def test_owl_equivalent_property_preprocessing(self):
        """Test shape extension with owl:equivalentProperty."""
        # Create ontology with equivalent properties
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.author, OWL.equivalentProperty, EX.creator))
        
        # Create shape
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.BookShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.BookShape, SH.targetClass, EX.Book))
        shapes_graph.add((EX.BookShape, SH.closed, Literal(True)))
        
        prop_node = URIRef(EX.BookShape_author)
        shapes_graph.add((EX.BookShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.author))
        
        # Run preprocessing
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='rdfs'
        )
        
        # Verify equivalent property added
        allowed = extract_allowed_paths(entailed_shapes, EX.BookShape)
        assert EX.author in allowed
        assert EX.creator in allowed, "Equivalent property should be added"
    
    def test_closed_shape_transitive_extension(self):
        """Test that closed shapes handle transitive sub-properties."""
        # Create ontology with transitive hierarchy
        ontology = Graph()
        ontology.bind("ex", EX)
        ontology.add((EX.writes, RDFS.subPropertyOf, EX.authors))
        ontology.add((EX.pens, RDFS.subPropertyOf, EX.writes))
        
        # Create closed shape
        shapes_graph = Graph()
        shapes_graph.bind("ex", EX)
        shapes_graph.add((EX.PersonShape, RDF.type, SH.NodeShape))
        shapes_graph.add((EX.PersonShape, SH.targetClass, EX.Person))
        shapes_graph.add((EX.PersonShape, SH.closed, Literal(True)))
        
        prop_node = URIRef(EX.PersonShape_authors)
        shapes_graph.add((EX.PersonShape, SH.property, prop_node))
        shapes_graph.add((prop_node, SH.path, EX.authors))
        
        # Run preprocessing
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='rdfs'
        )
        
        # Verify transitive closure
        allowed = extract_allowed_paths(entailed_shapes, EX.PersonShape)
        assert EX.authors in allowed
        assert EX.writes in allowed, "Direct sub-property should be added"
        assert EX.pens in allowed, "Transitive sub-property should be added"
    
    def test_ignored_properties_management(self):
        """Test that ignored properties are handled correctly per regime."""
        ontology = Graph()
        
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
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='owl-ld'
        )
        
        # Verify shape has sh:ignoredProperties
        has_ignored = any(
            entailed_shapes.triples((EX.PersonShape, SH.ignoredProperties, None))
        )
        assert has_ignored, "Shape should have sh:ignoredProperties"
        
        # Check that owl:sameAs is in ignored list
        for _, _, ignored_list in entailed_shapes.triples((EX.PersonShape, SH.ignoredProperties, None)):
            items = list(entailed_shapes.items(ignored_list))
            assert OWL.sameAs in items


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
        return os.path.join(os.path.dirname(__file__), "fixtures")
    
    def test_person_closed_shape_fixture(self, fixtures_dir):
        """Test preprocessing with the person closed shape fixture."""
        shape_path = os.path.join(fixtures_dir, "person_shape_closed.ttl")
        
        if not os.path.exists(shape_path):
            pytest.skip("Fixture files not found")
        
        shapes_graph = load_turtle_graph(shape_path)
        ontology = Graph()  # Empty ontology for basic test
        
        # Run preprocessing
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='rdfs'
        )
        
        # Basic sanity checks
        assert len(entailed_shapes) >= len(shapes_graph)
    
    def test_preprocessing_preserves_original_shapes(self):
        """Test that preprocessing doesn't destroy original shape triples."""
        original_shapes = Graph()
        original_shapes.bind("ex", EX)
        original_shapes.add((EX.PersonShape, RDF.type, SH.NodeShape))
        original_shapes.add((EX.PersonShape, SH.targetClass, EX.Person))
        original_shapes.add((EX.PersonShape, SH.closed, Literal(True)))
        
        original_triples = set(original_shapes)
        
        ontology = Graph()
        
        entailed_shapes = pre_process_shacl_graph_full(
            original_shapes, ontology, regime='rdfs'
        )
        
        # All original triples should still be present
        for triple in original_triples:
            assert triple in entailed_shapes


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
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph, ontology, regime='none'
        )
        
        assert isinstance(entailed_shapes, Graph)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
