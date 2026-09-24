# ECCOS Precomputed Simulation Traces & Experimental Dataset

[![DOI: 10.5281/zenodo.22947855](https://zenodo.org/badge/DOI/10.5281/zenodo.22947855.svg)](https://doi.org/10.5281/zenodo.22947855)

This directory is the designated workspace for the precomputed, 5,000-step raw simulation output traces (`Simulation{i}.json`) used in the research paper:

> **"Event-Driven Computing Continuum Orchestration Solver (ECCOS): A Discrete-Event Simulation Framework for Optimal Service Placement and ML-Ready Trace Generation"**  
> *Mireia Jaume, Isaac Lera, Carlos Guerrero* (Submitted for evaluation).

---

## 📦 Obtaining the Full Dataset from Zenodo

Due to GitHub's file size policies, the full high-resolution trace dataset (~3.1 GB uncompressed across 4 scenarios) is permanently archived on **Zenodo**:

- **Zenodo DOI:** [10.5281/zenodo.22947855](https://doi.org/10.5281/zenodo.22947855)
- **Archive File:** `eccos_simulation_traces.tar.gz` (or `eccos_dataset.zip`)
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Quick Download & Extraction Instructions

To download and extract the dataset directly into this directory:

```bash
# 1. Navigate to the repository root
cd path/to/ECCOS

# 2. Download the archive from Zenodo
curl -L -o eccos_simulation_traces.tar.gz https://zenodo.org/records/22947855/files/eccos_simulation_traces.tar.gz?download=1

# 3. Extract contents into this directory
tar -xzf eccos_simulation_traces.tar.gz -C experiments/simulation_json_outputs_results/

# 4. Verify directory contents
ls experiments/simulation_json_outputs_results/
```

### Expected Directory Layout

Once extracted, this directory should contain the four canonical paper scenarios:

```text
experiments/simulation_json_outputs_results/
├── README.md                                          # This file
├── electric_storm_multi_ilp_all_20260910_130039/      # Scenario 1 (5,000 step JSON snapshots)
├── crowd_event_multi_ilp_all_20260916_131352/        # Scenario 2 (5,000 step JSON snapshots)
├── demand_surge_multi_ilp_all_20260910_131401/        # Scenario 3 (5,000 step JSON snapshots)
└── normal_conditions_multi_ilp_all_20260910_072946/   # Scenario 4 (5,000 step JSON snapshots)
```

---

## 🔄 Alternative: Local Deterministic Regeneration

You do not need to download the Zenodo archive if you prefer to recompute the exact traces locally. ECCOS includes full deterministic simulation seeds (`seed: 42`). 

From the repository root, run:

```bash
# Regenerate all 4 scenarios (5,000 iterations each)
python run_experiments.py --iterations 5000

# Or regenerate a single scenario (e.g., Scenario 2: Crowd Event)
python run_experiments.py --experiments 2 --iterations 5000
```

---

## 📈 Generating Publication Figures from Traces

Once the traces are present in this directory, generate all vector PDF publication plots (Figures 3–19) by executing:

```bash
python experiments/run_all_plots.py --skip-geo
```

The resulting figures will be saved in [`experiments/figures/`](../figures/).

---

## 🔬 Trace Format Specification (`Simulation{i}.json`)

Each step snapshot is formatted as a Markov Decision Process (MDP) transition $(s_t, a_t, r_t, s_{t+1})$:

```json
{
  "users_before":         { "u_id": { "pos": [x, y], "connectedTo": "n_id", "app_requests": { "app_id": rate } } },
  "apps_before":          { "app_id": { "services": [ { "name": "s1", "CPU": 0.5, "RAM": 1.0 } ] } },
  "placement_before":     { "app_id": { "s1": "node_id" } },
  "node_before":          { "node_id": { "CPU": cap, "RAM": cap, "enable": true, "layer": "edge" } },
  "edge_before":          [ { "source": "n1", "target": "n2", "latency": 10.0, "bandwidth": 100.0, "enable": true } ],
  "action":               { "global_time": 12.4, "action": { "action": "node_drop", "target": 5 } },
  "ilp_executed":         true,
  "placement_after":      { "app_id": { "s1": "new_node_id" } },
  "metrics_after": {
    "objective": 12.45,
    "total_latency": 10.2,
    "solver_status": "Optimal",
    "solve_time_seconds": 0.045
  }
}
```
