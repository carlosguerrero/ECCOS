#!/usr/bin/env python3
"""
Master orchestrator script that generates ALL plots for ALL four experiments.
Reads simulation data from experiments/simulation_json_outputs_results/ and outputs PDF
figures to experiments/figures/.

Usage:
    python run_all_plots.py                     # Run all plots for all experiments
    python run_all_plots.py --skip-geo          # Skip plot 2 (geolocation, 4000 files)
    python run_all_plots.py --only 1 3 5        # Run only specific plot numbers
    python run_all_plots.py --experiments 1 3   # Run only specific experiments
"""

import os
import sys
import time
import argparse
import re
from datetime import datetime

# Add plotting_scripts to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTTING_DIR = os.path.join(SCRIPT_DIR, 'plotting_scripts')
sys.path.insert(0, PLOTTING_DIR)

# Import all plot modules
from plot1_system_overview import plot_system_overview
from plot2_geolocation import plot_geolocation_all
from plot3_app_popularity import plot_app_popularity
from plot4_user_activity import plot_user_activity
from plot5_node_availability import plot_node_availability
from plot6_event_timeline import plot_event_timeline
from plot7_optimization import plot_optimization_metric
from plot8_app_request_rate import plot_app_request_rate
from plot9_single_objective import plot_single_objective
from plot10_event_timeline_by_time import plot_event_timeline_by_time
from plot11_optimization_by_time import plot_optimization_metric_by_time
from plot12_single_objective_by_time import plot_single_objective_by_time
from plot13_node_availability_by_time import plot_node_availability_by_time
from plot14_app_migrations import plot_app_migrations
from plot15_app_request_rate_lines import plot_app_request_rate as plot_app_request_rate_lines
from plot16_user_heatmap import plot_user_heatmap
from plot17_user_tracks import plot_user_tracks

# =============================================================================
# Experiment configuration
# =============================================================================
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, 'simulation_json_outputs_results')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'figures')

EXPERIMENTS = {
    1: {
        'prefix': '1.electric_storm_multi_ilp_all_',
        'key': 'electric_storm',
        'label': 'Electric Storm',
    },
    2: {
        'prefix': '2.crowd_event_multi_ilp_all_',
        'key': 'crowd_event',
        'label': 'Crowd Event',
    },
    3: {
        'prefix': '3.demand_surge_multi_ilp_all_',
        'key': 'demand_surge',
        'label': 'Demand Surge',
    },
    4: {
        'prefix': '4.normal_conditions_multi_ilp_all_',
        'key': 'normal_conditions',
        'label': 'Normal Conditions',
    },
}

MAX_STEPS = None  # None = dynamically detect all available steps from simulation files

# =============================================================================
# Plot registry
# =============================================================================
PLOTS = {
    1: ('System Overview', plot_system_overview),
    2: ('Geolocation Maps', plot_geolocation_all),
    3: ('App Popularity', plot_app_popularity),
    4: ('User Activity', plot_user_activity),
    5: ('Node Availability', plot_node_availability),
    6: ('Event Timeline', plot_event_timeline),
    7: ('Optimization Metric', plot_optimization_metric),
    8: ('App Request Rate', plot_app_request_rate),
    9: ('Single-Objective Latency', plot_single_objective),
    10: ('Event Timeline (by Time)', plot_event_timeline_by_time),
    11: ('Optimization Metric (by Time)', plot_optimization_metric_by_time),
    12: ('Single-Objective Latency (by Time)', plot_single_objective_by_time),
    13: ('Node Availability (by Time)', plot_node_availability_by_time),
    14: ('App Migrations', plot_app_migrations),
    15: ('App Request Rate (Lines)', plot_app_request_rate_lines),
    16: ('User Heatmap', plot_user_heatmap),
    17: ('User Tracks', plot_user_tracks),
}


def find_latest_experiment_dir(base_dir, prefix):
    """
    Finds the directory in base_dir whose name starts with prefix and ends with
    a timestamp (YYYYMMDD_HHMMSS). If multiple matching directories exist,
    returns the one with the most recent timestamp.
    """
    if not os.path.isdir(base_dir):
        return None

    candidates = []
    # Primary search: directories starting with exact prefix
    for name in os.listdir(base_dir):
        full_path = os.path.join(base_dir, name)
        if not os.path.isdir(full_path):
            continue
        if name.startswith(prefix):
            m = re.search(r'(\d{8}_\d{6})$', name)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
                    candidates.append((dt, name))
                except ValueError:
                    pass

    # Fallback: check if directory name lacks the numeric index prefix (e.g. electric_storm_multi_ilp_all_)
    if not candidates:
        alt_prefix = re.sub(r'^\d+\.', '', prefix)
        if alt_prefix != prefix:
            for name in os.listdir(base_dir):
                full_path = os.path.join(base_dir, name)
                if not os.path.isdir(full_path):
                    continue
                if name.startswith(alt_prefix):
                    m = re.search(r'(\d{8}_\d{6})$', name)
                    if m:
                        try:
                            dt = datetime.strptime(m.group(1), '%Y%m%d_%H%M%S')
                            candidates.append((dt, name))
                        except ValueError:
                            pass

    if candidates:
        # Sort descending by parsed timestamp so the newest is at index 0
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    return None


def run_all(args):
    """Execute the plotting pipeline."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_data_dir = getattr(args, 'data_dir', None) or BASE_DATA_DIR
    max_steps = args.max_steps if args.max_steps is not None else MAX_STEPS

    # Determine which experiments to run
    if args.experiments:
        exp_ids = [int(e) for e in args.experiments]
    else:
        exp_ids = list(EXPERIMENTS.keys())

    # Determine which plots to run
    if args.only:
        plot_ids = [int(p) for p in args.only]
    else:
        plot_ids = list(PLOTS.keys())

    if args.skip_geo and 2 in plot_ids:
        plot_ids.remove(2)
        print("⏭️  Skipping Plot 2 (Geolocation Maps) — use --no-skip-geo to include.\n")

    total_tasks = len(exp_ids) * len(plot_ids)
    completed = 0
    t_start = time.time()

    print("=" * 70)
    print(f"  ECCOS Experiment Plotting Pipeline")
    print(f"  Data dir: {os.path.abspath(base_data_dir)}")
    print(f"  Experiments: {exp_ids}")
    print(f"  Plots: {plot_ids}")
    print(f"  Output: {os.path.abspath(OUTPUT_DIR)}")
    print(f"  Max steps: {max_steps if max_steps is not None else 'Auto-detected from data'}")
    print("=" * 70)
    print()

    for exp_id in exp_ids:
        exp = EXPERIMENTS[exp_id]
        dir_name = find_latest_experiment_dir(base_data_dir, exp['prefix'])

        if not dir_name:
            print(f"❌ ERROR: Simulation directory not found for prefix '{exp['prefix']}' in {base_data_dir}")
            continue

        sim_dir = os.path.join(base_data_dir, dir_name)

        print(f"{'─' * 60}")
        print(f"📊 Experiment {exp_id}: {exp['label']}")
        print(f"   Directory: {dir_name}")
        print(f"   Data: {sim_dir}")
        print(f"{'─' * 60}")

        for plot_id in plot_ids:
            plot_name, plot_func = PLOTS[plot_id]
            print(f"\n  🖊️  Plot {plot_id}: {plot_name}...")
            t_plot = time.time()

            try:
                plot_func(sim_dir, exp['key'], OUTPUT_DIR, max_steps)
                elapsed = time.time() - t_plot
                completed += 1
                print(f"     ✅ Done in {elapsed:.1f}s")
            except Exception as e:
                print(f"     ❌ FAILED: {e}")
                import traceback
                traceback.print_exc()

        print()

    elapsed_total = time.time() - t_start
    print("=" * 70)
    print(f"  ✅ Completed {completed}/{total_tasks} tasks in {elapsed_total:.1f}s")
    print(f"  📁 Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 70)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Master plotting script for ECCOS experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_plots.py                       # All plots, all experiments
  python run_all_plots.py --skip-geo            # Skip geolocation (fast)
  python run_all_plots.py --only 1 5 6 7        # Only specific plots
  python run_all_plots.py --experiments 1 4     # Only experiments 1 and 4
  python run_all_plots.py --only 2 --experiments 1  # Geo maps for storm only
  python run_all_plots.py --max-steps 1000      # Limit to 1000 steps
  python run_all_plots.py --data-dir path/to/dir # Specify custom data directory
        """
    )
    parser.add_argument('--data-dir', type=str, default=BASE_DATA_DIR,
                        help=f'Base directory containing experiment simulation runs (default: {BASE_DATA_DIR})')
    parser.add_argument('--skip-geo', action='store_true', default=False,
                        help='Skip Plot 2 (geolocation maps — generates PDFs per step)')
    parser.add_argument('--max-steps', type=int, default=None,
                        help='Max steps to plot (defaults to all available steps detected in data)')
    parser.add_argument('--only', nargs='+', type=int,
                        help='Only run specific plot numbers (1-7)')
    parser.add_argument('--experiments', nargs='+', type=int,
                        help='Only run specific experiment numbers (1-4)')
    args = parser.parse_args()
    run_all(args)
