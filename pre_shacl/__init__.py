"""
PreSHACL: SHACL Shape Preprocessing and Entailment

This package provides tools for preprocessing SHACL shapes graphs with semantic entailment,
enabling more comprehensive validation of RDF data graphs.

Main Components:
- pre_processor: Core preprocessing pipeline for SHACL shapes
- rdfs_entailment: RDFS entailment rule implementation
- owl_entailment: OWL entailment rule implementation
- EntailEngine: Unified entailment engine with configurable inference levels

Public API:
    pre_process_shacl_graph_full: Main entrypoint for preprocessing SHACL graphs
"""

from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pre_shacl.EntailEngine import EntailEngine, InferenceLevel
from pre_shacl import rdfs_entailment, owl_entailment

__version__ = "0.1.0"

__all__ = [
    "pre_process_shacl_graph_full",
    "EntailEngine",
    "InferenceLevel",
    "rdfs_entailment",
    "owl_entailment",
]
