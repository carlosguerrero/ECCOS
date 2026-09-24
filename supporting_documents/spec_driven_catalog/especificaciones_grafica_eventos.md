# Especificaciones para la Visualización de Eventos del Simulador (Swimlane Scatter Plot)

**Objetivo:** Desarrollar una gráfica para visualizar de forma clara la ocurrencia de eventos discretos a lo largo del tiempo continuo de simulación. El objetivo es identificar ráfagas de eventos, distribuciones temporales y efectos cascada entre las distintas capas del *Computing Continuum*.

---

## 1. Estructura de los Ejes

* **Eje X (Tiempo):** * Debe representar el **tiempo continuo de simulación** (p. ej., milisegundos, segundos o ticks reales), no un índice secuencial de salto. 
    * Debe incluir un *grid* (cuadrícula) vertical ligero para facilitar la lectura del momento exacto en el que ocurren los eventos.

* **Eje Y (Entidades / Carriles):**
    * Debe ser un eje **categórico** dividido en los 3 grandes grupos del sistema, creando "carriles" (*swimlanes*) horizontales:
        1.  `Usuarios` (Carril superior)
        2.  `Aplicaciones` (Carril central)
        3.  `Infraestructura` (Carril inferior)

---

## 2. Representación de los Datos (Marcadores)

Cada evento registrado en la traza se pintará como un punto (o marcador) en la gráfica. Las coordenadas de cada punto serán:
* **X:** Timestamp exacto del evento.
* **Y:** El carril correspondiente a la entidad que sufre el evento.

### Codificación de Color (Semántica del Evento)
Para no saturar la leyenda con decenas de eventos distintos, los marcadores deben agruparse por colores según su **naturaleza e impacto** en el sistema:

* 🟢 **Verde (Creación / Recuperación):** Eventos que añaden recursos o levantan servicios.
    * *Ejemplos:* `new_user`, `resume_user`, `new_app`, `revive_node`, `revive_edge`, `restore_node_capacity`, `clear_edge`.
* 🟠 **Naranja / Azul (Modificación / Movilidad / Degradación):** Eventos que alteran el estado o la ubicación sin destruir la entidad.
    * *Ejemplos:* `move_user`, `increase_request_ratio`, `change_app_footprint`, `suspend_user`, `degrade_node_capacity`, `congest_edge`.
* 🔴 **Rojo (Destrucción / Caída):** Eventos que eliminan entidades o simulan fallos.
    * *Ejemplos:* `remove_user`, `remove_app`, `disable_node`, `disable_random_node`, `disable_edge`.

---

## 3. Interactividad y Tooltips (Muy Recomendado)

Dado que un punto rojo en el carril "Infraestructura" puede ser tanto la caída de un enlace como la caída de un nodo, es crucial incluir interactividad (si el formato de salida lo permite):
* **Hover / Tooltip:** Al pasar el ratón por encima de cualquier marcador, debe aparecer una caja de texto flotante con la siguiente información:
    * **Tiempo exacto:** `T = 42.35s`
    * **Tipo de Evento:** `disable_node`
    * **Detalle / Entidad afectada:** `Node ID: 14` (Opcional, pero muy útil para debugear).

---

## 4. Sugerencias de Implementación Técnica (Para el desarrollador)

* **Librería Recomendada para Interactividad:** `Plotly` (Python). Permite crear *Scatter plots* con ejes categóricos (Y) y ejes continuos (X) de manera nativa, y los tooltips vienen activados por defecto. Es ideal para exportar a HTML y explorar el dataset interactuando con la gráfica.
* **Librería Recomendada para el Paper (Estático):** `Seaborn` (usando `sns.stripplot` con `jitter=False` o `sns.scatterplot`) o `Matplotlib` clásico. Ideal para exportar figuras en PDF de alta resolución requeridas por las revistas JCR. Si hay eventos simultáneos, se sugiere aplicar un valor de transparencia (`alpha=0.6`) a los marcadores para que se aprecie la densidad.
