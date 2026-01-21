"""Shape Entailer

This module extends SHACL shapes based on semantic entailment in the data graph.
It adds new property shapes to closed shapes based on inferred relationships.
"""

import logging
from rdflib import Graph, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS, SH
from typing import Set, Tuple
from pre_shacl.EntailEngine import InferenceLevel
from pre_shacl.rdf_list_utils import get_elements_in_rdf_list
from pre_shacl.shape_analyzer import get_all_target_classes_for_shape

logger = logging.getLogger(__name__)


def get_subgraph_for_entailment(data_graph: Graph, regime: str) -> Graph:
    """
    Extract relevant triples for entailment based on the inference regime.
    
    Args:
        data_graph: The entailed data graph
        regime: The inference regime (rdfs, owl-ld, owlrl)
        
    Returns:
        Subgraph containing only relevant entailment triples
    """
    subgraph = Graph()

    for s, p, o in data_graph.triples((None, RDFS.subPropertyOf, None)):
        subgraph.add((s, p, o))

    if regime == InferenceLevel.RDFS.value:
        return subgraph

    elif regime in (InferenceLevel.OWL_LD.value, InferenceLevel.OWLRL.value):
        for s, p, o in data_graph.triples((None, OWL.sameAs, None)):
            subgraph.add((s, p, o))

    return subgraph


def entail_shape_graph(data_graph: Graph, regime: str, shacl_graph: Graph, 
                      shape_properties: Set, property_shape: URIRef, 
                      shape: URIRef, old_ignored_properties: Set) -> Tuple[Graph, Set]:
    """
    Add new property shapes based on entailment in the data graph.
    
    Args:
        data_graph: The entailed data graph
        regime: The inference regime
        shacl_graph: The SHACL shapes graph
        shape_properties: Set of current property paths for the shape
        property_shape: The property shape node to extend from
        shape: The shape URI
        old_ignored_properties: Previously ignored properties
        
    Returns:
        Tuple of (modified SHACL graph, updated property set)
    """
    subgraph = get_subgraph_for_entailment(data_graph, regime)
    property_shape_path = shacl_graph.value(property_shape, SH.path)

    for dg_s, dg_p, dg_o in subgraph.triples((None, None, URIRef(property_shape_path))):
        # Check if the new property is not already in the shape properties
        if dg_s not in shape_properties and dg_s not in old_ignored_properties:
            # Create a new property shape
            property_node = BNode()
            shacl_graph.add((URIRef(shape), SH.property, property_node))
            # Add the path
            shacl_graph.add((property_node, SH.path, dg_s))

            shape_properties.add(dg_s)
            logger.info(f"Added new property path {dg_s}")

    return shacl_graph, shape_properties


def entail_has_value_on_property(data_graph: Graph, shape: URIRef, 
                                 shacl_graph: Graph, shape_properties: Set) -> Tuple[Graph, Set]:
    """
    Add property shapes based on OWL hasValue restrictions.
    
    Args:
        data_graph: The entailed data graph
        shape: The shape URI
        shacl_graph: The SHACL shapes graph
        shape_properties: Set of current property paths for the shape
        
    Returns:
        Tuple of (modified SHACL graph, updated property set)
    """
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    if not target_classes:
        return shacl_graph, shape_properties

    for target_class in target_classes:
        for _, _, superclass_name in data_graph.triples((URIRef(target_class),
                                                         RDFS.subClassOf,
                                                         None)):

            on_property_value = data_graph.value(subject=superclass_name, predicate=OWL.onProperty)
            if on_property_value in shape_properties:
                continue

            bn_has_value_exists = data_graph.value(subject=superclass_name, predicate=OWL.hasValue) is not None
            bn_on_property_exists = on_property_value is not None

            if bn_has_value_exists and bn_on_property_exists:
                property_node = BNode()
                shacl_graph.add((URIRef(shape), SH.property, property_node))
                shacl_graph.add((property_node, SH.path, on_property_value))
                shape_properties.add(on_property_value)
                logger.info(f"Added new property path {on_property_value}")

    return shacl_graph, shape_properties


def entail_property_chain_axiom(data_graph: Graph, shacl_graph: Graph, 
                                shape: URIRef, shape_properties: Set) -> Tuple[Graph, Set]:
    """
    Add property shapes based on OWL property chain axioms.
    
    Args:
        data_graph: The entailed data graph
        shacl_graph: The SHACL shapes graph
        shape: The shape URI
        shape_properties: Set of current property paths for the shape
        
    Returns:
        Tuple of (modified SHACL graph, updated property set)
    """
    # Get the first element of the list and if it matches, add s to the SHACL shape
    for new_property, p, list_of_elements in data_graph.triples((None,
                                                                 OWL.propertyChainAxiom,
                                                                 None)):
        if new_property in shape_properties:
            continue

        elements = get_elements_in_rdf_list(data_graph, list_of_elements)

        # This says that if the first element of a property chain is in the list of elements
        # That we can assume that the whole chain occurs - because the probability is larger than zero
        # This cannot cause violations - it can cause additional properties, however
        if elements[0] in shape_properties:
            property_node = BNode()
            shacl_graph.add((URIRef(shape), SH.property, property_node))
            shacl_graph.add((property_node, SH.path, new_property))
            shape_properties.add(new_property)
            logger.info(f"Added new property path {new_property}")

    return shacl_graph, shape_properties


def extend_shacl_shape(shape: URIRef, property_blank_nodes: Set, shacl_graph: Graph, 
                      shape_properties: Set, data_graph: Graph, regime: str, 
                      old_ignored_properties: Set) -> Graph:
    """
    Extend a SHACL shape with additional property shapes based on entailment.
    
    Args:
        shape: The shape URI
        property_blank_nodes: Set of existing property shape nodes
        shacl_graph: The SHACL shapes graph
        shape_properties: Set of current property paths
        data_graph: The entailed data graph
        regime: The inference regime
        old_ignored_properties: Previously ignored properties
        
    Returns:
        The modified SHACL graph
    """
    for property_shape in property_blank_nodes:
        shacl_graph, shape_properties = entail_shape_graph(data_graph, regime, shacl_graph, shape_properties,
                                                           property_shape, shape, old_ignored_properties)

    # Only in case of owlrl extra work is needed
    if regime == InferenceLevel.OWLRL.value:
        shacl_graph, shape_properties = entail_property_chain_axiom(data_graph, shacl_graph, shape,
                                                                    shape_properties)
        shacl_graph, shape_properties = entail_has_value_on_property(data_graph, shape, shacl_graph,
                                                                     shape_properties)

    return shacl_graph
