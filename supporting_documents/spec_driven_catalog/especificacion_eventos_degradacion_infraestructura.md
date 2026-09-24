# Especificación de Eventos de Degradación de Infraestructura (Brownouts)

En entornos de *Computing Continuum* (especialmente en la capa Edge y redes inalámbricas), los componentes físicos rara vez fallan de manera binaria (100% operativos o 0% caídos). Lo habitual son episodios de degradación temporal (*brownouts*), como interferencias de radio, contención de recursos en el sistema operativo subyacente, o enrutamientos subóptimos por tráfico de terceros.

Este documento define la inclusión de eventos de degradación temporal, los cuales inyectan "ruido" en las capacidades de la infraestructura y fuerzan al algoritmo ILP a reevaluar umbrales de tolerancia.

---

## 1. Tipología de Eventos Pareados

Al igual que los eventos de popularidad transitoria, las degradaciones se modelan inyectando **dos eventos pareados** en la cola de simulación: el inicio de la degradación y su futura y garantizada recuperación.

### 1.1 Degradación de Capacidad de Cómputo (Node Brownout)
Afecta a los recursos internos de un nodo (CPU y/o RAM disponible).
* **Evento de Inicio (`degrade_node`):** En el tiempo $T$, el nodo seleccionado reduce su capacidad máxima disponible. Si el nodo albergaba aplicaciones cuyo consumo sumado supera la nueva capacidad degradada, el nodo entra en estado de sobrecarga (*Overload*), lo que debería disparar inmediatamente el ILP para realizar una migración de evacuación parcial (Shedding).
* **Evento de Recuperación (`restore_node`):** En el tiempo $T + \Delta t$, el nodo recupera sus capacidades nominales originales.

### 1.2 Congestión de Red (Edge/Link Congestion)
Afecta a los enlaces de comunicación (Aristas del grafo) entre nodos.
* **Evento de Inicio (`congest_edge`):** En el tiempo $T$, el enlace sufre una merma en su Ancho de Banda ($BW$) disponible y un incremento en su Latencia ($Lat$). Si esto provoca que alguna cadena SFC incumpla su restricción de latencia máxima ($L_{max}$), el ILP deberá ser invocado.
* **Evento de Recuperación (`clear_edge`):** En el tiempo $T + \Delta t$, el enlace limpia su canal y restaura el ancho de banda y latencia originales.

---

## 2. Modelado Estadístico de la Degradación

Para garantizar el realismo JCR del dataset, los parámetros de estos eventos no serán constantes, sino muestreados de distribuciones estadísticas contrastadas en ingeniería de fiabilidad de redes.

### 2.1 Magnitud de la Degradación de Recursos (Distribución Beta)
Para calcular cuánta CPU, RAM o Ancho de Banda se pierde durante el evento, se utiliza un factor de pérdida $p_{loss} \in (0, 1)$.

* **Distribución:** **Distribución Beta** $Beta(\alpha, \beta)$.
* **Implementación:** $Capacidad_{degradada} = Capacidad_{nominal} \times (1 - p_{loss})$.
* **Justificación:** La distribución Beta está naturalmente acotada entre 0 y 1. Configurando parámetros (por ejemplo, $\alpha=2, \beta=5$), se logra una distribución asimétrica donde las degradaciones leves (pérdida del 10-30%) son muy comunes, pero las degradaciones casi totales (pérdida del 90%) son posibles pero estadísticamente raras.

### 2.2 Magnitud del Incremento de Latencia (Distribución Lognormal)
La latencia, a diferencia de la capacidad, no se reduce, sino que se multiplica.
* **Distribución:** **Distribución Lognormal** o factor multiplicativo basado en distribución Normal truncada positiva.
* **Implementación:** $Latencia_{degradada} = Latencia_{nominal} \times M_{lat}$, donde $M_{lat} > 1.0$ (ej. $M_{lat} \sim Lognormal(\mu, \sigma)$).
* **Efecto:** Simula desde pequeños retrasos de encolamiento (jitter) hasta severas caídas de rendimiento