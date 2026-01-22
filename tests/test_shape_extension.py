"""Unit tests for ontology-based shape extension.

Tests the shape extension functionality including subPropertyOf extension,
generated node properties, and idempotence.
"""

import pytest
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDFS, OWL, RDF, SH
from pre_shacl.ontology_shape_entailer import (
    entail_shape_from_ontology,
    extend_shacl_shape_from_ontology,
    mark_generated_node,
    extract_allowed_paths,
    EX as GEN_NS
)
from pre_shacl.ontology_closure import compute_subproperty_closure
from pre_shacl.shape_preprocessor import pre_process_shacl_graph_full

# Test namespaces
EX = Namespace("http://example.org/")


def test_simple_subproperty_extension():
    """Test basic subPropertyOf extension."""
    # Create shapes graph with closed shape
    shapes = Graph()
    shape = EX.PersonShape
    pshape = BNode()
    p_super = EX.authors
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    # Create ontology with subPropertyOf
    ont = Graph()
    p_sub = EX.writes
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    # Preprocess
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    # Extract allowed paths
    allowed = extract_allowed_paths(result, shape)
    
    assert p_super in allowed, "Original property should be present"
    assert p_sub in allowed, "Sub-property should be added"


def test_transitive_subproperty_extension():
    """Test transitive subPropertyOf extension."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    p_top = EX.creates
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_top))
    
    # Create ontology with transitive hierarchy
    ont = Graph()
    p_mid = EX.authors
    p_bottom = EX.writes
    ont.add((p_bottom, RDFS.subPropertyOf, p_mid))
    ont.add((p_mid, RDFS.subPropertyOf, p_top))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    assert p_top in allowed
    assert p_mid in allowed, "Middle property should be added (transitive)"
    assert p_bottom in allowed, "Bottom property should be added (transitive)"


def test_generated_nodes_are_path_only():
    """Test generated property shapes have only sh:path and generation marker."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    p_super = EX.authors
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    shapes.add((pshape, SH.minCount, Literal(1)))  # existing constraint
    
    ont = Graph()
    p_sub = EX.writes
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    # Find generated nodes
    for _, _, gen_node in result.triples((shape, SH.property, None)):
        if result.value(gen_node, GEN_NS.generatedBy):
            path = result.value(gen_node, SH.path)
            assert path == p_sub, "Generated node should have correct path"
            
            # Count predicates on generated node
            predicates = set(p for _, p, _ in result.triples((gen_node, None, None)))
            # Should only have sh:path and ex:generatedBy
            assert predicates == {SH.path, GEN_NS.generatedBy}, \
                f"Generated node should only have sh:path and generatedBy, got {predicates}"


def test_idempotence():
    """Test that preprocessing twice yields no changes."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    p_super = EX.authors
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    ont = Graph()
    p_sub = EX.writes
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    # First preprocessing
    result1 = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed1 = extract_allowed_paths(result1, shape)
    
    # Second preprocessing (on already processed graph)
    result2 = pre_process_shacl_graph_full(result1, ont, "rdfs")
    allowed2 = extract_allowed_paths(result2, shape)
    
    # Allowed paths should be identical
    assert allowed1 == allowed2, "Allowed paths should not change on second preprocessing"
    
    # Graph size should not grow
    assert len(result1) == len(result2), "Graph should not grow on second preprocessing"


def test_no_duplicate_paths():
    """Test that duplicate paths are not added."""
    shapes = Graph()
    shape = EX.Shape1
    pshape1 = BNode()
    pshape2 = BNode()
    p_super = EX.authors
    
    # Add same property twice (edge case)
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape1))
    shapes.add((pshape1, SH.path, p_super))
    shapes.add((shape, SH.property, pshape2))
    shapes.add((pshape2, SH.path, p_super))
    
    ont = Graph()
    p_sub = EX.writes
    ont.add((p_sub, RDFS.subPropertyOf, p_super))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    # Should have properties + rdf:type (added automatically by rdfs regime)
    assert p_super in allowed
    assert p_sub in allowed
    assert RDF.type in allowed  # Added automatically for rdfs regime
    assert len(allowed) == 3


def test_ignored_properties_not_added():
    """Test that properties in ignoredProperties are not added as sub-properties."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    p_super = EX.authors
    p_ignored = EX.writes
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p_super))
    
    # Add to ignored properties
    ignored_list = BNode()
    shapes.add((shape, SH.ignoredProperties, ignored_list))
    shapes.add((ignored_list, RDF.first, p_ignored))
    shapes.add((ignored_list, RDF.rest, RDF.nil))
    
    ont = Graph()
    ont.add((p_ignored, RDFS.subPropertyOf, p_super))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    # p_ignored should be in allowed (from ignoredProperties)
    # but should not be added again as a property shape
    assert p_ignored in allowed, "Ignored property should be in allowed set"
    
    # Count property shapes with p_ignored path
    count = 0
    for _, _, prop_node in result.triples((shape, SH.property, None)):
        path = result.value(prop_node, SH.path)
        if path == p_ignored:
            count += 1
    
    assert count == 0, "Ignored property should not be added as property shape"


def test_multiple_shapes():
    """Test preprocessing with multiple closed shapes."""
    shapes = Graph()
    
    # Shape 1
    shape1 = EX.Shape1
    pshape1 = BNode()
    shapes.add((shape1, RDF.type, SH.NodeShape))
    shapes.add((shape1, SH.closed, Literal(True)))
    shapes.add((shape1, SH.property, pshape1))
    shapes.add((pshape1, SH.path, EX.prop1))
    
    # Shape 2
    shape2 = EX.Shape2
    pshape2 = BNode()
    shapes.add((shape2, RDF.type, SH.NodeShape))
    shapes.add((shape2, SH.closed, Literal(True)))
    shapes.add((shape2, SH.property, pshape2))
    shapes.add((pshape2, SH.path, EX.prop2))
    
    # Ontology
    ont = Graph()
    ont.add((EX.subProp1, RDFS.subPropertyOf, EX.prop1))
    ont.add((EX.subProp2, RDFS.subPropertyOf, EX.prop2))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    
    allowed1 = extract_allowed_paths(result, shape1)
    allowed2 = extract_allowed_paths(result, shape2)
    
    assert EX.prop1 in allowed1
    assert EX.subProp1 in allowed1
    assert EX.prop2 in allowed2
    assert EX.subProp2 in allowed2


def test_open_shape_not_modified():
    """Test that non-closed shapes are not modified."""
    shapes = Graph()
    shape = EX.OpenShape
    pshape = BNode()
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    # Note: sh:closed NOT set
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, EX.authors))
    
    ont = Graph()
    ont.add((EX.writes, RDFS.subPropertyOf, EX.authors))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    # Only original property should be present
    assert EX.authors in allowed
    assert EX.writes not in allowed, "Sub-property should not be added to open shape"


def test_no_ontology_no_changes():
    """Test that without ontology relationships, no changes occur."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, EX.authors))
    
    # Empty ontology
    ont = Graph()
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    # Original property + rdf:type (added automatically for rdfs regime)
    assert EX.authors in allowed
    assert RDF.type in allowed
    assert len(allowed) == 2


def test_equivalent_property_extension():
    """Test that owl:equivalentProperty results in property addition."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    p1 = EX.author
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, p1))
    
    ont = Graph()
    p2 = EX.creator
    ont.add((p1, OWL.equivalentProperty, p2))
    
    result = pre_process_shacl_graph_full(shapes, ont, "rdfs")
    allowed = extract_allowed_paths(result, shape)
    
    # Both properties should be allowed (equivalence is bidirectional)
    assert p1 in allowed
    assert p2 in allowed


def test_extract_allowed_paths_with_ignored():
    """Test extract_allowed_paths includes both property paths and ignored properties."""
    shapes = Graph()
    shape = EX.Shape1
    pshape = BNode()
    
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.closed, Literal(True)))
    shapes.add((shape, SH.property, pshape))
    shapes.add((pshape, SH.path, EX.prop1))
    
    # Add ignored properties list
    ignored_list = BNode()
    node1 = BNode()
    shapes.add((shape, SH.ignoredProperties, ignored_list))
    shapes.add((ignored_list, RDF.first, EX.ignored1))
    shapes.add((ignored_list, RDF.rest, node1))
    shapes.add((node1, RDF.first, EX.ignored2))
    shapes.add((node1, RDF.rest, RDF.nil))
    
    allowed = extract_allowed_paths(shapes, shape)
    
    assert EX.prop1 in allowed
    assert EX.ignored1 in allowed
    assert EX.ignored2 in allowed
    assert len(allowed) == 3
