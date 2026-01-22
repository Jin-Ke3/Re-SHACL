"""
Plot comparison of open vs closed shapes for baseline validation under RDFS and OWL-LD inference.
This demonstrates the impact of closing shapes on violation detection.
"""

import matplotlib.pyplot as plt
import numpy as np

# Plot configuration
PANEL_WIDTH = 3.0
PANEL_HEIGHT = 2.4
AXIS_LABEL_SIZE = 14
TICK_LABEL_SIZE = 12
LEGEND_SIZE = 12

# Data from baseline comparison experiment
datasets = ['SG1', 'SG2', 'SG3', 'SG4']

# RDFS inference results
rdfs_open = [0, 1, 1, 1]
rdfs_closed = [11, 9, 3, 2]

# OWL-LD inference results
owl_open = [0, 4, 2, 0]
owl_closed = [37, 35, 27, 5]

# Calculate y-axis limits for consistency across both panels
all_values = rdfs_open + rdfs_closed + owl_open + owl_closed
y_max = max(all_values) * 1.15  # Add 15% margin for bar labels

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(PANEL_WIDTH * 2, PANEL_HEIGHT))

# Bar width and positions
x = np.arange(len(datasets))
width = 0.35

# Plot 1: RDFS comparison
bars1_open = ax1.bar(x - width/2, rdfs_open, width, label='Open Shapes', 
                     color='#3498db', alpha=0.8, edgecolor='black')
bars1_closed = ax1.bar(x + width/2, rdfs_closed, width, label='Closed Shapes', 
                       color='#e74c3c', alpha=0.8, edgecolor='black')

ax1.set_title('RDFS Inference', fontsize=AXIS_LABEL_SIZE, fontweight='bold', pad=10)
ax1.set_ylabel('Violation Count', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax1.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax1.set_ylim(0, y_max)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Add value labels on bars
for bars in [bars1_open, bars1_closed]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

# Plot 2: OWL-LD comparison
bars2_open = ax2.bar(x - width/2, owl_open, width, label='Open Shapes', 
                     color='#3498db', alpha=0.8, edgecolor='black')
bars2_closed = ax2.bar(x + width/2, owl_closed, width, label='Closed Shapes', 
                       color='#e74c3c', alpha=0.8, edgecolor='black')

ax2.set_title('OWL-LD Inference', fontsize=AXIS_LABEL_SIZE, fontweight='bold', pad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax2.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax2.set_ylim(0, y_max)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_axisbelow(True)

# Add value labels on bars
for bars in [bars2_open, bars2_closed]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

# Add shared xlabel centered between panels
fig.text(0.5, -0.05, 'Shape Graph', ha='center', fontsize=AXIS_LABEL_SIZE, fontweight='bold')

plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # Make room for shared xlabel

# Save the figure
output_path = 'Outputs/baseline_comparison.pdf'
plt.savefig(output_path, format='pdf', bbox_inches='tight')
print(f"Plot saved to: {output_path}")

# Create separate legend figure (horizontal)
fig_legend, ax_legend = plt.subplots(figsize=(3.5, 0.4))
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
legend_path = 'Outputs/baseline_comparison_legend.pdf'
plt.savefig(legend_path, format='pdf', bbox_inches='tight')
print(f"Legend saved to: {legend_path}")

plt.show()
