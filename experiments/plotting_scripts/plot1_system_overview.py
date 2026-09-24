"""
Plot 1: System Overview — Evolution of key system metrics over simulation steps.
Generates a single multi-panel figure showing:
  - Number of users
  - Number of applications
  - Total RAM demand
  - Total CPU demand
  - Total request rate
"""

import os
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import (configure_matplotlib, load_all_steps, ensure_output_dir,
                        SCENARIO_COLORS, SCENARIO_LABELS)


def plot_system_overview(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a 5-panel system overview figure for one experiment."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    steps = data['steps']
    
    color = SCENARIO_COLORS.get(scenario_key, '#333333')
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)
    
    fig, axes = plt.subplots(5, 1, figsize=(10, 12), sharex=True)
    fig.suptitle(f'System Overview — {label}', fontsize=15, fontweight='bold', y=0.98)
    
    panels = [
        ('num_users', 'Number of Users', 'Users', '#1565C0'),
        ('num_apps', 'Number of Applications', 'Applications', '#6A1B9A'),
        ('total_ram_demand', 'Total RAM Demand (GB)', 'RAM (GB)', '#C62828'),
        ('total_cpu_demand', 'Total CPU Demand (vCPUs)', 'CPU (vCPUs)', '#EF6C00'),
        ('total_requests', 'Total Request Rate', 'Req/unit time', '#2E7D32'),
    ]
    
    for ax, (key, title, ylabel, panel_color) in zip(axes, panels):
        values = data[key]
        ax.plot(steps, values, color=panel_color, linewidth=1.2, alpha=0.85)
        # Add smoothed trend line (adaptive moving average window)
        if len(values) > 20:
            window = max(5, min(50, len(values) // 50))
            smoothed = np.convolve(values, np.ones(window)/window, mode='valid')
            ax.plot(steps[window-1:], smoothed, color=panel_color, linewidth=2.2, 
                    alpha=0.95, linestyle='-', label='Trend')
        ax.fill_between(steps, values, alpha=0.08, color=panel_color)
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11, loc='left', pad=4)
        ax.tick_params(axis='both', which='major')
    
    axes[-1].set_xlabel('Simulation Step')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot1_system_overview_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 1] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 1: System Overview')
    parser.add_argument('--sim-dir', required=True, help='Path to simulation directory')
    parser.add_argument('--scenario-key', required=True, help='Scenario identifier key')
    parser.add_argument('--output-dir', required=True, help='Output directory for PDF')
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_system_overview(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
