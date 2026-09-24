# Catálogo de Eventos - Simulador de Computing Continuum

Este documento contiene el listado completo de eventos contemplados para el simulador del *Computing Continuum*, organizados por la entidad sobre la que impactan. Se incluyen tanto los eventos ya implementados inicialmente como las nuevas sugerencias orientadas a mejorar el realismo físico y la idoneidad para artículos científicos de alto impacto.

---

## 👤 Usuarios (`user`)

### Eventos Implementados
* **Crear (`new_user`):** Genera un nuevo usuario en la topología, asociándolo a la petición de una aplicación (bien escogida aleatoriamente por su popularidad, o una en concreto) y conectándolo a un nodo de la red.
* **Eliminar (`remove_user`):** Borra a un usuario concreto del simulador y purga sus futuros eventos.
* **Eliminar por aplicación solicitada (`remove_user_by_requested_app`):** Elimina en bloque a todos los usuarios que estuvieran haciendo peticiones a una aplicación determinada.
* **Mover de punto de conexión (`move_user`):** Cambia el nodo al que está conectado actualmente el usuario hacia un nodo adyacente.
* **Aumentar ratio de peticiones individual (`increase_request_ratio`):** Incrementa la frecuencia con la que un usuario concreto solicita servicios.
* **Aumentar ratio de peticiones global (`increase_request_ratio_by_requested_app`):** Aumenta el ratio de peticiones de todos los usuarios asociados a una aplicación específica.
* **Disminuir ratio de peticiones individual (`decrease_request_ratio`):** Reduce la frecuencia de solicitud de un usuario.
* **Disminuir ratio de peticiones global (`decrease_request_ratio_by_requested_app`):** Disminuye de forma generalizada el ratio de las peticiones para todos los usuarios de una aplicación concreta.

* **Suspensión aleatoria de usuario (`suspend_random_user`):** Simula estocásticamente la pérdida de conexión o un hand-off de un usuario al azar que esté conectado.
* **Desconexión temporal de usuario (`suspend_user`):** Acción directa o disparada por movimiento (`move_user` excediendo `coverage_radius`). El usuario pierde la conexión temporalmente, reduciendo su `requestRatio` a cero pero sin ser eliminado.
* **Reconexión de usuario (`resume_user`):** Reactiva a un usuario previamente suspendido tras una desconexión (hand-off). El usuario retoma su ratio de peticiones original y se simula un "movimiento fantasma" a lo largo de las coordenadas del mapa durante el tiempo que estuvo desconectado, reconectándolo al nodo Edge más cercano.

---

## 📱 Aplicaciones (`app`)

### Eventos Implementados
* **Crear (`new_app`):** Instancia un nuevo servicio o aplicación en el simulador. Al crearlo, también se encarga de crear simultáneamente una serie de nuevos usuarios que comiencen a solicitar dicho servicio.
* **Eliminar (`remove_app`):** Desmantela la aplicación del sistema. Esto conlleva la eliminación en cascada de todos los usuarios que estuvieran conectados pidiendo esta aplicación, así como de sus eventos en cola.

### Eventos de Popularidad (Nuevos / Modificados)
* **Incremento Abrupto de Popularidad (`surge_popularity`):** Mejora drásticamente el rango de la aplicación simulando un pico viral o nueva tendencia (cambio en la Ley de Zipf mediante intercambio de rango). Puede ser permanente o formar parte de un evento transitorio (*Flash Crowd*). Reemplaza al antiguo `increase_popularity`.
* **Caída Abrupta de Popularidad (`drop_popularity`):** Empeora el rango de popularidad simulando pérdida de interés o interrupción del servicio. Reemplaza al antiguo `decrease_popularity`.
* **Restauración de Popularidad (`restore_popularity`):** Evento programado pareado a un evento transitorio. Se encarga de devolver a la aplicación a su rango de popularidad original una vez pasado el *Flash Crowd* o apagón.

### Eventos de Actualización y Demanda (Nuevos)
* **Actualización de Aplicación (`update_app`):** Evento transversal que perturba el Service Function Chain (SFC) de una aplicación en vivo. Puede incluir mutaciones en los recursos de los microservicios (CPU/RAM), alteraciones en las exigencias de red (Ancho de Banda/Latencia) o mutaciones topológicas (inserción/eliminación de microservicios de la cadena). Reemplaza y unifica sugerencias anteriores (`change_app_footprint`, `add_app_dependency`, `remove_app_dependency`).
* **Desplazamiento Geográfico de la Demanda (`geo_demand_shift`):** Exclusivo para aplicaciones locales. Simula el movimiento espacial del interés de los usuarios a través del mapa alterando su centro de influencia $(x_c, y_c)$ mediante saltos directos (Discrete Jumps) o caminatas aleatorias (Spatial Drifts).

---

## 🌐 Infraestructura / Grafo de Red (`graph`)

### Eventos Implementados
* **Caída de nodo aleatorio (`disable_random_node`):** Simula el fallo de un nodo cualquiera en la red (teniendo mayor probabilidad de caer aquellos con menor centralidad). Libera la memoria usada y programa automáticamente en el tiempo un evento para reactivarlo más tarde.
* **Caída de nodo específico (`disable_node`):** Deshabilita un nodo concreto en la red perdiendo las aplicaciones que estuvieran corriendo en él.
* **Recuperación de nodo (`revive_node`):** Vuelve a habilitar y levantar un nodo que previamente había caído.
* **Corte de enlace aleatorio (`disable_random_edge`):** Simula la pérdida o corte de conexión en una arista activa al azar y programa su futuro restablecimiento.
* **Corte de enlace específico (`disable_edge`):** Deshabilita de forma directa la comunicación entre dos nodos dados.
* **Recuperación de enlace (`revive_edge`):** Vuelve a habilitar el paso de tráfico a través de una arista (enlace) que estuviera inactiva.

* **Degradación aleatoria de capacidad de nodo (`degrade_random_node`):** Selecciona aleatoriamente un nodo activo y reduce temporalmente un porcentaje de la CPU o RAM nominal disponible (simulando sobrecalentamiento, mantenimiento o batería baja). Programa su futura recuperación.
* **Degradación de capacidad de nodo específico (`degrade_node`):** En lugar de un apagado total, reduce de manera directa la capacidad disponible en el nodo usando un factor de pérdida.
* **Restaurar capacidad de nodo (`restore_node`):** Devuelve al nodo degradado sus capacidades máximas y nominales originales de recursos.
* **Congestión aleatoria de enlace (`congest_random_edge`):** Selecciona un enlace activo y simula problemas de tráfico incrementando drásticamente la latencia y recortando el ancho de banda. Programa su futura restauración.
* **Congestión de enlace específico (`congest_edge`):** Aplica directamente factores de degradación en el ancho de banda y multiplicadores de latencia en un enlace en concreto.
* **Descongestión de enlace (`clear_edge`):** Limpia el canal y restablece los valores nominales de rendimiento (latencia y ancho de banda) del enlace de red.

