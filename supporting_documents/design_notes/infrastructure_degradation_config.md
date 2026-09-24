# Configuración de Eventos de Degradación de Infraestructura (Brownouts)

Además de los eventos de destrucción total (como la caída de nodos y aristas), el simulador permite inyectar **eventos de degradación temporal** que simulan reducciones de capacidad, contención de recursos, o congestión de red (brownouts). Estos eventos son esenciales para estresar el optimizador ILP, forzándolo a realizar migraciones parciales (*shedding*) o a recalcular el enrutamiento antes de que los recursos lleguen al límite extremo.

Estos eventos se configuran bajo la sección `graph.actions` del archivo de configuración general (`config_random.yaml`).

## 1. Degradación Aleatoria de Nodos (`degrade_random_node`)

Reduce temporalmente un porcentaje de los recursos computacionales (CPU, RAM) de un nodo activo. El algoritmo ILP será informado de esta reducción, y si la suma de aplicaciones alojadas en el nodo supera el nuevo límite degradado, forzará la migración.

### Ejemplo de Configuración
```yaml
graph:
  actions:
    degrade_random_node:
      frequency:
        type: exponential
        scale: 150              # Tiempo promedio entre ocurrencias del evento (en segundos)
      impact:

          
        # 1. Magnitud de la Degradación (Distribución Beta recomendada)
        p_loss_dist:
          type: beta
          a: 2                  # Alpha. Valores bajos + Beta alto = sesgado hacia pérdidas pequeñas (10-30%)
          b: 5                  # Beta.
          
        # 2. Duración de la Degradación (Distribución del tiempo de recuperación)
        distribution_to_restore_node:
          type: exponential
          scale: 50             # El nodo recupera sus capacidades en ~50 segundos
```

> **Efecto Interno:** Si un nodo tiene una capacidad nominal de 16GB de RAM, y la distribución genera un `p_loss = 0.25`, la memoria disponible pasará a ser temporalmente $16 \times (1 - 0.25) = 12$ GB. 

---

## 2. Congestión Aleatoria de Red (`congest_random_edge`)

Provoca interferencias de radio, contención del sistema o congestión de tráfico a través de una arista (enlace) específica. Este evento tiene un efecto doble:
1. **Reduce** temporalmente el ancho de banda disponible (`bandwidth`).
2. **Incrementa** exponencialmente el retardo o latencia del enlace (`delay`).

### Ejemplo de Configuración
```yaml
graph:
  actions:
    congest_random_edge:
      frequency:
        type: exponential
        scale: 150              # Frecuencia de aparición de congestiones en la red
      impact:
          
        # 1. Magnitud de pérdida de Ancho de Banda (Distribución Beta)
        p_loss_dist:
          type: beta
          a: 2
          b: 5
            
        # 2. Incremento de Latencia (Distribución Lognormal recomendada)
        m_lat_dist:
          type: lognormal
          mean: 0.5             # Multiplicador promedio.
          sigma: 0.2            # Desviación.
          
        # 3. Duración de la Congestión (Tiempo hasta restaurar enlace)
        distribution_to_clear_edge:
          type: exponential
          scale: 50             # El enlace recupera valores nominales en ~50s
```

> **Efecto Interno:** Si un enlace con 100 Mbps y 5.0ms de latencia sufre un evento con `p_loss = 0.5` y `m_lat = 2.0`, el enlace se degradará pasando a ofrecer 50 Mbps con una latencia de 10.0ms hasta que pase el evento de recuperación.
