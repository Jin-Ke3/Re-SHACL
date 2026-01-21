"""Experiment Configuration Management

This module provides configuration classes for SHACL validation experiments.
"""

from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path


@dataclass
class ExperimentConfig:
    """
    Configuration settings for validation experiments.
    
    Attributes:
        num_repetitions: Number of times to repeat each validation run.
        time_multiplier: Multiplier for timing results (for unit conversion).
        confidence_level: Statistical confidence level for error bars (default: 0.95).
        data_graph_format: RDF format for data graphs (default: 'turtle').
        shacl_graph_format: RDF format for shapes graphs (default: 'turtle').
        default_inference: Default inference level ('none', 'rdfs', 'owl-ld').
    """
    num_repetitions: int = 3
    time_multiplier: float = 1.0
    confidence_level: float = 0.95
    data_graph_format: str = 'turtle'
    shacl_graph_format: str = 'turtle'
    default_inference: str = 'none'


@dataclass
class DatasetConfig:
    """
    Configuration for a specific dataset and shapes graph pair.
    
    Attributes:
        shapes_graph_path: Path to the SHACL shapes graph file.
        data_graph_path: Path to the RDF data graph file.
        name: Human-readable name for this dataset configuration.
    """
    shapes_graph_path: str
    data_graph_path: str
    name: str = ""


# Pre-defined experiment configurations
DEFAULT_CONFIG = ExperimentConfig()

ENDE_LITE_50_CONFIGS = [
    DatasetConfig(
        shapes_graph_path="./../source/ShapesGraphs/Shape_30_closed_3.ttl",
        data_graph_path="./../source/Datasets/EnDe-Lite50(without_Ontology).ttl",
        name="EnDe-Lite50 (3 closed shapes)"
    ),
    DatasetConfig(
        shapes_graph_path="./../source/ShapesGraphs/Shape_30_closed_6.ttl",
        data_graph_path="./../source/Datasets/EnDe-Lite50(without_Ontology).ttl",
        name="EnDe-Lite50 (6 closed shapes)"
    ),
    DatasetConfig(
        shapes_graph_path="./../source/ShapesGraphs/Shape_30_closed_15.ttl",
        data_graph_path="./../source/Datasets/EnDe-Lite50(without_Ontology).ttl",
        name="EnDe-Lite50 (15 closed shapes)"
    ),
    DatasetConfig(
        shapes_graph_path="./../source/ShapesGraphs/Shape_30_closed_30.ttl",
        data_graph_path="./../source/Datasets/EnDe-Lite50(without_Ontology).ttl",
        name="EnDe-Lite50 (30 closed shapes)"
    )
]


# ============================================================================
# Virtuoso Configuration
# ============================================================================

# Directory paths
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
GRAPHS_DIR = SOURCE_DIR / "Datasets"
SHACL_SHAPES_DIR = SOURCE_DIR / "ShapesGraphs"
SPARQL_QUERIES_DIR = SOURCE_DIR / "queries"  # Create this directory if needed

# File paths
ONTOLOGY_PATH = SOURCE_DIR / "dbpedia_ontology.owl"
DBPEDIA_SHACL_PATH = SHACL_SHAPES_DIR / "DBpedia_SHACL.ttl"
DBPEDIA_QUERY_PATH = SPARQL_QUERIES_DIR / "dbpedia_query.txt"

# SPARQL endpoints
DBPEDIA_SPARQL_ENDPOINT = "http://dbpedia.org/sparql"
DATABUS_ENDPOINT = "https://databus.dbpedia.org/sparql"

# Virtuoso connection settings
VIRTUOSO_ENDPOINT = "http://localhost:8890/sparql"
VIRTUOSO_UPDATE_ENDPOINT = "http://localhost:8890/sparql-auth"  # Use sparql-auth for updates
VIRTUOSO_USER = "dba"
VIRTUOSO_PASSWORD = "dba"
DOCKER_CONTAINER_NAME = "new_virtuoso"  # Docker container name for ISQL commands

# Named graphs
VIRTUOSO_DATA_GRAPH_URI = "http://dbpedia.org/data"  # Named graph for data (large)
VIRTUOSO_ONTOLOGY_GRAPH_URI = "http://dbpedia.org/ontology"  # Named graph for ontology (small)
VIRTUOSO_SHAPES_GRAPH_URI = "http://shaclshapes.org/shapes"  # Named graph for SHACL shapes (small)
