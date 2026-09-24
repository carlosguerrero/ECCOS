from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

class BaseSolver(ABC):
    """
    Clase abstracta base para todos los algoritmos de optimización (Estrategias)
    en el problema de emplazamiento de servicios.
    """
    
    @abstractmethod
    def solve(self, graph_dict: Any, application_set: Any, user_set: Any, 
              config: Dict[str, Any], previous_placement: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """
        Calcula el emplazamiento óptimo de aplicaciones.
        
        Args:
            graph_dict: Objeto con la información de la infraestructura de red.
            application_set: Conjunto de aplicaciones instanciadas.
            user_set: Conjunto de usuarios instanciados.
            config: Configuración proveniente del archivo YAML.
            previous_placement: (Opcional) Diccionario con el estado anterior de emplazamiento.
                                Formato: {'App_X': {'X_ms_Y': node_id, ...}, ...}
        
        Returns:
            Tuple: 
                - Diccionario de emplazamiento resultante: {'App_X': {'X_ms_Y': node_id, ...}, ...}
                - Diccionario con todas las métricas evaluadas por el solver (e.g. {'total_latency': ..., 'objective': ...}).
        """
        pass

    @staticmethod
    def check_topological_connectivity(
        placement: Dict[str, Dict[str, Any]],
        applications: Dict[str, Any],
        users: Dict[str, Any],
        active_nodes: Any,
        all_pairs_shortest_paths: Dict[Any, Dict[Any, float]],
    ) -> bool:
        """
        Verifies if all active user requests and microservice chain links have
        valid physical network paths under the current placement.
        """
        active_nodes_set = set(active_nodes)

        # 1. Verify path from each user's home node to their app's ingress microservice
        for user_id, user_data in users.items():
            if float(user_data.get('requestRatio', 0.0)) <= 0:
                continue
            home_node = user_data.get('connectedTo')
            if home_node not in active_nodes_set:
                return False

            req_app = user_data.get('requestedApp')
            if req_app not in applications:
                continue
            app_data = applications[req_app]
            app_name = app_data.get('name', req_app)
            microservices = app_data.get('microservices', [])
            if not microservices:
                continue

            first_ms_id = microservices[0]['id']
            first_node = placement.get(app_name, {}).get(first_ms_id)
            if first_node is None or first_node not in active_nodes_set:
                return False

            if first_node != home_node:
                paths_from_home = all_pairs_shortest_paths.get(home_node, {})
                if first_node not in paths_from_home:
                    return False

        # 2. Verify path between connected microservices in the SFC chains
        for user_id, user_data in users.items():
            if float(user_data.get('requestRatio', 0.0)) <= 0:
                continue
            req_app = user_data.get('requestedApp')
            if req_app not in applications:
                continue
            app_data = applications[req_app]
            app_name = app_data.get('name', req_app)
            edges = app_data.get('edges', [])
            for edge in edges:
                n1 = placement.get(app_name, {}).get(edge['source'])
                n2 = placement.get(app_name, {}).get(edge['target'])
                if n1 is None or n2 is None:
                    return False
                if n1 not in active_nodes_set or n2 not in active_nodes_set:
                    return False
                if n1 != n2:
                    paths_from_n1 = all_pairs_shortest_paths.get(n1, {})
                    if n2 not in paths_from_n1:
                        return False

        return True

    @staticmethod
    def compute_weighted_mean_latency(
        placement: Dict[str, Dict[str, Any]],
        applications: Dict[str, Any],
        users: Dict[str, Any],
        active_nodes: Any,
        all_pairs_shortest_paths: Dict[Any, Dict[Any, float]],
    ) -> float:
        """
        Calcula la latencia media ponderada de todas las peticiones (en milisegundos):
        Media Ponderada = Sum(requestRatio_u * Latency_u) / Sum(requestRatio_u)
        
        donde Latency_u es la latencia de acceso (usuario -> primer microservicio)
        más la suma de latencias entre microservicios de la cadena SFC.
        """
        total_weighted_latency = 0.0
        total_weight = 0.0

        def get_delay(src: Any, tgt: Any) -> float:
            if src == tgt:
                return 0.0
            return float(all_pairs_shortest_paths.get(src, {}).get(tgt, 0.0))

        for user_id, user_data in users.items():
            w_u = float(user_data.get('requestRatio', 0.0))
            if w_u <= 0:
                continue
            total_weight += w_u

            req_app = user_data.get('requestedApp')
            home_node = user_data.get('connectedTo')
            if req_app not in applications:
                continue
            app_data = applications[req_app]
            app_name = app_data.get('name', req_app)
            microservices = app_data.get('microservices', [])
            if not microservices:
                continue

            first_ms_id = microservices[0]['id']
            first_ms_node = placement.get(app_name, {}).get(first_ms_id)
            user_latency = get_delay(home_node, first_ms_node) if first_ms_node is not None else 0.0

            for edge in app_data.get('edges', []):
                n1 = placement.get(app_name, {}).get(edge['source'])
                n2 = placement.get(app_name, {}).get(edge['target'])
                if n1 is not None and n2 is not None:
                    user_latency += get_delay(n1, n2)

            total_weighted_latency += w_u * user_latency

        if total_weight > 0:
            return round(total_weighted_latency / total_weight, 4)
        return 0.0
