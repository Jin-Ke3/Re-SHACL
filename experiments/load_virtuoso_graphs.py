"""Script to load ontology, data, and shapes graphs into Virtuoso."""

from pathlib import Path
from experiments import config
from experiments import virtuoso_backend


def load_all_graphs():
    """Load ontology, data graph, and shapes graph into Virtuoso."""
    
    # Define file paths - adjust these paths based on your actual file locations
    ontology_path = config.ONTOLOGY_PATH
    data_graph_path = config.GRAPHS_DIR / "EnDe-Lite50(without_Ontology).ttl"
    shapes_graph_path = config.SHACL_SHAPES_DIR / "Shape_30_closed_30.ttl"
    
    # 1. Load Ontology
    print("=" * 80)
    print("LOADING ONTOLOGY")
    print("=" * 80)
    try:
        print(f"Loading ontology from: {ontology_path}")
        if not ontology_path.exists():
            print(f"⚠ Warning: Ontology file not found at {ontology_path}")
            print("Skipping ontology loading...")
        else:
            virtuoso_backend.load_ontology_to_virtuoso(
                str(ontology_path), 
                config.VIRTUOSO_ONTOLOGY_GRAPH_URI
            )
            print(f"✓ Ontology loaded into <{config.VIRTUOSO_ONTOLOGY_GRAPH_URI}>")
    except Exception as e:
        print(f"✗ Error loading ontology: {e}")
        raise
    
    # 2. Load Data Graph
    print("\n" + "=" * 80)
    print("LOADING DATA GRAPH")
    print("=" * 80)
    try:
        print(f"Loading data graph from: {data_graph_path}")
        if not data_graph_path.exists():
            raise FileNotFoundError(f"Data graph file not found: {data_graph_path}")
            
        virtuoso_backend.load_data_to_virtuoso(
            str(data_graph_path), 
            config.VIRTUOSO_DATA_GRAPH_URI
        )
        print(f"✓ Data graph loaded into <{config.VIRTUOSO_DATA_GRAPH_URI}>")
    except Exception as e:
        print(f"✗ Error loading data graph: {e}")
        raise
    
    # 3. Load Shapes Graph
    print("\n" + "=" * 80)
    print("LOADING SHAPES GRAPH")
    print("=" * 80)
    try:
        print(f"Loading shapes graph from: {shapes_graph_path}")
        if not shapes_graph_path.exists():
            raise FileNotFoundError(f"Shapes graph file not found: {shapes_graph_path}")
            
        virtuoso_backend.load_shapes_to_virtuoso(
            str(shapes_graph_path), 
            config.VIRTUOSO_SHAPES_GRAPH_URI
        )
        print(f"✓ Shapes graph loaded into <{config.VIRTUOSO_SHAPES_GRAPH_URI}>")
    except Exception as e:
        print(f"✗ Error loading shapes graph: {e}")
        raise
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("All graphs loaded successfully!")
    print(f"  Ontology: <{config.VIRTUOSO_ONTOLOGY_GRAPH_URI}>")
    print(f"  Data:     <{config.VIRTUOSO_DATA_GRAPH_URI}>")
    print(f"  Shapes:   <{config.VIRTUOSO_SHAPES_GRAPH_URI}>")
    print()
    print("Verifying graphs in Virtuoso...")
    
    # Verify the graphs were loaded
    try:
        if ontology_path.exists():
            ontology_count = virtuoso_backend.get_graph_count(config.VIRTUOSO_ONTOLOGY_GRAPH_URI)
            print(f"  Ontology in Virtuoso: {ontology_count} triples")
        
        data_count = virtuoso_backend.get_graph_count(config.VIRTUOSO_DATA_GRAPH_URI)
        shapes_count = virtuoso_backend.get_graph_count(config.VIRTUOSO_SHAPES_GRAPH_URI)
        
        print(f"  Data in Virtuoso:     {data_count} triples")
        print(f"  Shapes in Virtuoso:   {shapes_count} triples")
    except Exception as e:
        print(f"Warning: Could not verify graphs in Virtuoso: {e}")


if __name__ == '__main__':
    load_all_graphs()
