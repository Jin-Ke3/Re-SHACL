"""Performance Bar Plotter for SHACL Validation Experiments

This module provides visualization tools for comparing SHACL validation
performance across different methods and datasets.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Tuple, Optional


class PerformanceBarPlotter:
    """
    Creates error bar plots for comparing validation performance metrics.
    
    This class encapsulates the logic for creating publication-quality
    performance comparison plots with confidence intervals.
    """
    
    # Plot style constants
    BAR_WIDTH = 0.15
    ERROR_BAR_X_OFFSET = -0.1
    DEFAULT_FIG_WIDTH = 7
    
    def __init__(self, 
                 regimes: Tuple[str, ...], 
                 measurements: Dict[str, Tuple[List[float], ...]],
                 title: str = "Performance Comparison",
                 ylabel: str = "Mean Run Time"):
        """
        Initialize the plotter with data and configuration.
        
        Args:
            regimes: Tuple of regime labels (x-axis labels).
            measurements: Dictionary mapping method names to measurement tuples.
                Each measurement is [mean, lower_bound, upper_bound].
            title: Plot title.
            ylabel: Y-axis label.
        """
        self.regimes = regimes
        self.measurements = measurements
        self.title = title
        self.ylabel = ylabel
        self.fig = None
        self.ax = None
    
    def _prepare_error_bars(self, measurement: List[List[float]]) -> Tuple[List[float], List[List[float]]]:
        """
        Convert measurement data to format suitable for error bars.
        
        Args:
            measurement: List of [mean, lower, upper] for each regime.
        
        Returns:
            Tuple of (mean_values, error_bars) where error_bars are [lower_err, upper_err].
        """
        measurement_with_errors = [
            [mean, abs(lower - mean), abs(upper - mean)] 
            for mean, lower, upper in measurement
        ]
        mean_values = list(zip(*measurement_with_errors))[0]
        error_bars = list(zip(*measurement_with_errors))[1:]
        return mean_values, error_bars
    
    def create_plot(self, 
                    figwidth: Optional[float] = None,
                    ylim: Optional[Tuple[float, float]] = None,
                    legend_loc: str = 'upper right',
                    legend_ncol: int = 3) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create the error bar plot with all configured data.
        
        Args:
            figwidth: Figure width in inches (uses default if None).
            ylim: Y-axis limits as (min, max) tuple.
            legend_loc: Legend location string.
            legend_ncol: Number of columns in legend.
        
        Returns:
            Tuple of (figure, axes) matplotlib objects.
        """
        x_positions = np.arange(len(self.regimes))
        
        self.fig, self.ax = plt.subplots(layout='constrained')
        self.fig.set_figwidth(figwidth or self.DEFAULT_FIG_WIDTH)
        
        bar_group_multiplier = 0
        for method_name, measurement in self.measurements.items():
            offset = self.BAR_WIDTH * bar_group_multiplier
            mean_values, error_bars = self._prepare_error_bars(measurement)
            
            print(f"{method_name}: means={mean_values}, errors={error_bars}")
            
            self.ax.errorbar(
                x_positions + offset + self.ERROR_BAR_X_OFFSET,
                mean_values,
                yerr=error_bars,
                fmt='o',
                label=method_name,
                elinewidth=1,
                capsize=2
            )
            bar_group_multiplier += 1
        
        # Configure axes and labels
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_title(self.title)
        self.ax.set_xticks(x_positions + self.BAR_WIDTH, self.regimes)
        self.ax.legend(loc=legend_loc, ncol=legend_ncol)
        
        if ylim:
            self.ax.set_ylim(*ylim)
        
        return self.fig, self.ax
    
    def save_plot(self, output_path: str, **kwargs) -> None:
        """
        Save the plot to a file.
        
        Args:
            output_path: Path where the plot should be saved.
            **kwargs: Additional arguments passed to plt.savefig().
        """
        if self.fig is None:
            raise ValueError("Plot not created yet. Call create_plot() first.")
        
        plt.savefig(output_path, **kwargs)
        print(f"Plot saved to: {output_path}")


def main():
    """Example usage: Plot EnDe-Lite50 performance comparison."""
    regimes = ('$Shapes30_3$', '$Shapes30_6$', '$Shapes30_{15}$', '$Shapes30_{30}$')
    
    measurements = {
        'PySHACL': (
            [17.27, 16.328200006102552, 18.220788654074045],
            [23.8, 22.723141578442835, 24.870773248268186],
            [29.3, 25.802633762848437, 32.80241950304105],
            [71.85, 38.03763274916024, 105.65997874172517]
        ),
        'PySHACL-RDFS': (
            [67.08, 65.14345396891795, 69.02022324665822],
            [75.95, 69.81117387341648, 82.09265490643988],
            [102.0, 34.84305603003645, 169.14742709501442],
            [127.83, 75.08217486062446, 180.58288168590468]
        ),
        'Closed-Shaper-RDFS': (
            [67.82, 66.20835399093018, 69.42612855174356],
            [75.19, 66.30620034084214, 84.07111120675512],
            [78.52, 76.52822111472115, 80.50510280902559],
            [120.11, 101.2162830688039, 139.0069868706187]
        ),
    }
    
    plotter = PerformanceBarPlotter(
        regimes=regimes,
        measurements=measurements,
        title='Total execution time with and without Closed-Shaper\nin seconds for dataset EnDe-Lite50',
        ylabel='Mean Run Time'
    )
    
    plotter.create_plot(ylim=(1, 210))
    plotter.save_plot("./plots/runtime_analysis_endelite_new50.pdf", bbox_inches='tight')


if __name__ == "__main__":
    main()