import matplotlib.pyplot as plt
import numpy as np

# Constants for plot configuration
BAR_WIDTH = 0.15
ERROR_BAR_X_OFFSET = -0.1

regimes = ('$Shapes30_3$', '$Shapes30_6$', '$Shapes30_{15}$', '$Shapes30_{30}$')
num_violations = {
    'PySHACL': (
    [17.27, 16.328200006102552, 18.220788654074045], [23.8, 22.723141578442835, 24.870773248268186], [29.3, 25.802633762848437, 32.80241950304105], [71.85, 38.03763274916024, 105.65997874172517]),
    'PySHACL-RDFS': (
    [67.08, 65.14345396891795, 69.02022324665822], [75.95, 69.81117387341648, 82.09265490643988], [102.0, 34.84305603003645, 169.14742709501442], [127.83, 75.08217486062446, 180.58288168590468]),
    'Closed-Shaper-RDFS': (
    [67.82, 66.20835399093018, 69.42612855174356], [75.19, 66.30620034084214, 84.07111120675512], [78.52, 76.52822111472115, 80.50510280902559], [120.11, 101.2162830688039, 139.0069868706187]),
}

x_positions = np.arange(len(regimes))  # the label locations
bar_group_multiplier = 0


fig, ax = plt.subplots(layout='constrained')
fig.set_figwidth(7)

for attribute, measurement in num_violations.items():
    offset = BAR_WIDTH * bar_group_multiplier
    measurement_with_errors = [[mean, abs(lower-mean), abs(upper-mean)] for mean, lower, upper in measurement]
    print(measurement_with_errors)
    mean_values = list(zip(*measurement_with_errors))[0]
    error_bars = list(zip(*measurement_with_errors))[1:]

    print(mean_values)
    print(error_bars)
    ax.errorbar(x_positions + offset + ERROR_BAR_X_OFFSET, mean_values, yerr=error_bars, fmt='o', label=attribute,
                elinewidth=1, capsize=2)
    bar_group_multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Mean Run Time')
ax.set_title('Total execution time with and without Closed-Shaper\nin seconds for dataset EnDe-Lite50')
ax.set_xticks(x_positions + BAR_WIDTH, regimes)
ax.legend(loc='upper right', ncol=3)
ax.set_ylim(1, 210)

plt.savefig("./plots/runtime_analysis_endelite_new50.pdf", bbox_inches='tight')