from pulp import LpVariable, LpProblem, LpMinimize, lpSum, PULP_CBC_CMD, value, LpStatus
import logging
import time
from typing import Any, Dict, Optional, Tuple
from src.constants import INFEASIBLE_PENALTY, PENALTY_DELAY, DEFAULT_INFRA_ID
from .base_solver import BaseSolver

logger = logging.getLogger(__name__)


class ILPSingleObjectiveSolver(BaseSolver):
    def solve(self, graph_dict: Any, application_set: Any, user_set: Any, 
              config: Dict[str, Any], previous_placement: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Solves the application placement problem using ILP to minimize weighted latency
        for Service Function Chaining (SFC) microservices.
        """
        if config is None:
            config = {}
        infeasible_penalty = float(config.get('setup', {}).get('infeasible_penalty', INFEASIBLE_PENALTY))
        gap_rel = config.get('setup', {}).get('ilp_solver', {}).get('gapRel', 0.05)
        time_limit = config.get('setup', {}).get('ilp_solver', {}).get('timeLimit', 60)

        graph = graph_dict.get_main_graph() 

        if graph is None:
            logger.error("Main graph not found in InfrastructureSet.")
            return None, {
                "objective": infeasible_penalty,
                "total_latency": infeasible_penalty,
                "solver_status": "Infeasible",
                "solve_time_seconds": 0.0
            }

        graph_item = graph_dict.infrastructures.get(DEFAULT_INFRA_ID, {})
        all_pairs_shortest_paths = graph_item.get('shortest_paths', {})

        applications = application_set.get_all_apps()
        users = user_set.get_all_users()

        active_nodes = [n for n, attrs in graph.nodes(data=True) if attrs.get('enable', True)]

        if not active_nodes:
            return None, {
                "objective": infeasible_penalty,
                "total_latency": infeasible_penalty,
                "solver_status": "Infeasible",
                "solve_time_seconds": 0.0
            }

        # Prepare microservices lists
        # Each app has a list of microservices: [{'id': 'ms0', 'ram': 2.0}, ...]
        ms_indices = []
        for app_id, app_data in applications.items():
            microservices = app_data.get('microservices', [])
            for m_idx, ms in enumerate(microservices):
                ms_indices.append((app_id, ms['id'], m_idx))

        # Decision Variable: x_amn is 1 if microservice 'm' of app 'a' is placed on node 'n'
        x_amn = LpVariable.dicts("Place_MS", 
                                 [(app_id, ms_id, node) for app_id, ms_id, m_idx in ms_indices for node in active_nodes], 
                                 cat='Binary')

        # Decision Variable for SFC links: y_amnn is 1 if source ms is on n1 AND target ms is on n2
        y_amnn = {}
        for app_id, app_data in applications.items():
            edges = app_data.get('edges', [])
            for e_idx, edge in enumerate(edges):
                for n1 in active_nodes:
                    for n2 in active_nodes:
                        y_amnn[(app_id, e_idx, n1, n2)] = LpVariable(f"Link_{app_id}_{e_idx}_{n1}_{n2}", lowBound=0, cat='Continuous')

        # Total request weight across all users to compute weighted mean latency
        total_user_weight = sum(float(u.get('requestRatio', 0.0)) for u in users.values())
        norm_factor = 1.0 / total_user_weight if total_user_weight > 0 else 1.0

        prob = LpProblem("SFC_Placement", LpMinimize)
        objective_terms = []

        # 1. User Latency: Delay to the FIRST microservice of the requested app
        for user_id, user_data in users.items():
            requested_app_id = user_data.get('requestedApp')
            user_home_node = user_data.get('connectedTo')
            user_weight = float(user_data.get('requestRatio', 0.0))

            if requested_app_id in applications and user_home_node in active_nodes and user_weight > 0:
                app_data = applications[requested_app_id]
                if not app_data.get('microservices'):
                    continue
                first_ms_id = app_data['microservices'][0]['id']

                norm_user_weight = user_weight * norm_factor
                paths_from_user = all_pairs_shortest_paths.get(user_home_node, {})

                for n in active_nodes:
                    if n == user_home_node:
                        delay_value = 0.0
                    elif n in paths_from_user:
                        delay_value = paths_from_user[n]
                    else:
                        delay_value = infeasible_penalty * (total_user_weight / max(user_weight, 1.0))
                    objective_terms.append(delay_value * norm_user_weight * x_amn[requested_app_id, first_ms_id, n])

        # 2. Internal SFC Latency: Delay between microservices
        for app_id, app_data in applications.items():
            edges = app_data.get('edges', [])
            if not edges:
                continue

            # Weight internal delay by the total request ratio for this app
            app_request_ratio = sum(float(u.get('requestRatio', 0.0)) for u in users.values() if u.get('requestedApp') == app_id)
            if app_request_ratio > 0:
                norm_app_weight = app_request_ratio * norm_factor
            else:
                norm_app_weight = 1e-5 / max(1, len(applications))

            for e_idx, edge in enumerate(edges):
                for n1 in active_nodes:
                    paths_from_n1 = all_pairs_shortest_paths.get(n1, {})
                    for n2 in active_nodes:
                        if n1 == n2:
                            delay_value = 0.0
                        elif n2 in paths_from_n1:
                            delay_value = paths_from_n1[n2]
                        else:
                            if app_request_ratio > 0:
                                delay_value = infeasible_penalty * (total_user_weight / app_request_ratio)
                            else:
                                delay_value = infeasible_penalty
                        objective_terms.append(delay_value * norm_app_weight * y_amnn[(app_id, e_idx, n1, n2)])

        # 3. Symmetry Breaker: Add a tiny penalty based on node index to break symmetry for apps without users
        app_idx_map = {app_id: idx for idx, app_id in enumerate(applications.keys())}
        for app_id, ms_id, m_idx in ms_indices:
            a_idx = app_idx_map.get(app_id, 0)
            for node in active_nodes:
                try:
                    node_idx = int(node)
                except ValueError:
                    node_idx = hash(node) % 1000

                sym_penalty = 1e-6 * (node_idx + a_idx * 100)
                objective_terms.append(sym_penalty * x_amn[app_id, ms_id, node])

        prob += lpSum(objective_terms), "Weighted_Mean_Latency"

        # Constraint 1: Every microservice must be placed exactly once
        for app_id, ms_id, m_idx in ms_indices:
            prob += lpSum(x_amn[app_id, ms_id, node] for node in active_nodes) == 1, f"Placement_{app_id}_{ms_id}"

        # Constraint 2: Generic Resource Capacity constraints per node
        for node in active_nodes:
            node_attrs = graph.nodes[node]
            for attr_name, node_cap in node_attrs.items():
                # We only want numeric capacities
                if isinstance(node_cap, (int, float)):
                    attr_terms = []
                    for app_id, ms_id, m_idx in ms_indices:
                        app_data = applications[app_id]
                        ms_attr_val = app_data['microservices'][m_idx].get(attr_name, 0.0)
                        if ms_attr_val > 0:
                            attr_terms.append(ms_attr_val * x_amn[app_id, ms_id, node])
                    if attr_terms:
                        prob += lpSum(attr_terms) <= node_cap, f"Cap_{attr_name}_{node}"

        # Constraint 3: Linearization of y variables
        for app_id, app_data in applications.items():
            edges = app_data.get('edges', [])
            for e_idx, edge in enumerate(edges):
                ms_id1 = edge['source']
                ms_id2 = edge['target']
                for n1 in active_nodes:
                    # The sum of links originating from ms_id1 on n1 must equal x_amn for ms_id1 on n1
                    prob += lpSum(y_amnn[(app_id, e_idx, n1, n2)] for n2 in active_nodes) == x_amn[app_id, ms_id1, n1], f"Lin3_{app_id}_{e_idx}_{n1}"
                for n2 in active_nodes:
                    # The sum of links terminating at ms_id2 on n2 must equal x_amn for ms_id2 on n2
                    prob += lpSum(y_amnn[(app_id, e_idx, n1, n2)] for n1 in active_nodes) == x_amn[app_id, ms_id2, n2], f"Lin4_{app_id}_{e_idx}_{n2}"

        # Limit solving time to prevent hanging on complex topologies
        start_time = time.time()
        prob.solve(PULP_CBC_CMD(msg=0, timeLimit=time_limit, gapRel=gap_rel))
        solve_time = round(time.time() - start_time, 4)

        status_str = LpStatus.get(prob.status, "Undefined")

        if status_str == "Optimal":
            placement = {}
            for app_id, app_data in applications.items():
                app_name = app_data['name']
                placement[app_name] = {}
                for ms in app_data.get('microservices', []):
                    for node in active_nodes:
                        val = value(x_amn[app_id, ms['id'], node])
                        if val is not None and val > 0.5:
                            placement[app_name][ms['id']] = node
                            break

            # Topological check: verify all active users have reachable paths
            is_connected = self.check_topological_connectivity(
                placement, applications, users, active_nodes, all_pairs_shortest_paths
            )

            if not is_connected:
                return None, {
                    "objective": infeasible_penalty,
                    "total_latency": infeasible_penalty,
                    "solver_status": "Disconnected",
                    "solve_time_seconds": solve_time
                }

            # Exact weighted mean latency in milliseconds
            mean_latency = self.compute_weighted_mean_latency(
                placement, applications, users, active_nodes, all_pairs_shortest_paths
            )

            return placement, {
                "objective": mean_latency,
                "total_latency": mean_latency,
                "solver_status": "Optimal",
                "solve_time_seconds": solve_time
            }
        elif status_str == "Not Solved":
            # Time limit reached without finding or certifying an optimal solution
            return None, {
                "objective": infeasible_penalty,
                "total_latency": infeasible_penalty,
                "solver_status": "Not Solved",
                "solve_time_seconds": solve_time
            }
        else:
            # "Infeasible", "Unbounded", etc.
            status_label = status_str if status_str in ["Infeasible", "Unbounded"] else "Infeasible"
            return None, {
                "objective": infeasible_penalty,
                "total_latency": infeasible_penalty,
                "solver_status": status_label,
                "solve_time_seconds": solve_time
            }



