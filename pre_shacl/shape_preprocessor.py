"""Shape Preprocessor - Main Orchestrator

This module provides the main preprocessing pipeline for SHACL shapes graphs.
It coordinates entailment, shape analysis, and shape extension for closed shapes.
"""

import logging
from rdflib import Graph, URIRef, RDFS
from rdflib.namespace import OWL, RDF, SH
from typing import Tuple, List, Set
from pre_shacl.EntailEngine import EntailEngine, InferenceLevel
from pre_shacl.shape_analyzer import (
    list_all_shape_names,
    map_shapes_to_properties,
    get_shape_property_paths,
    get_all_target_classes_for_shape
)
from pre_shacl.shape_entailer import extend_shacl_shape
from pre_shacl.ignored_properties_manager import (
    get_current_ignored_properties,
    add_ignored_properties_to_graph
)

logger = logging.getLogger(__name__)


def check_incongruences(shape: URIRef, data_graph: Graph, shacl_graph: Graph, 
                       shape_properties: Set) -> List[str]:
    """
    Check for potential incongruences in closed shape definitions.
    
    This identifies situations where closed shapes might be too restrictive,
    such as:
    - Target classes that are superclasses (subclasses might have additional properties)
    - Properties with domain matching target class but not included in shape
    
    Args:
        shape: The shape URI
        data_graph: The data graph
        shacl_graph: The SHACL shapes graph
        shape_properties: Set of property paths in the shape
        
    Returns:
        List of warning messages
    """
    warning_messages = []
    target_classes = get_all_target_classes_for_shape(shape, shacl_graph)

    # subclass inconsistency
    for target_class in target_classes:
        for class_name, _, _ in data_graph.triples((None, RDFS.subClassOf, target_class)):
            warning_messages.append(
                f"{target_class} is a super-class of {class_name}, using this as the target class "
                f"for a SHACL closed shape {shape} could lead to incongruences."
            )

        for property_name, _, _ in data_graph.triples((None, RDFS.domain, target_class)):
            if property_name not in shape_properties:
                warning_messages.append(
                    f"Property {property_name} was not found in the property constraints for "
                    f"shape {shape} with {target_class}. Since {target_class} is the domain of "
                    f"{property_name}, this could lead to incongruences."
                )

    return warning_messages


def pre_process_shacl_graph_full(data_graph: Graph, shacl_graph: Graph, regime: str) -> Tuple[Graph, Graph]:
    """
    Preprocess SHACL shapes graph with entailment-based extension for closed shapes.
    
    This is the main entry point for SHACL preprocessing. It:
    1. Applies semantic entailment to the data graph based on the regime
    2. Analyzes all closed shapes in the SHACL graph
    3. Extends closed shapes with additional property shapes based on entailed relationships
    4. Updates ignoredProperties lists to match the inference regime
    5. Checks for potential incongruences
    
    Args:
        data_graph: The RDF data graph to validate
        shacl_graph: The SHACL shapes graph
        regime: The inference regime ('none', 'rdfs', 'owl-ld', 'owlrl')
        
    Returns:
        Tuple of (entailed data graph, extended shapes graph)
        
    Raises:
        ValueError: If an invalid regime is provided
    """
    # Validate regime
    valid_regimes = {level.value for level in InferenceLevel}
    if regime not in valid_regimes:
        raise ValueError(f"Invalid regime '{regime}'. Must be one of: {', '.join(valid_regimes)}")
    
    if regime == InferenceLevel.NONE.value:
        return data_graph, shacl_graph

    warning_messages = []

    ignored_properties = set()
    if regime == InferenceLevel.RDFS.value:
        ignored_properties.add(RDF.type)
    if regime == InferenceLevel.OWL_LD.value:
        ignored_properties.add(OWL.sameAs)

    engine = EntailEngine(data_graph, regime)
    # The engine entails the data graph given a regime
    entailed_data_graph = engine.entail()
    if entailed_data_graph:
        data_graph = entailed_data_graph
    else:
        return data_graph, shacl_graph

    shape_names = list_all_shape_names(shacl_graph)
    shape_with_properties = map_shapes_to_properties(shacl_graph, shape_names)
    shape_property_paths = get_shape_property_paths(shacl_graph, shape_names, shape_with_properties)
    
    for shape_uri in shape_names:
        if not shacl_graph.value(URIRef(shape_uri), SH.closed):
            continue

        old_ignored_properties = get_current_ignored_properties(shacl_graph, shape_uri)

        warning_messages += check_incongruences(shape_uri, data_graph, shacl_graph, shape_property_paths[shape_uri])
        shacl_graph = extend_shacl_shape(shape_uri, shape_with_properties[shape_uri], shacl_graph,
                                         shape_property_paths[shape_uri], data_graph, regime, old_ignored_properties)

        ignored_properties = set(ignored_properties).union(set(old_ignored_properties))
        ignored_properties = set([x for x in ignored_properties if x not in shape_property_paths[shape_uri]])
        shacl_graph = add_ignored_properties_to_graph(shacl_graph, shape_uri, ignored_properties)
        ignored_properties = set()

    if warning_messages:
        logger.warning(f"{regime} entailment found the following incongruences in the data graph (WARNING):")
        for warning in warning_messages:
            logger.warning(warning)

    return data_graph, shacl_graph
