#!/usr/bin/env python3
"""
Plot Three-Approach Comparison Results

Creates three panels showing violation counts for:
- Panel 1: ReSHACL Only
- Panel 2: Entailed Shapes Only
- Panel 3: Combined (Entailed + ReSHACL)

Each panel shows three bars per dataset (one for each reasoning level: none, RDFS, OWL)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_results(results_file="Outputs/three_approach_comparison/results.json"):
    """Load results from JSON file"""
    with open(results_file, 'r') as f:
        data = json.load(f)
    return data

def plot_three_approach_comparison():
    """Create three-panel comparison plot"""
    
    # Load results
    data = load_results()
    datasets = data["datasets"]
    reasoning_levels = data["reasoning_levels"]
    results = data["results"]
    
    # Prepare data for plotting
    reshacl_only = results["reshacl_only"]
    entailed_only = results["entailed_only"]
    combined = results["combined"]
    
    # Create figure with three panels side by side
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Common settings
    x = np.arange(len(datasets))
    width = 0.25
    
    colors = {
        "none": "#e74c3c",      # Red
        "rdfs": "#f39c12",      # Orange
        "owl": "#27ae60"        # Green
    }
    
    # Panel 1: ReSHACL Only
    ax1 = axes[0]
    for i, reasoning in enumerate(reasoning_levels):
        violations = reshacl_only[reasoning]
        offset = (i - 1) * width
        ax1.bar(x + offset, violations, width, label=reasoning.upper(), color=colors[reasoning])
    
    ax1.set_xlabel('Dataset', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Number of Violations', fontsize=12, fontweight='bold')
    ax1.set_title('ReSHACL Only', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(datasets)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Panel 2: Entailed Shapes Only
    ax2 = axes[1]
    for i, reasoning in enumerate(reasoning_levels):
        violations = entailed_only[reasoning]
        offset = (i - 1) * width
        ax2.bar(x + offset, violations, width, label=reasoning.upper(), color=colors[reasoning])
    
    ax2.set_xlabel('Dataset', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Number of Violations', fontsize=12, fontweight='bold')
    ax2.set_title('Entailed Shapes Only', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(datasets)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # Panel 3: Combined (Entailed + ReSHACL)
    ax3 = axes[2]
    for i, reasoning in enumerate(reasoning_levels):
        violations = combined[reasoning]
        offset = (i - 1) * width
        ax3.bar(x + offset, violations, width, label=reasoning.upper(), color=colors[reasoning])
    
    ax3.set_xlabel('Dataset', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Number of Violations', fontsize=12, fontweight='bold')
    ax3.set_title('Combined (Entailed + ReSHACL)', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(datasets)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # Overall title
    fig.suptitle('Three-Approach Comparison: Violation Detection Across Reasoning Levels', 
                 fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    # Save figure
    output_path = "Outputs/three_approach_comparison/three_approach_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Also save as PDF
    output_path_pdf = "Outputs/three_approach_comparison/three_approach_comparison.pdf"
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"Plot saved to: {output_path_pdf}")
    
    plt.show()

def print_summary_table():
    """Print a summary table of results"""
    data = load_results()
    datasets = data["datasets"]
    reasoning_levels = data["reasoning_levels"]
    results = data["results"]
    
    print("\n" + "=" * 100)
    print("Summary Table: Violation Counts")
    print("=" * 100)
    
    # Header
    header = f"{'Dataset':<12}"
    for approach in ["ReSHACL Only", "Entailed Only", "Combined"]:
        header += f" | {approach:^30}"
    print(header)
    print("-" * 100)
    
    # Subheader with reasoning levels
    subheader = " " * 12
    for _ in range(3):
        subheader += f" | {'None':>8} {'RDFS':>8} {'OWL':>8}"
    print(subheader)
    print("=" * 100)
    
    # Data rows
    for i, dataset in enumerate(datasets):
        row = f"{dataset:<12}"
        
        for approach_key in ["reshacl_only", "entailed_only", "combined"]:
            none_val = results[approach_key]["none"][i]
            rdfs_val = results[approach_key]["rdfs"][i]
            owl_val = results[approach_key]["owl"][i]
            row += f" | {none_val:>8} {rdfs_val:>8} {owl_val:>8}"
        
        print(row)
    
    print("=" * 100)

if __name__ == "__main__":
    try:
        print("Loading results and creating plots...")
        plot_three_approach_comparison()
        print_summary_table()
        print("\nDone!")
    except FileNotFoundError:
        print("Error: Results file not found. Please run run_three_approach_comparison.py first.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
