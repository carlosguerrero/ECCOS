"""
Plot 4: User Activity Evolution — Shows per-user request rate over time.
Each user is a separate line/series, colored to distinguish individuals.
A thick line shows the mean request rate across all active users.
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
from plot_utils import (configure_matplotlib, load_simulation_step, ensure_output_dir,
                        get_num_steps, get_multi_color, SCENARIO_LABELS)


def plot_user_activity(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a figure showing per-user request rate evolution."""
    configure_matplotlib()
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # Collect per-user request ratio over time
    user_req_ts = defaultdict(lambda: defaultdict(float))
    all_user_names = set()
    mean_req = []

    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            mean_req.append(0)
            continue

        users = step_data.get('users_after', step_data.get('users_before', {}))
        step_ratios = []
        for uid, udata in users.items():
            uname = udata.get('name', uid[:8])
            req_ratio = udata.get('requestRatio', 0)
            user_req_ts[uname][i] = req_ratio
            all_user_names.add(uname)
            step_ratios.append(req_ratio)
        mean_req.append(np.mean(step_ratios) if step_ratios else 0)

    steps = list(range(num_steps))
    # Sort users by name for consistent ordering
    sorted_users = sorted(all_user_names, key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle(f'User Activity Evolution — {label}',
                 fontsize=14, fontweight='bold', y=0.98)

    # Draw individual user lines (thin, semi-transparent)
    for idx, uname in enumerate(sorted_users):
        color = get_multi_color(idx % 20, 20)
        x_vals = sorted(user_req_ts[uname].keys())
        y_vals = [user_req_ts[uname][s] for s in x_vals]
        ax.plot(x_vals, y_vals, color=color, linewidth=0.5, alpha=0.35, zorder=1)

    # Draw mean request rate (thick dark line)
    ax.plot(steps, mean_req, color='#212121', linewidth=2.5, alpha=0.9,
            label='Mean Request Rate', zorder=3)

    # Add smoothed mean
    if len(mean_req) > 20:
        window = max(5, min(50, len(mean_req) // 50))
        smoothed = np.convolve(mean_req, np.ones(window)/window, mode='valid')
        ax.plot(steps[window-1:], smoothed, color='#D32F2F', linewidth=2.0,
                linestyle='--', alpha=0.8, label=f'Smoothed Mean (w={window})', zorder=4)

    # Add percentile bands (25th-75th)
    p25 = []
    p75 = []
    for i in range(num_steps):
        active_vals = [user_req_ts[u].get(i, np.nan) for u in sorted_users]
        active_vals = [v for v in active_vals if not np.isnan(v)]
        if active_vals:
            p25.append(np.percentile(active_vals, 25))
            p75.append(np.percentile(active_vals, 75))
        else:
            p25.append(0)
            p75.append(0)

    ax.fill_between(steps, p25, p75, alpha=0.15, color='#1565C0',
                    label='25th–75th Percentile', zorder=2)

    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Request Rate (requests/time unit)')
    ax.set_title('Per-User Request Rate', fontsize=11, loc='left', pad=4)
    ax.legend(loc='upper right', fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot4_user_activity_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 4] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 4: User Activity')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_user_activity(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
