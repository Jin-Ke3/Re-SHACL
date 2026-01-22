"""Shape Preprocessor - Main Orchestrator

This module provides the main preprocessing pipeline for SHACL shapes graphs.
It coordinates entailment, shape analysis, and shape extension for closed shapes.
"""

import logging
from rdflib import Graph, URIRef, RDFS
from rdflib.namespace import OWL, RDF, SH
from typing import Tuple, List, Set
from pre_shacl.EntailEngine import InferenceLevel
from pre_shacl.shape_analyzer import (
    list_all_shape_names,
    map_shapes_to_properties,
    get_shape_property_paths,
    get_all_target_classes_for_shape
)
from pre_shacl.ontology_shape_entailer import extend_shacl_shape_from_ontology
from pre_shacl.ontology_closure import compute_subproperty_closure
from pre_shacl.ignored_properties_manager import (
    get_current_ignored_properties,
    add_ignored_properties_to_graph
)

logger = logging.getLogger(__name__)


def check_incongruences(shape: URIRef, ontology_graph: Graph, shacl_graph: Graph, 
                       shape_properties: Set) -> List[str]:
    """
    Check for potential incongruences in closed shape definitions.
    
    This identifies situations where closed shapes might be too restrictive,
    such as:
    - Target classes that are superclasses (subclasses might have additional properties)
    - Properties with domain matching target class but not included in shape
    
    Args:
        shape: The shape URI
        ontology_graph: The ontology graph
        shacl_graph: The SHACL shapes graph
        shape_properties: Set of property paths in the shape
        
    Returns:
        List of warning messages
    """
    warning_messages = []
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    # subclass inconsistency
    for target_class in target_classes:
        for class_name, _, _ in ontology_graph.triples((None, RDFS.subClassOf, target_class)):
            warning_messages.append(
                f"{target_class} is a super-class of {class_name}, using this as the target class "
                f"for a SHACL closed shape {shape} could lead to incongruences."
            )

        for property_name, _, _ in ontology_graph.triples((None, RDFS.domain, target_class)):
            if property_name not in shape_properties:
                warning_messages.append(
                    f"Property {property_name} was not found in the property constraints for "
                    f"shape {shape} with {target_class}. Since {target_class} is the domain of "
                    f"{property_name}, this could lead to incongruences."
                )

    return warning_messages


def pre_process_shacl_graph_full(shacl_graph: Graph, ontology_graph: Graph, regime: str) -> Graph:
    """
    Preprocess SHACL shapes graph with ontology-based extension for closed shapes.
    
    This is the main entry point for SHACL preprocessing. It:
    1. Computes property closure from ontology (TBox)
    2. Analyzes all closed shapes in the SHACL graph
    3. Extends closed shapes with additional property shapes based on ontology relationships
    4. Updates ignoredProperties lists to match the inference regime
    5. Checks for potential incongruences
    
    NOTE: The ontology graph is NOT entailed - it is used as-is.
    NOTE: The data graph is NOT used - all entailment is ontology-based (TBox only).
    
    Args:
        shacl_graph: The SHACL shapes graph
        ontology_graph: The ontology graph (TBox)
        regime: The inference regime ('none', 'rdfs', 'owl-ld', 'owlrl')
        
    Returns:
        Extended shapes graph (copy-on-write)
        
    Raises:
        ValueError: If an invalid regime is provided
    """
    # Validate regime
    valid_regimes = {level.value for level in InferenceLevel}
    if regime not in valid_regimes:
        raise ValueError(f"Invalid regime '{regime}'. Must be one of: {', '.join(valid_regimes)}")
    
    if regime == InferenceLevel.NONE.value:
        return shacl_graph

    # Copy-on-write: create fresh output graph
    result_graph = Graph()
    result_graph += shacl_graph
    shacl_graph = result_graph

    warning_messages = []

    ignored_properties = set()
    if regime == InferenceLevel.RDFS.value:
        ignored_properties.add(RDF.type)
    if regime == InferenceLevel.OWL_LD.value:
        ignored_properties.add(OWL.sameAs)

    # Precompute property closure from ontology
    logger.info(f"Computing property closure from ontology for regime '{regime}'")
    subprop_closure = compute_subproperty_closure(ontology_graph)
    logger.info(f"Computed closure for {len(subprop_closure)} properties")

    shape_names = list_all_shape_names(shacl_graph)
    shape_with_properties = map_shapes_to_properties(shacl_graph, shape_names)
    shape_property_paths = get_shape_property_paths(shacl_graph, shape_names, shape_with_properties)
    
    for shape_uri in shape_names:
        if not shacl_graph.value(URIRef(shape_uri), SH.closed):
            continue

        old_ignored_properties = get_current_ignored_properties(shacl_graph, shape_uri)

        warning_messages += check_incongruences(shape_uri, ontology_graph, shacl_graph, shape_property_paths[shape_uri])
        shacl_graph = extend_shacl_shape_from_ontology(shape_uri, shape_with_properties[shape_uri], shacl_graph,
                                                       shape_property_paths[shape_uri], ontology_graph, regime, 
                                                       old_ignored_properties, subprop_closure)

        ignored_properties = set(ignored_properties).union(set(old_ignored_properties))
        ignored_properties = set([x for x in ignored_properties if x not in shape_property_paths[shape_uri]])
        shacl_graph = add_ignored_properties_to_graph(shacl_graph, shape_uri, ignored_properties)
        ignored_properties = set()

    if warning_messages:
        logger.warning(f"{regime} entailment found the following incongruences in the ontology (WARNING):")
        for warning in warning_messages:
            logger.warning(warning)

    return shacl_graph
