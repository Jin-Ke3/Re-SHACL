#!/usr/bin/env python3
"""
Run baseline validation comparison: Open shapes vs Closed shapes

This script runs baseline SHACL validation (no shape entailment) on open vs closed shapes
to demonstrate the impact of closing shapes on violation detection.
Both experiments use RDFS and OWL-LD inference on the data graph before validation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, SH, RDF
from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics, OWLRL_Semantics
import os

# Dataset pairs: (data_graph, open_shapes, closed_shapes, display_name)
DATASET_PAIRS = [
    ("tests/fixtures/DG1.ttl", "tests/fixtures/SG1_open.ttl", "tests/fixtures/SG1.ttl", "SG1"),
    ("tests/fixtures/DG2.ttl", "tests/fixtures/SG2_open.ttl", "tests/fixtures/SG2.ttl", "SG2"),
    ("tests/fixtures/person_data_with_equivalences.ttl", "tests/fixtures/person_shape_open_v2.ttl", "tests/fixtures/person_shape_closed.ttl", "SG3"),
    ("tests/fixtures/minimal_test_data.ttl", "tests/fixtures/closed_shape_example_open.ttl", "tests/fixtures/closed_shape_example.ttl", "SG4"),
]

# Inference levels to test
INFERENCE_LEVELS = ["rdfs", "owl-ld"]

def load_graph(file_path):
    """Load a turtle file into an RDF graph"""
    g = Graph()
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

def run_baseline_comparison():
    """Run baseline validation comparison for open vs closed shapes"""
    
    print("=" * 80)
    print("Baseline Validation Comparison: Open vs Closed Shapes")
    print("=" * 80)
    print()
    
    # Store results for reporting
    results = {
        "rdfs": {"open": [], "closed": []},
        "owl-ld": {"open": [], "closed": []}
    }
    
    for data_graph_path, open_shapes_path, closed_shapes_path, display_name in DATASET_PAIRS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {display_name}")
        print(f"{'=' * 80}")
        
        # Load data graph
        print(f"\n1. Loading data graph: {data_graph_path}")
        data_graph = load_graph(data_graph_path)
        print(f"   Loaded {len(data_graph)} triples")
        
        # Load shape graphs
        print(f"\n2. Loading shape graphs...")
        open_shapes = load_graph(open_shapes_path)
        closed_shapes = load_graph(closed_shapes_path)
        print(f"   Open shapes: {len(open_shapes)} triples")
        print(f"   Closed shapes: {len(closed_shapes)} triples")
        
        # Process with different inference levels
        for inference_level in INFERENCE_LEVELS:
            print(f"\n3. Testing with inference level: {inference_level}")
            
            # Apply reasoning to data graph
            print(f"   Applying {inference_level} reasoning to data graph...")
            reasoned_data = apply_reasoning(data_graph, inference_level)
            print(f"   Data graph: {len(data_graph)} -> {len(reasoned_data)} triples")
            
            # Validate with OPEN shapes
            print(f"\n4a. Baseline validation with OPEN shapes...")
            open_conforms, open_graph, open_text = validate(
                reasoned_data,
                shacl_graph=open_shapes,
                inference='none',
                abort_on_first=False
            )
            open_violations = count_violations(open_graph)
            open_status = "[OK] CONFORMS" if open_conforms else "[X] VIOLATIONS"
            print(f"    {open_status}: {open_violations} violations")
            results[inference_level]["open"].append(open_violations)
            
            # Validate with CLOSED shapes
            print(f"\n4b. Baseline validation with CLOSED shapes...")
            closed_conforms, closed_graph, closed_text = validate(
                reasoned_data,
                shacl_graph=closed_shapes,
                inference='none',
                abort_on_first=False
            )
            closed_violations = count_violations(closed_graph)
            closed_status = "[OK] CONFORMS" if closed_conforms else "[X] VIOLATIONS"
            diff = closed_violations - open_violations
            diff_str = f"({diff:+d})" if diff != 0 else "(no change)"
            print(f"    {closed_status}: {closed_violations} violations {diff_str}")
            results[inference_level]["closed"].append(closed_violations)
            
            # Save validation reports
            report_dir = f"Outputs/baseline_comparison/{inference_level}"
            os.makedirs(report_dir, exist_ok=True)
            
            open_report_path = os.path.join(report_dir, f"{display_name}_open_report.ttl")
            open_graph.serialize(destination=open_report_path, format="turtle")
            
            closed_report_path = os.path.join(report_dir, f"{display_name}_closed_report.ttl")
            closed_graph.serialize(destination=closed_report_path, format="turtle")
            print(f"    Reports saved to: {report_dir}")
        
        print()
    
    print("\n" + "=" * 80)
    print("Baseline Comparison Completed!")
    print("=" * 80)
    print("\nSummary:")
    print("-" * 80)
    
    dataset_names = [pair[3] for pair in DATASET_PAIRS]
    
    for inference_level in INFERENCE_LEVELS:
        print(f"\n{inference_level.upper()} Inference:")
        print(f"  Open shapes violations:   {results[inference_level]['open']}")
        print(f"  Closed shapes violations: {results[inference_level]['closed']}")
    
    print("\n" + "=" * 80)
    print("Outputs:")
    print("  - Validation reports: Outputs/baseline_comparison/{rdfs,owl-ld}/")
    print("=" * 80)
    
    # Print Python dictionary format for easy copy-paste into plotting script
    print("\n" + "=" * 80)
    print("Data for plotting script:")
    print("=" * 80)
    print(f"\ndatasets = {dataset_names}")
    print(f"\n# RDFS inference results")
    print(f"rdfs_open = {results['rdfs']['open']}")
    print(f"rdfs_closed = {results['rdfs']['closed']}")
    print(f"\n# OWL-LD inference results")
    print(f"owl_open = {results['owl-ld']['open']}")
    print(f"owl_closed = {results['owl-ld']['closed']}")

if __name__ == "__main__":
    try:
        run_baseline_comparison()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
