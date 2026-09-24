"""
Plot 6: Event Timeline — Scatter plot showing which events were triggered at
each simulation step. Events are represented on the Y-axis, and each dot
indicates an occurrence at that step on the X-axis.
"""

import os
import sys
import argparse
import numpy as np
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import (configure_matplotlib, load_all_steps, ensure_output_dir,
                        SCENARIO_LABELS)
# Ordered event types grouped by domain for a clean Y-axis
EVENT_ORDER = [
    # Infrastructure
    'disable_node', 'degrade_node', 'revive_node', 'restore_node',
    'disable_edge', 'congest_edge', 'revive_edge', 'clear_edge',
    # User
    'new_user', 'remove_user', 'move_user', 'suspend_user', 'resume_user',
    'change_request_ratio',
    # Application
    'new_app', 'remove_app', 'surge_popularity', 'drop_popularity', 'restore_popularity',
    'geo_demand_shift', 'update_app_footprint', 'update_app_network',
    'update_app_topology',
    # Composed / custom
    'lightning_strike', 'crowd_surge', 'viral_cascade',
    'catastrophic_failure_and_surge',
]

EVENT_DOMAIN_COLORS = {
    'disable_node': '#D32F2F', 'degrade_node': '#E57373', 'revive_node': '#81C784',
    'restore_node': '#66BB6A',
    'disable_edge': '#BF360C', 'congest_edge': '#FF8A65', 'revive_edge': '#A5D6A7',
    'clear_edge': '#4CAF50',
    'new_user': '#1565C0', 'remove_user': '#42A5F5', 'move_user': '#90CAF9',
    'suspend_user': '#7986CB', 'resume_user': '#64B5F6',
    'change_request_ratio': '#5C6BC0',
    'new_app': '#F57C00', 'remove_app': '#FFB74D', 'surge_popularity': '#FF6F00',
    'drop_popularity': '#FFA726', 'restore_popularity': '#FF8F00',
    'geo_demand_shift': '#FFCA28',
    'update_app_footprint': '#FFB300', 'update_app_network': '#FDD835',
    'update_app_topology': '#FFE082',
    'lightning_strike': '#880E4F', 'crowd_surge': '#4A148C',
    'viral_cascade': '#311B92', 'catastrophic_failure_and_surge': '#1A237E',
}


def plot_event_timeline(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate an event timeline scatter plot for one experiment."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # Collect events per step
    event_steps = defaultdict(list)
    for i, action in enumerate(data['event_action']):
        if action and action != 'init':
            event_steps[action].append(i)

    # Determine which events actually appear in this experiment
    present_events = [e for e in EVENT_ORDER if e in event_steps]
    # Add any events not in the predefined order
    extra = [e for e in event_steps if e not in present_events]
    present_events.extend(sorted(extra))

    if not present_events:
        print(f'  [Plot 6] WARNING: No events found for {scenario_key}')
        return None

    # Create y-axis mapping
    event_to_y = {e: i for i, e in enumerate(present_events)}
    n_events = len(present_events)

    # Height reduced by 25% (spacing reduced from 0.32 to 0.24 per event line)
    fig, ax = plt.subplots(figsize=(14, max(3.0, n_events * 0.24)))

    for event_name in present_events:
        steps_list = event_steps[event_name]
        y_val = event_to_y[event_name]
        color = EVENT_DOMAIN_COLORS.get(event_name, '#757575')
        # Dots 50% larger: s=12 (was s=8)
        ax.scatter(steps_list, [y_val] * len(steps_list),
                   s=12, color=color, alpha=0.65, edgecolors='none', zorder=2)
        # Add subtle horizontal line
        ax.axhline(y=y_val, color='#E0E0E0', linewidth=0.5, zorder=1)

    num_steps = len(data['steps'])
    ax.set_yticks(range(n_events))
    ax.set_yticklabels(present_events, fontsize=8)
    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Event Type')
    ax.set_title(f'Event Timeline — {label}', fontsize=13, fontweight='bold')
    ax.set_xlim(-5, num_steps + 5)
    ax.set_ylim(-0.5, n_events - 0.5)
    ax.invert_yaxis()

    # Add domain separators (solid black lines to clearly demarcate subgroups)
    domain_boundaries = []
    current_domain = None
    for i, ename in enumerate(present_events):
        if ename in ('disable_node', 'degrade_node', 'revive_node', 'restore_node',
                      'disable_edge', 'congest_edge', 'revive_edge', 'clear_edge'):
            domain = 'Infrastructure'
        elif ename in ('new_user', 'remove_user', 'move_user', 'suspend_user',
                        'resume_user', 'change_request_ratio'):
            domain = 'User'
        elif ename in ('new_app', 'remove_app', 'surge_popularity', 'drop_popularity',
                        'restore_popularity', 'geo_demand_shift', 'update_app_footprint',
                        'update_app_network', 'update_app_topology'):
            domain = 'Application'
        else:
            domain = 'Composed'
        if domain != current_domain and current_domain is not None:
            ax.axhline(y=i - 0.5, color='black', linewidth=1.2,
                       linestyle='-', alpha=1.0, zorder=3)
        current_domain = domain

    plt.tight_layout()

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot6_event_timeline_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 6] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 6: Event Timeline')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_event_timeline(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
