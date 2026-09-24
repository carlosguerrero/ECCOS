# Especificación del Modelo de Distribución y Movilidad de Usuarios

Este documento detalla el enfoque seleccionado para modelar la ubicación espacial inicial de los usuarios y su dinámica de movimiento a lo largo del tiempo de simulación. Se ha optado por un enfoque híbrido que maximiza el realismo en entornos urbanos o *Smart Cities*, combinando aglomeraciones naturales con restricciones físicas de movimiento.

---

## 1. Topología Espacial de la Infraestructura

Para que el modelo de movilidad tenga sentido, **es un requisito indispensable que todos los nodos de la infraestructura posean coordenadas geográficas $(x, y)$.** Sin embargo, el tratamiento de estas coordenadas varía según la capa del Continuum:

* **Capa Far-Edge (Acceso):** Sus coordenadas $(x,y)$ representan ubicaciones físicas reales en el plano de la ciudad (ej. farolas, semáforos, torres de telefonía). La distancia física entre estos nodos y los usuarios es determinante para la latencia y la calidad de la señal.
* **Capas Fog y Cloud:** Aunque técnicamente se les puede asignar una coordenada para la visualización global, a efectos prácticos de conexión de usuarios, estas capas son "invisibles" geográficamente. Se asume que su conexión con el Edge se enruta por una red troncal de fibra óptica.

---

## 2. Reglas de Asociación Usuario-Infraestructura

**Los usuarios solo deben conectarse directamente a los nodos de la capa Far-Edge.**

* **Fundamento:** En el mundo real, un teléfono móvil o un dispositivo IoT no se conecta directamente mediante un enlace inalámbrico (Radio Access Network) a un macro-servidor de Amazon AWS (Cloud) ni a una central de conmutación regional (Fog). Se conectan a la antena (gNodeB) o al punto de acceso WiFi más cercano.
* **Comportamiento en la simulación:** 1. El usuario evalúa las coordenadas de todos los nodos Far-Edge disponibles.
    2. Se asocia al nodo Far-Edge que ofrezca la mejor señal (habitualmente el de menor distancia euclídea, siempre y cuando no esté saturado y el usuario se encuentre dentro de su radio de cobertura $R$).
    3. Si el usuario necesita un servicio que está alojado en el Fog o en el Cloud, el nodo Edge actuará como pasarela (*gateway*), reenviando la petición hacia arriba en la jerarquía.

---

## 3. Modelo de Distribución Inicial: Thomas Cluster Process

La ubicación inicial de los usuarios en el tiempo $t=0$ se genera mediante un **Proceso de Clúster de Thomas**. 

### 3.1 Algoritmo de Generación
1.  **Semillas (Padres):** Se definen $N$ coordenadas en el mapa que actuarán como "puntos de interés" (hotspots), simulando centros comerciales, estadios o plazas principales.
2.  **Dispersión (Hijos):** Al instanciar a los usuarios, no se reparten uniformemente por el mapa, sino que se asignan a uno de estos puntos de interés. Sus coordenadas $(x_{user}, y_{user})$ se calculan aplicando una distribución normal bidimensional (Gaussiana) centrada en las coordenadas del punto de interés asignado.
3.  **Resultado:** Los usuarios aparecerán fuertemente aglomerados en el centro de los hotspots, disipándose gradualmente hacia las afueras, dejando zonas del mapa casi vacías (como polígonos industriales de noche o parques grandes).

---

## 4. Modelo de Movilidad: Manhattan Mobility Model

Una vez situados, los usuarios se moverán siguiendo un patrón de cuadrícula que simula calles y manzanas reales (bloques de edificios).

### 4.1 Modificación de los Eventos de Movilidad
Los eventos actuales relacionados con el movimiento de usuarios deben reescribirse para ajustarse a este modelo físico:

* **Redefinición de `move_user`:** Anteriormente definido de forma abstracta ("cambia el nodo al que está conectado"). Ahora, el evento `move_user` **debe consistir en una actualización de las coordenadas $(x, y)$ del usuario**.
    * El usuario solo podrá modificar su posición incrementando o decrementando exclusivamente su coordenada $X$ (simulando moverse por una calle horizontal) o su coordenada $Y$ (moviéndose por una calle vertical). No se permiten movimientos diagonales libres.
    * El usuario se mueve con una velocidad $v$ durante un tiempo $t$ hasta llegar a un cruce (intersección), donde hay una probabilidad de cambiar de dirección o seguir recto.

### 4.2 Impacto del Movimiento en la Asociación
Es fundamental separar el *movimiento físico* del *cambio de conexión de red*:

1.  El evento principal es la actualización de las coordenadas $(x,y)$.
2.  Tras moverse, el sistema debe comprobar la distancia entre el usuario y su nodo Edge actual.
3.  Si la distancia supera el radio de cobertura $R$ del nodo, o si otro nodo Edge pasa a estar significativamente más cerca, **entonces se dispara un evento secundario de reasociación de infraestructura (`handoff`)**.
4.  Este `handoff` forzará al algoritmo ILP a evaluar si la aplicación que consumía el usuario debe migrar al nuevo nodo Edge o quedarse en el antiguo.
