# Distribución Espacial y Movilidad de Usuarios

Para representar escenarios realistas de ciudades inteligentes (*Smart Cities*) o grandes despliegues geográficos de red, el simulador asigna a cada usuario coordenadas reales en un mapa (plano euclídeo) y gestiona sus conexiones en función de su cercanía física a la infraestructura Edge de acceso.

Todo se parametriza mediante el bloque `user` dentro de `attributes` en el archivo de configuración YAML.

---

## 1. Distribución Espacial Inicial (Thomas Cluster Process)

La disposición inicial de los usuarios en el tiempo $t=0$ no es aleatoria uniforme, sino que emplea el **Thomas Cluster Process**. Esto simula aglomeraciones de personas en "puntos calientes" (hotspots) como centros comerciales, estadios o estaciones de tren.

El simulador reparte una serie de Hotspots en el mapa, y cuando genera a los usuarios, los asigna a uno de estos puntos mediante una distribución Gaussiana Bidimensional. Como resultado, los usuarios quedan agrupados densamente en el centro del hotspot y se disipan progresivamente hacia la periferia.

### Configuración YAML
```yaml
user:
  spatial_distribution:
    model: "thomas_cluster"
    hotspots: 5           # Número de puntos de interés centrales generados en el mapa
    spread: 0.05          # Desviación típica (Gaussiana) alrededor del hotspot. Valores más bajos = agrupaciones más densas.
```

---

## 2. Movilidad (Manhattan Mobility Model)

A lo largo de la simulación se despachan eventos de `move_user` que desplazan físicamente a los usuarios. El modelo adoptado es el **Manhattan Mobility Model**, el cual simula los movimientos de peatones o vehículos en un entorno cuadriculado (bloques de edificios y manzanas urbanas).

En cada movimiento, el usuario avanza de manera aleatoria a través del Eje X (horizontal) o el Eje Y (vertical), pero no de manera diagonal, imitando las restricciones de movimiento de las calles de una ciudad moderna. Las coordenadas físicas de los usuarios nunca excederán los márgenes geográficos definidos $[0, 1]$.

### Configuración YAML
```yaml
user:
  mobility:
    model: manhattan
    speed: 
      type: uniform
      low: 0.005
      high: 0.02
    coverage_radius: 
      type: normal
      mean: 0.2
      sigma: 0.02
```

---

## 3. Conexión de Capa Física y Red de Acceso

La lógica de asociación de los usuarios está profundamente ligada a estas coordenadas. 

Independientemente del modelo topológico escogido (`scale_free`, `multi_tier`, etc.), **los usuarios únicamente pueden conectarse a nodos que pertenezcan a la capa de acceso (`layer: edge`)**. 

Cuando un usuario nace (o cada vez que se desplaza tras un evento `move_user`), su terminal evalúa qué antena Edge tiene la menor distancia euclidiana hacia su posición y se conecta a ella. 

> **Límite de Cobertura Flexible (Soft Limit):**
> Siguiendo las directrices del diseño (Opción A recomendada en la especificación), el simulador fuerza al dispositivo del usuario a estar siempre conectado al Edge más cercano. Esto quiere decir que si un usuario se desplaza a una zona periférica o "muerta", no se cortará su conexión drásticamente ni quedará excluido del optimizador ILP, sino que se mantendrá anclado a la estación Edge perimetral con mejor distancia relativa.
