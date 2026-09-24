"""
Plot 17: User Mobility Tracks
Generates a single global map drawing the trajectory (tracks) of each user across the simulation.
Nodes are sized by their average connected users and labeled with [min, max] mean.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import configure_matplotlib, load_simulation_step, ensure_output_dir, SCENARIO_LABELS, get_num_steps
from plot2_geolocation import compute_node_positions

def plot_user_tracks(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate a global user mobility track map for the entire simulation."""
    configure_matplotlib()
    
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    
    if num_steps == 0:
        print(f'  [Plot 17] ERROR: No steps found in {sim_dir}')
        return None

    # Compute static node positions from step 0
    step0 = load_simulation_step(sim_dir, 0)
    edges_step0 = step0.get('edge_after', step0.get('edge_before', []))
    nodes_step0 = step0.get('node_after', step0.get('node_before', {}))
    node_positions = compute_node_positions(edges_step0, nodes_step0)

    # Initialize data structures for tracking
    # user_id -> [(x1,y1), (x2,y2), ...]
    user_tracks = {}
    
    # node_id -> list of user counts per step
    users_per_node_history = {n_id: [] for n_id in node_positions.keys()}

    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            continue
            
        users = step_data.get('users_after', step_data.get('users_before', {}))
        
        # Track user positions
        for uid_str, u in users.items():
            uid = u.get('id', uid_str)
            pos = u.get('pos')
            if pos and len(pos) == 2:
                if uid not in user_tracks:
                    user_tracks[uid] = []
                user_tracks[uid].append((pos[0], pos[1]))
                
        # Track connected users per node for this step
        current_step_users_per_node = {n_id: 0 for n_id in node_positions.keys()}
        for u in users.values():
            conn = u.get('connectedTo')
            if conn is not None and conn in current_step_users_per_node:
                current_step_users_per_node[conn] += 1
                
        # Append to history
        for n_id, count in current_step_users_per_node.items():
            users_per_node_history[n_id].append(count)

    # Calculate normalization boundaries to scale user coordinates to node coordinates
    all_user_x = [pt[0] for track in user_tracks.values() for pt in track]
    all_user_y = [pt[1] for track in user_tracks.values() for pt in track]
    node_xs = [p[0] for p in node_positions.values()]
    node_ys = [p[1] for p in node_positions.values()]

    if all_user_x:
        ux_min, ux_max = min(all_user_x), max(all_user_x)
        uy_min, uy_max = min(all_user_y), max(all_user_y)
        nx_min, nx_max = min(node_xs), max(node_xs)
        ny_min, ny_max = min(node_ys), max(node_ys)

        margin = 0.1
        ux_range = max(ux_max - ux_min, 1e-6)
        uy_range = max(uy_max - uy_min, 1e-6)
        nx_range = (nx_max - nx_min) * (1 + 2 * margin)
        ny_range = (ny_max - ny_min) * (1 + 2 * margin)

        def scale_coord(x, y):
            sx = (x - ux_min) / ux_range * nx_range + nx_min - margin * (nx_max - nx_min)
            sy = (y - uy_min) / uy_range * ny_range + ny_min - margin * (ny_max - ny_min)
            return sx, sy
    else:
        def scale_coord(x, y):
            return x, y

    # Calculate node metrics
    node_metrics = {}
    for n_id, history in users_per_node_history.items():
        if history:
            node_metrics[n_id] = {
                'min': np.min(history),
                'max': np.max(history),
                'mean': np.mean(history)
            }
        else:
            node_metrics[n_id] = {'min': 0, 'max': 0, 'mean': 0.0}

    # Plotting
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)
    fig, ax = plt.subplots(figsize=(10, 8))

    # 1. Draw edges (static topology) first (bottom layer)
    for e in edges_step0:
        s, t = e['source'], e['target']
        if s in node_positions and t in node_positions:
            xs = [node_positions[s][0], node_positions[t][0]]
            ys = [node_positions[s][1], node_positions[t][1]]
            edge_color = '#E0E0E0' if e.get('enable', True) else '#FFEBEE'
            ax.plot(xs, ys, color=edge_color, linewidth=0.5, linestyle='-', zorder=1)

    # 2. Draw user tracks
    track_color = '#1f77b4' # Publication-friendly blue
    for uid, track in user_tracks.items():
        if len(track) < 2:
            # Draw as point if only one position
            if len(track) == 1:
                sx, sy = scale_coord(track[0][0], track[0][1])
                ax.scatter([sx], [sy], c=track_color, s=5, alpha=0.3, zorder=2)
            continue
            
        scaled_x = []
        scaled_y = []
        for x, y in track:
            sx, sy = scale_coord(x, y)
            scaled_x.append(sx)
            scaled_y.append(sy)
            
        ax.plot(scaled_x, scaled_y, color=track_color, alpha=0.15, linewidth=1.2, zorder=2)

    # 3. Draw nodes and labels (top layer)
    layer_colors = {'cloud': '#D32F2F', 'fog': '#1976D2', 'edge': '#4CAF50'}
    
    for nid_str, ndata in nodes_step0.items():
        node_id = ndata['id']
        if node_id not in node_positions:
            continue
            
        x, y = node_positions[node_id]
        layer = ndata.get('layer', 'edge')
        metrics = node_metrics[node_id]
        
        # Size based on mean connected users
        size = 50 + metrics['mean'] * 80
        color = layer_colors.get(layer, '#999999')
        
        ax.scatter(x, y, s=size, c=color, alpha=0.95, edgecolors='black', linewidths=1.0, zorder=3)
        
        # Label: [min, max] mean
        if metrics['max'] > 0:
            label_text = f"[{metrics['min']}, {metrics['max']}]\n{metrics['mean']:.2f}"
            ax.annotate(label_text, (x, y), textcoords="offset points", xytext=(0, -8), 
                        ha='center', va='top', fontsize=6, fontweight='bold', 
                        color='black', bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.85, ec='none'), zorder=4)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#D32F2F', markersize=8, label='Cloud'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#1976D2', markersize=8, label='Fog'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#4CAF50', markersize=8, label='Edge'),
        Line2D([0], [0], marker='', color=track_color, alpha=0.5, linewidth=2.0, label='User Track'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    ax.set_title(f'Global User Mobility Tracks — {label}\nNode Labels: [Min, Max] Mean connected users',
                 fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal', adjustable='datalim')
    
    # Hide axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'plot17_user_tracks_{scenario_key}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    print(f'  [Plot 17] Saved global tracks: {filepath}')
    return filepath

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 17: User Tracks')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None)
    args = parser.parse_args()
    plot_user_tracks(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
