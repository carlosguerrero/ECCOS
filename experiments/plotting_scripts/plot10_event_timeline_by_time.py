"""
Plot 10: Event Timeline by Simulation Time — Scatter plot showing which events
occurred across continuous simulation time (X-axis). Each event type is displayed
on the Y-axis with points indicating occurrences, and small vertical tick marks
along the axis / rug track indicate each event occurrence in time.
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


def plot_event_timeline_by_time(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate an event timeline plot indexed by continuous simulation time."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    event_times = defaultdict(list)
    all_event_times = []
    all_event_colors = []

    for action, t in zip(data['event_action'], data['time']):
        if action and action != 'init':
            event_times[action].append(t)
            all_event_times.append(t)
            all_event_colors.append(EVENT_DOMAIN_COLORS.get(action, '#424242'))

    present_events = [e for e in EVENT_ORDER if e in event_times]
    extra = [e for e in event_times if e not in present_events]
    present_events.extend(sorted(extra))

    if not present_events:
        print(f'  [Plot 10] WARNING: No events found for {scenario_key}')
        return None

    event_to_y = {e: i for i, e in enumerate(present_events)}
    n_events = len(present_events)
    rug_y = n_events  # Row index for the event tick marks

    # Figure height: compact spacing consistent with plot6
    fig, ax = plt.subplots(figsize=(14, max(3.2, (n_events + 1) * 0.24 + 0.5)))

    # 1. Plot dots for each event row
    for event_name in present_events:
        times_list = event_times[event_name]
        y_val = event_to_y[event_name]
        color = EVENT_DOMAIN_COLORS.get(event_name, '#757575')
        ax.scatter(times_list, [y_val] * len(times_list),
                   s=14, color=color, alpha=0.65, edgecolors='none', zorder=3)
        ax.axhline(y=y_val, color='#EEEEEE', linewidth=0.5, zorder=1)

    # 2. Add domain separators (solid black lines)
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
                       linestyle='-', alpha=1.0, zorder=4)
        current_domain = domain

    # Separator before the All Events rug track
    ax.axhline(y=n_events - 0.5, color='black', linewidth=1.2, linestyle='-', zorder=4)

    # 3. Dedicated All Events rug track: small vertical lines for every event occurrence
    ax.axhline(y=rug_y, color='#E0E0E0', linewidth=0.5, zorder=1)
    if all_event_times:
        ax.vlines(all_event_times, ymin=rug_y - 0.35, ymax=rug_y + 0.35,
                  colors=all_event_colors, linewidth=0.9, alpha=0.75, zorder=3)

    # Configure axes
    y_ticks = list(range(n_events)) + [rug_y]
    y_labels = present_events + ['│ All Events']
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels, fontsize=8)

    # Bold font for the '│ All Events' label
    yticklabels = ax.get_yticklabels()
    yticklabels[-1].set_fontweight('bold')
    yticklabels[-1].set_color('#212121')

    max_t = float(np.max(data['time'])) if len(data['time']) > 0 else 100.0
    ax.set_xlabel('Simulation Time (time units)', fontsize=10)
    ax.set_ylabel('Event Type', fontsize=10)
    ax.set_title(f'Event Timeline across Simulation Time — {label}', fontsize=13, fontweight='bold', pad=10)
    ax.set_xlim(-0.01 * max_t, max_t * 1.015)
    ax.set_ylim(-0.5, rug_y + 0.6)
    ax.invert_yaxis()
    ax.grid(True, axis='x', linestyle='--', alpha=0.35)

    plt.tight_layout()

    ensure_output_dir(output_dir)
    pdf_path = os.path.join(output_dir, f'plot10_event_timeline_by_time_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot10_event_timeline_by_time_{scenario_key}.png')
    fig.savefig(pdf_path, format='pdf')
    fig.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

    print(f'  [Plot 10] Saved: {pdf_path}')
    print(f'  [Plot 10] Saved: {png_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 10: Event Timeline by Simulation Time')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_event_timeline_by_time(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
