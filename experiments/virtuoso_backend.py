"""Virtuoso triplestore backend for loading and querying RDF data."""

from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST, BASIC, TURTLE
from typing import Dict, Any, Optional
import subprocess
import os
from pathlib import Path
from experiments import config


# Cache for SPARQL wrapper instances
_sparql_cache = {}


def get_virtuoso_sparql(use_update_endpoint: bool = False) -> SPARQLWrapper:
    """Create or retrieve cached authenticated SPARQL wrapper for Virtuoso.
    
    Args:
        use_update_endpoint: If True, use the UPDATE endpoint for INSERT/DELETE operations.
        
    Returns:
        Configured SPARQLWrapper instance with authentication.
    """
    cache_key = 'update' if use_update_endpoint else 'query'
    
    if cache_key not in _sparql_cache:
        endpoint = config.VIRTUOSO_UPDATE_ENDPOINT if use_update_endpoint else config.VIRTUOSO_ENDPOINT
        sparql = SPARQLWrapper(endpoint)
        
        # Set credentials for authentication
        sparql.setCredentials(config.VIRTUOSO_USER, config.VIRTUOSO_PASSWORD)
        
        # Use DIGEST authentication for update operations (Virtuoso requires this)
        if use_update_endpoint:
            sparql.setHTTPAuth(DIGEST)
        
        _sparql_cache[cache_key] = sparql
    
    return _sparql_cache[cache_key]


def load_graph_via_isql(file_path: str, graph_uri: str, isql_port: str = "1111") -> None:
    """Load an RDF file into Virtuoso using ISQL bulk loader via Docker.
    
    Loads RDF files directly into Virtuoso without any intermediate processing.
    
    Args:
        file_path: Absolute path to the RDF file to load.
        graph_uri: The named graph URI to load the data into.
        isql_port: ISQL port (default: 1111).
        
    Raises:
        subprocess.CalledProcessError: If ISQL command fails.
        FileNotFoundError: If file or docker executable is not found.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"RDF file not found: {file_path}")
    
    # Copy file into Docker container
    container_path = f"/tmp/{Path(file_path).name}"
    print(f"Copying file to Docker container: {container_path}")
    
    subprocess.run(
        ["docker", "cp", file_path, f"{config.DOCKER_CONTAINER_NAME}:{container_path}"],
        capture_output=True,
        text=True,
        check=True
    )
    print("File copied to container")
    
    # Clear existing graph
    print(f"Clearing existing graph <{graph_uri}>...")
    clear_command = f"SPARQL DROP SILENT GRAPH <{graph_uri}>;"
    
    try:
        subprocess.run(
            ["docker", "exec", "-i", config.DOCKER_CONTAINER_NAME, "isql", isql_port, config.VIRTUOSO_USER, config.VIRTUOSO_PASSWORD],
            input=clear_command,
            text=True,
            capture_output=True,
            check=True
        )
        print(f"Cleared graph <{graph_uri}>")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to clear graph (may not exist): {e.stderr}")
    
    # Clean load_list for this file
    print(f"Cleaning load_list...")
    cleanup_command = f"DELETE FROM DB.DBA.load_list WHERE ll_file = '{container_path}';"
    
    try:
        subprocess.run(
            ["docker", "exec", "-i", config.DOCKER_CONTAINER_NAME, "isql", isql_port, config.VIRTUOSO_USER, config.VIRTUOSO_PASSWORD],
            input=cleanup_command,
            text=True,
            capture_output=True,
            check=True
        )
        print("Load list cleaned")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to clean load_list: {e.stderr}")
    
    # Load the file using Virtuoso's bulk loader
    print(f"Loading file into graph <{graph_uri}>...")
    load_command = f"""
    ld_dir('/tmp', '{Path(file_path).name}', '{graph_uri}');
    rdf_loader_run();
    SELECT * FROM DB.DBA.load_list WHERE ll_file = '{container_path}';
    """
    
    process = subprocess.run(
        ["docker", "exec", "-i", config.DOCKER_CONTAINER_NAME, "isql", isql_port, config.VIRTUOSO_USER, config.VIRTUOSO_PASSWORD],
        input=load_command,
        text=True,
        capture_output=True,
        check=True
    )
    
    print("✅ Graph loaded successfully via ISQL!")
    if process.stdout:
        print("ISQL output:")
        print(process.stdout)


def query_virtuoso(query: str, graph_uri: Optional[str] = None) -> Dict[str, Any]:
    """Execute a SELECT query against Virtuoso.
    
    Args:
        query: The SPARQL SELECT query string to execute.
        graph_uri: Optional named graph URI to query from.
        
    Returns:
        Dictionary containing the query results in JSON format.
    """
    try:
        sparql = get_virtuoso_sparql()
        sparql.setReturnFormat(JSON)
        
        # If graph_uri is specified, wrap query with FROM clause
        if graph_uri:
            # Check if query already has FROM clause
            if 'FROM' not in query.upper():
                # Insert FROM clause after SELECT line
                parts = query.split('WHERE', 1)
                if len(parts) == 2:
                    query = f"{parts[0]} FROM <{graph_uri}> WHERE {parts[1]}"
        
        sparql.setQuery(query)
        return sparql.query().convert()
    except Exception as e:
        print(f"Error executing SPARQL query on Virtuoso: {e}")
        print(f"Query: {query[:200]}...")
        raise


def construct_virtuoso(query: str, graph_uri: Optional[str] = None) -> str:
    """Execute a CONSTRUCT query against Virtuoso and return the resulting RDF in TTL format.
    
    Args:
        query: The SPARQL CONSTRUCT query string to execute.
        graph_uri: Optional named graph URI to construct from.
        
    Returns:
        A string containing the RDF data in Turtle (TTL) format.
    """
    try:
        sparql = get_virtuoso_sparql()
        sparql.setReturnFormat(TURTLE)
        
        # If graph_uri is specified, wrap query with FROM clause
        if graph_uri:
            if 'FROM' not in query.upper():
                parts = query.split('WHERE', 1)
                if len(parts) == 2:
                    query = f"{parts[0]} FROM <{graph_uri}> WHERE {parts[1]}"
        
        sparql.setQuery(query)
        result = sparql.query().convert()
        
        # Convert bytes to string if necessary
        if isinstance(result, bytes):
            return result.decode('utf-8')
        return result
    except Exception as e:
        print(f"Error executing CONSTRUCT query on Virtuoso: {e}")
        print(f"Query: {query[:200]}...")
        raise


def load_ontology_to_virtuoso(file_path: str, graph_uri: str) -> None:
    """Load an ontology RDF file into Virtuoso backend using ISQL bulk loader.
    
    Args:
        file_path: Absolute path to the ontology RDF file.
        graph_uri: The named graph URI to load the ontology into.
    """
    try:
        print(f"\n=== Loading Ontology ===")
        load_graph_via_isql(file_path, graph_uri)
        print(f"Successfully loaded ontology into <{graph_uri}>")
    except Exception as e:
        print(f"Error loading ontology to Virtuoso: {e}")
        raise


def load_shapes_to_virtuoso(file_path: str, graph_uri: str) -> None:
    """Load a SHACL shapes RDF file into Virtuoso backend using ISQL bulk loader.
    
    Args:
        file_path: Absolute path to the SHACL shapes RDF file.
        graph_uri: The named graph URI to load the shapes into.
    """
    try:
        print(f"\n=== Loading SHACL Shapes ===")
        load_graph_via_isql(file_path, graph_uri)
        print(f"Successfully loaded shapes into <{graph_uri}>")
    except Exception as e:
        print(f"Error loading shapes to Virtuoso: {e}")
        raise


def load_data_to_virtuoso(file_path: str, graph_uri: str) -> None:
    """Load a data RDF file into Virtuoso backend using ISQL bulk loader.
    
    Args:
        file_path: Absolute path to the data RDF file.
        graph_uri: The named graph URI to load the data into.
    """
    try:
        print(f"\n=== Loading Data Graph ===")
        load_graph_via_isql(file_path, graph_uri)
        print(f"Successfully loaded data into <{graph_uri}>")
    except Exception as e:
        print(f"Error loading data to Virtuoso: {e}")
        raise


def clear_graph(graph_uri: str) -> None:
    """Clear all triples from a named graph in Virtuoso.
    
    Args:
        graph_uri: The URI of the named graph to clear.
    """
    try:
        sparql = get_virtuoso_sparql(use_update_endpoint=True)
        sparql.setMethod(POST)
        
        update_query = f"CLEAR GRAPH <{graph_uri}>"
        sparql.setQuery(update_query)
        sparql.query()
        
        print(f"Cleared graph <{graph_uri}>")
    except Exception as e:
        print(f"Error clearing graph <{graph_uri}>: {e}")
        raise


def fetch_graph_from_virtuoso(graph_uri: str) -> str:
    """Fetch all triples from a named graph in Virtuoso.
    
    Args:
        graph_uri: The URI of the named graph to fetch.
        
    Returns:
        A string containing the RDF data in Turtle (TTL) format.
    """
    try:
        query = f"""
        CONSTRUCT {{ ?s ?p ?o }}
        WHERE {{ 
            GRAPH <{graph_uri}> {{
                ?s ?p ?o 
            }}
        }}
        """
        
        return construct_virtuoso(query)
    except Exception as e:
        print(f"Error fetching graph <{graph_uri}> from Virtuoso: {e}")
        raise


def graph_exists(graph_uri: str) -> bool:
    """Check if a named graph exists in Virtuoso.
    
    Args:
        graph_uri: The URI of the named graph to check.
        
    Returns:
        True if the graph exists and contains triples, False otherwise.
    """
    try:
        query = f"""
        ASK WHERE {{
            GRAPH <{graph_uri}> {{
                ?s ?p ?o
            }}
        }}
        """
        
        sparql = get_virtuoso_sparql()
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        result = sparql.query().convert()
        
        return result.get('boolean', False)
    except Exception as e:
        print(f"Error checking if graph <{graph_uri}> exists: {e}")
        return False


def get_graph_count(graph_uri: str) -> int:
    """Get the number of triples in a named graph.
    
    Args:
        graph_uri: The URI of the named graph to count.
        
    Returns:
        Number of triples in the graph.
    """
    try:
        query = f"""
        SELECT (COUNT(*) as ?count)
        WHERE {{
            GRAPH <{graph_uri}> {{
                ?s ?p ?o
            }}
        }}
        """
        
        result = query_virtuoso(query)
        count = int(result["results"]["bindings"][0]["count"]["value"])
        return count
    except Exception as e:
        print(f"Error counting triples in graph <{graph_uri}>: {e}")
        raise
