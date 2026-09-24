# ECCOS Experimental Evaluation and Reproducibility Suite

This directory contains the declarative scenario configurations, simulation output traces, and plotting pipeline used to generate the experimental results presented in the research article:

> **"Event-Driven Computing Continuum Orchestration Solver (ECCOS): A Discrete-Event Simulation Framework for Optimal Service Placement and ML-Ready Trace Generation"**  
> *Mireia Jaume, Isaac Lera, Carlos Guerrero* (Submitted for evaluation).

---

## Directory Organization

```text
experiments/
├── README.md                          # This reproducibility guide
├── configuration_files/               # Canonical YAML definitions for the 4 paper scenarios
│   ├── scenario_1_electric_storm.yaml
│   ├── scenario_2_crowd_event.yaml
│   ├── scenario_3_demand_surge.yaml
│   └── scenario_4_normal_conditions.yaml
├── simulation_json_outputs_results/   # 5000-step simulation runs (archived/Zenodo)
│   ├── electric_storm_multi_ilp_all_20260910_130039/
│   ├── crowd_event_multi_ilp_all_20260916_131352/
│   ├── demand_surge_multi_ilp_all_20260910_131401/
│   └── normal_conditions_multi_ilp_all_20260910_072946/
├── plotting_scripts/                  # 17 specialized Matplotlib visualization modules
│   ├── plot1_system_overview.py
│   ├── plot2_geolocation_and_connectivity.py
│   ├── ...
│   ├── plot16_user_mobility_heatmap.py
│   └── plot17_user_tracks.py
├── figures/                           # Generated vector PDF plots (Figures 3-19)
└── run_all_plots.py                   # Master plotting orchestrator
```

---

## The 4 Benchmark Evaluation Scenarios

Each scenario models distinct stress profiles and continuum dynamics using declarative stochastic event sequences:

| ID | Scenario | Configuration File | Key Dynamics & Simulated Phenomena |
| :-: | :--- | :--- | :--- |
| **1** | **Electric Storm** | [`configuration_files/scenario_1_electric_storm.yaml`](configuration_files/scenario_1_electric_storm.yaml) | Severe weather event triggering correlated multi-node dropouts and physical edge failures across geographical zones. Tests placement recovery, failover policies, and service migration under degraded capacity. |
| **2** | **Crowd Event** | [`configuration_files/scenario_2_crowd_event.yaml`](configuration_files/scenario_2_crowd_event.yaml) | Massive localized influx of mobile users concentrated in an ultra-dense area (e.g., stadium, urban square). High spatial density and fast user arrival rate test access-point congestion and edge server offloading. |
| **3** | **Demand Surge** | [`configuration_files/scenario_3_demand_surge.yaml`](configuration_files/scenario_3_demand_surge.yaml) | Sudden viral spike in service request frequency coupled with localized link degradations (brownouts). Tests dynamic elasticity, CPU/RAM footprint changes, and SLA compliance. |
| **4** | **Normal Conditions** | [`configuration_files/scenario_4_normal_conditions.yaml`](configuration_files/scenario_4_normal_conditions.yaml) | Baseline steady-state conditions with standard Poisson arrivals, continuous uniform mobility, and degree-correlated resource distribution across Cloud, Fog, and Edge tiers. |

---

## Reproducing the Simulations

All simulations can be reproduced from the project root using `run_experiments.py`:

```bash
# 1. Activate the environment
source .venv/bin/activate

# 2. List all registered experiment scenarios
python run_experiments.py --list

# 3. Quick sanity check (100 iterations per scenario)
python run_experiments.py --iterations 100

# 4. Full paper reproduction (5000 iterations per scenario)
python run_experiments.py --iterations 5000

# 5. Run only specific scenarios (e.g., Scenario 1 and Scenario 2)
python run_experiments.py --experiments 1 2 --iterations 5000
```

---

## Telemetry and Trace Structure (`Simulation{i}.json`)

ECCOS emits fine-grained, telemetry-rich JSON snapshots before and after every discrete event. These files are explicitly formatted as **Markov Decision Process (MDP)** transitions $(s_t, a_t, r_t, s_{t+1})$, enabling direct ingestion by Supervised Learning and Reinforcement Learning (RL) agents:

```json
{
  "users_before":         { "...": "User coordinates, request ratios, and connected access points at step t" },
  "apps_before":          { "...": "Microservice chains (SFC), resource requirements (CPU, RAM) at step t" },
  "placement_before":     { "...": "Active mapping of microservices to physical infrastructure nodes" },
  "node_before":          { "...": "Node capacities, current load, and operational status" },
  "edge_before":          { "...": "Physical edge latencies, bandwidth availability, and degradation states" },
  "metrics_before":       { "...": "Latency, energy, migration overhead, and SLA objective score" },
  "action":               { "...": "The discrete event executed at step t (e.g., node_drop, user_move)" },
  "diff_message":         "Human-readable log of the state change",
  "ilp_executed":         true,
  "placement_after":      { "...": "New optimal service placement computed by the solver" },
  "users_after":          { "...": "Updated user states at step t + 1" },
  "node_after":           { "...": "Updated node allocations after placement execution" },
  "edge_after":           { "...": "Updated network states" },
  "metrics_after": {
    "objective": 8.5322,
    "total_latency": 8.5322,
    "solver_status": "Optimal",
    "solve_time_seconds": 0.2135,
    "total_ram_occupied": 0.34
  }
}
```

---

## Open Science Data Archiving Policy

- **Repository Size Optimization:** Because 5,000 iterations across 4 scenarios generate ~3.1 GB of raw JSON telemetry, raw output directories (`Simulations_raw/` and `experiments/simulation_json_outputs_results/`) are excluded from Git tracking via [`.gitignore`](../.gitignore) to ensure fast and lightweight repository cloning.
- **Open Data Archive (Zenodo):** The full 5,000-step raw dataset is permanently archived on Zenodo with an open-access DOI:
  - **Zenodo Record:** [10.5281/zenodo.XXXXXXX](https://doi.org/10.5281/zenodo.XXXXXXX) *(update with publication DOI)*
- **Local Replication:** Any researcher can regenerate the identical raw dataset locally by executing `python run_experiments.py --iterations 5000` with the preconfigured master seed (`42`).

---

## Generating Publication Figures

The orchestrator `run_all_plots.py` extracts time-series and spatial data from the simulation outputs and produces publication-ready vector PDFs in `figures/`:

```bash
# Generate all 17 plot families for all 4 experiments
python experiments/run_all_plots.py --skip-geo

# Generate specific plots (e.g., Plot 16: Heatmap, Plot 17: User Tracks)
python experiments/run_all_plots.py --only 16 17

# Generate plots for a single experiment (e.g., Scenario 2: Crowd Event)
python experiments/run_all_plots.py --experiments 2 --skip-geo

# Point to an external dataset directory
python experiments/run_all_plots.py --data-dir path/to/simulation_runs
```

### Plot Catalog

| Script | Visualization Output | Description |
| :--- | :--- | :--- |
| `plot1_system_overview.py` | `plot1_system_overview_*.pdf` | Aggregated counts of active users, applications, operational nodes, and edges. |
| `plot2_geolocation_and_connectivity.py` | `plot2_geolocation_*.pdf` | Spatial connectivity graph showing user-node associations per discrete step. |
| `plot3_app_popularity.py` | `plot3_app_popularity_*.pdf` | Request volume distribution per application across simulation time. |
| `plot4_user_activity.py` | `plot4_user_activity_*.pdf` | User churn, active connection transitions, and request frequency variations. |
| `plot5_node_availability.py` | `plot5_node_availability_*.pdf` | CPU and RAM utilization timelines across Cloud, Fog, and Edge tiers. |
| `plot6_event_timeline.py` | `plot6_event_timeline_*.pdf` | Discrete step occurrence timeline categorized by event type. |
| `plot7_optimization.py` | `plot7_optimization_*.pdf` | Multi-objective cost breakdown (latency, migration penalties, server usage). |
| `plot8_app_request_rate.py` | `plot8_app_request_rate_*.pdf` | Request rate evolution per microservice application. |
| `plot9_single_objective.py` | `plot9_single_objective_*.pdf` | Latency convergence curves for single-objective optimization baselines. |
| `plot10_event_timeline_by_time.py` | `plot10_event_timeline_by_time_*.pdf` | Continuous simulation time event occurrence distribution. |
| `plot11_optimization_by_time.py` | `plot11_optimization_by_time_*.pdf` | Objective value trajectories mapped over simulated wall-clock seconds. |
| `plot12_single_objective_by_time.py` | `plot12_single_objective_by_time_*.pdf` | Continuous-time latency under single-objective solver. |
| `plot13_node_availability_by_time.py` | `plot13_node_availability_by_time_*.pdf` | Tier-wise resource capacity evolution plotted against continuous time. |
| `plot14_app_migrations.py` | `plot14_app_migrations_*.pdf` | Cumulative and per-step service migration frequencies. |
| `plot15_app_request_rate_lines.py` | `plot15_app_request_rate_lines_*.pdf` | High-resolution multi-line request throughput traces. |
| `plot16_user_mobility_heatmap.py` | `plot16_user_heatmap_*.pdf` | Spatial density heatmaps illustrating user concentration and hotspot emergence. |
| `plot17_user_tracks.py` | `plot17_user_tracks_*.pdf` | Spatial vector trajectories of mobile users across the 2D continuum coordinate plane. |
