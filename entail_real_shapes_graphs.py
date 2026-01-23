#!/usr/bin/env python3
"""
Entail all Shape_30_closed_*.ttl shapes graphs with DBpedia ontology using RDFS reasoning.

This script:
1. Loads the DBpedia ontology once
2. For each shapes graph (Shape_30_closed_3, 6, 15, 30):
   - Loads the shapes graph
   - Applies shape entailment with RDFS reasoning
   - Times the entailment operation
   - Saves the entailed shapes graph
3. Reports timing for each shapes graph

Output: Entailed shapes graphs saved to source/ShapesGraphs/entailed/
"""

import sys
from pathlib import Path
import time
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph
from pre_shacl.pre_processor import pre_process_shacl_graph_full
import os

# Paths
ONTOLOGY_PATH = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\dbpedia_ontology.owl"
SHAPES_DIR = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\ShapesGraphs"
OUTPUT_DIR = r"C:\Users\zenon\eclipse-workspace\closed-shaper\source\ShapesGraphs\entailed"

# Shape files to process
SHAPE_FILES = [
    "Shape_30_closed_3.ttl",
    "Shape_30_closed_6.ttl",
    "Shape_30_closed_15.ttl",
    "Shape_30_closed_30.ttl"
]

INFERENCE_LEVEL = "rdfs"

def load_graph(file_path, format="turtle"):
    """Load a file into an RDF graph"""
    g = Graph()
    g.parse(file_path, format=format)
    return g

def main():
    print("=" * 80)
    print("Shape Entailment for Real Dataset (EnDe-Lite50)")
    print("=" * 80)
    print(f"Inference level: {INFERENCE_LEVEL.upper()}")
    print()
    
    # Load ontology once
    print("1. Loading DBpedia ontology...")
    start = time.perf_counter()
    ontology = load_graph(ONTOLOGY_PATH, format="xml")
    elapsed = time.perf_counter() - start
    print(f"   Loaded {len(ontology)} triples in {elapsed:.2f}s")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Store timing results
    results = {
        "inference_level": INFERENCE_LEVEL,
        "shapes": []
    }
    
    print("\n" + "=" * 80)
    print("2. Processing shapes graphs...")
    print("=" * 80)
    
    for i, shape_file in enumerate(SHAPE_FILES, 1):
        print(f"\n[{i}/{len(SHAPE_FILES)}] Processing: {shape_file}")
        print("-" * 80)
        
        # Load shapes graph
        shape_path = os.path.join(SHAPES_DIR, shape_file)
        print(f"  Loading shapes graph...")
        start = time.perf_counter()
        shapes_graph = load_graph(shape_path)
        load_time = time.perf_counter() - start
        print(f"    Loaded {len(shapes_graph)} triples in {load_time:.4f}s")
        
        # Apply shape entailment
        print(f"  Applying shape entailment with {INFERENCE_LEVEL.upper()}...")
        start = time.perf_counter()
        entailed_shapes = pre_process_shacl_graph_full(
            shapes_graph,
            ontology,
            INFERENCE_LEVEL
        )
        entailment_time = time.perf_counter() - start
        
        print(f"    Entailment completed in {entailment_time:.4f}s")
        print(f"    Entailed shapes: {len(entailed_shapes)} triples")
        added_triples = len(entailed_shapes) - len(shapes_graph)
        print(f"    Added {added_triples} triples")
        
        # Save entailed shapes
        output_file = shape_file.replace(".ttl", "_entailed.ttl")
        output_path = os.path.join(OUTPUT_DIR, output_file)
        print(f"  Saving entailed shapes to: {output_file}")
        start = time.perf_counter()
        entailed_shapes.serialize(destination=output_path, format="turtle")
        save_time = time.perf_counter() - start
        print(f"    Saved in {save_time:.4f}s")
        
        # Store results
        results["shapes"].append({
            "name": shape_file,
            "original_triples": len(shapes_graph),
            "entailed_triples": len(entailed_shapes),
            "added_triples": added_triples,
            "load_time_s": round(load_time, 4),
            "entailment_time_s": round(entailment_time, 4),
            "save_time_s": round(save_time, 4),
            "total_time_s": round(load_time + entailment_time + save_time, 4),
            "output_file": output_file
        })
        
        print(f"  ✓ Complete!")
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    print(f"\n{'Shape File':<30} | {'Original':<10} | {'Entailed':<10} | {'Added':<8} | {'Entailment Time':<18}")
    print("-" * 100)
    for result in results["shapes"]:
        print(f"{result['name']:<30} | {result['original_triples']:<10} | {result['entailed_triples']:<10} | "
              f"{result['added_triples']:<8} | {result['entailment_time_s']:<18.4f}s")
    
    total_entailment_time = sum(r["entailment_time_s"] for r in results["shapes"])
    print("-" * 100)
    print(f"{'Total Entailment Time:':<30} {total_entailment_time:.4f}s ({total_entailment_time/60:.2f} minutes)")
    
    # Save results to JSON
    json_path = os.path.join(OUTPUT_DIR, "entailment_results.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: {json_path}")
    
    print("\n" + "=" * 80)
    print("All shapes graphs entailed successfully!")
    print("=" * 80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nEntailed shapes files:")
    for result in results["shapes"]:
        print(f"  - {result['output_file']}")
    
    print("\n" + "=" * 80)
    print("Next step: Run Java SHACL validation")
    print("=" * 80)
    print(f"\nData graph: source/Datasets/EnDe-Lite50_RDFS_entailed.ttl")
    print(f"Shapes graphs: {OUTPUT_DIR}/*.ttl")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
