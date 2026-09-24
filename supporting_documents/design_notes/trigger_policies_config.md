# Políticas de Disparo del ILP (Trigger Policies)

Debido a que la optimización del emplazamiento mediante Programación Lineal Entera (ILP) es un problema NP-difícil, ejecutar el solver ante cada mínimo evento de la simulación resulta extremadamente costoso y poco realista.

El simulador implementa un sistema dinámico de **Políticas de Disparo (Trigger Policies)** que permite configurar (vía `config_random.yaml`) exactamente cuándo debe ejecutarse el optimizador y cuándo debe saltarse (reciclando el emplazamiento previo). 

Cuando el solver *no* se ejecuta y algún nodo del que dependía la aplicación ha sido desconectado, el motor lo registrará internamente y guardará en las métricas del JSON dicha aplicación como "Desconectada" (ideal para penalizaciones en datasets de ML).

A continuación se detalla cada modo disponible y cómo configurarlo en la raíz del archivo YAML dentro de la etiqueta `trigger_policy`.

---

## 1. Modos de Ejecución Total y Nula

### `solve_all` (Por defecto)
Ejecuta el optimizador ante **cada evento** de la simulación de forma ininterrumpida. Útil para entornos con pocos nodos o pruebas unitarias de depuración.
```yaml
trigger_policy:
  type: solve_all
```

### `solve_none`
Actúa como un *simulador seco*. Genera la infraestructura, posiciona inicialmente todo y lanza el motor de eventos temporales, pero nunca invoca al ILP de nuevo.
```yaml
trigger_policy:
  type: solve_none
```

---

## 2. Modos Estocásticos

### `solve_random_prob`
Decide en cada evento si debe ejecutar o no el ILP lanzando una moneda con una probabilidad fija (de 0.0 a 1.0).
```yaml
trigger_policy:
  type: solve_random_prob
  probability: 0.15  # 15% de probabilidad de ejecutar en cada iteración
```

---

## 3. Modos Basados en Rangos y Ventanas

### `solve_time_windows`
Solo ejecuta el ILP si el tiempo global (`global_time`) de la simulación cae dentro de alguna de las ventanas especificadas en la lista (intervalo cerrado).
```yaml
trigger_policy:
  type: solve_time_windows
  windows:
    - [100.0, 150.0]  # Desde el tiempo 100 al 150
    - [300.0, 350.0]  # Desde el tiempo 300 al 350
```

### `solve_event_index_ranges`
Similar al anterior, pero basado en el número absoluto de evento procesado (`event_counter`).
```yaml
trigger_policy:
  type: solve_event_index_ranges
  ranges:
    - [1, 50]         # Eventos del 1 al 50 (ambos inclusive)
    - [1000, 1500]    # Eventos del 1000 al 1500
```

---

## 4. Modos de Patrones y Batches

### `solve_custom_pattern`
Ejecuta el ILP siguiendo un bucle repetitivo de booleanos definido por el usuario. Cuando el arreglo termina, vuelve a comenzar.
```yaml
trigger_policy:
  type: solve_custom_pattern
  # True, False, False -> Ejecuta 1, salta 2.
  pattern: [True, False, False]
```

### `solve_every_n_events`
Acumula eventos y ejecuta el ILP de forma periódica estricta cada `N` eventos procesados. Útil para *batching* regular.
```yaml
trigger_policy:
  type: solve_every_n_events
  batch_size: 25  # Ejecuta el ILP en el evento 25, 50, 75...
```

### `solve_every_t_seconds`
Ejecuta el ILP solo si ha transcurrido un lapso de tiempo igual o superior a `interval_seconds` desde la última vez que se ejecutó. Esto garantiza que la carga de reconfiguración tenga un enfriamiento (*cooldown*).
```yaml
trigger_policy:
  type: solve_every_t_seconds
  interval_seconds: 5.0  # El ILP no se ejecutará más de 1 vez cada 5 segundos de simulación.
```

---

## 5. Modos Semánticos

### `solve_on_event_types`
El ILP se activa de forma reactiva y exclusiva ante ciertos "eventos críticos" o destructivos definidos en la lista. Ante movimientos de usuarios o fluctuaciones menores, se saltará la ejecución.
```yaml
trigger_policy:
  type: solve_on_event_types
  critical_events: 
    - "disable_node"
    - "disable_edge"
    - "update_app_footprint"
    - "update_app_network"
    - "update_app_topology"
```

### `combined` (Recomendado para ML)
Una política mixta inteligente. Ejecuta el ILP de inmediato si ocurre un evento crítico (como que un nodo se caiga). Sin embargo, para evitar que movimientos superficiales se ignoren para siempre, también ejecutará el ILP de forma periódica (fallback) si ha pasado demasiado tiempo sin hacerlo. El disparador semántico resetea el temporizador.
```yaml
trigger_policy:
  type: combined
  critical_events: 
    - "disable_node"
    - "disable_edge"
    - "geo_demand_shift"
  interval_seconds: 15.0  # Si no hay eventos críticos en 15s, ejecuta de todas formas.
```
