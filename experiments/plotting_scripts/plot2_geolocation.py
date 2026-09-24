"""
Plot 2: Geolocation Map — Per-step spatial visualization of nodes and users.
Generates one figure per simulation step showing:
  - Node positions (computed from graph layout) with circle size proportional
    to the number of connected users
  - User positions (from their pos attribute) as small dots
  - Color-coded by node layer (cloud/fog/edge)
"""

import os
import sys
import argparse
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import configure_matplotlib, load_simulation_step, ensure_output_dir, SCENARIO_LABELS


def build_graph_from_edges(edges, nodes_dict):
    """Build a NetworkX graph from the edge list and node dictionary."""
    G = nx.Graph()
    for nid_str, ndata in nodes_dict.items():
        node_id = ndata['id']
        G.add_node(node_id, **ndata)
    for e in edges:
        if e.get('enable', True):
            G.add_edge(e['source'], e['target'])
    return G


def compute_node_positions(edges, nodes_dict, seed=42):
    """Compute stable node positions using saved positions or fallback to spring layout."""
    pos = {}
    has_all_pos = bool(nodes_dict)
    for nid_str, ndata in nodes_dict.items():
        node_id = ndata.get('id')
        n_pos = ndata.get('pos')
        if node_id is not None and n_pos is not None and len(n_pos) == 2:
            pos[node_id] = np.array(n_pos, dtype=float)
        else:
            has_all_pos = False
            break
    if has_all_pos and len(pos) == len(nodes_dict):
        return pos

    G = build_graph_from_edges(edges, nodes_dict)
    pos = nx.spring_layout(G, seed=seed, k=0.3, iterations=100)
    return pos


def plot_geolocation_step(sim_dir, step_idx, node_positions, scenario_key, output_dir):
    """Generate a single geolocation map for one simulation step."""
    step_data = load_simulation_step(sim_dir, step_idx)
    if step_data is None:
        return None

    label = SCENARIO_LABELS.get(scenario_key, scenario_key)
    nodes = step_data.get('node_after', step_data.get('node_before', {}))
    users = step_data.get('users_after', step_data.get('users_before', {}))

    # Count users per node
    users_per_node = {}
    for u in users.values():
        conn = u.get('connectedTo')
        if conn is not None:
            users_per_node[conn] = users_per_node.get(conn, 0) + 1

    # Layer colors
    layer_colors = {
        'cloud': '#D32F2F',
        'fog': '#1976D2',
        'edge': '#4CAF50',
    }

    fig, ax = plt.subplots(figsize=(8, 7))

    # Draw edges (from step data)
    edges = step_data.get('edge_after', step_data.get('edge_before', []))
    for e in edges:
        s, t = e['source'], e['target']
        if s in node_positions and t in node_positions:
            xs = [node_positions[s][0], node_positions[t][0]]
            ys = [node_positions[s][1], node_positions[t][1]]
            edge_color = '#CCCCCC' if e.get('enable', True) else '#FF000033'
            lw = 0.5 if e.get('enable', True) else 0.3
            ls = '-' if e.get('enable', True) else ':'
            ax.plot(xs, ys, color=edge_color, linewidth=lw, linestyle=ls, zorder=1)

    # Draw nodes
    for nid_str, ndata in nodes.items():
        node_id = ndata['id']
        if node_id not in node_positions:
            continue
        x, y = node_positions[node_id]
        layer = ndata.get('layer', 'edge')
        enabled = ndata.get('enable', True)
        n_users = users_per_node.get(node_id, 0)

        # Size: minimum base + proportional to connected users
        size = 40 + n_users * 60
        color = layer_colors.get(layer, '#999999')
        alpha = 0.85 if enabled else 0.2
        edge_c = 'black' if enabled else 'red'
        lw = 0.8 if enabled else 1.5

        ax.scatter(x, y, s=size, c=color, alpha=alpha,
                   edgecolors=edge_c, linewidths=lw, zorder=3)
        # Label with user count if > 0
        if n_users > 0:
            ax.annotate(str(n_users), (x, y), textcoords="offset points",
                        xytext=(0, -3), ha='center', va='center',
                        fontsize=7, fontweight='bold', color='white', zorder=4)

    # Draw users
    user_xs, user_ys = [], []
    for u in users.values():
        pos = u.get('pos')
        if pos and len(pos) == 2:
            user_xs.append(pos[0])
            user_ys.append(pos[1])

    if user_xs:
        # Scale user positions to match node layout range
        node_xs = [p[0] for p in node_positions.values()]
        node_ys = [p[1] for p in node_positions.values()]
        ux_min, ux_max = min(user_xs), max(user_xs)
        uy_min, uy_max = min(user_ys), max(user_ys)
        nx_min, nx_max = min(node_xs), max(node_xs)
        ny_min, ny_max = min(node_ys), max(node_ys)

        # Normalized scaling
        margin = 0.1
        ux_range = max(ux_max - ux_min, 1e-6)
        uy_range = max(uy_max - uy_min, 1e-6)
        nx_range = (nx_max - nx_min) * (1 + 2 * margin)
        ny_range = (ny_max - ny_min) * (1 + 2 * margin)

        scaled_ux = [(x - ux_min) / ux_range * nx_range + nx_min - margin * (nx_max - nx_min)
                     for x in user_xs]
        scaled_uy = [(y - uy_min) / uy_range * ny_range + ny_min - margin * (ny_max - ny_min)
                     for y in user_ys]

        ax.scatter(scaled_ux, scaled_uy, s=12, c='#FF6F00', alpha=0.7,
                   edgecolors='#BF360C', linewidths=0.3, marker='^', zorder=2,
                   label=f'Users ({len(user_xs)})')

    # Action info
    action_block = step_data.get('action', {})
    action_inner = action_block.get('action', {})
    event_name = action_inner.get('action', 'init')
    global_time = action_block.get('global_time', 0.0)

    # Legend entries
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#D32F2F',
               markersize=8, label='Cloud'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#1976D2',
               markersize=8, label='Fog'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#4CAF50',
               markersize=8, label='Edge'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#FF6F00',
               markersize=6, label=f'Users ({len(user_xs)})'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='red', markersize=8, alpha=0.3, label='Disabled Node'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

    ax.set_title(f'{label} — Step {step_idx}  |  t = {global_time:.1f}s  |  Event: {event_name}',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal', adjustable='datalim')

    ensure_output_dir(output_dir)
    filepath = os.path.join(output_dir, f'geo_step_{step_idx:04d}.pdf')
    fig.savefig(filepath, format='pdf')
    plt.close(fig)
    return filepath


def plot_geolocation_all(sim_dir, scenario_key, output_dir, max_steps=None):
    """Generate geolocation maps for all steps of an experiment."""
    configure_matplotlib()
    geo_dir = os.path.join(output_dir, f'plot2_geolocation_{scenario_key}')
    ensure_output_dir(geo_dir)

    # Compute stable node positions from step 0
    step0 = load_simulation_step(sim_dir, 0)
    if step0 is None:
        print(f'  [Plot 2] ERROR: Cannot load step 0 from {sim_dir}')
        return
    
    edges = step0.get('edge_after', [])
    nodes = step0.get('node_after', step0.get('node_before', {}))
    node_positions = compute_node_positions(edges, nodes)

    from plot_utils import get_num_steps
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps

    for i in range(num_steps):
        plot_geolocation_step(sim_dir, i, node_positions, scenario_key, geo_dir)
        if (i + 1) % 100 == 0:
            print(f'  [Plot 2] {scenario_key}: {i+1}/{num_steps} steps rendered')

    print(f'  [Plot 2] Saved {num_steps} figures in: {geo_dir}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 2: Geolocation Maps')
    parser.add_argument('--sim-dir', required=True)
    parser.add_argument('--scenario-key', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to plot (defaults to all available)')
    args = parser.parse_args()
    plot_geolocation_all(args.sim_dir, args.scenario_key, args.output_dir, args.max_steps)
