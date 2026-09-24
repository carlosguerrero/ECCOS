"""
Plot 5: Node Availability — Shows the evolution of active vs. disabled nodes.
A two-series line/area chart with a stacked area showing the number of
enabled and disabled infrastructure nodes at each simulation step.
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
                        SCENARIO_LABELS)


def plot_node_availability(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a figure showing node availability evolution."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    steps = data['steps']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    enabled = data['enabled_nodes']
    disabled = data['disabled_nodes']
    total = enabled + disabled

    # Width unchanged (10), height halved (5 -> 2.5)
    fig, ax = plt.subplots(figsize=(10, 2.5))

    # Stacked area: enabled (green) + disabled (red)
    ax.fill_between(steps, 0, enabled, alpha=0.35, color='#2E7D32',
                    label='Active Nodes')
    ax.fill_between(steps, enabled, total, alpha=0.35, color='#C62828',
                    label='Disabled Nodes')

    # Lines on top
    ax.plot(steps, enabled, color='#1B5E20', linewidth=1.8, alpha=0.9)
    ax.plot(steps, total, color='#B71C1C', linewidth=1.2, alpha=0.7, linestyle='--')
    ax.plot(steps, disabled, color='#D32F2F', linewidth=1.5, alpha=0.9)

    # Annotate max disabled
    max_disabled_idx = np.argmax(disabled)
    max_disabled_val = disabled[max_disabled_idx]
    if max_disabled_val > 0:
        offset_x = max(10, len(steps) // 30)
        ax.annotate(f'Max disabled: {max_disabled_val}',
                    xy=(steps[max_disabled_idx], max_disabled_val),
                    xytext=(steps[max_disabled_idx] + offset_x, max_disabled_val + 2),
                    arrowprops=dict(arrowstyle='->', color='#C62828', lw=1.2),
                    fontsize=9, color='#C62828', fontweight='bold')

    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Number of Nodes')
    ax.set_title(f'Node Availability — {label}', fontsize=13, fontweight='bold')
    ax.legend(loc='center right', fontsize=10)
    ax.set_ylim(bottom=0, top=total.max() + 3)

    plt.tight_layout()

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot5_node_availability_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 5] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 5: Node Availability')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_node_availability(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
