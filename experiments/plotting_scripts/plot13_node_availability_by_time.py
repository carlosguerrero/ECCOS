"""
Plot 13: Node Availability across Simulation Time — Shows the evolution of
active vs. disabled nodes over continuous simulation time (stacked area & lines),
with an annotation of peak disabled nodes and a bottom event rug track.
Based on Plot 5.
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


def plot_node_availability_by_time(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a figure showing node availability evolution across continuous simulation time."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    times = data['time']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    enabled = data['enabled_nodes']
    disabled = data['disabled_nodes']
    total = enabled + disabled

    max_t = float(np.max(times)) if len(times) > 0 else 100.0
    min_t = float(np.min(times)) if len(times) > 0 else 0.0
    t_range = max_t - min_t if max_t > min_t else 1.0

    fig, (ax, rug_ax) = plt.subplots(2, 1, figsize=(10, 3.2), sharex=True,
                                     gridspec_kw={'height_ratios': [1.0, 0.22]})
    fig.suptitle(f'Node Availability across Simulation Time — {label}',
                 fontsize=13, fontweight='bold', y=0.98)

    # Stacked area: enabled (green) + disabled (red)
    ax.fill_between(times, 0, enabled, alpha=0.35, color='#2E7D32',
                    label='Active Nodes')
    ax.fill_between(times, enabled, total, alpha=0.35, color='#C62828',
                    label='Disabled Nodes')

    # Lines on top
    ax.plot(times, enabled, color='#1B5E20', linewidth=1.8, alpha=0.9)
    ax.plot(times, total, color='#B71C1C', linewidth=1.2, alpha=0.7, linestyle='--')
    ax.plot(times, disabled, color='#D32F2F', linewidth=1.5, alpha=0.9)

    # Annotate max disabled
    max_disabled_idx = np.argmax(disabled)
    max_disabled_val = disabled[max_disabled_idx]
    if max_disabled_val > 0:
        t_peak = times[max_disabled_idx]
        offset_x = 0.05 * t_range
        if t_peak + offset_x > max_t * 0.85:
            text_x = t_peak - offset_x
            ha = 'right'
        else:
            text_x = t_peak + offset_x
            ha = 'left'

        ax.annotate(f'Max disabled: {max_disabled_val} (t={t_peak:.1f})',
                    xy=(t_peak, max_disabled_val),
                    xytext=(text_x, max_disabled_val + 2),
                    arrowprops=dict(arrowstyle='->', color='#C62828', lw=1.2),
                    fontsize=9, color='#C62828', fontweight='bold', ha=ha)

    ax.set_ylabel('Number of Nodes', fontsize=10)
    ax.legend(loc='center right', fontsize=9.5, framealpha=0.9, facecolor='white', edgecolor='#B0BEC5')
    ax.set_ylim(bottom=0, top=total.max() + 3.5)
    ax.grid(True, linestyle='--', alpha=0.35)

    # -------------------------------------------------------------------------
    # Bottom Rug Track: Event Occurrences in Time
    # -------------------------------------------------------------------------
    all_event_times = []
    all_event_colors = []
    for action, t in zip(data['event_action'], times):
        if action and action != 'init':
            all_event_times.append(t)
            all_event_colors.append(EVENT_DOMAIN_COLORS.get(action, '#424242'))

    rug_ax.set_facecolor('#FAFAFA')
    rug_ax.axhline(y=0, color='#CFD8DC', linewidth=0.6, zorder=1)
    if all_event_times:
        rug_ax.vlines(all_event_times, ymin=-0.45, ymax=0.45,
                      colors=all_event_colors, linewidth=0.9, alpha=0.75, zorder=3)

    rug_ax.set_yticks([0])
    rug_ax.set_yticklabels(['│ Events'], fontsize=8.5, fontweight='bold', color='#212121')
    rug_ax.set_ylim(-0.6, 0.6)
    rug_ax.grid(True, axis='x', linestyle='--', alpha=0.35)
    rug_ax.set_xlabel('Simulation Time (time units)', fontsize=10.5)
    rug_ax.set_xlim(-0.01 * max_t, max_t * 1.015)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    ensure_output_dir(output_dir)
    pdf_path = os.path.join(output_dir, f'plot13_node_availability_by_time_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot13_node_availability_by_time_{scenario_key}.png')
    fig.savefig(pdf_path, format='pdf')
    fig.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

    print(f'  [Plot 13] Saved: {pdf_path}')
    print(f'  [Plot 13] Saved: {png_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 13: Node Availability across Simulation Time')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_node_availability_by_time(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
