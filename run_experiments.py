#!/usr/bin/env python3
"""
Batch runner for ECCOS simulation experiments.

Usage:
    python run_experiments.py                         # All 4 experiments, 1000 iterations
    python run_experiments.py --iterations 5000       # All 4 experiments, 5000 iterations
    python run_experiments.py --experiments 1 3       # Only experiments 1 and 3
    python run_experiments.py --experiments 2 --iterations 500  # Only experiment 2, 500 iters
    python run_experiments.py --list                  # List available experiments
"""

import os
import sys
import time
import argparse
import logging
from main import run_simulation, setup_logging

logger = logging.getLogger("ExperimentBatchRunner")

SCENARIOS = {
    1: ("Scenario 1 (Electric Storm)", "experiments/configuration_files/scenario_1_electric_storm.yaml"),
    2: ("Scenario 2 (Crowd Event)", "experiments/configuration_files/scenario_2_crowd_event.yaml"),
    3: ("Scenario 3 (Demand Surge)", "experiments/configuration_files/scenario_3_demand_surge.yaml"),
    4: ("Scenario 4 (Normal Conditions)", "experiments/configuration_files/scenario_4_normal_conditions.yaml"),
}


def list_experiments():
    """Print available experiments and exit."""
    print("\nAvailable experiments:")
    for num, (name, path) in sorted(SCENARIOS.items()):
        print(f"  {num}. {name}")
        print(f"     File: {path}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Run ECCOS simulation experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_experiments.py                           # All experiments, 1000 iterations
  python run_experiments.py --iterations 5000         # All experiments, 5000 iterations
  python run_experiments.py --experiments 1 3         # Only experiments 1 and 3
  python run_experiments.py --experiments 2 -n 500    # Only experiment 2, 500 iterations
  python run_experiments.py --list                    # List available experiments
        """
    )
    parser.add_argument('--experiments', '-e', nargs='+', type=int,
                        help='Experiment numbers to run (1-4). Default: all')
    parser.add_argument('--iterations', '-n', type=int, default=1000,
                        help='Number of simulation iterations (default: 1000)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available experiments and exit')
    args = parser.parse_args()

    if args.list:
        list_experiments()
        sys.exit(0)

    setup_logging()

    # Determine which experiments to run
    if args.experiments:
        exp_ids = []
        for e in args.experiments:
            if e not in SCENARIOS:
                print(f"ERROR: Unknown experiment number {e}. Valid: {list(SCENARIOS.keys())}")
                sys.exit(1)
            exp_ids.append(e)
    else:
        exp_ids = sorted(SCENARIOS.keys())

    total_iterations = args.iterations
    scenarios_to_run = [(SCENARIOS[e][0], SCENARIOS[e][1]) for e in exp_ids]

    start_total = time.time()
    results = []

    print(f"\n{'='*70}")
    print(f"  ECCOS Experiment Batch Runner")
    print(f"  Experiments: {exp_ids}")
    print(f"  Iterations: {total_iterations}")
    print(f"{'='*70}\n", flush=True)

    for name, path in scenarios_to_run:
        full_path = os.path.join(os.path.dirname(__file__), path)
        print(f"\n{'='*70}\nSTARTING: {name}\nFile: {path}\nIterations: {total_iterations}\n{'='*70}\n", flush=True)
        start_sim = time.time()
        try:
            run_simulation(
                scenario_path=full_path,
                total_iterations=total_iterations,
            )
            elapsed = time.time() - start_sim
            print(f"\nCOMPLETED: {name} in {elapsed:.2f}s\n", flush=True)
            results.append((name, path, "SUCCESS", elapsed))
        except Exception as e:
            elapsed = time.time() - start_sim
            print(f"\nFAILED: {name} after {elapsed:.2f}s. Error: {e}\n", flush=True)
            results.append((name, path, f"FAILED: {e}", elapsed))

    total_elapsed = time.time() - start_total
    print(f"\n{'='*70}\nEXPERIMENT BATCH SUMMARY\nTotal Time: {total_elapsed:.2f}s\n{'='*70}", flush=True)
    for name, path, status, elapsed in results:
        print(f" - {name} ({path}): {status} [{elapsed:.2f}s]", flush=True)

if __name__ == "__main__":
    main()
