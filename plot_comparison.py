"""
Plot comparison of baseline validation vs entailed shapes for RDFS and OWL-LD inference.
"""

import matplotlib.pyplot as plt
import numpy as np

# Plot configuration
PANEL_WIDTH = 3.0
PANEL_HEIGHT = 2.4
AXIS_LABEL_SIZE = 14
TICK_LABEL_SIZE = 12
LEGEND_SIZE = 12

# Data from pipeline run
datasets = ['DG1', 'DG2', 'DG3', 'DG4']

# RDFS inference results
rdfs_baseline = [11, 9, 3, 2]
rdfs_entailed = [6, 4, 3, 2]

# OWL-LD inference results
owl_baseline = [37, 35, 27, 5]
owl_entailed = [14, 9, 8, 0]

# Calculate y-axis limits for consistency across both panels
all_values = rdfs_baseline + rdfs_entailed + owl_baseline + owl_entailed
y_max = max(all_values) * 1.15  # Add 15% margin for bar labels

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(PANEL_WIDTH * 2, PANEL_HEIGHT))

# Bar width and positions
x = np.arange(len(datasets))
width = 0.35

# Plot 1: RDFS comparison
bars1_baseline = ax1.bar(x - width/2, rdfs_baseline, width, label='Baseline (Original Shapes)', 
                         color='#e74c3c', alpha=0.8, edgecolor='black')
bars1_entailed = ax1.bar(x + width/2, rdfs_entailed, width, label='Entailed Shapes', 
                         color='#2ecc71', alpha=0.8, edgecolor='black')

ax1.set_ylabel('Violation Count', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax1.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax1.set_ylim(0, y_max)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Add value labels on bars
for bars in [bars1_baseline, bars1_entailed]:
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

# Plot 2: OWL-LD comparison
bars2_baseline = ax2.bar(x - width/2, owl_baseline, width, label='Baseline (Original Shapes)', 
                         color='#e74c3c', alpha=0.8, edgecolor='black')
bars2_entailed = ax2.bar(x + width/2, owl_entailed, width, label='Entailed Shapes', 
                         color='#2ecc71', alpha=0.8, edgecolor='black')

ax2.set_xticks(x)
ax2.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax2.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax2.set_ylim(0, y_max)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_axisbelow(True)

# Add value labels on bars
for bars in [bars2_baseline, bars2_entailed]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

# Add shared xlabel centered between panels
fig.text(0.5, -0.05, 'Dataset', ha='center', fontsize=AXIS_LABEL_SIZE, fontweight='bold')

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # Make room for shared xlabel

# Save the figure
output_path = 'Outputs/validation_comparison.pdf'
plt.savefig(output_path, format='pdf', bbox_inches='tight')
print(f"Plot saved to: {output_path}")

# Create separate legend figure (horizontal)
fig_legend, ax_legend = plt.subplots(figsize=(4, 0.4))
ax_legend.axis('off')

# Get handles and labels from one of the plots
handles, labels = ax1.get_legend_handles_labels()

# Create horizontal legend
legend = ax_legend.legend(handles, labels, 
                         loc='center', 
                         ncol=2, 
                         fontsize=LEGEND_SIZE,
                         frameon=False)

# Save legend separately
legend_path = 'Outputs/validation_comparison_legend.pdf'
plt.savefig(legend_path, format='pdf', bbox_inches='tight')
print(f"Legend saved to: {legend_path}")

# 