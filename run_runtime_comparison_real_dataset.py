#!/usr/bin/env python3
"""
Runtime Comparison for Real Dataset: EnDe-Lite50 with DBpedia Ontology

This script measures and compares execution times for:
1. Baseline: Direct validation with original shapes
2. Our Approach: Shape entailment + validation with entailed shapes

Dataset:
- Data Graph: EnDe-Lite50(without_Ontology).ttl
- Ontology: dbpedia_ontology.owl
- Shapes Graphs: Shape_30_closed_3.ttl, Shape_30_closed_6.ttl, 
                 Shape_30_closed_15.ttl, Shape_30_closed_30.ttl
"""

import sys
from pathlib import Path
import time
import json
import glob

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, SH, RDF
from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics, OWLRL_Semantics
import os

# Dataset configuration
DATA_GRAPH = "source/Datasets/EnDe-Lite50(without_Ontology).ttl"
ONTOLOGY = "source/dbpedia_ontology.owl"
SHAPES_PATTERN = "source/ShapesGraphs/Shape_30_closed_*.ttl"

# Inference levels to test (starting with RDFS only)
INFERENCE_LEVELS = ["rdfs"]

# Number of runs for timing
NUM_RUNS = 3

def load_graph(file_path):
    """Load a turtle or OWL file into an RDF graph"""
    g = Graph()
    if file_path.endswith('.owl'):
        g.parse(file_path, format="xml")
    else:
        g.parse(file_path, format="turtle")
    return g

def apply_reasoning(data_graph, inference_level):
    """Apply reasoning to a data graph based on inference level"""
    # Create a copy of the graph for reasoning
    reasoned_graph = Graph()
    for triple in data_graph:
        reasoned_graph.add(triple)
    
    if inference_level == "rdfs":
        DeductiveClosure(RDFS_Semantics).expand(reasoned_graph)
    elif inference_level == "owl-ld":
        DeductiveClosure(OWLRL_Semantics).expand(reasoned_graph)
    
    return reasoned_graph

def count_violations(validation_report_graph):
    """Count the number of validation violations in a SHACL validation report"""
    violation_count = len(list(validation_report_graph.triples((None, RDF.type, SH.ValidationResult))))
    return violation_count

def measure_baseline_validation(data_graph, shapes_graph):
    """Measure time for baseline validation"""
    start = time.perf_counter()
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference='none',
        abort_on_first=False
    )
    end = time.perf_counter()
    return end - start, count_violations(results_graph)

def measure_shape_entailment(shapes_graph, ontology_graph, inference_level):
    """Measure time for shape entailment"""
    start = time.perf_counter()
    entailed_shapes = pre_process_shacl_graph_full(
        shapes_graph,
        ontology_graph,
        inference_level
    )
    end = time.perf_counter()
    return end - start, entailed_shapes

def measure_entailed_validation(data_graph, entailed_shapes):
    """Measure time for validation with entailed shapes"""
    start = time.perf_counter()
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=entailed_shapes,
        inference='none',
        abort_on_first=False
    )
    end = time.perf_counter()
    return end - start, count_violations(results_graph)

def run_runtime_comparison():
    """Run runtime comparison experiment on real dataset"""
    
    print("=" * 80)
    print("Runtime Comparison: Real Dataset (EnDe-Lite50 + DBpedia Ontology)")
    print("=" * 80)
    print(f"Running {NUM_RUNS} iterations per experiment for timing accuracy")
    print()
    
    # Load data graph once
    print(f"Loading data graph: {DATA_GRAPH}")
    data_graph = load_graph(DATA_GRAPH)
    print(f"  Loaded {len(data_graph)} triples")
    
    # Load ontology once
    print(f"\nLoading ontology: {ONTOLOGY}")
    ontology_graph = load_graph(ONTOLOGY)
    print(f"  Loaded {len(ontology_graph)} triples")
    
    # Find all shape graphs
    shapes_files = sorted(glob.glob(SHAPES_PATTERN))
    if not shapes_files:
        print(f"\n❌ ERROR: No shape graphs found matching pattern: {SHAPES_PATTERN}")
        return
    
    print(f"\nFound {len(shapes_files)} shape graphs:")
    for sf in shapes_files:
        print(f"  - {os.path.basename(sf)}")
    
    # Store results for reporting and plotting
    results = {}
    for inference_level in INFERENCE_LEVELS:
        results[inference_level] = {
            "baseline_time": [],
            "entailment_time": [],
            "entailed_validation_time": [],
            "total_our_approach_time": [],
            "baseline_violations": [],
            "entailed_violations": []
        }
    
    dataset_names = []
    
    for shapes_path in shapes_files:
        display_name = os.path.basename(shapes_path).replace("Shape_30_closed_", "SG").replace(".ttl", "")
        dataset_names.append(display_name)
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {os.path.basename(shapes_path)}")
        print(f"{'=' * 80}")
        
        # Load shapes graph
        print(f"\n1. Loading shapes graph: {shapes_path}")
        shapes_graph = load_graph(shapes_path)
        print(f"   Loaded {len(shapes_graph)} triples")
        
        # Process with different inference levels
        for inference_level in INFERENCE_LEVELS:
            print(f"\n2. Testing with inference level: {inference_level}")
            
            # Apply reasoning to data graph ONCE (reused for all runs)
            print(f"   Applying {inference_level} reasoning to data graph...")
            start_reasoning = time.perf_counter()
            reasoned_data = apply_reasoning(data_graph, inference_level)
            reasoning_time = time.perf_counter() - start_reasoning
            print(f"   Data graph: {len(data_graph)} -> {len(reasoned_data)} triples ({reasoning_time:.2f}s)")
            
            # === Measure BASELINE validation ===
            print(f"\n3a. Measuring BASELINE validation time ({NUM_RUNS} runs)...")
            baseline_times = []
            baseline_viols = None
            for i in range(NUM_RUNS):
                elapsed, viols = measure_baseline_validation(reasoned_data, shapes_graph)
                baseline_times.append(elapsed)
                baseline_viols = viols
                print(f"    Run {i+1}/{NUM_RUNS}: {elapsed:.4f}s")
            
            avg_baseline_time = sum(baseline_times) / len(baseline_times)
            print(f"    Average: {avg_baseline_time:.4f}s, Violations: {baseline_viols}")
            
            # === Measure SHAPE ENTAILMENT ===
            print(f"\n3b. Measuring SHAPE ENTAILMENT time ({NUM_RUNS} runs)...")
            entailment_times = []
            entailed_shapes = None
            for i in range(NUM_RUNS):
                # Reload shapes for each run to ensure fair timing
                shapes_to_process = load_graph(shapes_path)
                elapsed, ent_shapes = measure_shape_entailment(
                    shapes_to_process, 
                    ontology_graph, 
                    inference_level
                )
                entailment_times.append(elapsed)
                entailed_shapes = ent_shapes
                print(f"    Run {i+1}/{NUM_RUNS}: {elapsed:.4f}s")
            
            avg_entailment_time = sum(entailment_times) / len(entailment_times)
            print(f"    Average: {avg_entailment_time:.4f}s")
            
            # Save entailed shapes for inspection
            output_dir = f"Outputs/runtime_comparison_real/entailed_shapes/{inference_level}"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(shapes_path))
            entailed_shapes.serialize(destination=output_path, format="turtle")
            print(f"    Entailed shapes saved to: {output_path}")
            
            # === Measure ENTAILED validation ===
            print(f"\n3c. Measuring ENTAILED SHAPES validation time ({NUM_RUNS} runs)...")
            entailed_val_times = []
            entailed_viols = None
            for i in range(NUM_RUNS):
                elapsed, viols = measure_entailed_validation(reasoned_data, entailed_shapes)
                entailed_val_times.append(elapsed)
                entailed_viols = viols
                print(f"    Run {i+1}/{NUM_RUNS}: {elapsed:.4f}s")
            
            avg_entailed_val_time = sum(entailed_val_times) / len(entailed_val_times)
            print(f"    Average: {avg_entailed_val_time:.4f}s, Violations: {entailed_viols}")
            
            # === Calculate total time for our approach ===
            total_our_approach = avg_entailment_time + avg_entailed_val_time
            
            # === Summary for this dataset/inference level ===
            print(f"\n4. Runtime Summary:")
            print(f"   Baseline:       {avg_baseline_time:.4f}s ({baseline_viols} violations)")
            print(f"   Our Approach:   {total_our_approach:.4f}s ({entailed_viols} violations)")
            print(f"     - Entailment: {avg_entailment_time:.4f}s")
            print(f"     - Validation: {avg_entailed_val_time:.4f}s")
            
            speedup = avg_baseline_time / total_our_approach if total_our_approach > 0 else float('inf')
            if speedup > 1:
                print(f"   Performance:    {speedup:.2f}x FASTER")
            elif speedup < 1:
                print(f"   Performance:    {1/speedup:.2f}x SLOWER")
            else:
                print(f"   Performance:    Same")
            
            # Store results
            results[inference_level]["baseline_time"].append(avg_baseline_time)
            results[inference_level]["entailment_time"].append(avg_entailment_time)
            results[inference_level]["entailed_validation_time"].append(avg_entailed_val_time)
            results[inference_level]["total_our_approach_time"].append(total_our_approach)
            results[inference_level]["baseline_violations"].append(baseline_viols)
            results[inference_level]["entailed_violations"].append(entailed_viols)
        
        print()
    
    print("\n" + "=" * 80)
    print("Runtime Comparison Completed!")
    print("=" * 80)
    
    # Print summary table
    print("\nSummary Table:")
    print("-" * 80)
    for inference_level in INFERENCE_LEVELS:
        print(f"\n{inference_level.upper()} Inference:")
        print(f"  Dataset    | Baseline (s) | Our Approach (s) | Entailment (s) | Validation (s) | Speedup")
        print(f"  {'-'*10} | {'-'*12} | {'-'*16} | {'-'*14} | {'-'*14} | {'-'*7}")
        for i, name in enumerate(dataset_names):
            baseline = results[inference_level]["baseline_time"][i]
            total = results[inference_level]["total_our_approach_time"][i]
            entail = results[inference_level]["entailment_time"][i]
            valid = results[inference_level]["entailed_validation_time"][i]
            speedup = baseline / total if total > 0 else float('inf')
            print(f"  {name:10} | {baseline:12.4f} | {total:16.4f} | {entail:14.4f} | {valid:14.4f} | {speedup:7.2f}x")
    
    # Save results to JSON for plotting
    output_dir = "Outputs/runtime_comparison_real"
    os.makedirs(output_dir, exist_ok=True)
    
    results_json = {
        "datasets": dataset_names,
        "inference_levels": INFERENCE_LEVELS,
        "results": results,
        "metadata": {
            "data_graph": DATA_GRAPH,
            "ontology": ONTOLOGY,
            "shapes_pattern": SHAPES_PATTERN,
            "num_runs": NUM_RUNS
        }
    }
    
    json_path = os.path.join(output_dir, "runtime_results.json")
    with open(json_path, 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n\nResults saved to: {json_path}")
    
    print("\n" + "=" * 80)
    print("Data for plotting script (copy-paste):")
    print("=" * 80)
    print(f"\ndatasets = {dataset_names}")
    
    for inference_level in INFERENCE_LEVELS:
        prefix = inference_level.replace("-", "_")
        print(f"\n# {inference_level.upper()} inference results (in seconds)")
        print(f"{prefix}_baseline = {[round(t, 4) for t in results[inference_level]['baseline_time']]}")
        print(f"{prefix}_entailment = {[round(t, 4) for t in results[inference_level]['entailment_time']]}")
        print(f"{prefix}_validation = {[round(t, 4) for t in results[inference_level]['entailed_validation_time']]}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        run_runtime_comparison()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
