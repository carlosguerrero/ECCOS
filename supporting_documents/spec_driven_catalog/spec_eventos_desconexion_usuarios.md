# Especificación de Eventos de Desconexión Temporal de Usuarios

En redes móviles (5G/6G) y entornos IoT, la conectividad de los dispositivos en el *Far-Edge* es intrínsecamente volátil. Los usuarios sufren pérdidas de señal temporales debido a *hand-offs* entre celdas, zonas de sombra (túneles, ascensores) o modos de ahorro de energía.

Este documento define el ciclo de vida de las desconexiones temporales, implementado a través de pares de eventos vinculados, y su impacto espacial y computacional en la simulación.

---

## 1. Ciclo de Vida de la Desconexión (Eventos Pareados)

La interrupción de la conectividad se modela inyectando dos eventos dependientes en la cola temporal del simulador.

### 1.1 Suspensión de Usuario (`suspend_user`)
* **Acción:** En el instante $T$, el usuario pierde la conexión con la red. Su ratio de peticiones de aplicaciones cae a cero instantáneamente.
* **Estado interno:** El usuario **no** se elimina del sistema (a diferencia de `remove_user`). Pasa a un estado latente (`status = disconnected`), manteniendo en memoria las aplicaciones a las que estaba suscrito y su vector de movimiento.

### 1.2 Reconexión de Usuario (`resume_user`)
* **Acción:** En el instante $T + \Delta t$, el usuario recupera la señal. Vuelve a generar peticiones (retomando su actividad normal).
* **Actualización Espacial:** Obliga a reevaluar qué nodo Edge está ahora más cerca y forzará, con alta probabilidad, una reasociación de red.

---

## 2. Modelado Matemático y Estadístico

### 2.1 Disparadores del Evento (Triggers)
La suspensión de un usuario puede ser invocada por dos vías complementarias:
1. **Determinista/Espacial:** El simulador detecta que, tras un evento `move_user`, las coordenadas $(x, y)$ del usuario quedan fuera del radio de cobertura $R$ de todos los nodos de la capa *Far-Edge*.
2. **Estocástico:** Para simular averías, bloqueos del dispositivo o interferencias, se utiliza un **Proceso de Poisson** con una tasa $\lambda_{suspend}$ que elige aleatoriamente a un usuario activo para desconectarlo.

### 2.2 Duración de la Desconexión ($\Delta t$)
El tiempo de permanencia en la "zona de sombra" debe ser fuertemente asimétrico.
* **Distribución Sugerida:** **Distribución Lognormal** $Lognormal(\mu, \sigma)$.
* **Justificación:** Representa fielmente las mediciones empíricas de redes celulares. El cuerpo de la distribución acomoda la altísima frecuencia de micro-cortes y *handoffs* (1 a 5 segundos), mientras que la cola extendida permite simular escenarios de pérdida de cobertura prolongada (viajes en túneles o sótanos que duran varios minutos).

### 2.3 Cálculo del "Movimiento Fantasma" (Ghost Movement)
Mientras el usuario está en estado suspendido, el tiempo de simulación sigue avanzando. Al dispararse el evento `resume_user`, el usuario no debe reaparecer necesariamente en la coordenada exacta donde desapareció.
* **Matemática:** Si el usuario tenía un vector de velocidad promedio $\vec{v}$ al momento de desconectarse, sus nuevas coordenadas al reconectarse serán aproximadamente: 
  $(x, y)_{resume} = (x, y)_{suspend} + \vec{v} \times \Delta t$
* *(Nota de implementación: Este cálculo debe estar acotado por los límites del mapa y las reglas del modelo de movilidad de Manhattan).*

---

## 3. Impacto en el Optimizador (ILP) y Retención de Estado

La desconexión temporal de usuarios es uno de los mayores desafíos para los orquestadores del Continuum, ya que introduce el dilema de la **Retención de Estado (State Retention)**.

* **Requisito para el Simulador:** Cuando un usuario sufre un `suspend_user`, la aplicación o cadena SFC que estaba consumiendo **no debe ser destruida inmediatamente**. 
* **Lógica del ILP:** El ILP debe ser capaz de modelar un "Toleration Time" (Tiempo de Tolerancia). La aplicación se mantiene "caliente" (consumiendo RAM pero sin generar CPU/tráfico) en el nodo Edge durante un tiempo prudencial. 
    * *Si el usuario se reconecta rápido:* Retoma su servicio sin latencia de inicio (Cold Start).
    * *Si el usuario tarda demasiado en reconectarse:* El orquestador (en sus pasadas periódicas) detecta el *timeout*, desmantela la instancia de la aplicación en ese nodo para liberar recursos y re-optimiza el sistema.