"""
Plot 12: Single-Objective Optimization Evolution across Simulation Time — Shows the
single optimized objective (Weighted Mean Latency in ms) and Solver Execution Time (s)
over continuous simulation time (dual Y-axis). Includes non-optimal status bands and
a bottom event rug track with vertical tick marks.
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

INFEASIBLE_THRESHOLD = 500000.0

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


def plot_single_objective_by_time(sim_dir, scenario_key, output_dir, max_steps=None):
    """
    Generate a plot showing the evolution of the single objective
    (Weighted Mean Latency in ms) and Solver Execution Time (s) across
    continuous simulation time with event rug marks.
    """
    configure_matplotlib()
    data = load_all_steps(sim_dir, max_steps)
    times = data['time']
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # In single-objective, 'total_latency' or 'objective' represent weighted latency
    raw_values = data.get('total_latency', data.get('objective', np.zeros(len(times))))
    if len(raw_values) == 0:
        raw_values = data.get('objective', np.zeros(len(times)))

    fig, (ax, rug_ax) = plt.subplots(2, 1, figsize=(10, 4.6), sharex=True,
                                     gridspec_kw={'height_ratios': [1.0, 0.16]})
    fig.suptitle(f'Single-Objective Optimization across Simulation Time — {label}',
                 fontsize=13, fontweight='bold', y=0.98)

    color = '#1565C0'  # Deep blue

    solver_statuses = data.get('solver_status', np.array(['Optimal'] * len(times), dtype=object))

    # Detect non-optimal steps (infeasible, disconnected, not solved)
    infeasible_mask = (raw_values >= INFEASIBLE_THRESHOLD) | (solver_statuses != 'Optimal')
    feasible_values = np.where(infeasible_mask, np.nan, raw_values)

    max_t = float(np.max(times)) if len(times) > 0 else 100.0
    min_t = float(np.min(times)) if len(times) > 0 else 0.0
    t_range = max_t - min_t if max_t > min_t else 1.0

    # -------------------------------------------------------------------------
    # 1. Primary Axis: Weighted Mean Latency (ms)
    # -------------------------------------------------------------------------
    ax.plot(times, feasible_values, color=color, linewidth=1.4, alpha=0.75,
            label='Objective (Weighted Mean Latency)')
    ax.fill_between(times, feasible_values, alpha=0.10, color=color)

    # Moving average trend for feasible values
    valid_indices = np.where(~infeasible_mask)[0]
    if len(valid_indices) > 20:
        valid_times = times[valid_indices]
        valid_vals = feasible_values[valid_indices]
        window = max(5, min(50, len(valid_vals) // 50))
        smoothed = np.convolve(valid_vals, np.ones(window) / window, mode='valid')
        smoothed_times = valid_times[window - 1:]

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
            smoothed_t_seg.append(smoothed_times[i])
            smoothed_v_seg.append(smoothed[i])

        ax.plot(smoothed_t_seg, smoothed_v_seg, color='#0D47A1', linewidth=2.2,
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

    # Render shaded bands for each distinct non-optimal state across simulation time
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
                blocks.append((block_start, prev))
                block_start = idx
                prev = idx
        blocks.append((block_start, prev))

        labeled = False
        for b_start, b_end in blocks:
            t0 = times[b_start]
            t1 = times[b_end]
            if t1 <= t0:
                next_idx = min(len(times) - 1, b_end + 1)
                t1 = times[next_idx] if times[next_idx] > t0 else t0 + 0.002 * t_range

            ax.axvspan(t0, t1, facecolor=style['facecolor'], alpha=style['alpha'],
                       hatch=style['hatch'], edgecolor=style['edgecolor'], linewidth=0.5,
                       label=style['label'] if not labeled else None)
            labeled = True

    # Statistics calculation (excluding non-optimal penalties)
    clean_vals = raw_values[~infeasible_mask]
    if len(clean_vals) > 0:
        mean_val = np.mean(clean_vals)
        std_val = np.std(clean_vals)
        min_val = np.min(clean_vals)
        max_val = np.max(clean_vals)

        ax.axhline(y=mean_val, color='#37474F', linewidth=1.1, linestyle='--',
                   alpha=0.75, label=f'Mean Latency (μ={mean_val:.1f} ms)')

    # -------------------------------------------------------------------------
    # 2. Secondary Y-axis (Right): Solver Execution Time (s)
    # -------------------------------------------------------------------------
    ax2 = ax.twinx()
    time_color = '#D84315'  # Distinct warm amber/rust
    solve_times = data.get('solve_time_seconds', np.zeros(len(times)))
    if len(solve_times) == 0:
        solve_times = np.zeros(len(times))

    # Raw solve time points / line
    ax2.plot(times, solve_times, color=time_color, linewidth=0.9, alpha=0.45,
             label='Solve Time (s)')

    # Smoothed trend for solve time
    max_solve_t = float(np.max(solve_times)) if len(solve_times) > 0 else 0.0
    if len(solve_times) > 20 and max_solve_t > 0:
        window_t = max(5, min(50, len(solve_times) // 50))
        smoothed_st = np.convolve(solve_times, np.ones(window_t) / window_t, mode='valid')
        smoothed_st_times = times[window_t - 1:]
        ax2.plot(smoothed_st_times, smoothed_st, color=time_color, linewidth=1.8,
                 linestyle='-', alpha=0.95, label=f'Solve Time Trend (MA, w={window_t})')

    ax2.set_ylabel('Solver Execution Time (s)', color=time_color, fontsize=10.5)
    ax2.tick_params(axis='y', labelcolor=time_color)
    ax2.grid(False)

    if max_solve_t > 0:
        ax2.set_ylim(bottom=0, top=max(0.5, max_solve_t * 1.35))
    else:
        ax2.set_ylim(bottom=0, top=1.0)

    # Statistics text annotation
    if len(clean_vals) > 0:
        stats_text = (f'Latency:\n'
                      f'  μ = {mean_val:.1f} ms\n'
                      f'  σ = {std_val:.1f} ms\n'
                      f'  Min = {min_val:.1f} ms\n'
                      f'  Max = {max_val:.1f} ms')
        if max_solve_t > 0:
            mean_solve_t = float(np.mean(solve_times[solve_times > 0])) if np.any(solve_times > 0) else 0.0
            stats_text += (f'\nSolve Time:\n'
                           f'  μ = {mean_solve_t:.3f} s\n'
                           f'  Max = {max_solve_t:.3f} s')

        ax.text(0.98, 0.94, stats_text,
                transform=ax.transAxes, ha='right', va='top',
                fontsize=8.0, color='#212121',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                          edgecolor='#B0BEC5', alpha=0.9, linewidth=0.8))

        # Adequate headroom so data doesn't collide with upper annotations
        y_range = max_val - min_val if max_val > min_val else max_val * 0.1
        y_bottom = max(0, min_val - 0.1 * y_range)
        y_top = max_val + 0.32 * y_range
        ax.set_ylim(bottom=y_bottom, top=y_top)

    ax.set_ylabel('Weighted Mean Latency (ms)', color=color, fontsize=10.5)
    ax.tick_params(axis='y', labelcolor=color)
    ax.grid(True, linestyle='--', alpha=0.4)

    # Consolidated legend combining both axes
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8.0, framealpha=0.9,
              facecolor='white', edgecolor='#B0BEC5')

    # -------------------------------------------------------------------------
    # 3. Bottom Rug Track: Event Occurrences in Time
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
    pdf_path = os.path.join(output_dir, f'plot12_single_objective_by_time_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot12_single_objective_by_time_{scenario_key}.png')

    fig.savefig(pdf_path, format='pdf')
    fig.savefig(png_path, format='png', dpi=300)
    plt.close(fig)

    print(f'  [Plot 12] Saved: {pdf_path}')
    print(f'  [Plot 12] Saved: {png_path}')
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 12: Single-Objective Optimization Metric across Simulation Time')
    parser.add_argument('--sim-dir', required=True, help='Directory containing Simulation*.json files')
    parser.add_argument('--scenario-key', required=True, help='Scenario identifier key')
    parser.add_argument('--output-dir', required=True, help='Output directory for generated plots')
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_single_objective_by_time(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
