#!/usr/bin/env python3
"""
Plot Three-Approach Comparison Results

Creates three panels showing violation counts for:
- Panel 1: ReSHACL Only
- Panel 2: Entailed Shapes Only
- Panel 3: Combined (Entailed + ReSHACL)

Each panel shows three bars per dataset (one for each reasoning level: none, RDFS, OWL-LD)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Plot configuration (matching plot_reasoning_comparison.py)
FIGURE_WIDTH = 14.0
FIGURE_HEIGHT = 2.4
AXIS_LABEL_SIZE = 14
TICK_LABEL_SIZE = 12
LEGEND_SIZE = 12

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
    
    # Create figure with two panels side by side (RDFS and OWL-LD only)
    fig, axes = plt.subplots(1, 2, figsize=(FIGURE_WIDTH * 0.67, FIGURE_HEIGHT))
    
    # Common settings
    x = np.arange(len(datasets))
    width = 0.25
    
    # Colors for the three approaches
    approach_colors = {
        "reshacl": "#95a5a6",      # Gray
        "entailed": "#3498db",     # Blue
        "combined": "#e74c3c"      # Red
    }
    
    approach_labels = {
        "reshacl": "ReSHACL",
        "entailed": "Entailed Shapes",
        "combined": "Entailed + ReSHACL"
    }
    
    # Calculate y-axis limit
    all_values = []
    for approach in [reshacl_only, entailed_only, combined]:
        for reasoning in reasoning_levels:
            all_values.extend([v for v in approach[reasoning] if v >= 0])
    y_max = max(all_values) * 1.15 if all_values else 10
    
    reasoning_titles = {
        "rdfs": "RDFS",
        "owl-ld": "OWL-LD"
    }
    
    # Filter reasoning levels to only use RDFS and OWL-LD (skip 'none')
    active_reasoning_levels = [r for r in reasoning_levels if r != "none"]
    
    # Create two panels, one for each reasoning level
    for panel_idx, reasoning in enumerate(active_reasoning_levels):
        ax = axes[panel_idx]
        
        # Get data for this reasoning level
        reshacl_vals = reshacl_only[reasoning]
        entailed_vals = entailed_only[reasoning]
        combined_vals = combined[reasoning]
        
        # Plot three bars for each dataset (reshacl, entailed, combined)
        bars1 = ax.bar(x - width, reshacl_vals, width, label=approach_labels["reshacl"], 
                      color=approach_colors["reshacl"], alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x, entailed_vals, width, label=approach_labels["entailed"], 
                      color=approach_colors["entailed"], alpha=0.8, edgecolor='black')
        bars3 = ax.bar(x + width, combined_vals, width, label=approach_labels["combined"], 
                      color=approach_colors["combined"], alpha=0.8, edgecolor='black')
        
        # Add value labels
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                if height >= 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom', 
                           fontsize=9, fontweight='bold')
        
        # Configure axes
        ax.set_xlabel('Shape Graph', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
        if panel_idx == 0:
            ax.set_ylabel('Violation Count', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
        ax.set_title(reasoning_titles[reasoning], fontsize=AXIS_LABEL_SIZE, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
        ax.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
        ax.set_ylim(0, y_max)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # Save figure
    output_path = "Outputs/three_approach_comparison/three_approach_comparison.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    print(f"Plot saved to: {output_path}")
    
    # Create separate legend figure (horizontal)
    fig_legend, ax_legend = plt.subplots(figsize=(4.5, 0.4))
    ax_legend.axis('off')
    
    # Get handles and labels from the plot
    handles, labels_list = axes[0].get_legend_handles_labels()
    
    # Create horizontal legend
    legend = ax_legend.legend(handles, labels_list, 
                             loc='center', 
                             ncol=3, 
                             fontsize=LEGEND_SIZE,
                             frameon=False)
    
    # Save legend separately
    legend_path = 'Outputs/three_approach_comparison/three_approach_comparison_legend.pdf'
    plt.savefig(legend_path, format='pdf', bbox_inches='tight')
    print(f"Legend saved to: {legend_path}")
    
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
    
    # Subheader with reasoning levels (only RDFS and OWL-LD)
    subheader = " " * 12
    for _ in range(3):
        subheader += f" |      {'RDFS':>8} {'OWL-LD':>8}"
    print(subheader)
    print("=" * 100)
    
    # Data rows
    for i, dataset in enumerate(datasets):
        row = f"{dataset:<12}"
        
        for approach_key in ["reshacl_only", "entailed_only", "combined"]:
            rdfs_val = results[approach_key].get("rdfs", [])[i] if i < len(results[approach_key].get("rdfs", [])) else -1
            owl_val = results[approach_key].get("owl-ld", [])[i] if i < len(results[approach_key].get("owl-ld", [])) else -1
            row += f" |      {rdfs_val:>8} {owl_val:>8}"
        
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
