"""
Plot 11: Optimization Metric Evolution across Simulation Time — Shows the objective
function value and its components (weighted mean latency, migration, server usage costs)
over continuous simulation time. Multi-panel figure with total objective + breakdown,
non-optimal status bands, and a bottom event rug track with vertical tick marks.
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


def plot_optimization_metric_by_time(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a multi-panel figure showing optimization metric evolution across continuous simulation time."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    times = data['time']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    panels = [
        ('objective', 'Total Objective', '#212121', True),
        ('latency_cost', 'Latency Cost (Weighted Mean Latency)', '#1565C0', False),
        ('migration_cost', 'Migration Cost', '#C62828', False),
        ('server_usage_cost', 'Server Usage Cost', '#2E7D32', False),
    ]

    solver_statuses = data.get('solver_status', np.array(['Optimal'] * len(times), dtype=object))
    infeasible_mask = (data['objective'] >= 500000.0) | (solver_statuses != 'Optimal')

    STATUS_STYLES = {
        'Infeasible': {'facecolor': '#FFCDD2', 'edgecolor': '#E57373', 'alpha': 0.35, 'hatch': '///', 'label': 'Infeasible (Resource Limit)'},
        'Disconnected': {'facecolor': '#D1C4E9', 'edgecolor': '#9575CD', 'alpha': 0.35, 'hatch': '\\\\\\', 'label': 'Disconnected (No Viable Paths)'},
        'Not Solved': {'facecolor': '#FFE082', 'edgecolor': '#FFA000', 'alpha': 0.35, 'hatch': 'xx', 'label': 'Not Solved (Time Limit)'},
    }

    # Collect events for the rug plot
    all_event_times = []
    all_event_colors = []
    for action, t in zip(data['event_action'], times):
        if action and action != 'init':
            all_event_times.append(t)
            all_event_colors.append(EVENT_DOMAIN_COLORS.get(action, '#424242'))

    # 4 metric panels + 1 slim bottom strip for event occurrence rug ticks
    fig, axes = plt.subplots(5, 1, figsize=(10, 10.5), sharex=True,
                             gridspec_kw={'height_ratios': [1.0, 1.0, 1.0, 1.0, 0.22]})
    fig.suptitle(f'Optimization Metric Evolution across Simulation Time — {label}',
                 fontsize=13, fontweight='bold', y=0.985)

    metric_axes = axes[:4]
    rug_ax = axes[4]

    max_t = float(np.max(times)) if len(times) > 0 else 100.0
    min_t = float(np.min(times)) if len(times) > 0 else 0.0
    t_range = max_t - min_t if max_t > min_t else 1.0

    # -------------------------------------------------------------------------
    # Render Metric Panels
    # -------------------------------------------------------------------------
    for ax, (key, title, color, is_total) in zip(metric_axes, panels):
        raw_vals = data[key]
        clean_vals = np.where(infeasible_mask, np.nan, raw_vals)
        valid_indices = np.where(~infeasible_mask)[0]

        ax.plot(times, clean_vals, color=color, linewidth=1.2 if not is_total else 1.8,
                alpha=0.7, label=title if is_total else None)

        # Smoothed trend over time
        if len(valid_indices) > 20:
            valid_times = times[valid_indices]
            valid_data = clean_vals[valid_indices]
            window = max(5, min(50, len(valid_data) // 50))
            smoothed = np.convolve(valid_data, np.ones(window) / window, mode='valid')
            smoothed_t = valid_times[window - 1:]

            # Break trend line across non-optimal gaps so it does not bridge through infeasible/disconnected periods
            smoothed_t_seg = []
            smoothed_v_seg = []
            for i in range(len(smoothed)):
                if i > 0:
                    orig_idx = valid_indices[window - 1 + i]
                    prev_orig_idx = valid_indices[window - 1 + i - 1]
                    if orig_idx > prev_orig_idx + 1:
                        smoothed_t_seg.append(np.nan)
                        smoothed_v_seg.append(np.nan)
                smoothed_t_seg.append(smoothed_t[i])
                smoothed_v_seg.append(smoothed[i])

            ax.plot(smoothed_t_seg, smoothed_v_seg, color=color, linewidth=2.2,
                    alpha=0.95, label=f'Trend (MA, w={window})' if is_total else None)

        ax.fill_between(times, clean_vals, alpha=0.08, color=color)
        ax.set_ylabel('Cost', fontsize=9.5)
        ax.set_title(title, fontsize=10.5, loc='left', pad=4)
        ax.grid(True, linestyle='--', alpha=0.35)

        # Draw shaded bands for non-optimal periods mapped over continuous time
        for status_key, style in STATUS_STYLES.items():
            matching_indices = np.where(solver_statuses == status_key)[0]
            if len(matching_indices) == 0:
                continue

            blocks = []
            block_start = matching_indices[0]
            prev = block_start
            for idx in matching_indices[1:]:
                if idx == prev + 1:
                    prev = idx
                else:
                    blocks.append((block_start, prev))
                    block_start = idx
                    prev = idx
            blocks.append((block_start, prev))

            labeled = False
            for b_start, b_end in blocks:
                t0 = times[b_start]
                t1 = times[b_end]
                # Ensure single-step or instantaneous events have visible width
                if t1 <= t0:
                    next_idx = min(len(times) - 1, b_end + 1)
                    t1 = times[next_idx] if times[next_idx] > t0 else t0 + 0.002 * t_range

                ax.axvspan(t0, t1, facecolor=style['facecolor'],
                           alpha=style['alpha'], hatch=style['hatch'],
                           edgecolor=style['edgecolor'], linewidth=0.5,
                           label=style['label'] if (is_total and not labeled) else None)
                labeled = True

        # Statistics annotation (on valid values)
        finite_vals = raw_vals[~infeasible_mask]
        if len(finite_vals) > 0:
            mean_val = np.mean(finite_vals)
            std_val = np.std(finite_vals)
            ax.axhline(y=mean_val, color=color, linewidth=0.8, linestyle=':', alpha=0.5)
            ax.text(0.98, 0.90, f'μ = {mean_val:.2f}   σ = {std_val:.2f}',
                    transform=ax.transAxes, ha='right', va='top',
                    fontsize=8, color=color,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=color, alpha=0.8, linewidth=0.7))

            y_min = np.nanmin(clean_vals)
            y_max = np.nanmax(clean_vals)
            if y_max > y_min:
                y_rng = y_max - y_min
                ax.set_ylim(bottom=max(0, y_min - 0.1 * y_rng), top=y_max + 0.28 * y_rng)
            elif y_max > 0:
                ax.set_ylim(bottom=0, top=y_max * 1.35)
            else:
                ax.set_ylim(bottom=-0.05, top=1.0)

        if is_total:
            ax.legend(loc='upper left', fontsize=8.0, framealpha=0.9, facecolor='white', edgecolor='#B0BEC5')

    # -------------------------------------------------------------------------
    # Render Bottom Rug Track: Event Occurrences in Time
    # -------------------------------------------------------------------------
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

    plt.tight_layout(rect=[0, 0, 1, 0.97])

    ensure_output_dir(output_dir)
    pdf_path = os.path.join(output_dir, f'plot11_optimization_by_time_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot11_optimization_by_time_{scenario_key}.png')
    fig.savefig(pdf_path, format='pdf')
    fig.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

    print(f'  [Plot 11] Saved: {pdf_path}')
    print(f'  [Plot 11] Saved: {png_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 11: Optimization Metric Evolution across Simulation Time')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_optimization_metric_by_time(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
