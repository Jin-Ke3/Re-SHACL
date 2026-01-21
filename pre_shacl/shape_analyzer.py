"""Shape Analyzer

This module provides functions for analyzing SHACL shape graphs,
extracting shape information, and querying shape properties.
"""

from rdflib import Graph, URIRef, RDFS
from rdflib.namespace import RDF, SH
from typing import Set, Dict


def list_all_shape_names(shacl_graph: Graph) -> Set[URIRef]:
    """
    Return a set of all SHACL NodeShape URIs in the graph.
    
    Args:
        shacl_graph: The SHACL shapes graph
        
    Returns:
        Set of all NodeShape URIs
    """
    shape_names = set()
    for s, p, o in shacl_graph.triples((None, RDF.type, SH.NodeShape)):
        shape_names.add(s)
    return shape_names


def map_shapes_to_properties(shacl_graph: Graph, shape_names: Set[URIRef]) -> Dict[URIRef, Set]:
    """
    Create a mapping from each shape to its property shapes.
    
    Args:
        shacl_graph: The SHACL shapes graph
        shape_names: Set of shape URIs to analyze
        
    Returns:
        Dictionary mapping shape URIs to sets of property shape nodes
    """
    shape_with_properties = {}
    for shape in shape_names:
        property_shapes = set(shacl_graph.objects(URIRef(shape), SH.property))
        shape_with_properties[shape] = property_shapes

    return shape_with_properties


def get_shape_property_paths(shacl_graph: Graph, shape_names: Set[URIRef], 
                             shape_with_properties: Dict[URIRef, Set]) -> Dict[URIRef, Set]:
    """
    Extract property paths for each shape from its property shapes.
    
    Args:
        shacl_graph: The SHACL shapes graph
        shape_names: Set of shape URIs to analyze
        shape_with_properties: Mapping from shapes to their property shape nodes
        
    Returns:
        Dictionary mapping shape URIs to sets of property paths
    """
    shape_property_paths = {}
    for shape in shape_names:
        property_paths = set()
        for property_shape in shape_with_properties[shape]:
            property_path = shacl_graph.value(property_shape, SH.path)
            property_paths.add(property_path)
        shape_property_paths[shape] = property_paths

    return shape_property_paths


def get_all_target_classes_for_shape(shape: URIRef, shacl_graph: Graph) -> Set:
    """
    Get all target classes for a SHACL shape.
    
    This includes:
    - Direct targetClass specifications
    - Classes derived from targetSubjectsOf with domain
    - Classes derived from targetObjectsOf with range
    
    Args:
        shape: The shape URI
        shacl_graph: The SHACL shapes graph
        
    Returns:
        Set of target class URIs
    """
    target_classes = set()

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetClass, None)):
        target_classes.add(target_property)

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetSubjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.domain, None)):
            target_classes.add(class_name)

    for _, _, target_property in shacl_graph.triples((URIRef(shape), SH.targetObjectsOf, None)):
        for _, _, class_name in shacl_graph.triples((target_property, RDFS.range, None)):
            target_classes.add(class_name)

    return target_classes
