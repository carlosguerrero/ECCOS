# Generación de la Topología y Atributos de Red

El simulador permite configurar topologías de red que representen fielmente entornos de _Computing Continuum_. Toda la configuración de generación de grafo recae en el archivo YAML bajo las secciones `setup` y `model_params`.

Además de generar la estructura de enlaces (aristas) entre nodos, el proceso clasifica a cada nodo generado en una de tres **capas (layers)**: `cloud`, `fog` o `edge`. Esta clasificación es crítica, ya que el sistema posterior de atributos (RAM, disco, latencia...) puede utilizar el modo `layered` para dotar a los nodos de características diferentes en función de su capa.

---

## Modelos de Topología Soportados (`graph_model`)

Existen cuatro modelos principales. El número total de nodos que tendrá la infraestructura viene dado obligatoriamente por el campo `num_nodes` dentro de `setup`.

### 1. Scale-Free (Libre de Escala)
Modela redes troncales y núcleos de Internet donde unos pocos nodos actúan como grandísimos concentradores (hubs). Se genera utilizando el modelo de **Barabási-Albert**.

**Parámetros en `model_params`:**
- `m`: El número de enlaces iniciales a añadir para los nuevos nodos (generalmente `2`).

**Asignación de Capas (`layer`):**
En grafos de este tipo, la capa se asigna midiendo la centralidad (Betweenness Centrality) de los nodos una vez generados. Los nodos más céntricos reciben la etiqueta `cloud`. Para configurar esto, se utilizan `layer_centrality_thresholds` como atributos en los que se fija un valor mínimo (`min`) para clasificar como cloud o fog.

**Ejemplo YAML:**
```yaml
setup:
  mode: random
  num_nodes: 50
  graph_model: scale_free
model_params:
  m: 2
  layer_centrality_thresholds:
    cloud_min: 0.1  # Nodos con centralidad >= 0.1 -> cloud
    fog_min: 0.02   # Nodos con centralidad < 0.1 pero >= 0.02 -> fog. Resto -> edge.
```

---

### 2. Spatial (Geométrico)
Los nodos se distribuyen de manera aleatoria en un espacio plano 2D. Se interconectan si su distancia se encuentra bajo un radio definido. Muy apto para dispositivos Far-Edge o redes inalámbricas.

**Parámetros en `model_params`:**
- `radius`: El radio máximo de conexión (valor típico recomendado entre `0.1` y `0.3`).

**Asignación de Capas (`layer`):**
Al igual que en `scale_free`, la clasificación se rige midiendo la centralidad física resultante y comparándola con `layer_centrality_thresholds`.

**Ejemplo YAML:**
```yaml
setup:
  mode: random
  num_nodes: 100
  graph_model: spatial
model_params:
  radius: 0.15
  layer_centrality_thresholds:
    cloud_min: 0.2
    fog_min: 0.05
```

---

### 3. Fat-Tree / Tree
Grafos estrictamente jerárquicos basados en árboles perfectamente balanceados. Ideal para Data Centers o mallas de infraestructura altamente jerarquizada.

**Parámetros en `model_params`:**
- `branching_r`: El número de "ramas" o hijos de cada nodo.
- `branching_h`: La altura total del árbol.

**Asignación de Capas (`layer`):**
La clasificación depende directamente de la **profundidad (nivel)** del nodo en el árbol, donde el nodo raíz está en la profundidad 0. En este caso se utiliza el mapeo `layer_depth_thresholds` para definir la profundidad máxima en la que el nodo sigue clasificándose como cloud o fog.

**Ejemplo YAML:**
```yaml
setup:
  mode: random
  num_nodes: 50
  graph_model: fat_tree
model_params:
  branching_r: 3
  branching_h: 4
  layer_depth_thresholds:
    cloud_max: 0   # Profundidad 0 (Root) es Cloud
    fog_max: 2     # Profundidades 1 y 2 son Fog. Resto es Edge.
```

---

### 4. Multi-Tier (El modelo Híbrido Recomendado)
Este modelo genera un escenario completo del Continuum fusionando 3 subgrafos diferentes:
- Un **Cloud** representado por una Malla Completa.
- Una zona **Fog** generada mediante modelo Libre de Escala.
- Un ecosistema **Edge** mediante un Grafo Espacial.

Finalmente los "cose" (stitch) uniendo los nodos Edge a sus Fog más cercanos, y los Fog a su nodo Cloud más cercano (calculando distancias euclídeas mediante asignación aleatoria en el plano 2D de todos los elementos centrales).

**Parámetros en `model_params`:**
- Bloque `cloud`:
  - `percentage`: Qué porcentaje del `num_nodes` total corresponderá a los centros Cloud.
- Bloque `fog`:
  - `percentage`: Porcentaje del total de nodos que actúan como pasarelas Fog.
  - `m`: El factor de conexiones de Barabási-Albert para la red interna Fog.
- Bloque `edge`:
  - `radius`: Radio de conexión interna para la capa inferior Edge.

**Asignación de Capas (`layer`):**
En este modo, las capas son explícitas e intrínsecas a la propia generación. El simulador etiqueta automáticamente al grupo Cloud de la malla como `cloud`, al subgrafo Scale-Free como `fog`, y al subgrafo Geométrico como `edge`. No requieren la inserción de thresholds manuales.

**Ejemplo YAML:**
```yaml
setup:
  mode: random
  num_nodes: 200
  graph_model: multi_tier
model_params:
  cloud:
    percentage: 2     # Aproximadamente 4 nodos Cloud
  fog:
    percentage: 18    # Aproximadamente 36 nodos Fog
    m: 2              # Factor de conexión Fog
  edge:               # El 80% restante (160 nodos Edge)
    radius: 0.1       # Cobertura de red IoT/5G
```

---

## Consideración sobre Atributos Adicionales

Cualquiera de estos modelos asigna por defecto a cada nodo de la infraestructura un string llamado `layer` (cuyos valores son `'cloud'`, `'fog'`, `'edge'`). Cuando configures los atributos adicionales en `graph.node.attributes` bajo la opción `mode: layered`, el optimizador revisará el campo interno `layer` y utilizará la distribución apropiada definida para dicho nivel.
