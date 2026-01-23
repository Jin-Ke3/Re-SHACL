#!/usr/bin/env python3
"""
Entail the EnDe-Lite50 data graph with RDFS reasoning and save it.

This script:
1. Loads the data graph (EnDe-Lite50 without ontology)
2. Loads the DBpedia ontology
3. Merges them together
4. Applies RDFS reasoning
5. Saves the entailed data graph to a file

This is done once to avoid repeated 22-minute entailment operations.
"""

import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph
from owlrl import DeductiveClosure, RDFS_Semantics
import os

# Paths
DATA_GRAPH_PATH = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\Datasets\EnDe-Lite50(without_Ontology).ttl"
ONTOLOGY_PATH = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\dbpedia_ontology.owl"
OUTPUT_PATH = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\Datasets\EnDe-Lite50_RDFS_entailed.ttl"

def load_graph(file_path, format="turtle"):
    """Load a file into an RDF graph"""
    print(f"Loading: {file_path}")
    g = Graph()
    start = time.perf_counter()
    g.parse(file_path, format=format)
    elapsed = time.perf_counter() - start
    print(f"  Loaded {len(g)} triples in {elapsed:.2f}s")
    return g

def main():
    print("=" * 80)
    print("RDFS Entailment for EnDe-Lite50 Data Graph")
    print("=" * 80)
    print()
    
    # Load data graph
    print("1. Loading data graph...")
    data_graph = load_graph(DATA_GRAPH_PATH, format="turtle")
    
    # Load ontology
    print("\n2. Loading DBpedia ontology...")
    ontology = load_graph(ONTOLOGY_PATH, format="xml")
    
    # Merge data graph and ontology
    print("\n3. Merging data graph with ontology...")
    combined_graph = Graph()
    start = time.perf_counter()
    
    for triple in data_graph:
        combined_graph.add(triple)
    for triple in ontology:
        combined_graph.add(triple)
    
    elapsed = time.perf_counter() - start
    print(f"  Combined graph: {len(combined_graph)} triples (merged in {elapsed:.2f}s)")
    
    # Apply RDFS reasoning
    print("\n4. Applying RDFS reasoning...")
    print("  This may take ~22 minutes...")
    start = time.perf_counter()
    
    DeductiveClosure(RDFS_Semantics).expand(combined_graph)
    
    elapsed = time.perf_counter() - start
    print(f"  RDFS reasoning complete!")
    print(f"  Final graph: {len(combined_graph)} triples")
    print(f"  Time taken: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
    
    # Save the entailed graph
    print(f"\n5. Saving entailed graph to: {OUTPUT_PATH}")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    start = time.perf_counter()
    
    combined_graph.serialize(destination=OUTPUT_PATH, format="turtle")
    
    elapsed = time.perf_counter() - start
    print(f"  Saved in {elapsed:.2f}s")
    
    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80)
    print(f"\nEntailed data graph saved to: {OUTPUT_PATH}")
    print(f"Use this file for validation experiments to avoid re-entailing.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
