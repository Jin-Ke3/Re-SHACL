"""
Plot comparison of reasoning levels (None, RDFS, OWL-LD) on closed shape validation.
Shows the impact of different reasoning regimes on violation detection.
"""

import matplotlib.pyplot as plt
import numpy as np

# Plot configuration
FIGURE_WIDTH = 6.0
FIGURE_HEIGHT = 2.4
AXIS_LABEL_SIZE = 14
TICK_LABEL_SIZE = 12
LEGEND_SIZE = 12

# Data from reasoning comparison experiment
datasets = ['SG1', 'SG2', 'SG3', 'SG4']

# Violation counts by reasoning level
no_reasoning = [11, 12, 0, 2]
rdfs_reasoning = [11, 9, 3, 2]
owl_reasoning = [37, 35, 27, 5]

# Calculate y-axis limit
all_values = no_reasoning + rdfs_reasoning + owl_reasoning
y_max = max(all_values) * 1.15  # Add 15% margin for bar labels

# Create figure
fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

# Bar width and positions
x = np.arange(len(datasets))
width = 0.25  # Width for 3 bars

# Plot three bars for each dataset
bars1 = ax.bar(x - width, no_reasoning, width, label='No Reasoning', 
               color='#95a5a6', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x, rdfs_reasoning, width, label='RDFS', 
               color='#3498db', alpha=0.8, edgecolor='black')
bars3 = ax.bar(x + width, owl_reasoning, width, label='OWL-LD', 
               color='#e74c3c', alpha=0.8, edgecolor='black')

# Configure axes
ax.set_ylabel('Violation Count', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
ax.set_xlabel('Shape Graph', fontsize=AXIS_LABEL_SIZE, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=TICK_LABEL_SIZE)
ax.tick_params(axis='y', labelsize=TICK_LABEL_SIZE)
ax.set_ylim(0, y_max)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

# Add value labels on bars
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{int(height)}',
               ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()

# Save the figure
output_path = 'Outputs/reasoning_comparison.pdf'
plt.savefig(output_path, format='pdf', bbox_inches='tight')
print(f"Plot saved to: {output_path}")

# Create separate legend figure (horizontal)
fig_legend, ax_legend = plt.subplots(figsize=(4.5, 0.4))
ax_legend.axis('off')

# Get handles and labels from the plot
handles, labels = ax.get_legend_handles_labels()

# Create horizontal legend
legend = ax_legend.legend(handles, labels, 
                         loc='center', 
                         ncol=3, 
                         fontsize=LEGEND_SIZE,
                         frameon=False)

# Save legend separately
legend_path = 'Outputs/reasoning_comparison_legend.pdf'
plt.savefig(legend_path, format='pdf', bbox_inches='tight')
print(f"Legend saved to: {legend_path}")

plt.show()
