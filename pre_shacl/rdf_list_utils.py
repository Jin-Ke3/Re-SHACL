"""RDF List Utilities

This module provides utilities for working with RDF lists (rdf:List).
RDF lists are represented as linked structures using rdf:first and rdf:rest properties.
"""

from rdflib import Graph, RDF, BNode
from typing import List


def get_elements_in_rdf_list(graph: Graph, rdf_list) -> List:
    """
    Extract all elements from an RDF list.
    
    Args:
        graph: The RDF graph containing the list
        rdf_list: The starting node of the RDF list
        
    Returns:
        List of all elements in the RDF list
    """
    current_element = rdf_list
    elements = []
    if current_element is not None:
        while current_element != RDF.nil:
            current_value = graph.value(subject=current_element, predicate=RDF.first)
            elements.append(current_value)
            current_element = graph.value(subject=current_element, predicate=RDF.rest)

            if current_element is None:
                break

    return elements


def add_element_to_rdf_list(graph: Graph, rdf_list, element):
    """
    Add an element to an RDF list.
    
    Args:
        graph: The RDF graph to add the element to
        rdf_list: The existing RDF list (or None to create a new list)
        element: The element to add
        
    Returns:
        The head of the RDF list (either the original rdf_list or the new list head)
    """
    # Traverse to last element
    current_element = rdf_list

    # Create new list blank node
    new_element = BNode()

    # Add value to list element
    graph.add((new_element, RDF.first, element))

    # Make new list element end of list
    graph.add((new_element, RDF.rest, RDF.nil))

    if current_element is not None:
        while graph.value(subject=current_element, predicate=RDF.rest) != RDF.nil:
            current_element = graph.value(subject=current_element, predicate=RDF.rest)

        # Add new element to end of list
        graph.set((current_element, RDF.rest, new_element))
    else:
        return new_element

    return rdf_list
