"""
Plot 3: Application Popularity Evolution — Two-panel figure showing:
  - Top panel: Number of users requesting each application over time
  - Bottom panel: Total request rate per application over time
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


def plot_app_popularity(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a two-panel figure showing application popularity evolution."""
    configure_matplotlib()
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # Collect per-app data across all steps
    # We track: app_name -> {step_idx: (num_users, total_requests)}
    app_users_ts = defaultdict(lambda: defaultdict(int))
    app_requests_ts = defaultdict(lambda: defaultdict(float))
    all_app_names = set()

    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            continue

        apps = step_data.get('apps_after', step_data.get('apps_before', {}))
        users = step_data.get('users_after', step_data.get('users_before', {}))

        # Map app_id -> app_name
        app_id_to_name = {}
        for aid, adata in apps.items():
            aname = adata.get('name', aid[:8])
            app_id_to_name[aid] = aname
            all_app_names.add(aname)

        # Count users per app and total requests per app
        for uid, udata in users.items():
            req_app = udata.get('requestedApp')
            req_ratio = udata.get('requestRatio', 0)
            if req_app and req_app in app_id_to_name:
                aname = app_id_to_name[req_app]
                app_users_ts[aname][i] += 1
                app_requests_ts[aname][i] += req_ratio

    # Sort apps by total users across all steps (most popular first)
    app_total = {a: sum(app_users_ts[a].values()) for a in all_app_names}
    sorted_apps = sorted(all_app_names, key=lambda a: app_total.get(a, 0), reverse=True)

    steps = list(range(num_steps))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle(f'Application Popularity Evolution — {label}',
                 fontsize=14, fontweight='bold', y=0.98)

    # Panel 1: Number of users per app (stacked area)
    user_matrix = np.zeros((len(sorted_apps), num_steps))
    for idx, aname in enumerate(sorted_apps):
        for s in steps:
            user_matrix[idx, s] = app_users_ts[aname].get(s, 0)

    colors = [get_multi_color(i, len(sorted_apps)) for i in range(len(sorted_apps))]
    ax1.stackplot(steps, user_matrix, labels=sorted_apps, colors=colors, alpha=0.75)
    ax1.set_ylabel('Number of Users')
    ax1.set_title('Users per Application', fontsize=11, loc='left', pad=4)
    # Legend: only show top 10 to avoid clutter
    handles, labels_leg = ax1.get_legend_handles_labels()
    n_legend = min(10, len(handles))
    ax1.legend(handles[:n_legend], labels_leg[:n_legend],
               loc='upper right', fontsize=7, ncol=2)

    # Panel 2: Total request rate per app (stacked area)
    req_matrix = np.zeros((len(sorted_apps), num_steps))
    for idx, aname in enumerate(sorted_apps):
        for s in steps:
            req_matrix[idx, s] = app_requests_ts[aname].get(s, 0)

    ax2.stackplot(steps, req_matrix, labels=sorted_apps, colors=colors, alpha=0.75)
    ax2.set_ylabel('Total Request Rate')
    ax2.set_xlabel('Simulation Step')
    ax2.set_title('Request Rate per Application', fontsize=11, loc='left', pad=4)
    ax2.legend(handles[:n_legend], labels_leg[:n_legend],
               loc='upper right', fontsize=7, ncol=2)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot3_app_popularity_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 3] Saved: {filepath}')
    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 3: App Popularity Evolution')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_app_popularity(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
