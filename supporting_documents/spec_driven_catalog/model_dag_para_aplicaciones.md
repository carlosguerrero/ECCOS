# Especificación Técnica: Implementación de Topología "Scale-Free Dirigida" (DAG) en el simulador

## Contexto y Motivación
Actualmente, el simulador genera topologías de red utilizando un modelo puramente lineal (Service Function Chaining - SFC). Aunque este modelo es útil para representar ciertos flujos de red estáticos o secuenciales, no refleja de manera realista la arquitectura moderna de microservicios de grandes aplicaciones (como Netflix o Uber). 

Estas arquitecturas distribuidas forman un **Grafo Acíclico Dirigido (DAG)** caracterizado por la presencia de nodos altamente conectados o "Hubs" (ej. API Gateways, Servicios de Autenticación, Bases de Datos centralizadas) y muchos nodos periféricos de lógica de negocio o microservicios de dominio.

El objetivo de esta tarea es implementar un nuevo motor de generación de grafos basado en el **Modelo de Libre Escala Dirigido (Directed Scale-Free)**, asegurando que la red generada mantenga propiedades de conexión preferencial (*preferential attachment*) sin introducir dependencias circulares (ciclos), garantizando la naturaleza estricta de un DAG.

---

## 1. Cambios en la Configuración (YAML)
El motor de topología del simulador debe ser parametrizable dinámicamente. La actual sección app.sfc debe de renombrarse a app.services. Dentro de esta sección se introducirá el el atributo `topology_model` que valdrá `sfc` para el modelo lineal nuevo, o `directed_scale_free` para el nuevo modelo. En este último caso se añadirán otros parámetros específicos para controlar el modelo de libre escala. El resto de atributos que cuelgan de services se mantienen (anteriromente sección llamada `sfc`)

```yaml
app:
  services:
    # Valores permitidos: "sfc"  o "directed_scale_free"
    topology_model: "directed_scale_free" 
    
    # Parámetros específicos para la generación del modelo Scale-Free
    scale_free_settings:
      initial_nodes: 2      # Nodos "core" iniciales con los que arranca el grafo (ej. Gateway, Auth)
      edges_per_node: 2     # Número de conexiones (aristas) que intenta crear cada nodo nuevo al unirse a la red
```

---

## 2. Especificación Algorítmica (Directed Scale-Free)
Cuando el parser del simulador detecte `topology_model: directed_scale_free`, invocará el nuevo submódulo generador que implementará la siguiente lógica matemática y de control:

### A. Inicialización
1. Se crea un conjunto inicial de nodos definidos por `initial_nodes` ($m_0$).
2. Estos nodos se conectan entre sí de forma básica para formar una red base inicial dirigida y acíclica.

### B. Crecimiento y Conexión Preferencial
1. Los nodos restantes necesarios para la simulación de la red se añaden secuencialmente (uno por uno).
2. Al añadir un nuevo nodo $i$, este debe crear un número de aristas orientado igual a `edges_per_node` ($m$, donde $m \le m_0$).
3. La probabilidad $P(j)$ de que el nuevo nodo se conecte a un nodo existente $j$ es directamente proporcional al grado actual $k_j$ de dicho nodo (suma de sus conexiones entrantes y salientes en el grafo actual).

La regla de probabilidad de conexión preferencial responde a la fórmula:

$$P(j) = \frac{k_j}{\sum_{x} k_x}$$

*Donde $k_j$ es el grado del nodo $j$, y el denominador representa la suma de los grados de todos los nodos presentes en el grafo en ese instante.*

### C. Restricción de Direccionalidad (Garantía de DAG)
Para evitar bucles infinitos de red o ciclos cerrados que violen el principio de un DAG, el algoritmo debe imponer una regla estricta de ordenamiento topológico durante el crecimiento:
* **Restricción de Orden Temporal:** Las aristas orientadas solo pueden originarse desde el nodo más nuevo hacia los nodos preexistentes (o viceversa, según se defina la dirección del tráfico aguas abajo). Al no permitir que un nodo antiguo apunte a un nodo más nuevo de forma arbitraria, se impide matemáticamente cualquier arista hacia atrás (*back-edge*) que genere un ciclo.
* **Estructuración por Capas:** Alternativamente, se puede asignar a los nodos un índice de jerarquía (`layer_id`) donde los Hubs iniciales ocupan la Capa 0 y los nodos subsiguientes se asientan en capas inferiores, forzando que las conexiones fluyan estrictamente en la dirección `Capa N -> Capa N+1`.

---

## 3. Criterios de Aceptación y Validación

### Validación de Configuración
- [ ] El parser de YAML debe validar correctamente `topology_model`. Si el campo no existe, debe aplicar por defecto `"sfc"` para mantener retrocompatibilidad.
- [ ] Si se introduce un valor de texto no soportado, debe lanzar una excepción de configuración clara: `InvalidTopologyModelError`.
- [ ] Los parámetros dentro de `scale_free_settings` deben ser enteros positivos. `edges_per_node` debe ser obligatoriamente menor o igual que `initial_nodes`.

### Validación del Grafo Generado
- [ ] **Propiedad DAG:** El grafo generado bajo el modelo `directed_scale_free` debe pasar una validación de ordenación topológica (ej. algoritmo de Kahn o DFS para detección de ciclos). Debe certificar **cero ciclos**.
- [ ] **Estructura Libre de Escala:** El log de diagnóstico o los tests unitarios de la red deben verificar estadísticamente la presencia de ley de potencias. Un pequeño porcentaje de los nodos (los Hubs centrales) debe concentrar la gran mayoría de las conexiones.
- [ ] **Aislamiento de SFC:** Si se selecciona `topology_model: sfc`, el sistema debe ignorar completamente la sección `scale_free_settings` y aplicar el comportamiento lineal tradicional sin alteraciones.