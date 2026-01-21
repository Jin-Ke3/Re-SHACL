import matplotlib.pyplot as plt
import numpy as np

# regimes = ("None", "RDFS", "OWL-LD")
# num_violations = {
#     'PySHACL': (8, 8, 31),
#     'Re-SHACL': (8, 8, 8),
#     'Closed-Shaper': (8, 3, 0),
#     'Re-SHACL+Closed-Shaper': (8, 3, 0),
# }

# regimes = ("None", "RDFS", "OWL-LD")
# num_violations = {
#     'PySHACL': (8, 8, 31),
#     'Re-SHACL': (8, 8, 8),
#     'Closed-Shaper': (8, 3, 4),
#     'Re-SHACL+Closed-Shaper': (8, 3, 1),
# }

# regimes = ("None", "RDFS", "OWL-LD")
# num_violations = {
#     'DG1 & SG1': (9, 11, 37),
#     'DG2 & SG2': (8, 8, 31),
#     'DG3 & SG3': (0, 3, 27),
#     'DG4 & SG4': (2, 2, 5),
# }


# Number of violations using PySHACL and different types of entailment
# regimes = ('$DG_1$ & $SG_1$', '$DG_2$ & $SG_2$', '$DG_3$ & $SG_3$', '$DG_4$ & $SG_4$')
# num_violations = {
#     'None': (9, 8, 0, 2),
#     'RDFS': (11, 8, 3, 2),
#     'OWL-LD': (37, 31, 27, 5),
# }


# # Comparison of PySHACL and Closed-Shaper using RDFS entailment
# regimes = ('$DG_1$ & $SG_1$', '$DG_2$ & $SG_2$', '$DG_3$ & $SG_3$', '$DG_4$ & $SG_4$')
# num_violations = {
#     'PySHACL': (11, 8, 3, 2),
#     'Closed-Shaper': (6, 3, 3, 2),
# }

# Comparison of PySHACL and Closed-Shaper using RDFS and OWL-LD entailment
# regimes = ('$DG_1$ & $SG_1$', '$DG_2$ & $SG_2$', '$DG_3$ & $SG_3$', '$DG_4$ & $SG_4$')
# num_violations = {
#     'PySHACL': (
#     [1.79, 1.79, 1.79], [1.91, 0, 0], [0.56, 0, 0], [0.79, 0, 0]),
#     'PySHACL-RDFS': (
#     [4.77, 4.77, 4.77], [4.08, 0, 0], [7.73, 0, 0], [2.24, 0, 0]),
#     'Closed-Shaper-RDFS': (
#     [4.92, 4.92, 4.92], [3.71, 0, 0], [8.05, 0, 0], [2.39, 0, 0]),
#     'PySHACL-OWL-LD': (
#     [28.83, 0, 0], [25.90, 0, 0], [48.03, 0, 0], [24.93, 0, 0]),
#     'Closed-Shaper-OWL-LD': (
#     [29.30, 0, 0], [26.24, 0, 0], [38.72, 0, 0], [17.86, 0, 0]),
#
# }
#
regimes = ('$Shapes30_3$', '$Shapes30_6$', '$Shapes30_{15}$', '$Shapes30_{30}$')
num_violations = {
    'PySHACL': (
    [17.27, 16.328200006102552, 18.220788654074045], [23.8, 22.723141578442835, 24.870773248268186], [29.3, 25.802633762848437, 32.80241950304105], [71.85, 38.03763274916024, 105.65997874172517]),
    'PySHACL-RDFS': (
    [67.08, 65.14345396891795, 69.02022324665822], [75.95, 69.81117387341648, 82.09265490643988], [102.0, 34.84305603003645, 169.14742709501442], [127.83, 75.08217486062446, 180.58288168590468]),
    'Closed-Shaper-RDFS': (
    [67.82, 66.20835399093018, 69.42612855174356], [75.19, 66.30620034084214, 84.07111120675512], [78.52, 76.52822111472115, 80.50510280902559], [120.11, 101.2162830688039, 139.0069868706187]),

}

# # Comparison of Re-SHACL, Closed-Shaper and both using OWL entailment
# regimes = ('$DG_1$ & $SG_1$', '$DG_2$ & $SG_2$', '$DG_3$ & $SG_3$', '$DG_4$ & $SG_4$')
# num_violations = {
#     'Re-SHACL': (11, 8, 5, 1),
#     'Closed-Shaper': (9, 0, 8, 0),
#     'Re-SHACL+Closed-Shaper': (3, 0, 2, 0),
# }

x = np.arange(len(regimes))  # the label locations
width = 0.15 # the width of the bars
multiplier = 0


fig, ax = plt.subplots(layout='constrained')
fig.set_figwidth(7)
# plt.yscale('log')
for attribute, measurement in num_violations.items():
    offset = width * multiplier
    # rects = ax.bar(x + offset + 0.105, measurement, width, label=attribute)
    # print(measurement[0][:])
    # print(measurement[:][1])
    temp_measurement = [[x, abs(y-x), abs(z-x)] for x, y, z in measurement]
    print(temp_measurement)
    y = list(zip(*temp_measurement))[0]
    yerr = list(zip(*temp_measurement))[1:]

    print(y)
    print(yerr)
    ax.errorbar(x + offset - 0.1, y, yerr=yerr, fmt='o', label=attribute,
                elinewidth=1, capsize=2)
    # ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Mean Run Time')
ax.set_title('Total execution time with and without Closed-Shaper\nin seconds for dataset EnDe-Lite50')
ax.set_xticks(x + width, regimes)
ax.legend(loc='upper right', ncol=3)
ax.set_ylim(1, 210)

# plt.show()
plt.savefig("./plots/runtime_analysis_endelite_new50.pdf", bbox_inches='tight')