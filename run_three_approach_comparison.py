#!/usr/bin/env python3
"""
Three-Approach Comparison: ReSHACL, Entailed Shapes, and Combined

This script compares three approaches for handling closed shapes:
1. ReSHACL only (recursive validation)
2. Our entailed shapes approach only
3. Combined: Entailed shapes + ReSHACL

Each approach is tested with three reasoning levels: none, RDFS, OWL-LD
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, SH, RDF
from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics, OWLRL_Semantics
import os
import json
from pre_shacl.pre_processor import pre_process_shacl_graph_full
from ReSHACL.re_shacl import merged_graph as merged_graph_owl
from ReSHACL.re_shacl_rdfs import merged_graph as merged_graph_rdfs
from ReSHACL.re_shacl import merged_graph

# Dataset pairs: (data_graph, closed_shapes, display_name)
DATASET_PAIRS = [
    ("tests/fixtures/DG1.ttl", "tests/fixtures/SG1.ttl", "SG1"),
    ("tests/fixtures/DG2.ttl", "tests/fixtures/SG2.ttl", "SG2"),
    ("tests/fixtures/person_data_with_equivalences.ttl", "tests/fixtures/person_shape_closed.ttl", "SG3"),
    ("tests/fixtures/minimal_test_data.ttl", "tests/fixtures/closed_shape_example.ttl", "SG4"),
]

# Reasoning levels to test (excluding 'none' as it provides no meaningful comparison)
REASONING_LEVELS = ["rdfs", "owl-ld"]

def load_graph(file_path):
    """Load a turtle file into an RDF graph"""
    g = Graph()
    g.parse(file_path, format="turtle")
    return g

def apply_reasoning(data_graph, reasoning_level):
    """Apply reasoning to a data graph based on reasoning level"""
    if reasoning_level == "none":
        return data_graph
    
    # Create a copy to avoid modifying original
    reasoned_graph = Graph()
    for triple in data_graph:
        reasoned_graph.add(triple)
    
    if reasoning_level == "rdfs":
        DeductiveClosure(RDFS_Semantics).expand(reasoned_graph)
    elif reasoning_level == "owl-ld":
        DeductiveClosure(OWLRL_Semantics).expand(reasoned_graph)
    
    return reasoned_graph

def count_violations(validation_report_graph):
    """Count the number of validation violations in a SHACL validation report"""
    violation_count = len(list(validation_report_graph.triples((None, RDF.type, SH.ValidationResult))))
    return violation_count

def approach1_reshacl_only(data_graph, shapes_graph, reasoning_level):
    """Approach 1: ReSHACL only with built-in reasoning"""
    # Use appropriate ReSHACL module based on reasoning level
    if reasoning_level == "rdfs":
        merged_func = merged_graph_rdfs
    else:  # owl-ld
        merged_func = merged_graph_owl
    
    # ReSHACL's merged_graph merges owl:sameAs AND applies reasoning
    fused_graph, same_dic, processed_shapes = merged_func(
        data_graph, 
        shacl_graph=shapes_graph,
        data_graph_format='turtle',
        shacl_graph_format='turtle'
    )
    
    # Validate WITHOUT additional inference (ReSHACL already did reasoning)
    conforms, report_graph, report_text = validate(
        fused_graph,
        shacl_graph=processed_shapes,
        inference='none',
        abort_on_first=False
    )
    violations = count_violations(report_graph)
    
    return conforms, violations, report_graph

def approach2_entailed_shapes_only(data_graph, shapes_graph, reasoning_level):
    """Approach 2: Our entailed shapes approach only"""
    original_size = len(data_graph)
    
    # Step 1: Entail shapes from ORIGINAL data graph (no reasoning on data yet)
    entailed_shapes = pre_process_shacl_graph_full(
        shacl_graph=shapes_graph,
        ontology_graph=data_graph,  # Use original data graph as ontology source
        regime=reasoning_level
    )
    
    # Step 2: Apply OWL RL reasoning to data graph
    reasoned_data = apply_reasoning(data_graph, reasoning_level)
    reasoned_size = len(reasoned_data)
    
    # Step 3: Validate REASONED data with entailed shapes (no additional inference)
    # Reasoning already applied, so inference='none'
    conforms, report_graph, report_text = validate(
        reasoned_data,
        shacl_graph=entailed_shapes,
        inference='none',
        abort_on_first=False
    )
    violations = count_violations(report_graph)
    
    return conforms, violations, report_graph, entailed_shapes, original_size, reasoned_size

def approach3_combined(data_graph, shapes_graph, reasoning_level):
    """Approach 3: Combined - ReSHACL FIRST (to merge data), then entail shapes from merged data"""
    # FIRST: Use ReSHACL to merge owl:sameAs and apply reasoning
    if reasoning_level == "rdfs":
        merged_func = merged_graph_rdfs
    else:  # owl-ld
        merged_func = merged_graph_owl
    
    # ReSHACL merges owl:sameAs + applies reasoning
    fused_graph, same_dic, _ = merged_func(
        data_graph, 
        shacl_graph=shapes_graph,  # Use original shapes for now
        data_graph_format='turtle',
        shacl_graph_format='turtle'
    )
    
    # SECOND: Entail shapes from the MERGED/REASONED data (not original)
    # This ensures the shapes match the data we'll actually validate
    entailed_shapes = pre_process_shacl_graph_full(
        shacl_graph=shapes_graph,
        ontology_graph=fused_graph,  # Use fused graph as ontology source!
        regime=reasoning_level
    )
    
    # THIRD: Validate the fused graph with entailed shapes
    conforms, report_graph, report_text = validate(
        fused_graph,
        shacl_graph=entailed_shapes,
        inference='none',  # No additional inference needed
        abort_on_first=False
    )
    violations = count_violations(report_graph)
    
    return conforms, violations, report_graph

def run_three_approach_comparison():
    """Run comparison across three approaches and three reasoning levels"""
    
    print("=" * 80)
    print("Three-Approach Comparison: ReSHACL vs Entailed Shapes vs Combined")
    print("=" * 80)
    print()
    
    # Store results for reporting
    results = {
        "reshacl_only": {"rdfs": [], "owl-ld": []},
        "entailed_only": {"rdfs": [], "owl-ld": []},
        "combined": {"rdfs": [], "owl-ld": []}
    }
    
    for data_graph_path, shapes_path, display_name in DATASET_PAIRS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {display_name}")
        print(f"{'=' * 80}")
        
        # Process with different reasoning levels
        for reasoning_level in REASONING_LEVELS:
            print(f"\n{'=' * 60}")
            print(f"Reasoning Level: {reasoning_level.upper()}")
            print(f"{'=' * 60}")
            
            # Approach 1: ReSHACL only (with built-in reasoning)
            print(f"\n--- Approach 1: ReSHACL Only ---")
            try:
                # Reload graphs fresh for each approach
                print(f"Loading data graph: {data_graph_path}")
                data_graph = load_graph(data_graph_path)
                print(f"  Loaded {len(data_graph)} triples")
                
                print(f"Loading shapes graph: {shapes_path}")
                shapes_graph = load_graph(shapes_path)
                print(f"  Loaded {len(shapes_graph)} triples")
                
                # ReSHACL merges owl:sameAs AND applies reasoning (rdfs or owl-ld)
                conforms, violations, report_graph = approach1_reshacl_only(
                    data_graph, shapes_graph, reasoning_level
                )
                status = "[OK] CONFORMS" if conforms else "[X] VIOLATIONS"
                print(f"    {status}: {violations} violations")
                print(f"    (ReSHACL with {reasoning_level} reasoning built-in)")
                results["reshacl_only"][reasoning_level].append(violations)
                
                # Save report
                report_dir = f"Outputs/three_approach_comparison/reshacl_only/{reasoning_level}"
                os.makedirs(report_dir, exist_ok=True)
                report_path = os.path.join(report_dir, f"{display_name}_report.ttl")
                report_graph.serialize(destination=report_path, format="turtle")
            except Exception as e:
                print(f"    [ERROR]: {e}")
                results["reshacl_only"][reasoning_level].append(-1)
            
            # Approach 2: Entailed shapes only
            print(f"\n--- Approach 2: Entailed Shapes Only ---")
            try:
                # Reload graphs fresh for each approach
                print(f"Loading data graph: {data_graph_path}")
                data_graph = load_graph(data_graph_path)
                print(f"  Loaded {len(data_graph)} triples")
                
                print(f"Loading shapes graph: {shapes_path}")
                shapes_graph = load_graph(shapes_path)
                print(f"  Loaded {len(shapes_graph)} triples")
                
                # Use ORIGINAL data (not reasoned) - reasoning happens during validation
                conforms, violations, report_graph, entailed_shapes, orig_size, reasoned_size = approach2_entailed_shapes_only(
                    data_graph, shapes_graph, reasoning_level
                )
                status = "[OK] CONFORMS" if conforms else "[X] VIOLATIONS"
                print(f"    {status}: {violations} violations")
                print(f"    Data graph: {orig_size} -> {reasoned_size} triples")
                print(f"    Entailed shapes: {len(entailed_shapes)} triples")
                results["entailed_only"][reasoning_level].append(violations)
                
                # Save report
                report_dir = f"Outputs/three_approach_comparison/entailed_only/{reasoning_level}"
                os.makedirs(report_dir, exist_ok=True)
                report_path = os.path.join(report_dir, f"{display_name}_report.ttl")
                report_graph.serialize(destination=report_path, format="turtle")
                
                # Save entailed shapes
                shapes_dir = f"Outputs/three_approach_comparison/entailed_shapes/{reasoning_level}"
                os.makedirs(shapes_dir, exist_ok=True)
                shapes_path_out = os.path.join(shapes_dir, f"{display_name}_entailed_shapes.ttl")
                entailed_shapes.serialize(destination=shapes_path_out, format="turtle")
            except Exception as e:
                print(f"    [ERROR]: {e}")
                results["entailed_only"][reasoning_level].append(-1)
            
            # Approach 3: Combined (Entailed shapes + ReSHACL)
            print(f"\n--- Approach 3: Combined (Entailed + ReSHACL) ---")
            try:
                # Reload graphs fresh for each approach
                print(f"Loading data graph: {data_graph_path}")
                data_graph = load_graph(data_graph_path)
                print(f"  Loaded {len(data_graph)} triples")
                
                print(f"Loading shapes graph: {shapes_path}")
                shapes_graph = load_graph(shapes_path)
                print(f"  Loaded {len(shapes_graph)} triples")
                
                # Combined approach: entail shapes FIRST, then use with ReSHACL
                conforms, violations, report_graph = approach3_combined(
                    data_graph, shapes_graph, reasoning_level
                )
                status = "[OK] CONFORMS" if conforms else "[X] VIOLATIONS"
                print(f"    {status}: {violations} violations")
                results["combined"][reasoning_level].append(violations)
                
                # Save report
                report_dir = f"Outputs/three_approach_comparison/combined/{reasoning_level}"
                os.makedirs(report_dir, exist_ok=True)
                report_path = os.path.join(report_dir, f"{display_name}_report.ttl")
                report_graph.serialize(destination=report_path, format="turtle")
            except Exception as e:
                print(f"    [ERROR]: {e}")
                results["combined"][reasoning_level].append(-1)
        
        print()
    
    print("\n" + "=" * 80)
    print("Three-Approach Comparison Completed!")
    print("=" * 80)
    
    # Save results to JSON for plotting
    results_file = "Outputs/three_approach_comparison/results.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump({
            "datasets": [pair[2] for pair in DATASET_PAIRS],
            "reasoning_levels": REASONING_LEVELS,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    print("\n" + "=" * 80)
    print("Summary by Approach:")
    print("=" * 80)
    
    dataset_names = [pair[2] for pair in DATASET_PAIRS]
    
    for approach in ["reshacl_only", "entailed_only", "combined"]:
        print(f"\n{approach.replace('_', ' ').title()}:")
        for reasoning_level in REASONING_LEVELS:
            print(f"  {reasoning_level.upper()}: {results[approach][reasoning_level]}")
    
    print("\n" + "=" * 80)
    print("Outputs:")
    print("  - Validation reports: Outputs/three_approach_comparison/{approach}/{reasoning}/")
    print("  - Results JSON: Outputs/three_approach_comparison/results.json")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_three_approach_comparison()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
