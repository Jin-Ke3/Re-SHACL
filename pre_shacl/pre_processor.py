"""SHACL Shape Preprocessor (Backward Compatibility Wrapper)

This module maintains backward compatibility by re-exporting functions from
the refactored module structure. New code should import from specific modules:
- shape_analyzer: Shape analysis functions
- shape_entailer: Shape extension based on entailment
- ignored_properties_manager: Ignored properties management
- rdf_list_utils: RDF list utilities
- shape_preprocessor: Main preprocessing pipeline

For backward compatibility, this module re-exports commonly used functions.
"""

# Re-export main preprocessing function
from pre_shacl.shape_preprocessor import pre_process_shacl_graph_full

# Re-export shape analyzer functions
from pre_shacl.shape_analyzer import (
    list_all_shape_names,
    map_shapes_to_properties,
    get_shape_property_paths,
    get_all_target_classes_for_shape
)

# Re-export shape entailer functions
from pre_shacl.shape_entailer import (
    get_subgraph_for_entailment,
    entail_shape_graph,
    entail_has_value_on_property,
    entail_property_chain_axiom,
    extend_shacl_shape
)

# Re-export ignored properties manager functions
from pre_shacl.ignored_properties_manager import (
    get_current_ignored_properties,
    add_ignored_properties_to_graph
)

# Re-export RDF list utils
from pre_shacl.rdf_list_utils import (
    get_elements_in_rdf_list,
    add_element_to_rdf_list
)

# Re-export incongruence checker
from pre_shacl.shape_preprocessor import check_incongruences

__all__ = [
    "pre_process_shacl_graph_full",
    "list_all_shape_names",
    "map_shapes_to_properties",
    "get_shape_property_paths",
    "get_all_target_classes_for_shape",
    "get_subgraph_for_entailment",
    "entail_shape_graph",
    "entail_has_value_on_property",
    "entail_property_chain_axiom",
    "extend_shacl_shape",
    "get_current_ignored_properties",
    "add_ignored_properties_to_graph",
    "get_elements_in_rdf_list",
    "add_element_to_rdf_list",
    "check_incongruences",
]
