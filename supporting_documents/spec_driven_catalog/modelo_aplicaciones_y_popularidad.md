# Especificación del Modelado de Aplicaciones y Servicios

Este documento define las características, dependencias y la dinámica de demanda de las aplicaciones dentro de la simulación del *Computing Continuum*. El objetivo es reflejar la extrema varianza de los entornos reales y la arquitectura moderna basada en microservicios y *Service Function Chaining* (SFC).

## 1. Arquitectura de las Aplicaciones: Service Function Chaining (SFC)

En el *Computing Continuum* moderno (5G/Edge), las aplicaciones no son monolíticas. Se modelan como cadenas o grafos de microservicios o Funciones de Red Virtuales (VNFs).

Una petición de usuario hacia una "Aplicación" despliega un **Grafo Acíclico Dirigido (DAG)** o una **Cadena Lineal (Linear Chain)**.

* **Estructura del SFC:**

  * **Longitud de la cadena (**$L$**):** El número de microservicios que componen la aplicación. Para mantener el realismo, $L$ se muestrea de una distribución uniforme discreta o de Poisson, típicamente con valores entre $2$ y $6$ microservicios por cadena.

  * **Nodos del Grafo (Microservicios):** Representan el procesamiento. Requieren recursos computacionales (CPU, RAM).

  * **Aristas del Grafo (Enlaces lógicos):** Representan el flujo de datos entre microservicios. Requieren recursos de red (Ancho de banda $BW$) y están sujetos a restricciones de latencia máxima ($L_{max}$).

* **Impacto JCR:** Al incluir SFC, el simulador obliga al ILP a resolver un problema de *VNF Forwarding Graph Embedding*. El ILP deberá decidir si agrupa todos los microservicios en un único nodo Edge de alta capacidad (minimizando latencia a 0 pero agotando recursos) o si los distribuye a lo largo del Continuum (Edge $\rightarrow$ Fog $\rightarrow$ Cloud), consumiendo ancho de banda de la red troncal.

## 2. Caracterización de Recursos (Footprint por Microservicio)

Cada *microservicio* dentro de un SFC representará una demanda de recursos específica. Estos atributos deben emparejarse semánticamente con las capacidades de los nodos y enlaces de la infraestructura.

Para generar perfiles realistas, se emplearán distribuciones de cola larga que reflejen la coexistencia de funciones ligeras y escasas funciones pesadas.

* **Distribución Sugerida:** **Lognormal**.

  * Se utilizará una distribución Lognormal parametrizada (con un $\mu$ y $\sigma$ definidos en la configuración) para generar el consumo de CPU y RAM de cada microservicio, así como el Ancho de Banda de las aristas lógicas.

* **Tipificación por Clases:** Para evitar combinaciones incongruentes, las cadenas pueden tipificarse:

  * *Cadena IoT / Telemetría:* Microservicios con CPU muy baja, RAM muy baja, Ancho de banda bajo.

  * *Cadena de Inferencia IA / Video:* Microservicio de ingesta (Edge) con alto BW $\rightarrow$ Microservicio de Inferencia con CPU/GPU altísima $\rightarrow$ Base de Datos (Cloud) con RAM alta.

## 3. Modelado de Popularidad General

La probabilidad de que un usuario (o dispositivo) solicite una cadena de servicios específica no es equiprobable.

* **Modelo de Popularidad:** **Ley de Zipf** (Zipf's Distribution / Pareto).

* **Lógica:** Al generar el catálogo de $K$ aplicaciones (cadenas de SFC), se las ordena por un "rango de popularidad" $r$ (donde $r=1$ es la más popular y $r=K$ la menos). La probabilidad $P(r)$ de que un usuario solicite la aplicación de rango $r$ está dada por:

  $$
  P(r) \propto \frac{1}{r^\alpha}
  $$

  Donde $\alpha$ es un parámetro que suele estar cercano a 1.0. Esto asegura que unas pocas "Mega-Apps" acaparen la mayoría de las peticiones.

## 4. Localidad Espacial (Geo-Popularidad)

En escenarios de *Smart Cities* o Edge Computing, la popularidad de ciertas aplicaciones depende directamente de la ubicación geográfica del usuario.

Para modelar este efecto, se introducen **Perfiles de Afinidad Espacial**:

1. **Aplicaciones Globales:** Siguen estrictamente la Ley de Zipf en todo el mapa de simulación, independientemente de la coordenada $(x, y)$ del usuario. (Ej. servicios de mensajería global o almacenamiento en la nube).

2. **Aplicaciones Locales (Local-Scoped Apps):** Tienen asociada una coordenada o área de influencia espacial (que puede coincidir con los centros generados por el *Thomas Cluster Process* de la distribución de usuarios).

   * *Mecanismo:* Si un usuario se encuentra dentro del radio de influencia de una Aplicación Local, la probabilidad de que la solicite se incrementa exponencialmente usando una función de decaimiento basada en la distancia (ej. Gaussiana), sobrescribiendo temporalmente su posición en la Ley de Zipf.

   * *Impacto en SFC:* Esto fuerza al algoritmo ILP a resolver problemas de emplazamiento de SFC muy localizados, migrando los *microservicios de entrada* (ingesta de datos) hacia nodos Edge específicos cuando hay eventos de concentración de usuarios, mientras que el resto de la cadena podría quedarse en el Fog/Cloud.