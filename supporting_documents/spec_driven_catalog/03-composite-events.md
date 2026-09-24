# Especificación de Eventos Compuestos (Composite Events)

## Motivación

El sistema actual de simulación lee los eventos a partir de la configuración en YAML y lanza las perturbaciones asociadas. No obstante, presenta dos limitaciones:
1. **Reutilización de Eventos:** Como los diccionarios de YAML (y de Python) no admiten claves duplicadas, no es posible definir dos "generadores" para el mismo evento base con diferentes distribuciones de frecuencia.
2. **Concurrencia Estricta:** No existe un mecanismo nativo para garantizar que múltiples eventos de distinta naturaleza (por ejemplo, `surge_popularity` y `update_app_network`) se ejecuten de manera simultánea en el mismo instante virtual (mismo `global_time`).

Los "Eventos Encapsuladores" o "Composite Events" resuelven ambas limitaciones, permitiendo definir agrupaciones de eventos bajo una nueva clave (actuando como nombre del macroevento) que define la frecuencia, y un listado `composed_of` que indica qué acciones base se disparan.

## Propuesta de Schema YAML (Ejemplo)

```yaml
app:
  actions:
    update_topology_fast:
      frequency:
        type: exponential
        scale: 60
      impact:
        composed_of:
          # Si no se indica type_object, asume el del evento padre (app en este caso)
          - action_type: update_app_topology
            impact_params:
              p_topo: {type: uniform, low: 0.4, high: 0.5}
              l_min: {type: integers, low: 2, high: 3}
              l_max_global: {type: integers, low: 6, high: 7}

    catastrophic_failure_and_surge:
      frequency:
        type: uniform
        low: 1000
        high: 2000
      impact:
        composed_of:
          - type_object: app  # Especificamos que esta accion es de App
            action_type: surge_popularity
            impact_params:
              transient_prob: {type: uniform, low: 0.9, high: 0.9}
              duration_dist: {type: weibull, a: 1.5, scale: 10.0}
          - type_object: graph_node # Podemos llamar a acciones de Infraestructura a la vez!
            action_type: disable_node
            impact_params:
              distribution_to_enable_node: {type: uniform, low: 0, high: 100}
```

## Cambios Requeridos en el Código

### 1. `src/simulation_runner.py`
En la función `_update_system_state` de `ServicePlacementSimulation`, se debe modificar el bloque que despacha y ejecuta la acción (etiqueta `# 3. Apply action`).

Se verificará si el impacto tiene la clave `composed_of`. Si la tiene, se itera, inyectando el contexto explícitamente en cada sub-acción. 

**Pseudocódigo de refactorización:**

```python
        # 3. Apply action
        raw_params = first_event.get("impact", {})
        impact_dict = raw_params.copy() if raw_params else {}
        
        composed_of = impact_dict.get("composed_of")
        
        if composed_of and isinstance(composed_of, list):
            messages = []
            for sub_action in composed_of:
                sub_action_name = sub_action.get("action_type")
                # Permitir cross-entity especificando el type_object
                sub_type = sub_action.get("type_object", first_event["type_object"])
                sub_target_object = set_map.get(sub_type)
                
                sub_params = sub_action.get("impact_params", {}).copy()
                
                # Inyección implícita de contexto
                sub_params["config"] = self.config
                sub_params["app_set"] = self.apps
                sub_params["user_set"] = self.users
                sub_params["infrastructure"] = self.infrastructure
                sub_params["sim_set"] = self.sim_set
                sub_params["event_set"] = self.events
                
                action_method = getattr(sub_target_object, sub_action_name)
                action_result = action_method(first_event.get("object_id"), **sub_params)
                
                # Manejo del mensaje (concatenación)
                if isinstance(action_result, str):
                    messages.append(f"[{sub_type}] {action_result}")
                elif isinstance(action_result, dict) and 'message' in action_result:
                    messages.append(f"[{sub_type}] {action_result['message']}")
                    
            first_event["message"] = " | ".join(messages)
            logger.info(f"Processing composite event: {first_event['message']}")
            
        else:
            # FLUJO ACTUAL para acciones simples
            params = impact_dict
            params["config"] = self.config
            # ... (inyección normal) ...
            
            action_method = getattr(target_object, first_event["action"])
            action_result = action_method(first_event["object_id"], **params)
            # ... (guardar message loguear normal) ...
```

### 2. `src/trigger_policies.py`
Actualmente las políticas evalúan si se debe recalcular el despliegue ILP basándose en el nombre de la acción (`event.get('action')`). Para que el trigger reaccione correctamente ante eventos compuestos, la lógica debe iterar sobre sus componentes.

En `TriggerPolicyManager.should_execute_ilp`, para las políticas `solve_on_event_types` y `combined`:

**Modificación propuesta:**
Se debe comprobar no sólo si `event.get('action')` (el nombre del macroevento) está en `critical_events`, sino también extraer `event.get('impact', {}).get('composed_of', [])` y ver si alguno de los `action_type` listados está en `critical_events`.

```python
    def _is_critical_event(self, event: Dict[str, Any], critical_events: list) -> bool:
        if event.get('action') in critical_events:
            return True
        
        composed_of = event.get('impact', {}).get('composed_of', [])
        for sub_action in composed_of:
            if sub_action.get('action_type') in critical_events:
                return True
                
        return False
```

Luego se usa `self._is_critical_event(event, critical_events)` en lugar de evaluar únicamente por `event.get('action')`.

### 3. `src/eventSet.py` (Opcional pero recomendable)
La función `update_event_time` se rige por el string de distribución en el config leyendo del diccionario base. Como un evento compuesto definirá una distribución global en su llave padre (`catastrophic_failure_and_surge > frequency`), no requiere cambios mayores allí, puesto que `eventSet.py` lee directamente la frecuencia asociada al nombre del evento configurado, sea base o compuesto.

## Selección de la Instancia Objetivo (Target Resolution)

Para flexibilizar sobre qué instancia(s) actúa una sub-acción, se introduce una nueva configuración en `impact_params` denominada `target_resolution`.

### Modos de Selección Individual
- **`random`**: Se escoge aleatoriamente una instancia del `type_object` indicado entre todas las disponibles.
- **`self`**: El evento recae estrictamente sobre la misma instancia que generó el evento padre (comportamiento por defecto para eventos simples).
- **`intelligent`**: Delega la resolución al propio Manejador (Handler). La función recibe el `object_id` en crudo, y sabe interpretar el contexto (Ej: recibe una "App" y ella misma deduce en qué nodo se ejecuta para apagarlo).
- **`id`**: Se especifica estáticamente un ID concreto (ej. `"Node_5"`) en el propio YAML.

### Modo de Selección Múltiple (`group`)
Si se elige `target_resolution: group`, el sistema afectará a más de un elemento. Se requerirá un sub-bloque de configuración `group_config` que defina `num_elements` (la cantidad total a afectar) y la estrategia (`strategy`) de selección:

> [!TIP]
> **Flexibilidad en `num_elements`**: Puede definirse como un valor absoluto (ej. `5` para cinco elementos exactos) o como un porcentaje en formato float (ej. `0.15` para afectar al 15% del total de elementos disponibles en el sistema).

- **`list`**: Proporciona un listado explícito de IDs en el YAML.
- **`random`**: Selecciona `num_elements` elegidos de forma totalmente aleatoria.
- **`self_random`**: Incluye obligatoriamente a la instancia origen (`self`) y rellena el resto con instancias aleatorias.
- **`self_proximity`**: Incluye a la instancia origen y rellena el resto con los elementos **más próximos** a ella.
- **`random_proximity`**: Escoge una instancia al azar, y rellena el resto con las **más próximas** a esa instancia elegida.

> [!TIP]
> **Sugerencias para definir "Proximidad" (Proximity):**
> *   **Infraestructura (`graph_node`):** Nodos con la menor distancia de saltos (shortest path) en el grafo, o menor latencia (`delay`) acumulada.
> *   **Usuarios (`user`):** Usuarios conectados al mismo nodo de acceso, o usuarios cercanos espacialmente usando sus coordenadas X, Y.
> *   **Aplicaciones (`app`):** Al no depender del despliegue físico (que es dinámico y lo decide el ILP), la "proximidad" entre aplicaciones debe ser **lógica o contextual**:
>     *   **Mismo Perfil (Profile):** Agrupar apps que sean del mismo tipo (ej. todas las apps de tipo `video` o `iot`).
>     *   **Afinidad Geográfica (Hotspot):** Si las apps tienen `local_app_ratio`, agrupar aquellas cuyo interés principal recae sobre el mismo cluster geográfico de usuarios.
>     *   **Popularidad Similar:** Aplicaciones adyacentes en el ranking Zipf de popularidad (ej. si cae la App top 1, arrastra a la top 2 y top 3).

### Ejemplo de Configuración YAML

```yaml
    catastrophic_failure_and_surge:
      frequency: ...
      impact:
        composed_of:
          # 1. Ejemplo Intelligent
          - type_object: graph_node
            action_type: disable_node
            impact_params:
              target_resolution:
                mode: intelligent # Disable_node se encarga de buscar el nodo de la App origen
              distribution_to_enable_node: {type: uniform, low: 0, high: 100}
              
          # 2. Ejemplo Group (Self + Proximity)
          - type_object: app
            action_type: surge_popularity
            impact_params:
              target_resolution:
                mode: group
                group_config:
                  strategy: self_proximity
                  num_elements: 0.1 # La App origen + 9% de apps colindantes (afecta al 10% del sistema)
              transient_prob: {type: uniform, low: 0.9, high: 0.9}
```

## Soporte en `global_spawner` y Entidades Específicas

Sí, la composición de eventos funcionará en **ambas partes**:
1. **Entidades específicas (`app`, `user`, `node`, etc.):** Para modelar escenarios donde una instancia provoca efectos en cadena (ej: una App que satura la red o tumba un nodo).
2. **Global Spawner (`global_spawner`):** Para lanzar eventos globales de caos (sin estar atados a una instancia concreta origen, es decir, con `object_id=None`) o para definir varias frecuencias de spawn para el mismo evento base.

**Casos de uso habilitados en el global_spawner:**
- Simulaciones de "Caos" general (ej. desactivar N apps aleatorias o nodos cada hora).
- Reutilizar eventos globales (ej. tener `new_user_fast` y `new_user_slow` con distintas distribuciones, ambas llamando a la acción real `new_user`).

### Decisión Técnica Pendiente: Refactor de `init_global_spawner`

Actualmente, el código de inicialización de los eventos globales (`init_global_spawner` en `eventSet.py`) usa un pequeño "hack" o suposición fuerte: deduce a qué entidad pertenece la acción leyendo su nombre y quitándole el prefijo `"new_"` (`type_object = action.removeprefix("new_")`).

**Cuando se retome esta especificación para implementarla, se evaluará este refactor:**
Exigir explícitamente el parámetro `type_object` en el YAML para *todos* los eventos del `global_spawner` (incluso los que no son compuestos, como `new_user`). Esto haría la implementación mucho más elegante, robusta y escalable, eliminando el chequeo en duro de strings.

Ejemplo propuesto para el YAML base futuro:
```yaml
global_spawner:
  actions:
    generar_usuarios_rapido:
      type_object: user
      action_type: new_user
      frequency:
        type: exponential
        scale: 30
```

---

## Decisiones Pendientes (Open Decisions) antes de Implementar

Antes de proceder a escribir el código, se requiere el Visto Bueno (Review) de las siguientes piezas de diseño:

1. **Refactor en `global_spawner`:** ¿Aprobamos eliminar el parsing del string `new_XXX` en favor de exigir siempre el parámetro `type_object` explícito para todas las acciones del `global_spawner`, tal como se ha propuesto en el ejemplo de arriba?
2. **Definición de Proximidad Lógica para Apps:** Como el despliegue físico de la app lo decide el ILP y no forma parte del contexto estático del evento, ¿cuál de estas métricas "lógicas" preferimos para definir que dos apps son "próximas" (`self_proximity`)?
   - A) Comparten el mismo `profile` (ej. ambas son de IoT).
   - B) Tienen una popularidad muy similar (rankings adyacentes).
   - C) Comparten el mismo foco geográfico de influencia (mismo hotspot de usuarios).
