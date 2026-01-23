"""
Plot runtime comparison with stacked bars: Baseline vs Our Approach (Entailment + Validation)

This script creates a visualization showing:
- Baseline: Single bar for direct validation time
- Our Approach: Stacked bar showing entailment time + validation time

The stacked bar clearly shows the time breakdown of our approach.
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os

# Plot configuration
PANEL_WIDTH = 3.5
PANEL_HEIGHT = 2.6
AXIS_LABEL_SIZE = 14
TICK_LABEL_SIZE = 12
LEGEND_SIZE = 11

# Try to load from JSON file first, fall back to hardcoded data
json_path = 'Outputs/runtime_comparison/runtime_results.json'
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    datasets = data['datasets']
    rdfs_baseline = data['results']['rdfs']['baseline_time']
    rdfs_entailment = data['results']['rdfs']['entailment_time']
    rdfs_validation = data['results']['rdfs']['entailed_validation_time']
    owl_baseline = data['results']['owl-ld']['baseline_time']
    owl_entailment = data['results']['owl-ld']['entailment_time']
    owl_validation = data['results']['owl-ld']['entailed_validation_time']
    print(f"Loaded data from: {json_path}")
else:
    print(f"JSON file not found: {json_path}")
    print("Using placeholder data. Run the experiment first!")
    # Placeholder data (will be replaced after running experiment)
    datasets = ['SG1', 'SG2', 'SG3', 'SG4']
    
    # RDFS inference results (in seconds)
    rdfs_baseline = [0.0500, 0.0480, 0.0450, 0.0420]
    rdfs_entailment = [0.0150, 0.0140, 0.0130, 0.0120]
    rdfs_validation = [0.0280, 0.0270, 0.0260, 0.0250]
    
    # OWL-LD inference results (in seconds)
    owl_baseline = [0.0800, 0.0780, 0.0750, 0.0650]
    owl_entailment = [0.0250, 0.0240, 0.0230, 0.0200]
    owl_validation = [0.0400, 0.0390, 0.0380, 0.0320]

# Convert to numpy arrays and convert seconds to milliseconds
rdfs_baseline = np.array(rdfs_baseline) * 1000
rdfs_entailment = np.array(rdfs_entailment) * 1000
rdfs_validation = np.array(rdfs_validation) * 1000
owl_baseline = np.array(owl_baseline) * 1000
owl_entailment = np.array(owl_entailment) * 1000
owl_validation = np.array(owl_validation) * 1000

# Calculate y-axis limits
all_values = np.concatenate([
    rdfs_baseline,
    rdfs_entailment + rdfs_validation,
    owl_baseline,
    owl_entailment + owl_validation
])
y_max = max(all_values) * 1.20  # Add 20% margin for labels

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(PANEL_WIDTH * 2, PANEL_HEIGHT))

# Bar width and positions
x = np.arange(len(datasets))
width = 0.35

# Colors
COLOR_BASELINE = '#e74c3c'  # Red for baseline
COLOR_ENTAILMENT = '#3498db'  # Blue for entailment
COLOR_VALIDATION = '#2ecc71'  # Green for validation

# ========== Plot 1: RDFS comparison ==========
# Baseline bars (simple)
bars1_baseline = ax1.bar(x - width/2, rdfs_baseline, width, 
                         label='Baseline', 
                         color=COLOR_BASELINE, alpha=0.8, edgecolor='black')

# Our approach bars (stacked)
bars1_entailment = ax1.bar(x + width/2, rdfs_entailment, width, 
                           label='Entailment', 
                           color=COLOR_ENTAILMENT, alpha=0.8, edgecolor='black')
bars1_validation = ax1.bar(x + width/2, rdfs_validation, width, 
                          bottom=rdfs_entailment,
                          label='Validation', 
                          color=COLOR_VALIDATION, alpha=0.8, edgecolor='black')

ax1.set_title('RDFS Inference', fontsize=AXIS_LABEL_SIZE, fontweight='bold', pad=10)
ax1.set_ylabel('Execution Time (ms)', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax1.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax1.set_ylim(0, y_max)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Add value labels on baseline bars
for bar in bars1_baseline:
    height = bar.get_height()
    if height > 0:
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

# Add total time labels on stacked bars (at top)
rdfs_total = rdfs_entailment + rdfs_validation
for i, (bar, total) in enumerate(zip(bars1_validation, rdfs_total)):
    if total > 0:
        ax1.text(bar.get_x() + bar.get_width()/2., total,
                f'{total:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

# ========== Plot 2: OWL-LD comparison ==========
# Baseline bars (simple)
bars2_baseline = ax2.bar(x - width/2, owl_baseline, width, 
                         label='Baseline', 
                         color=COLOR_BASELINE, alpha=0.8, edgecolor='black')

# Our approach bars (stacked)
bars2_entailment = ax2.bar(x + width/2, owl_entailment, width, 
                           label='Entailment', 
                           color=COLOR_ENTAILMENT, alpha=0.8, edgecolor='black')
bars2_validation = ax2.bar(x + width/2, owl_validation, width, 
                          bottom=owl_entailment,
                          label='Validation', 
                          color=COLOR_VALIDATION, alpha=0.8, edgecolor='black')

ax2.set_title('OWL-LD Inference', fontsize=AXIS_LABEL_SIZE, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax2.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax2.set_ylim(0, y_max)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_axisbelow(True)

# Add value labels on baseline bars
for bar in bars2_baseline:
    height = bar.get_height()
    if height > 0:
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

# Add total time labels on stacked bars (at top)
owl_total = owl_entailment + owl_validation
for i, (bar, total) in enumerate(zip(bars2_validation, owl_total)):
    if total > 0:
        ax2.text(bar.get_x() + bar.get_width()/2., total,
                f'{total:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

# Add shared xlabel centered between panels
fig.text(0.5, -0.05, 'Shape Graph', ha='center', fontsize=AXIS_LABEL_SIZE, fontweight='bold')

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # Make room for shared xlabel

# Save the figure
output_path = 'Outputs/runtime_comparison.pdf'
plt.savefig(output_path, format='pdf', bbox_inches='tight')
print(f"Plot saved to: {output_path}")

# Create separate legend figure (horizontal)
fig_legend, ax_legend = plt.subplots(figsize=(4.5, 0.4))
ax_legend.axis('off')

# Get handles and labels from one of the plots
# Baseline is standard validation, Entailment is our approach, Validation is standard SHACL validation
handles = [bars1_baseline, bars1_entailment, bars1_validation]
labels = ['Baseline (Validation Only)', 'Shape Entailment (Our Approach)', 'Validation']

# Create horizontal legend
legend = ax_legend.legend(handles, labels, 
                         loc='center', 
                         ncol=3, 
                         fontsize=LEGEND_SIZE,
                         frameon=False)

# Save legend separately
legend_path = 'Outputs/runtime_comparison_legend.pdf'
plt.savefig(legend_path, format='pdf', bbox_inches='tight')
print(f"Legend saved to: {legend_path}")

# Print summary statistics
print("\n" + "=" * 80)
print("Performance Summary:")
print("=" * 80)

print("\nRDFS Inference:")
for i, ds in enumerate(datasets):
    baseline = rdfs_baseline[i]
    total = rdfs_entailment[i] + rdfs_validation[i]
    speedup = baseline / total if total > 0 else float('inf')
    diff_pct = ((baseline - total) / baseline * 100) if baseline > 0 else 0
    print(f"  {ds}: Baseline={baseline:.2f}ms, Our Approach={total:.2f}ms, "
          f"Speedup={speedup:.2f}x, Diff={diff_pct:+.1f}%")

print("\nOWL-LD Inference:")
for i, ds in enumerate(datasets):
    baseline = owl_baseline[i]
    total = owl_entailment[i] + owl_validation[i]
    speedup = baseline / total if total > 0 else float('inf')
    diff_pct = ((baseline - total) / baseline * 100) if baseline > 0 else 0
    print(f"  {ds}: Baseline={baseline:.2f}ms, Our Approach={total:.2f}ms, "
          f"Speedup={speedup:.2f}x, Diff={diff_pct:+.1f}%")

plt.show()
