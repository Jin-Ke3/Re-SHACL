#!/usr/bin/env python3
"""Run shape entailment pipeline for all DG-SG pairs

This script processes each data graph (DG) and shapes graph (SG) pair,
extracts ontology from the data graph (TBox/ABox), and uses it to entail
the SHACL shapes graph using the pre_process_shacl_graph_full pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rdflib import Graph, SH, RDF
from pre_shacl.pre_processor import pre_process_shacl_graph_full
from pyshacl import validate
from owlrl import DeductiveClosure, RDFS_Semantics, OWLRL_Semantics
import os

# Dataset pairs: (data_graph, shapes_graph, output_name)
DATASET_PAIRS = [
    ("tests/fixtures/DG1.ttl", "tests/fixtures/SG1.ttl", "SG1_entailed.ttl"),
    ("tests/fixtures/DG2.ttl", "tests/fixtures/SG2.ttl", "SG2_entailed.ttl"),
    ("tests/fixtures/person_data_with_equivalences.ttl", "tests/fixtures/person_shape_closed.ttl", "SG3_entailed.ttl"),
    ("tests/fixtures/minimal_test_data.ttl", "tests/fixtures/closed_shape_example.ttl", "SG4_entailed.ttl"),
]

# Inference levels to test
INFERENCE_LEVELS = ["rdfs", "owl-ld"]

def load_graph(file_path):
    """Load a turtle file into an RDF graph"""
    g = Graph()
    g.parse(file_path, format="turtle")
    return g

def save_entailed_shapes(shapes_graph, output_path):
    """Save entailed shapes graph to file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    shapes_graph.serialize(destination=output_path, format="turtle")
    print(f"  [OK] Saved to: {output_path}")

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
    # Query for sh:ValidationResult nodes
    violation_count = len(list(validation_report_graph.triples((None, RDF.type, SH.ValidationResult))))
    return violation_count

def run_pipeline():
    """Run the shape entailment pipeline for all dataset pairs"""
    
    print("=" * 80)
    print("SHACL Shape Entailment Pipeline")
    print("=" * 80)
    print()
    
    for data_graph_path, shapes_graph_path, output_name in DATASET_PAIRS:
        print(f"\n{'=' * 80}")
        print(f"Processing: {os.path.basename(data_graph_path)} -> {os.path.basename(shapes_graph_path)}")
        print(f"{'=' * 80}")
        
        # Load data graph (contains both ABox and TBox/ontology)
        print(f"\n1. Loading data graph: {data_graph_path}")
        data_graph = load_graph(data_graph_path)
        print(f"   Loaded {len(data_graph)} triples")
        
        # Load shapes graph
        print(f"\n2. Loading shapes graph: {shapes_graph_path}")
        shapes_graph = load_graph(shapes_graph_path)
        print(f"   Loaded {len(shapes_graph)} triples")
        
        # The data graph contains both ABox and TBox, so we use it as the ontology
        ontology_graph = data_graph
        
        # Process with different inference levels
        for inference_level in INFERENCE_LEVELS:
            print(f"\n3. Running shape entailment with inference level: {inference_level}")
            print(f"   Using ontology from data graph...")
            
            # Reload shapes graph for each inference level
            shapes_to_process = load_graph(shapes_graph_path)
            
            # Apply shape entailment
            entailed_shapes = pre_process_shacl_graph_full(
                shapes_to_process,
                ontology_graph,
                inference_level
            )
            
            # Count properties before and after (sh:property + items in sh:ignoredProperties lists)
            def count_all_properties(graph):
                # Count sh:property declarations
                prop_count = len(list(graph.triples((None, SH.property, None))))
                # Count items in sh:ignoredProperties RDF lists
                ignored_count = 0
                for _, _, list_node in graph.triples((None, SH.ignoredProperties, None)):
                    current = list_node
                    while current and current != RDF.nil:
                        if (current, RDF.first, None) in graph:
                            ignored_count += 1
                        current = graph.value(current, RDF.rest)
                return prop_count, ignored_count
            
            orig_props, orig_ignored = count_all_properties(shapes_graph)
            ent_props, ent_ignored = count_all_properties(entailed_shapes)
            
            added_props = ent_props - orig_props
            added_ignored = ent_ignored - orig_ignored
            
            print(f"   sh:property: {orig_props} -> {ent_props} (added {added_props})")
            print(f"   sh:ignoredProperties: {orig_ignored} -> {ent_ignored} (added {added_ignored})")
            
            # Save output
            output_dir = f"Outputs/entailed_shapes/{inference_level}"
            output_path = os.path.join(output_dir, output_name)
            save_entailed_shapes(entailed_shapes, output_path)
            
            # Apply reasoning to data graph
            print(f"\n4. Applying {inference_level} reasoning to data graph...")
            reasoned_data = apply_reasoning(data_graph, inference_level)
            print(f"   Data graph: {len(data_graph)} -> {len(reasoned_data)} triples")
            
            # Validate with ORIGINAL shapes (baseline)
            print(f"\n5a. Baseline validation (original shapes, no entailment)...")
            baseline_conforms, baseline_graph, baseline_text = validate(
                reasoned_data,
                shacl_graph=shapes_graph,
                inference='none',
                abort_on_first=False
            )
            baseline_violations = count_violations(baseline_graph)
            baseline_status = "[OK] CONFORMS" if baseline_conforms else "[X] VIOLATIONS"
            print(f"    {baseline_status}: {baseline_violations} violations")
            
            # Validate reasoned data against entailed shapes
            print(f"\n5b. Validation with entailed shapes...")
            conforms, results_graph, results_text = validate(
                reasoned_data,
                shacl_graph=entailed_shapes,
                inference='none',  # No additional inference needed, already applied
                abort_on_first=False
            )
            
            num_violations = count_violations(results_graph)
            status = "[OK] CONFORMS" if conforms else "[X] VIOLATIONS"
            diff = num_violations - baseline_violations
            diff_str = f"({diff:+d})" if diff != 0 else "(no change)"
            print(f"    {status}: {num_violations} violations {diff_str}")
            
            # Save validation reports
            report_dir = f"Outputs/validation_reports/{inference_level}"
            os.makedirs(report_dir, exist_ok=True)
            
            baseline_path = os.path.join(report_dir, output_name.replace("_entailed.ttl", "_baseline_report.ttl"))
            baseline_graph.serialize(destination=baseline_path, format="turtle")
            
            report_path = os.path.join(report_dir, output_name.replace("_entailed.ttl", "_entailed_report.ttl"))
            results_graph.serialize(destination=report_path, format="turtle")
            print(f"    Reports saved to: {report_dir}")
        
        print()
    
    print("\n" + "=" * 80)
    print("Pipeline completed successfully!")
    print("=" * 80)
    print("\nOutputs:")
    print("  - Entailed shapes: Outputs/entailed_shapes/{rdfs,owl-ld}/")
    print("  - Validation reports: Outputs/validation_reports/{rdfs,owl-ld}/")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
