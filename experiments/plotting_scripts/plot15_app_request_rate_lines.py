"""
Plot 8: Per-Application Aggregated Request Rate — Shows the aggregated request
rate (sum of requestRatio of all users requesting each app) per application
over simulation steps.

Layout:
  - Top panel: Stacked request load for less popular applications (those
    not affected by viral spikes), allowing fine-grained visibility into
    baseline application demand.
  - Bottom panel: Stacked total system request rate across all applications,
    following the exact same format and height.
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


def plot_app_request_rate(sim_dir, scenario_key, output_dir, max_steps=None, top_n=5):
    """
    Generate a two-panel figure showing per-application aggregated request rate over time.
    - Top panel: Stacked area chart for less popular applications (unaffected by viral spikes).
    - Bottom panel: Stacked area chart for the total system request rate (all applications),
      matching the exact format and size of the top panel.
    """
    configure_matplotlib()
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)

    # Collect per-app aggregated request ratio per step
    # app_name -> {step: total_request_ratio}
    app_agg_req = defaultdict(lambda: defaultdict(float))
    app_user_count = defaultdict(lambda: defaultdict(int))
    all_app_names = set()
    
    # Track affected apps by specific events: list of (step, app_name, event_type)
    affected_events = []
    active_viral_apps = set()

    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            continue

        apps = step_data.get('apps_after', step_data.get('apps_before', {}))
        users = step_data.get('users_after', step_data.get('users_before', {}))
        
        action_block = step_data.get('action', {})
        action_inner = action_block.get('action', {})
        action_name = action_inner.get('action', 'init')

        # Build app_id -> app_name map
        app_id_to_name = {}
        for aid, adata in apps.items():
            aname = adata.get('name', aid[:8])
            app_id_to_name[aid] = aname
            all_app_names.add(aname)
            # Initialize to 0 for apps with no users this step
            if i not in app_agg_req[aname]:
                app_agg_req[aname][i] = 0.0
                app_user_count[aname][i] = 0

        # Aggregate request ratios per app
        for uid, udata in users.items():
            req_app = udata.get('requestedApp')
            req_ratio = udata.get('requestRatio', 0)
            if req_app and req_app in app_id_to_name:
                aname = app_id_to_name[req_app]
                app_agg_req[aname][i] += req_ratio
                app_user_count[aname][i] += 1
                
        # Record events that affect specific apps
        if action_name == 'viral_cascade':
            for sub in action_inner.get('executed_sub_actions', []):
                if sub.get('type_object') == 'app':
                    aid = sub.get('object_id')
                    if aid in app_id_to_name:
                        aname = app_id_to_name[aid]
                        affected_events.append((i, aname, 'viral_cascade_start'))
                        active_viral_apps.add(aname)
        elif action_name == 'restore_popularity':
            if action_inner.get('type_object') == 'app':
                aid = action_inner.get('object_id')
                if aid in app_id_to_name:
                    aname = app_id_to_name[aid]
                    if aname in active_viral_apps:
                        affected_events.append((i, aname, 'viral_cascade_end'))
                        active_viral_apps.remove(aname)
        elif action_name == 'change_request_ratio':
            if action_inner.get('type_object') == 'user':
                uid = action_inner.get('object_id')
                if uid in users:
                    req_app = users[uid].get('requestedApp')
                    if req_app in app_id_to_name:
                        msg = action_inner.get('message', '')
                        evt = 'change_request_ratio_up'
                        if 'changed from' in msg and 'to' in msg:
                            try:
                                p = msg.split('changed from ')[1].split(' to ')
                                old_v = float(p[0])
                                new_v = float(p[1].rstrip('.'))
                                if new_v < old_v:
                                    evt = 'change_request_ratio_down'
                            except:
                                pass
                        affected_events.append((i, app_id_to_name[req_app], evt))

    if not all_app_names:
        print(f'  [Plot 8] WARNING: No apps found for {scenario_key}')
        return None

    steps = list(range(num_steps))

    # Rank apps by peak aggregated request rate (most dramatic first)
    app_peak = {a: max(app_agg_req[a].values()) if app_agg_req[a] else 0
                for a in all_app_names}
    sorted_apps = sorted(all_app_names, key=lambda a: app_peak.get(a, 0), reverse=True)
    n_apps = len(sorted_apps)

    # Separate viral / most popular applications from less popular applications.
    # An application is considered affected by viralization if its peak request rate
    # experiences a sharp spike exceeding typical baseline demand.
    # We also ensure at least the top_n most popular applications are filtered out.
    med_peak = float(np.median([app_peak[a] for a in sorted_apps]))
    max_peak = max(app_peak.values()) if app_peak else 0

    if max_peak > 100:
        viral_threshold = max(50.0, med_peak * 5.0)
        viral_apps = {a for a in sorted_apps if app_peak[a] > viral_threshold}
        viral_apps.update(sorted_apps[:top_n])
    else:
        viral_apps = set(sorted_apps[:top_n])

    less_popular_apps = [a for a in sorted_apps if a not in viral_apps]
    if not less_popular_apps:
        less_popular_apps = sorted_apps[top_n:] if n_apps > top_n else sorted_apps

    # Consistent color palette mapped to each application
    app_color_map = {aname: get_multi_color(i, max(n_apps, 20)) for i, aname in enumerate(sorted_apps)}

    # --- Figure 1: Two panels of identical format and size ---
    # Order: All applications on top, Less popular applications on bottom
    # Height reduced by 15%: 7.5 * 0.85 = 6.375
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6.375), sharex=True,
                                    gridspec_kw={'height_ratios': [1, 1]})
    fig.suptitle(f'Per-Application Aggregated Request Rate — {label}',
                 fontsize=14, fontweight='bold', y=0.98)

    y_label = 'Aggregated Total Request Rate\nper Application'

    # Panel 1: Line chart for total system request load (all applications)
    colors_all = [app_color_map[a] for a in sorted_apps]
    req_matrix_all = np.zeros((n_apps, num_steps))
    for idx, aname in enumerate(sorted_apps):
        for s in steps:
            req_matrix_all[idx, s] = app_agg_req[aname].get(s, 0)
        ax1.plot(steps, req_matrix_all[idx], color=colors_all[idx], linewidth=2.0, alpha=0.9, zorder=5)

    ax1.set_ylabel(y_label)
    ax1.set_title(f'Line System Load. All the Applications ({n_apps} apps)',
                  fontsize=11, loc='left', pad=4)
                  
    # Plot markers for affected apps
    from matplotlib.lines import Line2D
    has_event_start = False
    has_event_finish = False
    for (step, app_name, evt_type) in affected_events:
        if app_name in sorted_apps and step < num_steps and app_name not in less_popular_apps:
            app_idx = sorted_apps.index(app_name)
            y_pos = req_matrix_all[app_idx, step]
            if evt_type in ('viral_cascade_start', 'change_request_ratio_up'):
                marker = '^'
                has_event_start = True
            else:
                marker = 'v'
                has_event_finish = True
            
            ax1.scatter([step], [y_pos], marker=marker, s=40, 
                        facecolor=app_color_map[app_name], edgecolor='black', linewidth=0.5, zorder=10)
                        
    # Add legend for events if they occurred
    legend_elements = []
    if has_event_start:
        legend_elements.append(Line2D([0], [0], marker='^', color='w', markerfacecolor='grey', markeredgecolor='black', markersize=8, label='Event Start'))
    if has_event_finish:
        legend_elements.append(Line2D([0], [0], marker='v', color='w', markerfacecolor='grey', markeredgecolor='black', markersize=8, label='Event Finish'))
    if legend_elements:
        ax1.legend(handles=legend_elements, loc='upper left', fontsize=9, title="Events")

    # Panel 2: Line chart for less popular applications (non-viral)
    n_less = len(less_popular_apps)
    colors_less = [app_color_map[a] for a in less_popular_apps]
    req_matrix_less = np.zeros((n_less, num_steps))
    for idx, aname in enumerate(less_popular_apps):
        for s in steps:
            req_matrix_less[idx, s] = app_agg_req[aname].get(s, 0)
        ax2.plot(steps, req_matrix_less[idx], color=colors_less[idx], linewidth=2.0, alpha=0.9, zorder=5)

    ax2.set_ylabel(y_label)
    ax2.set_xlabel('Simulation Step')
    ax2.set_title(f'Line System Load. Less Popular Applications ({n_less} apps)',
                  fontsize=11, loc='left', pad=4)

    for (step, app_name, evt_type) in affected_events:
        if app_name in less_popular_apps and step < num_steps:
            app_idx = less_popular_apps.index(app_name)
            y_pos = req_matrix_less[app_idx, step]
            if evt_type in ('viral_cascade_start', 'change_request_ratio_up'):
                marker = '^'
            else:
                marker = 'v'
            
            ax2.scatter([step], [y_pos], marker=marker, s=40, 
                        facecolor=app_color_map[app_name], edgecolor='black', linewidth=0.5, zorder=10)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot15_app_request_rate_lines_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 15] Saved 2-panel figure: {filepath}')

    # --- Figure 2: Single-panel clip showing only total system request load ---
    # Sized to match an individual subplot (width 12, height ~3.6) with the same titles
    fig_clip, ax_clip = plt.subplots(1, 1, figsize=(12, 3.6))
    fig_clip.suptitle(f'Per-Application Aggregated Request Rate — {label}',
                      fontsize=14, fontweight='bold', y=0.98)

    for idx, aname in enumerate(sorted_apps):
        ax_clip.plot(steps, req_matrix_all[idx], color=colors_all[idx], linewidth=2.0, alpha=0.9, zorder=5)
        
    ax_clip.set_ylabel(y_label)
    ax_clip.set_xlabel('Simulation Step')
    ax_clip.set_title(f'Line System Load. All the Applications ({n_apps} apps)',
                      fontsize=11, loc='left', pad=4)

    for (step, app_name, evt_type) in affected_events:
        if app_name in sorted_apps and step < num_steps:
            app_idx = sorted_apps.index(app_name)
            y_pos = req_matrix_all[app_idx, step]
            if evt_type in ('viral_cascade_start', 'change_request_ratio_up'):
                marker = '^'
            else:
                marker = 'v'
            ax_clip.scatter([step], [y_pos], marker=marker, s=40, 
                            facecolor=app_color_map[app_name], edgecolor='black', linewidth=0.5, zorder=10)
    if legend_elements:
        ax_clip.legend(handles=legend_elements, loc='upper left', fontsize=9, title="Events")

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    filepath_total = os.path.join(output_dir, f'plot15_app_request_rate_lines_{scenario_key}_total.pdf')
    fig_clip.savefig(filepath_total, format='pdf')
    plt.close(fig_clip)
    print(f'  [Plot 15] Saved total clip figure: {filepath_total}')

    return filepath


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Plot 8: Per-Application Aggregated Request Rate')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None,
                        help='Max steps to plot (defaults to all available)')
    parser.add_argument('--top-n', type=int, default=5,
                        help='Number of top popular apps to exclude (default: 5)')
    args = parser.parse_args()
    plot_app_request_rate(args.sim_dir, args.scenario_key, args.output_dir,
                          args.max_steps, args.top_n)
