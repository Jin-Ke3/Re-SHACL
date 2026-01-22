"""Legacy Compatibility Layer for PreSHACL Migration

This module provides backward-compatible wrappers that match the old PreSHACL
behavior of processing both data and shapes together. The new pre_shacl module
separates concerns:
- Data entailment: EntailEngine
- Shape preprocessing: pre_process_shacl_graph_full (ontology-based only)

This compatibility layer combines them to match old behavior for existing code.
New code should use the separated functions directly.
"""

from typing import Tuple
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, SH

from pre_shacl.EntailEngine import EntailEngine, InferenceLevel
from pre_shacl.shape_entailer import (
    extend_shacl_shape,
    get_subgraph_for_entailment
)
from pre_shacl.shape_analyzer import (
    list_all_shape_names,
    map_shapes_to_properties,
    get_shape_property_paths
)
from pre_shacl.ignored_properties_manager import (
    get_current_ignored_properties,
    add_ignored_properties_to_graph
)


def pre_process_shacl_graph_full_legacy(
    data_graph: Graph, 
    shacl_graph: Graph, 
    regime: str
) -> Tuple[Graph, Graph]:
    """
    Legacy wrapper that processes both data and shapes (PreSHACL behavior).
    
    This function mimics the old PreSHACL.pre_processor.pre_process_shacl_graph_full
    behavior by:
    1. Entailing the data graph based on the inference regime
    2. Extending closed shapes based on data-driven entailment
    3. Managing ignoredProperties
    
    Args:
        data_graph: The RDF data graph to entail
        shacl_graph: The SHACL shapes graph
        regime: Inference regime ('none', 'rdfs', 'owl-ld', 'owlrl')
        
    Returns:
        Tuple of (entailed_data_graph, extended_shapes_graph)
        
    Note:
        New code should use:
        - EntailEngine(data_graph, regime).entail() for data entailment
        - pre_process_shacl_graph_full(shacl_graph, ontology_graph, regime) for ontology-based shape preprocessing
    """
    if regime == InferenceLevel.NONE.value:
        return data_graph, shacl_graph

    ignored_properties = set()
    if regime == InferenceLevel.RDFS.value:
        ignored_properties.add(RDF.type)
    if regime == InferenceLevel.OWL_LD.value:
        ignored_properties.add(OWL.sameAs)

    # Entail data graph
    engine = EntailEngine(data_graph, regime)
    entailed_data_graph = engine.entail()
    if entailed_data_graph:
        data_graph = entailed_data_graph
    else:
        return data_graph, shacl_graph

    # Extend shapes based on data
    shape_names = list_all_shape_names(shacl_graph)
    shape_with_properties = map_shapes_to_properties(shacl_graph, shape_names)
    shape_property_paths = get_shape_property_paths(shacl_graph, shape_names, shape_with_properties)
    
    for shape_uri in shape_names:
        if not shacl_graph.value(URIRef(shape_uri), SH.closed):
            continue

        old_ignored_properties = get_current_ignored_properties(shacl_graph, shape_uri)

        # Extend shape based on data-driven entailment
        shacl_graph = extend_shacl_shape(
            shape_uri, 
            shape_with_properties[shape_uri], 
            shacl_graph,
            shape_property_paths[shape_uri], 
            data_graph, 
            regime, 
            old_ignored_properties
        )

        ignored_properties = set(ignored_properties).union(set(old_ignored_properties))
        ignored_properties = set([x for x in ignored_properties if x not in shape_property_paths[shape_uri]])
        shacl_graph = add_ignored_properties_to_graph(shacl_graph, shape_uri, ignored_properties)
        ignored_properties = set()

    return data_graph, shacl_graph
