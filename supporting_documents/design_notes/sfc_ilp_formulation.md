# Formulación Matemática ILP para Service Function Chaining (SFC)

Este documento describe la formulación del problema de Programación Lineal Entera (ILP) utilizado en `src/optimization.py` para emplazar aplicaciones que están compuestas por una cadena de microservicios (Service Function Chaining).

## 1. Conjuntos y Parámetros

- $\mathcal{A}$: Conjunto de aplicaciones activas en la red.
- $\mathcal{M}_a$: Cadena de microservicios ordenados que componen la aplicación $a \in \mathcal{A}$. Para una cadena de longitud $L$, los microservicios se indexan como $0, 1, \dots, L-1$.
- $\mathcal{N}$: Conjunto de nodos activos en la red.
- $\mathcal{U}$: Conjunto de usuarios conectados.
- $N_u \in \mathcal{N}$: Nodo al que está directamente conectado el usuario $u$.
- $A_u \in \mathcal{A}$: Aplicación solicitada por el usuario $u$.
- $w_u$: Ratio de peticiones (popularidad/peso) generado por el usuario $u$.
- $\text{Delay}(i, j)$: Retardo del camino más corto entre el nodo $i$ y el nodo $j$.
- $\text{RAM}_{a, m}$: Requisito de RAM del microservicio $m$ de la aplicación $a$.
- $\text{CapRAM}_n$: Capacidad máxima de RAM disponible en el nodo $n$.

## 2. Variables de Decisión

Para permitir que cada microservicio se aloje de forma independiente, sustituimos la variable monolítica $x_{a,n}$ por:

$$ x_{a, m, n} \in \{0, 1\} $$
Vale 1 si el microservicio $m$ de la aplicación $a$ se emplaza en el nodo $n$, y 0 en caso contrario.

Debido a que necesitamos calcular la latencia interna entre microservicios consecutivos ($m$ y $m+1$), deberíamos multiplicar $x_{a, m, i} \times x_{a, m+1, j}$. Sin embargo, esto hace que el problema sea cuadrático (no lineal). Para **linearizarlo**, introducimos una variable auxiliar $y$:

$$ y_{a, m, i, j} \in \{0, 1\} $$
Vale 1 si el microservicio $m$ está en el nodo $i$ **y** el microservicio $m+1$ está en el nodo $j$.

## 3. Función Objetivo

El objetivo es minimizar la latencia total ponderada en la red, que se compone de dos partes:
1. **Latencia del Usuario:** El retardo desde el nodo del usuario hasta el **primer microservicio** de la aplicación solicitada.
2. **Latencia Interna (SFC):** El retardo de comunicación secuencial a través de la cadena de microservicios.

$$
\text{Minimizar } Z = \sum_{u \in \mathcal{U}} w_u \times \left( \text{DelayUser}_u + \text{DelayInt}_{A_u} \right)
$$

Donde:
$$ \text{DelayUser}_u = \sum_{n \in \mathcal{N}} x_{A_u, 0, n} \times \text{Delay}(N_u, n) $$
$$ \text{DelayInt}_a = \sum_{m=0}^{|\mathcal{M}_a|-2} \sum_{i \in \mathcal{N}} \sum_{j \in \mathcal{N}} y_{a, m, i, j} \times \text{Delay}(i, j) $$

## 4. Restricciones

### 4.1. Unicidad de Emplazamiento
Cada microservicio de cada aplicación debe asignarse exactamente a un único nodo:
$$ \sum_{n \in \mathcal{N}} x_{a, m, n} = 1 \quad \forall a \in \mathcal{A}, \forall m \in \mathcal{M}_a $$

### 4.2. Capacidad de Recursos (RAM)
La suma de la RAM consumida por todos los microservicios alojados en un nodo no puede exceder su capacidad:
$$ \sum_{a \in \mathcal{A}} \sum_{m \in \mathcal{M}_a} \text{RAM}_{a, m} \times x_{a, m, n} \leq \text{CapRAM}_n \quad \forall n \in \mathcal{N} $$

### 4.3. Linearización de $y_{a, m, i, j}$
Para forzar matemáticamente que $y_{a, m, i, j} = x_{a, m, i} \wedge x_{a, m+1, j}$ en un solver ILP, se añaden las siguientes 4 restricciones estandarizadas $\forall a \in \mathcal{A}, \forall m \in \{0 \dots |\mathcal{M}_a|-2\}, \forall i, j \in \mathcal{N}$:

1. $y_{a, m, i, j} \leq x_{a, m, i}$
2. $y_{a, m, i, j} \leq x_{a, m+1, j}$
3. $\sum_{j \in \mathcal{N}} y_{a, m, i, j} = x_{a, m, i}$
4. $\sum_{i \in \mathcal{N}} y_{a, m, i, j} = x_{a, m+1, j}$

*(Nota: En muchos casos, al ser un problema de minimización con coeficientes de retardo positivos, las desigualdades 1 y 2 junto con las ecuaciones 3 y 4 obligan al solver a ajustar $y$ correctamente de forma automática).*
