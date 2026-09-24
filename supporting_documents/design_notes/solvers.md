# Configuración y Extensión de Solvers (Estrategias de Emplazamiento)

El simulador utiliza un motor de orquestación diseñado mediante un patrón arquitectónico de **Estrategia (Strategy)** combinado con una **Fábrica (Factory)**. Esto significa que el orquestador (`simulation_runner.py`) es agnóstico al algoritmo o librería matemática empleada para emplazar los servicios; simplemente delega en la fábrica la instanciación del solver configurado en el YAML.

## 1. Configuración desde YAML

En el archivo de configuración `config_random.yaml` (o cualquier otro YAML usado por el simulador), debes definir el bloque `ilp_solver` bajo `setup`:

```yaml
setup:
  ilp_solver:
    timeLimit: 60
    gapRel: 0.05
    objective: multi-objective # Llave que lee el Factory
    weights:
      latency: 1.0
      migration: 100.0
      server_usage: 50.0
```

El valor de `objective` determina qué solver exacto será instanciado.

## 2. Solvers Disponibles por Defecto

En el directorio `src/solvers/` encontrarás las estrategias actualmente implementadas:
- **`single-objective`**: Emplea `ILPSingleObjectiveSolver` (solo evalúa latencia de red, ignorando migraciones y servidores encendidos).
- **`multi-objective`**: Emplea `ILPMultiObjectiveSolver` (aplica los pesos definidos en `weights` para latencia, migración y uso de servidores).

## 3. Cómo Extender o Crear un Nuevo Solver

Gracias al patrón de diseño, no necesitas modificar el orquestador ni ninguna lógica core del simulador para añadir nuevas metaheurísticas o modelos matemáticos.

**Paso 1: Crear la clase del solver**
Crea un nuevo archivo en `src/solvers/` (ej. `mi_algoritmo.py`). Tu clase debe heredar obligatoriamente de `BaseSolver` e implementar el método `solve()`:

```python
from typing import Any, Dict, Optional, Tuple
from .base_solver import BaseSolver

class MiAlgoritmoSolver(BaseSolver):
    def solve(self, graph_dict: Any, application_set: Any, user_set: Any, 
              config: Dict[str, Any], previous_placement: Optional[Dict[str, Any]] = None) -> Tuple[Optional[Dict[str, Any]], float]:
        
        # 1. Tu lógica aquí (Metaheurística, Genético, ILP alternativo...)
        
        # 2. Devolver el emplazamiento resultante
        # Formato: {'App_Name': {'ms_id_1': node_id_X, ...}}
        placement = {'App_1': {'1_ms_0': 42}}
        cost = 150.5
        
        return placement, cost
```

**Paso 2: Registrar el solver en la Factory**
Abre el archivo `src/solvers/solver_factory.py` e importa tu nueva clase. A continuación, añádela al diccionario estático `SOLVER_REGISTRY`:

```python
# Importar tu nuevo solver
from .mi_algoritmo import MiAlgoritmoSolver

class SolverFactory:
    SOLVER_REGISTRY = {
        "single-objective": ILPSingleObjectiveSolver,
        "multi-objective": ILPMultiObjectiveSolver,
        "mi-nuevo-modo": MiAlgoritmoSolver  # <--- Registro añadido
    }
```

**Paso 3: Actívalo en tu YAML**
Edita el YAML para utilizar la llave asignada en el diccionario:
```yaml
setup:
  ilp_solver:
    objective: mi-nuevo-modo
```

El orquestador inyectará automáticamente tu clase en el motor de simulación. ¡Es así de sencillo!
