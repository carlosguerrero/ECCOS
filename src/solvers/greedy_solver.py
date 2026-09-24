import logging
import time
from typing import Any, Dict, Optional, Tuple, List
from src.constants import INFEASIBLE_PENALTY, PENALTY_DELAY, DEFAULT_INFRA_ID
from .base_solver import BaseSolver

logger = logging.getLogger(__name__)


class GreedySolver(BaseSolver):
    """
    Algoritmo Greedy para el emplazamiento de microservicios y aplicaciones.
    
    Estrategia del algoritmo:
    1. Ordena todas las aplicaciones desde la más solicitada a la menos solicitada,
       sumando los request rates (requestRatio) de todos los usuarios que solicitan
       una aplicación dada.
    2. Emplaza las aplicaciones en ese orden de prioridad (de mayor a menor solicitud).
    3. Para escoger el nodo donde emplazar una aplicación, busca el punto medio ponderado
       en el grafo de nodos utilizando shortest path hasta los nodos en los que están
       conectados los usuarios que solicitan la aplicación, ponderando por la tasa de
       petición (requestRatio) de cada usuario para atraer el emplazamiento hacia los
       usuarios más activos.
    4. Verifica estrictamente que los recursos utilizados no superen la capacidad
       disponible en cada nodo.
    """

    def solve(
        self,
        graph_dict: Any,
        application_set: Any,
        user_set: Any,
        config: Dict[str, Any],
        previous_placement: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        start_time = time.time()
        if config is None:
            config = {}

        infeasible_penalty = float(config.get('setup', {}).get('infeasible_penalty', INFEASIBLE_PENALTY))

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
            logger.warning("GreedySolver: No active nodes found in graph.")
            return None, {
                "objective": infeasible_penalty,
                "total_latency": infeasible_penalty,
                "solver_status": "Infeasible",
                "solve_time_seconds": 0.0
            }

        # 1. Initialize remaining resource capacities per active node
        remaining_resources: Dict[Any, Dict[str, float]] = {}
        for node in active_nodes:
            node_attrs = graph.nodes[node]
            remaining_resources[node] = {}
            for attr_name, node_cap in node_attrs.items():
                if isinstance(node_cap, (int, float)):
                    remaining_resources[node][attr_name] = float(node_cap)

        def can_fit_microservices(node: Any, ms_list: List[Dict[str, Any]]) -> bool:
            demands: Dict[str, float] = {}
            for ms in ms_list:
                for attr_name, demand in ms.items():
                    if isinstance(demand, (int, float)) and demand > 0 and attr_name in remaining_resources[node]:
                        demands[attr_name] = demands.get(attr_name, 0.0) + float(demand)
            for attr_name, total_demand in demands.items():
                if remaining_resources[node].get(attr_name, 0.0) < total_demand:
                    return False
            return True

        def consume_resources(node: Any, ms_list: List[Dict[str, Any]]) -> None:
            for ms in ms_list:
                for attr_name, demand in ms.items():
                    if isinstance(demand, (int, float)) and demand > 0 and attr_name in remaining_resources[node]:
                        remaining_resources[node][attr_name] -= float(demand)

        # Helper for shortest path lookup
        def get_delay(source_node: Any, target_node: Any) -> float:
            if source_node == target_node:
                return 0.0
            paths_from_source = all_pairs_shortest_paths.get(source_node, {})
            return float(paths_from_source.get(target_node, PENALTY_DELAY))

        # 2. Sum request rates per application and map users by requested application
        app_request_rates: Dict[str, float] = {app_id: 0.0 for app_id in applications.keys()}
        app_users_map: Dict[str, List[Dict[str, Any]]] = {app_id: [] for app_id in applications.keys()}

        for user_id, user_data in users.items():
            requested_app_id = user_data.get('requestedApp')
            if requested_app_id in applications:
                app_users_map[requested_app_id].append(user_data)
                app_request_rates[requested_app_id] += float(user_data.get('requestRatio', 0.0))

        # Sort applications from most requested to least requested
        # Tie-breaker: application id ascending for deterministic behavior
        sorted_app_ids = sorted(
            applications.keys(),
            key=lambda app_id: (-app_request_rates.get(app_id, 0.0), str(app_id))
        )

        # Helper to compute weighted median / attraction score of a candidate node for an app's users
        def compute_node_attraction_score(node: Any, app_users: List[Dict[str, Any]]) -> float:
            if not app_users:
                return 0.0
            score = 0.0
            for user_data in app_users:
                user_home_node = user_data.get('connectedTo')
                request_ratio = float(user_data.get('requestRatio', 0.0))
                delay = get_delay(user_home_node, node)
                score += request_ratio * delay
            return score

        # 3. Place applications greedily from most requested to least requested
        placement: Dict[str, Dict[str, Any]] = {}

        for app_id in sorted_app_ids:
            app_data = applications[app_id]
            app_name = app_data['name']
            microservices = app_data.get('microservices', [])
            app_users = app_users_map[app_id]

            # Order candidate nodes by weighted shortest-path score towards active users
            sorted_candidate_nodes = sorted(
                active_nodes,
                key=lambda n: (compute_node_attraction_score(n, app_users), str(n))
            )

            placement[app_name] = {}
            all_placed = False

            # First attempt: place the entire application (all microservices) on the best candidate node
            for candidate_node in sorted_candidate_nodes:
                if can_fit_microservices(candidate_node, microservices):
                    for ms in microservices:
                        placement[app_name][ms['id']] = candidate_node
                    consume_resources(candidate_node, microservices)
                    all_placed = True
                    break

            # Fallback attempt: if no single node can host all microservices, place microservice by microservice
            if not all_placed:
                for ms in microservices:
                    placed_ms = False
                    for candidate_node in sorted_candidate_nodes:
                        if can_fit_microservices(candidate_node, [ms]):
                            placement[app_name][ms['id']] = candidate_node
                            consume_resources(candidate_node, [ms])
                            placed_ms = True
                            break
                    if not placed_ms:
                        logger.warning(
                            f"GreedySolver: Could not place microservice '{ms['id']}' of app '{app_name}' due to resource constraints."
                        )

            # Check if all microservices for this app were placed
            if len(placement[app_name]) < len(microservices):
                logger.warning(
                    f"GreedySolver: Infeasible placement for application '{app_name}'. Not enough resources."
                )
                solve_time = round(time.time() - start_time, 4)
                return None, {
                    "objective": infeasible_penalty,
                    "total_latency": infeasible_penalty,
                    "solver_status": "Infeasible",
                    "solve_time_seconds": solve_time
                }

        # 4. Check topological connectivity and compute weighted mean latency
        solve_time = round(time.time() - start_time, 4)
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

        mean_latency = self.compute_weighted_mean_latency(
            placement, applications, users, active_nodes, all_pairs_shortest_paths
        )

        return placement, {
            "objective": mean_latency,
            "total_latency": mean_latency,
            "solver_status": "Optimal",
            "solve_time_seconds": solve_time
        }
