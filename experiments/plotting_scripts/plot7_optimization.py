"""
Plot 7: Optimization Metric Evolution — Shows the objective function value
and its components (latency, migration, server usage costs) over time.
Multi-panel figure with total objective + breakdown.
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


def plot_optimization_metric(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a multi-panel figure showing optimization metric evolution."""
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    steps = data['steps']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    fig.suptitle(f'Optimization Metric Evolution — {label}',
                 fontsize=14, fontweight='bold', y=0.98)

    panels = [
        ('objective', 'Total Objective', '#212121', True),
        ('latency_cost', 'Latency Cost (Weighted Mean Latency)', '#1565C0', False),
        ('migration_cost', 'Migration Cost', '#C62828', False),
        ('server_usage_cost', 'Server Usage Cost', '#2E7D32', False),
    ]

    solver_statuses = data.get('solver_status', np.array(['Optimal'] * len(steps), dtype=object))
    infeasible_mask = (data['objective'] >= 500000.0) | (solver_statuses != 'Optimal')

    STATUS_STYLES = {
        'Infeasible': {'facecolor': '#FFCDD2', 'edgecolor': '#E57373', 'alpha': 0.35, 'hatch': '///', 'label': 'Infeasible (Resource Limit)'},
        'Disconnected': {'facecolor': '#D1C4E9', 'edgecolor': '#9575CD', 'alpha': 0.35, 'hatch': '\\\\\\', 'label': 'Disconnected (Broken Paths)'},
        'Not Solved': {'facecolor': '#FFE082', 'edgecolor': '#FFA000', 'alpha': 0.35, 'hatch': 'xx', 'label': 'Not Solved (Time Limit)'},
    }

    for ax, (key, title, color, is_total) in zip(axes, panels):
        raw_vals = data[key]
        clean_vals = np.where(infeasible_mask, np.nan, raw_vals)
        valid_indices = np.where(~infeasible_mask)[0]

        ax.plot(steps, clean_vals, color=color, linewidth=1.2 if not is_total else 1.8,
                alpha=0.7, label=title if is_total else None)

        # Smoothed trend
        if len(valid_indices) > 20:
            valid_steps = steps[valid_indices]
            valid_data = clean_vals[valid_indices]
            window = max(5, min(50, len(valid_data) // 50))
            smoothed = np.convolve(valid_data, np.ones(window)/window, mode='valid')
            smoothed_steps = valid_steps[window-1:]

            # Break trend line across non-optimal gaps
            smoothed_s_seg = []
            smoothed_v_seg = []
            for i in range(len(smoothed)):
                if i > 0:
                    orig_idx = valid_indices[window - 1 + i]
                    prev_orig_idx = valid_indices[window - 1 + i - 1]
                    if orig_idx > prev_orig_idx + 1:
                        smoothed_s_seg.append(np.nan)
                        smoothed_v_seg.append(np.nan)
                smoothed_s_seg.append(smoothed_steps[i])
                smoothed_v_seg.append(smoothed[i])

            ax.plot(smoothed_s_seg, smoothed_v_seg, color=color, linewidth=2.2,
                    alpha=0.95, label=f'Trend (w={window})' if is_total else None)

        ax.fill_between(steps, clean_vals, alpha=0.08, color=color)
        ax.set_ylabel('Cost')
        ax.set_title(title, fontsize=11, loc='left', pad=4)

        # Draw shaded bands for non-optimal periods
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
                    blocks.append((steps[block_start], steps[prev]))
                    block_start = idx
                    prev = idx
            blocks.append((steps[block_start], steps[prev]))

            labeled = False
            for start_s, end_s in blocks:
                ax.axvspan(start_s - 0.5, end_s + 0.5, facecolor=style['facecolor'],
                           alpha=style['alpha'], hatch=style['hatch'],
                           edgecolor=style['edgecolor'], linewidth=0.5,
                           label=style['label'] if (is_total and not labeled) else None)
                labeled = True

        # Statistics annotation (on valid values)
        finite_vals = raw_vals[~infeasible_mask]
        if len(finite_vals) > 0:
            mean_val = np.mean(finite_vals)
            std_val = np.std(finite_vals)
            ax.axhline(y=mean_val, color=color, linewidth=0.8, linestyle=':',
                       alpha=0.5)
            ax.text(0.98, 0.92, f'μ={mean_val:.1f}  σ={std_val:.1f}',
                    transform=ax.transAxes, ha='right', va='top',
                    fontsize=8, color=color,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=color, alpha=0.7))

            y_min = np.nanmin(clean_vals)
            y_max = np.nanmax(clean_vals)
            if y_max > y_min:
                y_rng = y_max - y_min
                ax.set_ylim(bottom=max(0, y_min - 0.1 * y_rng), top=y_max + 0.25 * y_rng)
            elif y_max > 0:
                ax.set_ylim(bottom=0, top=y_max * 1.3)
            else:
                ax.set_ylim(bottom=-0.05, top=1.0)

        if is_total:
            ax.legend(loc='upper left', fontsize=8, framealpha=0.85)

    axes[-1].set_xlabel('Simulation Step')
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot7_optimization_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 7] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 7: Optimization Metric')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_optimization_metric(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
