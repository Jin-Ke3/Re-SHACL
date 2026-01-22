#!/usr/bin/env python3
"""
Run reasoning level comparison for closed shapes baseline validation

This script demonstrates the impact of different reasoning levels (none, RDFS, OWL-LD)
on violation detection when validating with closed shapes.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, SH, RDF
from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics, OWLRL_Semantics
import os

# Dataset pairs: (data_graph, closed_shapes, display_name)
DATASET_PAIRS = [
    ("tests/fixtures/DG1.ttl", "tests/fixtures/SG1.ttl", "SG1"),
    ("tests/fixtures/DG2.ttl", "tests/fixtures/SG2.ttl", "SG2"),
    ("tests/fixtures/person_data_with_equivalences.ttl", "tests/fixtures/person_shape_closed.ttl", "SG3"),
    ("tests/fixtures/minimal_test_data.ttl", "tests/fixtures/closed_shape_example.ttl", "SG4"),
]

# Reasoning levels to test
REASONING_LEVELS = ["none", "rdfs", "owl-ld"]

def load_graph(file_path):
    """Load a turtle file into an RDF graph"""
    g = Graph()
    g.parse(file_path, format="turtle")
    return g

def apply_reasoning(data_graph, reasoning_level):
    """Apply reasoning to a data graph based on reasoning level"""
    if reasoning_level == "none":
        return data_graph
    
    if reasoning_level == "rdfs":
        DeductiveClosure(RDFS_Semantics).expand(data_graph)
    elif reasoning_level == "owl-ld":
        DeductiveClosure(OWLRL_Semantics).expand(data_graph)
    
    return data_graph

def count_violations(validation_report_graph):
    """Count the number of validation violations in a SHACL validation report"""
    violation_count = len(list(validation_report_graph.triples((None, RDF.type, SH.ValidationResult))))
    return violation_count

def run_reasoning_comparison():
    """Run baseline validation comparison across different reasoning levels"""
    
    print("=" * 80)
    print("Reasoning Level Comparison: Impact on Closed Shape Validation")
    print("=" * 80)
    print()
    
    # Store results for reporting
    results = {
        "none": [],
        "rdfs": [],
        "owl-ld": []
    }
    
    for data_graph_path, shapes_path, display_name in DATASET_PAIRS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {display_name}")
        print(f"{'=' * 80}")
        
        # Load data graph
        print(f"\n1. Loading data graph: {data_graph_path}")
        data_graph = load_graph(data_graph_path)
        print(f"   Loaded {len(data_graph)} triples")
        
        # Load closed shapes
        print(f"\n2. Loading closed shapes: {shapes_path}")
        shapes_graph = load_graph(shapes_path)
        print(f"   Loaded {len(shapes_graph)} triples")
        
        # Process with different reasoning levels
        for reasoning_level in REASONING_LEVELS:
            print(f"\n3. Testing with reasoning level: {reasoning_level}")
            
            # Apply reasoning to data graph
            if reasoning_level == "none":
                print(f"   No reasoning applied")
                reasoned_data = data_graph
                print(f"   Data graph: {len(data_graph)} triples")
            else:
                print(f"   Applying {reasoning_level} reasoning to data graph...")
                reasoned_data = apply_reasoning(data_graph, reasoning_level)
                print(f"   Data graph: {len(data_graph)} -> {len(reasoned_data)} triples")
            
            # Validate with closed shapes
            print(f"\n4. Baseline validation with closed shapes...")
            conforms, report_graph, report_text = validate(
                reasoned_data,
                shacl_graph=shapes_graph,
                inference='none',
                abort_on_first=False
            )
            violations = count_violations(report_graph)
            status = "[OK] CONFORMS" if conforms else "[X] VIOLATIONS"
            print(f"    {status}: {violations} violations")
            results[reasoning_level].append(violations)
            
            # Save validation report
            report_dir = f"Outputs/reasoning_comparison/{reasoning_level}"
            os.makedirs(report_dir, exist_ok=True)
            
            report_path = os.path.join(report_dir, f"{display_name}_report.ttl")
            report_graph.serialize(destination=report_path, format="turtle")
            print(f"    Report saved to: {report_path}")
        
        print()
    
    print("\n" + "=" * 80)
    print("Reasoning Comparison Completed!")
    print("=" * 80)
    print("\nSummary:")
    print("-" * 80)
    
    dataset_names = [pair[2] for pair in DATASET_PAIRS]
    
    for reasoning_level in REASONING_LEVELS:
        print(f"\n{reasoning_level.upper()} Reasoning:")
        print(f"  Violations: {results[reasoning_level]}")
    
    print("\n" + "=" * 80)
    print("Outputs:")
    print("  - Validation reports: Outputs/reasoning_comparison/{none,rdfs,owl-ld}/")
    print("=" * 80)
    
    # Print Python dictionary format for easy copy-paste into plotting script
    print("\n" + "=" * 80)
    print("Data for plotting script:")
    print("=" * 80)
    print(f"\ndatasets = {dataset_names}")
    print(f"\n# Violation counts by reasoning level")
    print(f"no_reasoning = {results['none']}")
    print(f"rdfs_reasoning = {results['rdfs']}")
    print(f"owl_reasoning = {results['owl-ld']}")

if __name__ == "__main__":
    try:
        run_reasoning_comparison()
    except Exception as e:
        print(f"\n Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
