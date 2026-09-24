"""
Shared data loading and styling utilities for all plotting scripts.
Provides a common interface to load simulation JSON data and configure
matplotlib for publication-quality output.
"""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for PDF generation
import matplotlib.pyplot as plt
from matplotlib import rcParams

# =============================================================================
# Publication-quality matplotlib configuration
# =============================================================================
def configure_matplotlib():
    """Configure matplotlib for IEEE/ACM-style publication figures."""
    rcParams.update({
        # Font settings
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9,
        # Figure settings
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        # Line and marker settings
        'lines.linewidth': 1.5,
        'lines.markersize': 4,
        # Grid
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        # Spines
        'axes.spines.top': False,
        'axes.spines.right': False,
        # Legend
        'legend.framealpha': 0.8,
        'legend.edgecolor': '0.8',
    })

# =============================================================================
# Color palettes for scenarios and multi-series plots
# =============================================================================
SCENARIO_COLORS = {
    'electric_storm': '#D32F2F',      # Deep red
    'crowd_event': '#1976D2',          # Deep blue
    'demand_surge': '#F57C00',         # Deep orange
    'normal_conditions': '#388E3C',    # Deep green
}

SCENARIO_LABELS = {
    'electric_storm': 'Electric Storm',
    'crowd_event': 'Crowd Event',
    'demand_surge': 'Demand Surge',
    'normal_conditions': 'Normal Conditions',
}

# Qualitative palette for multi-series (apps, users, etc.)
MULTI_SERIES_CMAP = plt.cm.tab20
EVENT_CMAP = plt.cm.Set2

def get_multi_color(idx, total=20):
    """Get a distinct color from a qualitative colormap."""
    return MULTI_SERIES_CMAP(idx / max(total, 1))

# =============================================================================
# Data loading
# =============================================================================
def load_simulation_step(sim_dir, step_idx):
    """Load a single simulation step JSON file."""
    filepath = os.path.join(sim_dir, f'Simulation{step_idx}.json')
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def get_num_steps(sim_dir):
    """Count the number of simulation step files (Simulation{i}.json) in a directory."""
    if not os.path.isdir(sim_dir):
        return 0
    step_indices = []
    for f in os.listdir(sim_dir):
        if f.startswith('Simulation') and f.endswith('.json'):
            idx_part = f[len('Simulation'):-len('.json')]
            if idx_part.isdigit():
                step_indices.append(int(idx_part))
    return max(step_indices) + 1 if step_indices else 0

def load_all_steps(sim_dir, max_steps=None):
    """
    Load summary data from all simulation steps.
    Returns a dict of arrays for efficient plotting.
    """
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    
    data = {
        'steps': [],
        'time': [],
        'num_users': [],
        'num_apps': [],
        'total_ram_demand': [],
        'total_cpu_demand': [],
        'total_requests': [],
        'enabled_nodes': [],
        'disabled_nodes': [],
        'event_action': [],
        'event_type_object': [],
        'objective': [],
        'total_latency': [],
        'latency_cost': [],
        'migration_cost': [],
        'server_usage_cost': [],
        'total_ram_occupied': [],
        'solver_status': [],
        'solve_time_seconds': [],
    }
    
    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            continue
        
        data['steps'].append(i)
        
        # Action info
        action_block = step_data.get('action', {})
        action_inner = action_block.get('action', {})
        global_time = action_block.get('global_time', 0.0)
        data['time'].append(global_time)
        data['event_action'].append(action_inner.get('action', 'init'))
        data['event_type_object'].append(action_inner.get('type_object', 'init'))
        
        # Users (prefer 'after' if available, else 'before')
        users = step_data.get('users_after', step_data.get('users_before', {}))
        data['num_users'].append(len(users))
        total_req = sum(u.get('requestRatio', 0) for u in users.values())
        data['total_requests'].append(total_req)
        
        # Apps
        apps = step_data.get('apps_after', step_data.get('apps_before', {}))
        data['num_apps'].append(len(apps))
        data['total_cpu_demand'].append(
            sum(app.get('cpu', 0) for app in apps.values()))
        data['total_ram_demand'].append(
            sum(app.get('ram', 0) for app in apps.values()))
        
        # Nodes
        nodes = step_data.get('node_after', step_data.get('node_before', {}))
        num_disabled = sum(1 for n in nodes.values() if not n.get('enable', True))
        data['enabled_nodes'].append(len(nodes) - num_disabled)
        data['disabled_nodes'].append(num_disabled)
        
        # Metrics
        metrics = step_data.get('metrics_after', step_data.get('metrics_before', {}))
        obj_val = float(metrics.get('objective', 0.0))
        tot_lat = float(metrics.get('total_latency', 0.0))
        lat_cost = float(metrics.get('latency_cost', tot_lat if 'latency_cost' not in metrics else 0.0))
        mig_cost = float(metrics.get('migration_cost', 0.0))
        srv_cost = float(metrics.get('server_usage_cost', 0.0))
        ram_occ = float(metrics.get('total_ram_occupied', 0.0))
        s_time = float(metrics.get('solve_time_seconds', 0.0))

        # Check if this is a legacy dataset where total_latency / objective was the unnormalized sum
        # When unnormalized, tot_lat was sum(w * lat) which is >> 100 when total_req >> 10
        if tot_lat < 500000.0 and total_req > 0 and tot_lat > 100.0 and (tot_lat / total_req) < 1000.0:
            tot_lat = tot_lat / total_req
            if lat_cost < 500000.0 and lat_cost > 100.0:
                lat_cost = lat_cost / total_req
            if obj_val < 500000.0 and obj_val > 100.0:
                if 'latency_cost' in metrics:
                    obj_val = lat_cost + mig_cost + srv_cost
                else:
                    obj_val = tot_lat

        data['objective'].append(obj_val)
        data['total_latency'].append(tot_lat)
        data['latency_cost'].append(lat_cost)
        data['migration_cost'].append(mig_cost)
        data['server_usage_cost'].append(srv_cost)
        data['total_ram_occupied'].append(ram_occ)
        data['solve_time_seconds'].append(s_time)

        # Solver status (read from metrics or infer/correct for legacy datasets)
        status = metrics.get('solver_status')
        if not status or (status == 'Disconnected' and num_disabled == 0):
            # If all nodes are enabled, the network topology is intact
            if num_disabled == 0:
                status = 'Optimal'
            else:
                tot_ram_demand = sum(sum(m.get('ram', 0) for m in a.get('microservices', [])) for a in apps.values())
                tot_active_ram_cap = sum(d.get('ram', 0) for d in nodes.values() if d.get('enable', True))
                if tot_ram_demand > tot_active_ram_cap:
                    status = 'Infeasible'
                else:
                    status = 'Disconnected'
        data['solver_status'].append(status)
    
    # Convert to numpy arrays
    for key in data:
        if key not in ('event_action', 'event_type_object', 'solver_status'):
            data[key] = np.array(data[key])
        elif key == 'solver_status':
            data[key] = np.array(data[key], dtype=object)
    
    return data

def ensure_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

EVENT_MIGRATION_CATEGORIES = {
    'infra_failure': {
        'events': {'disable_node', 'degrade_node', 'disable_edge', 'congest_edge', 
                   'lightning_strike', 'catastrophic_failure_and_surge'},
        'color': '#D32F2F',  # Deep Crimson
        'label': 'Infra Failure / Hazard'
    },
    'infra_recovery': {
        'events': {'revive_node', 'restore_node', 'revive_edge', 'clear_edge'},
        'color': '#2E7D32',  # Forest Green
        'label': 'Infra Recovery'
    },
    'user_dynamics': {
        'events': {'new_user', 'remove_user', 'move_user', 'suspend_user', 
                   'resume_user', 'change_request_ratio', 'crowd_surge', 'viral_cascade'},
        'color': '#1976D2',  # Deep Blue
        'label': 'User Mobility & Churn'
    },
    'app_dynamics': {
        'events': {'new_app', 'remove_app', 'surge_popularity', 'drop_popularity', 
                   'restore_popularity', 'geo_demand_shift', 'update_app_footprint', 
                   'update_app_network', 'update_app_topology'},
        'color': '#F57C00',  # Amber / Orange
        'label': 'App Lifecycle & Config'
    },
}

def get_event_category_info(act_name):
    """Return category key, color, and label for an event action string."""
    for cat_key, cat_data in EVENT_MIGRATION_CATEGORIES.items():
        if act_name in cat_data['events']:
            return cat_key, cat_data['color'], cat_data['label']
    return 'other', '#757575', 'Other Event'

def load_migration_data(sim_dir, max_steps=None):
    """
    Load detailed application migration data across simulation steps.
    Compares placement_before and placement_after for each step.
    Returns a dictionary of numpy arrays and lists.
    """
    total_steps = get_num_steps(sim_dir)
    num_steps = min(total_steps, max_steps) if max_steps is not None else total_steps
    
    steps = []
    times = []
    mig_counts = []
    total_apps = []
    mig_pcts = []
    actions = []
    cat_keys = []
    cat_colors = []
    cat_labels = []
    statuses = []
    
    for i in range(num_steps):
        step_data = load_simulation_step(sim_dir, i)
        if step_data is None:
            continue
        
        pb = step_data.get('placement_before', {})
        pa = step_data.get('placement_after', {})
        action_block = step_data.get('action', {})
        action_inner = action_block.get('action', {})
        act_name = action_inner.get('action_type', action_inner.get('action', 'init'))
        g_time = action_block.get('global_time', 0.0)
        
        metrics = step_data.get('metrics_after', {})
        status = metrics.get('solver_status', 'Optimal')
        
        mig = 0
        for app, ms in pa.items():
            if app in pb:
                for m, node in ms.items():
                    if pb[app].get(m) is not None and pb[app].get(m) != node:
                        mig += 1
                        
        n_apps = len(pa) if pa else len(pb)
        pct = (mig / max(n_apps, 1)) * 100.0
        
        cat_key, col, lbl = get_event_category_info(act_name)
        
        steps.append(i)
        times.append(g_time)
        mig_counts.append(mig)
        total_apps.append(n_apps)
        mig_pcts.append(pct)
        actions.append(act_name)
        cat_keys.append(cat_key)
        cat_colors.append(col)
        cat_labels.append(lbl)
        statuses.append(status)
        
    mig_counts_arr = np.array(mig_counts)
    return {
        'steps': np.array(steps),
        'times': np.array(times),
        'mig_counts': mig_counts_arr,
        'total_apps': np.array(total_apps),
        'mig_pcts': np.array(mig_pcts),
        'actions': actions,
        'cat_keys': cat_keys,
        'cat_colors': cat_colors,
        'cat_labels': cat_labels,
        'solver_status': np.array(statuses, dtype=object),
        'cum_migs': np.cumsum(mig_counts_arr)
    }

