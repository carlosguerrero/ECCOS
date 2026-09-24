# Especificaciones Técnicas para Generación del Computing Continuum

Este documento define las directrices y modelos matemáticos que el simulador debe utilizar para la generación del escenario inicial. El objetivo es garantizar que la topología, la distribución de usuarios y la popularidad de las aplicaciones reflejen distribuciones realistas aceptadas en la literatura científica (artículos JCR).

Se recomienda el uso de librerías como `NetworkX` (para grafos) y `NumPy` / `SciPy` (para distribuciones probabilísticas y cálculos espaciales).

## 1. Generación de la Infraestructura (Modelos Topológicos)

Para dotar al simulador de flexibilidad y permitir estudios comparativos, se deben implementar varios generadores de topología basados en los estándares del estado del arte. La red no debe ser un grafo aleatorio simple (como Erdős-Rényi).

Se proponen los siguientes modelos de generación:

### 1.1 Modelos de Grafos Libres de Escala (Scale-Free Networks)

* **Concepto:** Basado en la teoría de redes complejas, donde unos pocos nodos (hubs) tienen un grado de conexión muy alto, y la mayoría tiene pocas conexiones (crecimiento preferencial).
* **Aplicación en el Continuum:** Ideal para modelar redes troncales (Backbone), el núcleo de Internet (Core) y las interconexiones en la capa Fog.
* **Implementación `NetworkX`:** Modelo de Barabási-Albert (`nx.barabasi_albert_graph`).

### 1.2 Modelos Geométricos y Espaciales

* **Concepto:** Nodos distribuidos en un plano euclídeo. La probabilidad de conexión depende directamente de la distancia física entre ellos.
* **Aplicación en el Continuum:** Esencial para la capa Edge, simulando el alcance de antenas 5G, puntos de acceso WiFi o dispositivos IoT y las restricciones de latencia basadas en la distancia física real.
* **Implementación `NetworkX`:**
    * Grafo Geométrico Aleatorio (`nx.random_geometric_graph`).
    * Modelo de Waxman (`nx.waxman_graph`), que introduce un decaimiento exponencial de la probabilidad de enlace basado en la distancia.

### 1.3 Topologías de Árbol y Fat-Tree (Jerárquicas Estrictas)

* **Concepto:** Estructuras en forma de árbol, diseñadas para evitar cuellos de botella en la raíz proporcionando múltiples caminos paralelos (Fat-Tree).
* **Aplicación en el Continuum:** Estándar de facto para simular la topología interna de Centros de Datos (Cloud Data Centers) y clústeres de alto rendimiento, así como algunas redes de acceso jerárquicas rígidas.
* **Implementación:** Generación basada en el parámetro $k$ (número de puertos por switch) para topologías Fat-Tree clásicas (Core, Aggregation, Edge switches).

### 1.4 LA RECOMENDACIÓN: Modelo Híbrido Multicapa (Multi-tier)

Para la máxima validez científica en el *Computing Continuum*, se debe usar una combinación jerárquica de los modelos anteriores estructurada en tres capas:

* **Capa 1: Cloud (Core):**
    * Malla completa (Full Mesh) con muy pocos nodos, configurable sobre el total de nodos del sistema, a traves de un porcentaje ($N_{cloud} \approx 1-2 \%$).
    * Recursos "infinitos" y latencia alta hacia abajo.
* **Capa 2: Fog (Regional / Agregación):**
    * Modelo Libre de Escala (Barabási-Albert) con cantidad media de nodos, configurable sobre el total de nodos del sistema a través de un porcentaje ($N_{fog} \approx 10-20 \%$).
    * Actúan como pasarelas hacia el Cloud.
* **Capa 3: Far-Edge (Acceso / Dispositivos IoT y 5G):**
    * Modelo Espacial (Grafo Geométrico) con gran cantidad de nodos, el total de nodos menos los asignados a cloud y fog.
    * Conectividad interna por radio de cobertura $R$ y conectividad ascendente al nodo Fog más cercano.

## 2. Configuración YAML del Entorno

La configuración de la infraestructura y la asignación de recursos a los nodos se define a través del archivo YAML (`config_random.yaml`).

### Ejemplo: Definición de Capas y Excepciones para Cloud

Independientemente del modelo de generación topológica, es imperativo establecer **excepciones para los nodos Cloud**, dotándolos de recursos virtualmente infinitos para poder dar soporte a aplicaciones pesadas (ej. Service Function Chaining), saltándose los límites máximos que aplican a los nodos Edge y Fog.

```yaml
    node:
      # Definición explícita de capas basada en la centralidad
      layer:
        mode: centrality_based_layer
        thresholds:
          cloud_min: 0.1
          fog_min: 0.02
        
      # Asignación de RAM a los nodos
      ram:
        mode: centrality_based
        centrality_type: direct_proportional
        distribution:      # Distribución para nodos normales (Fog/Edge)
          type: pareto
          a: 1.16
          cloud:           # Excepción que aplica SOLAMENTE a nodos Cloud
            type: uniform
            low: 100000.0  # Recursos enormes simulando un Centro de Datos
            high: 100000.0
        min: 8.0           # Límites para nodos normales
        max: 16.0
```

En la configuración anterior:
1. El sistema evalúa primero la clave `layer`, asignando el tipo de nodo (Cloud, Fog o Edge) matemáticamente.
2. Posteriormente, al asignar memoria `ram`, si el nodo fue clasificado como Cloud, el simulador **bypassesa** el modo `centrality_based` y le otorga directamente los recursos dictados bajo la directiva `cloud` dentro de `distribution` (eximiéndolo de los topes `max: 16.0`).
