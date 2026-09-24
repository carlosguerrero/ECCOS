"""
Plot 9: Single-Objective Optimization Evolution — Shows the single optimized
objective (Total Weighted Latency) across simulation steps.
Used specifically for single-objective ILP solver runs.
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

INFEASIBLE_THRESHOLD = 500000.0  # Values above this (e.g. 1e6 penalty) represent infeasible steps


def plot_single_objective(sim_dir, scenario_key, output_dir, max_steps=None):
    """
    Generate a plot showing the evolution of the single objective
    (Total Weighted Latency in ms) across simulation steps.
    """
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    steps = data['steps']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # In single-objective, 'objective' or 'total_latency' represent the weighted latency
    raw_values = data.get('total_latency', data.get('objective', np.zeros(len(steps))))
    if len(raw_values) == 0:
        raw_values = data.get('objective', np.zeros(len(steps)))

    fig, ax = plt.subplots(figsize=(10, 3.8))
    fig.suptitle(f'Single-Objective Optimization: Weighted Mean Latency & Solve Time — {label}',
                 fontsize=13, fontweight='bold', y=0.97)

    color = '#1565C0'  # Elegant deep blue

    solver_statuses = data.get('solver_status', np.array(['Optimal'] * len(steps), dtype=object))

    # Detect non-optimal steps (infeasible, disconnected, not solved)
    infeasible_mask = (raw_values >= INFEASIBLE_THRESHOLD) | (solver_statuses != 'Optimal')
    feasible_values = np.where(infeasible_mask, np.nan, raw_values)

    # Main plot curve
    ax.plot(steps, feasible_values, color=color, linewidth=1.4, alpha=0.75,
            label='Objective (Weighted Mean Latency)')
    ax.fill_between(steps, feasible_values, alpha=0.10, color=color)

    # Moving average trend for feasible values
    valid_indices = np.where(~infeasible_mask)[0]
    if len(valid_indices) > 20:
        valid_steps = steps[valid_indices]
        valid_vals = feasible_values[valid_indices]
        window = max(5, min(50, len(valid_vals) // 50))
        smoothed = np.convolve(valid_vals, np.ones(window) / window, mode='valid')
        smoothed_steps = valid_steps[window - 1:]

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

        ax.plot(smoothed_s_seg, smoothed_v_seg, color='#0D47A1', linewidth=2.2,
                alpha=0.95, label=f'Trend (MA, w={window})')

    # Visual styles for distinct non-optimal states
    STATUS_STYLES = {
        'Infeasible': {
            'facecolor': '#FFCDD2',
            'edgecolor': '#E57373',
            'alpha': 0.45,
            'hatch': '///',
            'label': 'Infeasible (Resource Limit)',
        },
        'Disconnected': {
            'facecolor': '#D1C4E9',
            'edgecolor': '#9575CD',
            'alpha': 0.45,
            'hatch': '\\\\\\',
            'label': 'Disconnected (No Viable Paths)',
        },
        'Not Solved': {
            'facecolor': '#FFE082',
            'edgecolor': '#FFA000',
            'alpha': 0.45,
            'hatch': 'xx',
            'label': 'Not Solved (Time Limit Reached)',
        },
    }

    # Render shaded bands for each distinct non-optimal state
    for status_key, style in STATUS_STYLES.items():
        matching_indices = np.where(solver_statuses == status_key)[0]
        if len(matching_indices) == 0:
            continue

        # Group contiguous blocks
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
            s_0 = start_s - 0.5
            s_1 = end_s + 0.5
            ax.axvspan(s_0, s_1, facecolor=style['facecolor'], alpha=style['alpha'],
                       hatch=style['hatch'], edgecolor=style['edgecolor'], linewidth=0.5,
                       label=style['label'] if not labeled else None)
            labeled = True

    # Statistics calculation (excluding infeasible penalties)
    clean_vals = raw_values[~infeasible_mask]
    if len(clean_vals) > 0:
        mean_val = np.mean(clean_vals)
        std_val = np.std(clean_vals)
        min_val = np.min(clean_vals)
        max_val = np.max(clean_vals)

        ax.axhline(y=mean_val, color='#37474F', linewidth=1.1, linestyle='--',
                   alpha=0.75, label=f'Mean Latency (μ={mean_val:.1f} ms)')

    # Secondary Y-axis (Right): Solver Execution Time (s)
    ax2 = ax.twinx()
    time_color = '#D84315'  # Distinct warm amber/rust
    solve_times = data.get('solve_time_seconds', np.zeros(len(steps)))
    if len(solve_times) == 0:
        solve_times = np.zeros(len(steps))

    # Raw solve time points / line
    ax2.plot(steps, solve_times, color=time_color, linewidth=0.9, alpha=0.45,
             label='Solve Time (s)')

    # Smoothed trend for solve time
    max_t = float(np.max(solve_times)) if len(solve_times) > 0 else 0.0
    if len(solve_times) > 20 and max_t > 0:
        window_t = max(5, min(50, len(solve_times) // 50))
        smoothed_t = np.convolve(solve_times, np.ones(window_t) / window_t, mode='valid')
        smoothed_t_steps = steps[window_t - 1:]
        ax2.plot(smoothed_t_steps, smoothed_t, color=time_color, linewidth=1.8,
                 linestyle='-', alpha=0.95, label=f'Solve Time Trend (MA, w={window_t})')

    ax2.set_ylabel('Solver Execution Time (s)', color=time_color, fontsize=10.5)
    ax2.tick_params(axis='y', labelcolor=time_color)
    ax2.grid(False)  # Keep grid only from primary axis

    if max_t > 0:
        ax2.set_ylim(bottom=0, top=max(0.5, max_t * 1.35))
    else:
        ax2.set_ylim(bottom=0, top=1.0)

    # Statistics text annotation
    if len(clean_vals) > 0:
        stats_text = (f'Latency:\n'
                      f'  μ = {mean_val:.1f} ms\n'
                      f'  σ = {std_val:.1f} ms\n'
                      f'  Min = {min_val:.1f} ms\n'
                      f'  Max = {max_val:.1f} ms')
        if max_t > 0:
            mean_t = float(np.mean(solve_times[solve_times > 0])) if np.any(solve_times > 0) else 0.0
            stats_text += (f'\nSolve Time:\n'
                           f'  μ = {mean_t:.3f} s\n'
                           f'  Max = {max_t:.3f} s')

        ax.text(0.98, 0.94, stats_text,
                transform=ax.transAxes, ha='right', va='top',
                fontsize=8.0, color='#212121',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                          edgecolor='#B0BEC5', alpha=0.9, linewidth=0.8))

        # Adequate headroom so data doesn't collide with upper annotations
        y_range = max_val - min_val if max_val > min_val else max_val * 0.1
        y_bottom = max(0, min_val - 0.1 * y_range)
        y_top = max_val + 0.28 * y_range
        ax.set_ylim(bottom=y_bottom, top=y_top)

    ax.set_xlabel('Simulation Step', fontsize=10.5)
    ax.set_ylabel('Weighted Mean Latency (ms)', color=color, fontsize=10.5)
    ax.tick_params(axis='y', labelcolor=color)
    ax.grid(True, linestyle='--', alpha=0.4)

    # Consolidated legend combining both axes
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8.0, framealpha=0.88)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    ensure_output_dir(output_dir)
    pdf_path = os.path.join(output_dir, f'plot9_single_objective_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot9_single_objective_{scenario_key}.png')

    fig.savefig(pdf_path, format='pdf')
    fig.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

    print(f'  [Plot 9] Saved: {pdf_path}')
    print(f'  [Plot 9] Saved: {png_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 9: Single-Objective Optimization Metric')
    parser.add_argument('--sim-dir', required=True, help='Directory containing Simulation*.json files')
    parser.add_argument('--scenario-key', required=True, help='Scenario identifier key')
    parser.add_argument('--output-dir', required=True, help='Output directory for generated plots')
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_single_objective(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
