# Configuración de Atributos de Infraestructura

Este documento describe la nueva estructura del archivo de configuración YAML (`config_random.yaml` o similares) que permite definir atributos dinámicos y personalizables para los nodos y los enlaces (edges) de la infraestructura en el entorno del _Computing Continuum_.

## Estructura General

Toda la configuración de atributos de la infraestructura (grafo) se encuentra dentro del bloque `graph`:

```yaml
graph:
  node:
      # Definición de atributos de los nodos (ej. ram, cpu, storage)
    edge:
      # Definición de atributos de los enlaces (ej. delay, bandwidth)
```

Cada atributo declarado como clave bajo `attributes` puede configurarse usando distintos modos de generación:
1. `homogenic`: La misma distribución para todos los elementos.
2. `centrality_based`: Los valores generados se ponderan según la centralidad del elemento.
3. `layered`: Distribuciones distintas dependiendo de la capa (cloud, fog, edge).

A continuación se detalla el funcionamiento de cada modo.

---

## 1. Modo `homogenic`

En este modo, se asume que todos los elementos (nodos o enlaces) obtienen sus valores de la misma distribución estadística subyacente. Los valores se asignan directamente y de manera generalizada.

### Parámetros
- `mode`: Debe ser `homogenic`.
- `distribution`: (Requerido) El diccionario que especifica la distribución estadística (e.g., `type: uniform`, `type: pareto`).
- `min` / `max`: (Opcional) Valores límite para truncar/acotar el resultado final.

### Ejemplo
```yaml
    edge:
      delay:
        mode: homogenic
        frequency:
          type: uniform
          low: 0.1
          high: 5.0
        min: 0.5
        max: 4.5
```

---

## 2. Modo `centrality_based`

Este modo es particularmente útil para simular el Computing Continuum, donde los recursos o las características cambian a medida que nos acercamos al Cloud (mayor centralidad) o nos alejamos hacia el Edge (menor centralidad). 

Primero se genera un valor base a partir de una distribución, y luego este valor es ponderado en función del cálculo de **Betweenness Centrality** de la topología de la red.

### Parámetros
- `mode`: Debe ser `centrality_based`.
- `centrality_type`: Determina cómo afecta la centralidad.
  - `direct_proportional`: A mayor centralidad, mayor valor del atributo. (Ponderación directa).
  - `inverted_proportional`: A mayor centralidad, menor valor del atributo. (Ponderación inversa, ideal por ejemplo para latencias si asumimos núcleos ultrarrápidos y bordes lentos).
- `distribution`: (Requerido) Distribución base de la que parten los valores.
- `min` / `max`: (Opcional) Limitan el valor resultante tras la ponderación.

### Ejemplo
```yaml
    node:
      ram:
        mode: centrality_based
        centrality_type: direct_proportional
        frequency:
          type: pareto
          a: 1.16
        min: 8.0
        max: 16.0
```
> En este ejemplo, los nodos que actúen como "cuellos de botella" o puentes centrales en la topología (simulando los data centers o nodos Cloud) obtendrán mayores puntuaciones en RAM gracias al factor multiplicador de la centralidad.

---

## 3. Modo `layered`

*(En fase de preparación)*
Este modo está diseñado para soportar jerarquías explícitas, asumiendo que los nodos o enlaces han sido categorizados en grupos: `cloud`, `fog`, o `edge`. 

Si un nodo está categorizado en la capa "cloud", se extraerá el valor exclusivamente de la distribución asignada a "cloud", en lugar de seguir una regla generalizada. Si un nodo carece de categorización en este momento, el simulador asignará una capa por defecto para evitar fallos.

### Parámetros
- `mode`: Debe ser `layered`.
- `distributions`: Un diccionario que mapea el nombre de la capa (e.g., `cloud`, `fog`, `edge`) con su respectiva distribución estadística.

### Ejemplo
```yaml
    node:
      storage:
        mode: layered
        distributions:
          cloud:
            type: uniform
            low: 1000
            high: 5000
          fog:
            type: uniform
            low: 100
            high: 500
          edge:
            type: uniform
            low: 10
            high: 50
```
