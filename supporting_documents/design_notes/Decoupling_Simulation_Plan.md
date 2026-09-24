# Desacoplamiento de Aleatoriedad y Simulación Estática

El objetivo de este plan es separar completamente la generación aleatoria de eventos y estados iniciales, de la ejecución de la simulación pesada (el motor ILP/Heurístico). Para ello se construirán dos fases separadas comunicadas mediante JSON.

## Consideraciones Arquitectónicas (Open Questions previas)

Para generar la lista completa de eventos (`events.json`) en el script `generate_event_list.py`, el script tendrá que simular internamente el paso del tiempo y aplicar "falsamente" los eventos en memoria (por ejemplo, crear un usuario nuevo o borrar uno existente). Esto es necesario porque si el evento en el tic 50 es "modificar popularidad de App_3", la App_3 debe existir en ese momento. 
Por tanto, `generate_event_list.py` debe aplicar las acciones en memoria para mantener consistencia durante la generación de la lista de eventos, pero sin ejecutar NUNCA el algoritmo de *Service Placement* (que es la parte computacionalmente pesada).

## Proposed Changes

### 1. Serialización y Deserialización de Clases [src/appSet.py, src/userSet.py, src/infrastructure.py, src/eventSet.py]
Las clases que contienen el estado en memoria actualmente no tienen mecanismos nativos para guardarse a JSON y reconstruirse de nuevo.
- Añadir métodos `to_dict()` y `from_dict()` a `UserSet` y `AppSet`.
- Añadir métodos `to_dict()` y `from_dict()` a `InfrastructureSet` (utilizando `nx.node_link_data` y `nx.node_link_graph` de la librería `networkx` para guardar y cargar el grafo base).
- Añadir un cargador estático en `EventSet` para instanciar la cronología de eventos de golpe sin usar `numpy.random`.

---

### 2. Script de Generación de Estado Inicial [NEW]
**`generate_initial_state.py`**
Este script leerá el `config_random.yaml` (o cualquier otro archivo config), ejecutará la creación de las aplicaciones, infraestructura y usuarios base resolviendo la estadística por única vez, y luego llamará a los nuevos métodos `to_dict()` para guardar un archivo resultante: `initial_state.json`.

---

### 3. Script de Generación de la Línea de Tiempo de Eventos [NEW]
**`generate_event_list.py`**
- Leerá el `initial_state.json` recién generado.
- Inicializará el reloj interno de la simulación.
- Ejecutará un bucle calculando qué evento toca a continuación, usando los motores estadísticos de Numpy.
- Guardará **todos los parámetros ya calculados estáticamente**. Si un evento es `move_user`, el script determinará a qué nodo exacto se mueve en ese momento, y guardará `{target: user_4, action: move_user, params: {node: 8}}`.
- Aplicará el estado en memoria (para saber qué nodos existen, etc.) pero omitiendo ejecutar el solver ILP.
- Volcará la lista cronológica total a un archivo definitivo `events.json`.

---

### 4. Nuevo Motor de Simulación [NEW / MODIFY]
**`run_simulation.py`** (Reemplazo del bucle de `main.py`)
- Este será el nuevo script principal que reemplazará el comportamiento interno actual del simulador.
- **Lectura:** Carga estáticamente `initial_state.json` (recuperando el grafo y todos los objetos sin invocar a RNGs ni distribuciones aleatorias).
- **Lectura:** Carga secuencialmente `events.json`.
- **Ejecución Determinista:** Por cada iteración/evento de la lista:
  1. Aplica la acción precalculada sobre el objeto correspondiente (ej. `user.move(node_8)`).
  2. Ejecuta `solve_application_placement` (el solver pesado).
  3. Registra el estado (logs/CSVs).

**Modificación de `src/simulation_runner.py`**
Adaptar el `ServicePlacementSimulation` actual para que reciba directamente el estado base y la cola estática de eventos, saltándose todas las generaciones iniciales y recálculos aleatorios que hace ahora en `def run(self)`.
