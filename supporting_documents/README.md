# Spec-Driven Development and Technical Documentation

This directory contains the formal design documentation, mathematical formulations, and domain specifications developed for the **ECCOS** (*Event-Driven Computing Continuum Orchestration Solver*) simulation framework.

In line with open-science reproducibility best practices, ECCOS was engineered following a **Spec-Driven Development (SDD)** methodology: every stochastic event, topology model, composite macro-phenomenon, and optimization objective was mathematically and algorithmically specified prior to implementation.

---

## Directory Overview

```text
supporting_documents/
├── README.md                      # This index and methodological guide
├── spec_driven_catalog/           # 10 formal specification documents for simulator entities
└── design_notes/                  # 14 technical architectural notes and mathematical formulations
```

---

## Spec-Driven Development Catalog (`spec_driven_catalog/`)

The following formal specifications detail the statistical distributions, state transition logic, and parameter semantics of the simulation engine:

| Specification Document | Focus Area | Key Concepts & Mathematical Models |
| :--- | :--- | :--- |
| [`03-composite-events.md`](spec_driven_catalog/03-composite-events.md) | Macro-Phenomena & Composite Events | Correlated cascades: electric storms (correlated node/link dropouts), flash crowd gatherings, demand surges, and zone-based brownouts. |
| [`especificacion_eventos_degradacion_infraestructura.md`](spec_driven_catalog/especificacion_eventos_degradacion_infraestructura.md) | Infrastructure Degradation | Stochastic node and link degradation models; Beta-distributed capacity losses ($p_{\text{loss}} \sim \text{Beta}(a, b)$) and exponential recovery times. |
| [`especificaciones_generacion_entorno.md`](spec_driven_catalog/especificaciones_generacion_entorno.md) | Multi-tier Continuum Graph | Procedural Barabási-Albert Scale-Free topology generation, betweenness-centrality layering (Cloud, Fog, Edge tiers), and latency assignment. |
| [`model_dag_para_aplicaciones.md`](spec_driven_catalog/model_dag_para_aplicaciones.md) | Microservice Workflows (SFC/DAG) | Directed Acyclic Graph (DAG) service composition, inter-microservice bandwidth demands, and dependency sequencing. |
| [`modelo_aplicaciones_y_popularidad.md`](spec_driven_catalog/modelo_aplicaciones_y_popularidad.md) | Application Ecosystem & Popularity | Zipf/Pareto application popularity skew, Poisson request arrivals, and dynamic popularity surge dynamics. |
| [`modelo_movilidad_usuarios.md`](spec_driven_catalog/modelo_movilidad_usuarios.md) | User Spatial Mobility | 2D continuous space user mobility models: Thomas Cluster Process (hotspot grouping), Random Waypoint, and Manhattan Grid models. |
| [`spec_eventos_desconexion_usuarios.md`](spec_driven_catalog/spec_eventos_desconexion_usuarios.md) | User Churn & Lifecycle | Exponential session durations, temporary radio disconnections, handoffs between edge access points, and reconnection events. |
| [`ampliar_eventos_app.md`](spec_driven_catalog/ampliar_eventos_app.md) | Day-2 Application Elasticity | Dynamic resource footprint expansion/shrinkage (Osmosis computing) and runtime service migration triggers. |
| [`catalogo_eventos_simulador.md`](spec_driven_catalog/catalogo_eventos_simulador.md) | Global Event Taxonomy | Exhaustive taxonomic index of atomic base events vs. composite macro-events across infrastructure, applications, and users. |
| [`especificaciones_grafica_eventos.md`](spec_driven_catalog/especificaciones_grafica_eventos.md) | Telemetry & Visual Analytics | Specifications for step-by-step event tracking, heatmap discretization, and timeline telemetry generation. |

---

## Architectural & Design Notes (`design_notes/`)

These documents archive the mathematical optimization formulations, solver decoupling architecture, and YAML schema mappings:

| Design Document | Architectural Scope | Key Details |
| :--- | :--- | :--- |
| [`sfc_ilp_formulation.md`](design_notes/sfc_ilp_formulation.md) | Optimization Formulation | Complete mathematical formulation of the Service Function Chaining (SFC) Integer Linear Program (ILP) with migration penalties. |
| [`solvers.md`](design_notes/solvers.md) | Optimization Engine Abstraction | Decoupled solver interface: BaseSolver, SingleObjectiveILP, MultiObjectiveILP, and Greedy heuristic backends. |
| [`Decoupling_Simulation_Plan.md`](design_notes/Decoupling_Simulation_Plan.md) | Architectural Decoupling | Architecture decoupling plan separating scenario definition (`scenario_config.yaml`) from solver triggers (`solver_config.yaml`). |
| [`trigger_policies_config.md`](design_notes/trigger_policies_config.md) | Solver Trigger Policies | Periodic, event-driven, threshold-based, and stochastic solver invocation policies (`solve_all`, `solve_every_t_seconds`, `combined`). |
| [`jcr_topology_models.md`](design_notes/jcr_topology_models.md) | Network Graph Models | Evaluation of Scale-Free, Small-World (Watts-Strogatz), and hierarchical multi-tier continuum graphs for JCR publication. |
| [`eventos_yaml_mapping.md`](design_notes/eventos_yaml_mapping.md) | YAML Event Binding | Mapping between declarative YAML event clauses and internal discrete-event priority queue triggers in `src/eventSet.py`. |
| [`app_architecture_modes.md`](design_notes/app_architecture_modes.md) | Monolithic vs. Microservices | Formal distinction and state transitions between monolithic services and modular microservice chains. |
| [`infrastructure_degradation_config.md`](design_notes/infrastructure_degradation_config.md) | Fault Modeling | Configuration parameters for partial capacity drops, complete node failure, edge disruption, and recovery intervals. |
| [`user_mobility_config.md`](design_notes/user_mobility_config.md) | Mobility Parameterization | Configuration schema for user movement velocities, directional angles, boundaries, and spatial clustering radii. |
| [`user_disconnection_config.md`](design_notes/user_disconnection_config.md) | Churn Configuration | Configuration schema for user connection dropouts, duration of outage, and reconnection policies. |
| [`topology_generation_config.md`](design_notes/topology_generation_config.md) | Infrastructure YAML Schema | Parameter specs for node degree distribution, link bandwidth capacities, and propagation latencies. |
| [`app_generation_config.md`](design_notes/app_generation_config.md) | Application YAML Schema | Parameter specs for CPU/RAM footprints, microservice chain depth, and inter-service dependencies. |
| [`graph_attributes_config.md`](design_notes/graph_attributes_config.md) | Node/Edge Attribute Profiles | Centrality-based resource assignment algorithms linking network position to compute capacity. |
| [`distributions_example.json`](design_notes/distributions_example.json) | Statistical Samples | Reference statistical parameterizations for Pareto, Exponential, Beta, Uniform, and Normal distributions. |

---

## Research Traceability

Every component in the Python source code directly implements one or more of these design specifications:

- **`src/infrastructure.py` & `src/factories/`** $\longleftrightarrow$ [`especificaciones_generacion_entorno.md`](spec_driven_catalog/especificaciones_generacion_entorno.md), [`topology_generation_config.md`](design_notes/topology_generation_config.md)
- **`src/appSet.py`** $\longleftrightarrow$ [`model_dag_para_aplicaciones.md`](spec_driven_catalog/model_dag_para_aplicaciones.md), [`modelo_aplicaciones_y_popularidad.md`](spec_driven_catalog/modelo_aplicaciones_y_popularidad.md)
- **`src/userSet.py`** $\longleftrightarrow$ [`modelo_movilidad_usuarios.md`](spec_driven_catalog/modelo_movilidad_usuarios.md), [`user_mobility_config.md`](design_notes/user_mobility_config.md)
- **`src/eventSet.py`** $\longleftrightarrow$ [`03-composite-events.md`](spec_driven_catalog/03-composite-events.md), [`especificacion_eventos_degradacion_infraestructura.md`](spec_driven_catalog/especificacion_eventos_degradacion_infraestructura.md)
- **`src/solvers/`** $\longleftrightarrow$ [`sfc_ilp_formulation.md`](design_notes/sfc_ilp_formulation.md), [`solvers.md`](design_notes/solvers.md)
