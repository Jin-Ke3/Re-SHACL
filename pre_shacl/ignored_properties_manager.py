"""Ignored Properties Manager

This module manages the sh:ignoredProperties list for SHACL closed shapes.
Ignored properties are properties that are allowed on a shape's targets
even when the shape is marked as closed.
"""

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, SH
from typing import Set
from pre_shacl.rdf_list_utils import add_element_to_rdf_list


def get_current_ignored_properties(shacl_graph: Graph, shape_uri: URIRef) -> Set:
    """
    Get the current set of ignored properties for a closed SHACL shape.
    
    Args:
        shacl_graph: The SHACL shapes graph
        shape_uri: The URI of the shape
        
    Returns:
        Set of currently ignored property URIs
    """
    current_ignored_properties = set()

    # Get the first ignored property blank node
    ignored_property_node = shacl_graph.value(subject=URIRef(shape_uri),
                                              predicate=SH.ignoredProperties)

    # While there is another member of the list do
    index = 0

    while ignored_property_node != RDF.nil and ignored_property_node is not None:

        # Get the value of the list member
        ignored_property = shacl_graph.value(subject=ignored_property_node,
                                             predicate=RDF.first)

        current_ignored_properties.add(ignored_property)
        # Get the next list member if exists
        ignored_property_node = shacl_graph.value(subject=ignored_property_node,
                                                  predicate=RDF.rest)

        index += 1

        if ignored_property_node is None:
            break

    return current_ignored_properties


def add_ignored_properties_to_graph(shacl_graph: Graph, shape_uri: URIRef, 
                                    ignored_properties: Set) -> Graph:
    """
    Add ignored properties to a SHACL shape as an RDF list.
    
    This replaces any existing ignoredProperties list on the shape.
    
    Args:
        shacl_graph: The SHACL shapes graph
        shape_uri: The URI of the shape
        ignored_properties: Set of property URIs to ignore
        
    Returns:
        The modified SHACL graph
    """
    list_subgraph = Graph()
    index = 0
    num_ignored_properties = len(ignored_properties)
    first_element = None

    for ignored_property in ignored_properties:
        first_element = add_element_to_rdf_list(list_subgraph, first_element, ignored_property)

        index += 1
        # For the last blank node, link it to the ignored properties
        if index == num_ignored_properties:

            # Recursively remove the old ignored properties
            old_ignored_properties = shacl_graph.value(URIRef(shape_uri),
                                                       SH.ignoredProperties)

            if old_ignored_properties is not None and old_ignored_properties != RDF.nil:
                while not old_ignored_properties == RDF.nil:
                    next_ignored_properties = shacl_graph.value(subject=old_ignored_properties,
                                                                predicate=RDF.rest)
                    shacl_graph.remove((old_ignored_properties, None, None))
                    old_ignored_properties = next_ignored_properties

            # Set the new ignored properties
            shacl_graph.set((URIRef(shape_uri),
                             SH.ignoredProperties,
                             first_element))

    # Add all other list values to the original graph
    for s, p, o in list_subgraph.triples((None, None, None)):
        shacl_graph.add((s, p, o))

    return shacl_graph
