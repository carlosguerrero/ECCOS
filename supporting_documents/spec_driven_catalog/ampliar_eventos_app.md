# Especificación del Evento: Actualización de Aplicación (update_app)

Este documento define la semántica y el modelado estadístico del evento de actualización de aplicaciones. En un entorno *Cloud Native* / Edge, el ciclo de vida del software es dinámico. Una actualización puede alterar las necesidades de la aplicación, forzando al ILP a reevaluar su emplazamiento actual.

## 1. Naturaleza del Evento de Actualización

Cuando una aplicación seleccionada sufre un evento `update_app`, la simulación aplicará perturbaciones a las características de su *Service Function Chain* (SFC). 

El simulador evaluará secuencialmente tres posibles vectores de mutación:

### 1.1 Mutación de Recursos (Footprint Mutation)
Simula la instalación de una nueva versión del software (parches de seguridad, optimizaciones de código o nuevas *features* pesadas).

* **Parámetros afectados:** CPU y RAM requerida por cada microservicio del SFC.
* **Modelado Estadístico:** El incremento/decremento se rige por una **Distribución Normal** centrada en cero: $N(\mu=0, \sigma^2)$.
* **Lógica:** $Recurso_{nuevo} = Recurso_{actual} \times (1 + \Delta)$, donde $\Delta \sim N(0, \sigma^2)$. 
* **Justificación JCR:** Garantiza que la inmensa mayoría de las actualizaciones introducen cambios marginales (el núcleo de la campana), mientras que permite la existencia infrecuente de actualizaciones que drásticamente inflan (o reducen) el consumo de la aplicación.

### 1.2 Mutación de Requerimientos de Red (Network Constraints)
Simula un cambio en la carga útil de la comunicación entre microservicios (ej. pasar de enviar texto plano a enviar telemetría en tiempo real, o requerir cifrado).

* **Parámetros afectados:** Ancho de Banda ($BW$) demandado en los enlaces lógicos del SFC, y la tolerancia a Latencia Máxima ($L_{max}$).
* **Modelado Estadístico:** Se aplicará una perturbación análoga a la mutación de recursos, utilizando una Distribución Normal $N(0, \sigma^2_{net})$.

### 1.3 Mutación Topológica de la Cadena (SFC Topology Mutation)
Simula refactorizaciones arquitectónicas mayores de la aplicación. Es el evento más disruptivo para el ILP.

* **Parámetros afectados:** La longitud $L$ del SFC (número de microservicios).
* **Modelado Estadístico:** Se utiliza una **Distribución de Bernoulli** con una probabilidad $p_{topo}$ (típicamente baja, ej. $p=0.15$).
* **Lógica:**
  * Si el ensayo de Bernoulli es exitoso ($1$), se procede a modificar la cadena.
  * Se decide aleatoriamente (con probabilidad $0.5$) si la modificación será una **Inserción** (añadir un nuevo microservicio en un punto aleatorio de la cadena) o una **Eliminación** (suprimir un microservicio existente).
  * *Excepción:* No se permitirá reducir la cadena por debajo de $L_{min}$ (ej. 1 o 2 microservicios) ni expandirla más allá de $L_{max\_global}$ definido en la configuración.

## 2. Frecuencia de Ocurrencia en la Simulación

Para determinar en qué instante de tiempo $t$ se disparan estos eventos de actualización a lo largo de la simulación:

* **Modelado Estadístico:** Se modelará como un **Proceso de Poisson**.
* **Lógica:** El tiempo entre dos actualizaciones sucesivas para el conjunto de aplicaciones seguirá una **Distribución Exponencial** con un parámetro de tasa $\lambda_{update}$.
* **Selección del objetivo:** Cuando el Proceso de Poisson determine que debe ocurrir un `update_app`, se seleccionará la aplicación a actualizar de forma aleatoria uniforme entre todas las aplicaciones instanciadas en ese momento, o bien, ponderada por su popularidad (las apps más usadas se actualizan más a menudo).


## 2. Mutación de la Demanda y Popularidad (Demand Shifts)

Además de los cambios arquitectónicos y de recursos (Footprint), las aplicaciones están sujetas a fluctuaciones severas en cómo y dónde son demandadas por los usuarios. Estos eventos son críticos para evaluar la agilidad del ILP a la hora de migrar servicios en vivo (Live Migration) para mantener una baja latencia.

### 2.1 Mutación de Popularidad Global (Trend Shifts y Flash Crowds)

La popularidad de las aplicaciones (su posición en la Ley de Zipf) sufre alteraciones que deben categorizarse por su duración en el tiempo: cambios de tendencia permanentes o picos/caídas transitorias.

#### A. Tipología del Cambio Temporal
Al generarse un evento que altera la popularidad, el simulador decidirá (mediante una probabilidad predefinida, ej. 70% transitorio / 30% permanente) a qué categoría pertenece:

1. **Cambio Permanente (Trend Shift):**
   * *Acción:* Se ejecuta un `surge_popularity` (la app gana usuarios, bajando su rango $r$ hacia el 1) o un `drop_popularity` (la app pierde usuarios, subiendo su rango hacia $K$). 
   * El cambio en la distribución de Zipf se mantiene indefinidamente hasta que otro evento aleatorio afecte a la aplicación.

2. **Cambio Transitorio (Flash Crowd / Temporary Outage):**
   * *Acción:* Se simula un pico viral o una caída temporal de interés (ej. durante un evento deportivo o una caída de servicio).
   * *Mecanismo de Eventos Pareados:* El simulador inyecta **dos eventos** en la cola temporal:
     1. Evento de inicio (`surge_popularity` o `drop_popularity`) en el instante $T$.
     2. Evento de reversión (`restore_popularity`) programado para el instante $T + \Delta t$. Este evento devolverá la aplicación a su rango $r$ original previo al *shock*.

#### B. Modelado Estadístico de la Duración ($\Delta t$)
Para los eventos transitorios, el tiempo de duración $\Delta t$ no será constante. 
* **Distribución Sugerida:** **Distribución Weibull**.
* **Justificación:** Es ampliamente utilizada en ingeniería de confiabilidad y modelado de tráfico web. Permite representar que la mayoría de los "ruidos" de popularidad duran un tiempo moderado (el cuerpo de la distribución), pero existe una probabilidad controlada de eventos que se extienden significativamente (la cola), simulando por ejemplo una crisis viral que dura días en lugar de horas.

#### C. Mecanismo de Intercambio (Rank Swapping)
Para aplicar el cambio matemático sin destruir la coherencia de las probabilidades, se utilizará el intercambio de rangos:
* Al aplicar un *Surge* a una aplicación en el rango $r=150$, se le asigna un nuevo rango "Top" (ej. $r=3$). La aplicación que estaba en $r=3$ (y potencialmente las adyacentes) son desplazadas para acomodar la nueva probabilidad, manteniendo la suma total de probabilidades de la Ley de Zipf igual a 1.

### 2.2 Desplazamiento de la Demanda Geográfica (Geo-Demand Shift)
Exclusivo para las "Aplicaciones Locales" (Local-Scoped Apps) definidas en el modelo base. Simula el movimiento del interés del usuario a través del mapa de la ciudad a lo largo del día (ej. patrones de tráfico pendular o eventos masivos que se desplazan).

* **Parámetros afectados:** Las coordenadas del centro de influencia espacial $(x_c, y_c)$ asociadas a la aplicación, que gobiernan la probabilidad de solicitud según el modelo de clúster de Thomas.
* **Modelado Espacial:** Se aplicará uno de los siguientes sub-eventos:
  1. **Salto de Hotspot (Discrete Jump):** Las coordenadas $(x_c, y_c)$ se reasignan instantáneamente a un nuevo "Punto de Interés" predefinido en la configuración (ej. la demanda salta del "Distrito Financiero" al "Estadio"). El ILP reaccionará con una migración abrupta de los microservicios de ingesta hacia el nuevo Edge local.
  2. **Deriva de Demanda (Spatial Drift):** El centro de influencia realiza un paso siguiendo un **Paseo Aleatorio (Random Walk)**: $(x_c, y_c)_{t+1} = (x_c, y_c)_t + \vec{v}_{drift}$. Simula un atasco de tráfico o una multitud en movimiento. Obliga al ILP a realizar migraciones más pequeñas y consecutivas (Handoffs de microservicios).

  