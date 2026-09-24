"""
Plot 16: User Mobility Heatmap
Generates a user mobility heatmap summarizing user positions up to different simulation steps.
By default, it plots the final state, and optionally before/after specific events like crowd_surge.
Nodes are sized by their average connected users and labeled with [min, max] mean.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import configure_matplotlib, load_simulation_step, ensure_output_dir, SCENARIO_LABELS, get_num_steps
from plot2_geolocation import compute_node_positions

def plot_user_heatmap(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate global user mobility heatmaps (intermediate and final)."""
    configure_matplotlib()
    
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    
    if num_steps == 0:
        print(f'  [Plot 16] ERROR: No steps found in {sim_dir}')
        return None

    # Compute static node positions from step 0
    step0 = load_simulation_step(sim_dir, 0)
    edges_step0 = step0.get('edge_after', step0.get('edge_before', []))
    nodes_step0 = step0.get('node_after', step0.get('node_before', {}))
    node_positions = compute_node_positions(edges_step0, nodes_step0)

    # =========================================================================
    # PASS 1: Compute global min/max for geometry, node metrics, and global_vmax
    # =========================================================================
    all_user_x_full = []
    all_user_y_full = []
    users_per_node_history = {n_id: [] for n_id in node_positions.keys()}

    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None: continue
            
        users = step_data.get('users_after', step_data.get('users_before', {}))
        
        for u in users.values():
            pos = u.get('pos')
            if pos and len(pos) == 2:
                all_user_x_full.append(pos[0])
                all_user_y_full.append(pos[1])
                
        current_step_users_per_node = {n_id: 0 for n_id in node_positions.keys()}
        for u in users.values():
            conn = u.get('connectedTo')
            if conn is not None and conn in current_step_users_per_node:
                current_step_users_per_node[conn] += 1
                
        for n_id, count in current_step_users_per_node.items():
            users_per_node_history[n_id].append(count)

    node_xs = [p[0] for p in node_positions.values()]
    node_ys = [p[1] for p in node_positions.values()]
    
    ux_min, ux_max, uy_min, uy_max = 0, 0, 0, 0
    nx_min, nx_max, ny_min, ny_max = 0, 0, 0, 0
    ux_range, uy_range, nx_range, ny_range = 1, 1, 1, 1
    margin = 0.1

    if all_user_x_full:
        ux_min, ux_max = min(all_user_x_full), max(all_user_x_full)
        uy_min, uy_max = min(all_user_y_full), max(all_user_y_full)
        nx_min, nx_max = min(node_xs), max(node_xs)
        ny_min, ny_max = min(node_ys), max(node_ys)

        ux_range = max(ux_max - ux_min, 1e-6)
        uy_range = max(uy_max - uy_min, 1e-6)
        nx_range = (nx_max - nx_min) * (1 + 2 * margin)
        ny_range = (ny_max - ny_min) * (1 + 2 * margin)

        scaled_ux_full = [(x - ux_min) / ux_range * nx_range + nx_min - margin * (nx_max - nx_min) for x in all_user_x_full]
        scaled_uy_full = [(y - uy_min) / uy_range * ny_range + ny_min - margin * (ny_max - ny_min) for y in all_user_y_full]
    else:
        scaled_ux_full, scaled_uy_full = [], []

    node_metrics = {}
    for n_id, history in users_per_node_history.items():
        if history:
            node_metrics[n_id] = {'min': np.min(history), 'max': np.max(history), 'mean': np.mean(history)}
        else:
            node_metrics[n_id] = {'min': 0, 'max': 0, 'mean': 0.0}

    # Find global vmax for the heatmap colorbar
    global_vmax = 1
    if scaled_ux_full:
        fig_temp, ax_temp = plt.subplots()
        hb_temp = ax_temp.hexbin(scaled_ux_full, scaled_uy_full, gridsize=30, mincnt=1)
        counts = hb_temp.get_array()
        if len(counts) > 0:
            global_vmax = counts.max()
        plt.close(fig_temp)

    # =========================================================================
    # DRAW HELPER
    # =========================================================================
    def draw_heatmap(scaled_ux, scaled_uy, title_suffix, filename_suffix, metrics_dict):
        fig, ax = plt.subplots(figsize=(10, 8))

        if scaled_ux:
            hb = ax.hexbin(scaled_ux, scaled_uy, gridsize=30, cmap='YlOrRd', mincnt=1, vmax=global_vmax, alpha=0.7, edgecolors='none', zorder=1)
            cb = fig.colorbar(hb, ax=ax, label='User Presence Density (scaled to final)')
            cb.outline.set_visible(False)

        for e in edges_step0:
            s, t = e['source'], e['target']
            if s in node_positions and t in node_positions:
                xs = [node_positions[s][0], node_positions[t][0]]
                ys = [node_positions[s][1], node_positions[t][1]]
                edge_color = '#CCCCCC' if e.get('enable', True) else '#FF000033'
                ax.plot(xs, ys, color=edge_color, linewidth=0.5, linestyle='-', zorder=2)

        layer_colors = {'cloud': '#D32F2F', 'fog': '#1976D2', 'edge': '#4CAF50'}
        for nid_str, ndata in nodes_step0.items():
            node_id = ndata['id']
            if node_id not in node_positions:
                continue
            x, y = node_positions[node_id]
            layer = ndata.get('layer', 'edge')
            metrics = metrics_dict[node_id]
            
            size = 50 + metrics['mean'] * 80
            color = layer_colors.get(layer, '#999999')
            
            ax.scatter(x, y, s=size, c=color, alpha=0.9, edgecolors='black', linewidths=1.0, zorder=3)
            
            if metrics['max'] > 0:
                label_text = f"[{metrics['min']}, {metrics['max']}]\n{metrics['mean']:.2f}"
                ax.annotate(label_text, (x, y), textcoords="offset points", xytext=(0, -8), 
                            ha='center', va='top', fontsize=6, fontweight='bold', 
                            color='black', bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8, ec='none'), zorder=4)

        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#D32F2F', markersize=8, label='Cloud'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#1976D2', markersize=8, label='Fog'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#4CAF50', markersize=8, label='Edge'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        label = SCENARIO_LABELS.get(scenario_key, scenario_key)
        ax.set_title(f'User Mobility Heatmap — {label}\n{title_suffix}', fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xticks([])
        ax.set_yticks([])

        ensure_output_dir(output_dir)
        filepath = os.path.join(output_dir, f'plot16_user_heatmap_{scenario_key}_{filename_suffix}.pdf')
        fig.savefig(filepath, format='pdf')
        plt.close(fig)
        print(f'  [Plot 16] Saved heatmap: {filepath}')

    # =========================================================================
    # PASS 2: Re-accumulate and plot intermediate & final steps
    # =========================================================================
    current_ux = []
    current_uy = []
    current_users_per_node_history = {n_id: [] for n_id in node_positions.keys()}
    
    def get_current_metrics():
        metrics = {}
        for n_id, history in current_users_per_node_history.items():
            if history:
                metrics[n_id] = {'min': np.min(history), 'max': np.max(history), 'mean': np.mean(history)}
            else:
                metrics[n_id] = {'min': 0, 'max': 0, 'mean': 0.0}
        return metrics
    
    def get_scaled(ux_list, uy_list):
        if not ux_list: return [], []
        sux = [(x - ux_min) / ux_range * nx_range + nx_min - margin * (nx_max - nx_min) for x in ux_list]
        suy = [(y - uy_min) / uy_range * ny_range + ny_min - margin * (ny_max - ny_min) for y in uy_list]
        return sux, suy

    crowd_surge_count = 0
    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None: continue
        
        action = step_data.get('action', {}).get('action', {})
        action_type = action.get('action_type', '')
        
        is_crowd_surge = (action_type == 'crowd_surge')
        
        if is_crowd_surge:
            crowd_surge_count += 1
            sux, suy = get_scaled(current_ux, current_uy)
            draw_heatmap(sux, suy, f"Step {i} — Before Crowd Surge {crowd_surge_count}", f"step_{i}_before", get_current_metrics())

        users = step_data.get('users_after', step_data.get('users_before', {}))
        
        # Track positions
        for u in users.values():
            pos = u.get('pos')
            if pos and len(pos) == 2:
                current_ux.append(pos[0])
                current_uy.append(pos[1])
                
        # Track connected users for the current step
        step_users_per_node = {n_id: 0 for n_id in node_positions.keys()}
        for u in users.values():
            conn = u.get('connectedTo')
            if conn is not None and conn in step_users_per_node:
                step_users_per_node[conn] += 1
                
        for n_id, count in step_users_per_node.items():
            current_users_per_node_history[n_id].append(count)
                
        if is_crowd_surge:
            sux, suy = get_scaled(current_ux, current_uy)
            draw_heatmap(sux, suy, f"Step {i} — After Crowd Surge {crowd_surge_count}", f"step_{i}_after", get_current_metrics())

    # Finally, draw the full simulation heatmap
    draw_heatmap(scaled_ux_full, scaled_uy_full, f"Step {num_steps} (Final Cumulative Map)", "final", node_metrics)
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 16: User Heatmap')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None)
    args = parser.parse_args()
    plot_user_heatmap(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
