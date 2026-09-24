# Mapeo de Eventos en Configuración YAML

Este documento ilustra cómo configurar cada evento disponible en el simulador a través del archivo `config_random.yaml`. El simulador leerá exclusivamente las secciones y eventos que estén declarados aquí; si un evento se omite o comenta, el simulador simplemente no lo utilizará en la ejecución.

A continuación se muestra un ejemplo completo con los bloques requeridos para inyectar cada evento, organizados por la entidad a la que afectan.

---

## 1. Eventos Globales de Creación (`global_spawner`)

Estos eventos pertenecen a la llave raíz `global_spawner` y se encargan de crear nuevas entidades durante la simulación de forma estocástica o determinista.

```yaml
global_spawner:
    
  # ----------------------------------------------------
  # Crear (***repeated***)
  # ----------------------------------------------------
  new_user:
    frequency:
      type: exponential
      scale: 250
      # Se pueden pasar parámetros adicionales vacíos o específicos
    
  # ----------------------------------------------------
  # Crear (***repeated***)
  # ----------------------------------------------------
  new_app:
    frequency:
      type: exponential
      scale: 800
```

---

## 2. Eventos de Usuarios (`user`)

Se definen dentro de `user.actions`. Cada usuario en el sistema programará estos eventos individualmente utilizando las distribuciones especificadas.

```yaml
user:
  actions:
      
    # ----------------------------------------------------
    # Mover de punto de conexión
    # ----------------------------------------------------
    move_user:
      frequency:
        type: exponential
        scale: 15
      
    # ----------------------------------------------------
    # Eliminar (***repeated***)
    # ----------------------------------------------------
    remove_user:
      frequency:
        type: exponential
        scale: 1500
          
    # ----------------------------------------------------
    # Eliminar por aplicación solicitada
    # ----------------------------------------------------
    remove_user_by_requested_app:
      frequency:
        type: lognormal
        mean: 5.0
        sigma: 0.2
      impact:
        requested_app: "App_1"

    # ----------------------------------------------------
    # Aumentar ratio de peticiones individual
    # ----------------------------------------------------
    increase_request_ratio:
      frequency:
        type: normal
        mean: 100
        std: 10
      impact:
        multiplier:
          type: uniform
          min: 1.1
          max: 3.5

    # ----------------------------------------------------
    # Aumentar ratio de peticiones global
    # ----------------------------------------------------
    increase_request_ratio_by_requested_app:
      frequency:
        type: exponential
        scale: 500
      impact:
        requested_app: "App_1"
        multiplier: 
          type: uniform
          min: 1.1
          max: 2.0

    # ----------------------------------------------------
    # Disminuir ratio de peticiones individual
    # ----------------------------------------------------
    decrease_request_ratio:
      frequency:
        type: exponential
        scale: 250
      impact:
        multiplier:
          type: uniform
          min: 0.1
          max: 0.9
            
    # ----------------------------------------------------
    # Disminuir ratio de peticiones global
    # ----------------------------------------------------
    decrease_request_ratio_by_requested_app:
      frequency:
        type: exponential
        scale: 600
      impact:
        requested_app: "App_1"
        multiplier: 
          type: uniform
          min: 0.1
          max: 0.5

    # ----------------------------------------------------
    # Suspensión aleatoria de usuario
    # ----------------------------------------------------
    suspend_random_user:
      frequency:
        type: exponential
        scale: 150
      impact:
        distribution_to_resume_user:
          type: lognormal
          mean: 1.0
          sigma: 0.5
      
    # ----------------------------------------------------
    # Desconexión temporal de usuario
    # ----------------------------------------------------
    suspend_user:
      frequency:
        type: exponential
        scale: 200
      impact:
        distribution_to_resume_user:
          type: uniform
          min: 2.0
          max: 5.0
            
    # ----------------------------------------------------
    # Reconexión de usuario
    # ----------------------------------------------------
    # resume_user: Se autoprograma por 'suspend_user'. No necesita config explicita.
```

---

## 3. Eventos de Aplicaciones (`app`)

Definidos bajo `app.actions`.

```yaml
app:
  actions:
      
    # ----------------------------------------------------
    # Eliminar (***repeated***)
    # ----------------------------------------------------
    remove_app:
      frequency:
        type: exponential
        scale: 3000
          
    # ----------------------------------------------------
    # Incremento Abrupto de Popularidad
    # ----------------------------------------------------
    surge_popularity:
      frequency:
        type: exponential
        scale: 400
      impact:
        rank_jump_distribution:
          type: random_int
          min: 5
          max: 20
        distribution_to_restore:
          type: lognormal
          mean: 3.5
          sigma: 0.8
            
    # ----------------------------------------------------
    # Caída Abrupta de Popularidad
    # ----------------------------------------------------
    drop_popularity:
      frequency:
        type: exponential
        scale: 500
      impact:
        rank_drop_distribution:
          type: random_int
          min: 2
          max: 10
        distribution_to_restore:
          type: lognormal
          mean: 4.0
          sigma: 1.0
            
    # ----------------------------------------------------
    # Restauración de Popularidad
    # ----------------------------------------------------
    # restore_popularity: Se autoprograma. No necesita config explícita.
            
    # ----------------------------------------------------
    # Actualización de Aplicación (Desacoplado)
    # ----------------------------------------------------
    update_app_footprint:
      frequency:
        type: exponential
        scale: 600
      impact:
        sigma_footprint:
          type: uniform
          low: 0.05
          high: 0.15
          
    update_app_network:
      frequency:
        type: exponential
        scale: 600
      impact:
        sigma_net:
          type: uniform
          low: 0.05
          high: 0.15
          
    update_app_topology:
      frequency:
        type: exponential
        scale: 600
      impact:
        p_topo:
          type: uniform
          low: 0.1
          high: 0.2
        l_min:
          type: integers
          low: 2
          high: 3
        l_max_global:
          type: integers
          low: 6
          high: 7
          
    # ----------------------------------------------------
    # Desplazamiento Geográfico de la Demanda
    # ----------------------------------------------------
    geo_demand_shift:
      frequency:
        type: exponential
        scale: 150
      impact:
        shift_type: "random_walk"
        shift_distance_distribution:
          type: uniform
          min: 0.05
          max: 0.15
```

---

## 4. Eventos de Infraestructura y Red (`graph`)

Se definen bajo `graph.actions`. Impactan sobre los nodos y los enlaces que forman el Cloud Continuum.

```yaml
graph:
  actions:
      
    # ----------------------------------------------------
    # Caída de nodo aleatorio
    # ----------------------------------------------------
    disable_random_node:
      frequency:
        type: exponential
        scale: 800
      impact:
        centrality: 0.05 
        distribution_to_revive_node:
          type: uniform
          min: 10.0
          max: 50.0
            
    # ----------------------------------------------------
    # Caída de nodo específico
    # ----------------------------------------------------
    disable_node:
      frequency:
        type: exponential
        scale: 1000
      impact:
        node_id: 12
        distribution_to_revive_node:
          type: normal
          mean: 30.0
          std: 5.0

    # ----------------------------------------------------
    # Recuperación de nodo
    # ----------------------------------------------------
    # revive_node: Se autoprograma. No necesita config explícita.
            
    # ----------------------------------------------------
    # Corte de enlace aleatorio
    # ----------------------------------------------------
    disable_random_edge:
      frequency:
        type: exponential
        scale: 750
      impact:
        distribution_to_revive_edge:
          type: uniform
          min: 5.0
          max: 20.0
            
    # ----------------------------------------------------
    # Corte de enlace específico
    # ----------------------------------------------------
    disable_edge:
      frequency:
        type: exponential
        scale: 900
      impact:
        edge: [2, 5]
        distribution_to_revive_edge:
          type: exponential
          scale: 25.0

    # ----------------------------------------------------
    # Recuperación de enlace
    # ----------------------------------------------------
    # revive_edge: Se autoprograma. No necesita config explícita.

    # ----------------------------------------------------
    # Degradación aleatoria de capacidad de nodo
    # ----------------------------------------------------
    degrade_random_node:
      frequency:
        type: exponential
        scale: 300
      impact:
        centrality: 0.05
        degradation_factor:
          type: beta
          alpha: 2.0
          beta: 2.0
        distribution_to_restore_node:
          type: lognormal
          mean: 2.5
          sigma: 0.5
            
    # ----------------------------------------------------
    # Degradación de capacidad de nodo específico
    # ----------------------------------------------------
    degrade_node:
      frequency:
        type: normal
        mean: 1500
        std: 50
      impact:
        node_id: 8
        degradation_factor:
          type: uniform
          min: 0.1
          max: 0.5
        distribution_to_restore_node:
          type: uniform
          min: 20
          max: 60

    # ----------------------------------------------------
    # Restaurar capacidad de nodo
    # ----------------------------------------------------
    # restore_node: Se autoprograma. No necesita config explícita.

    # ----------------------------------------------------
    # Congestión aleatoria de enlace
    # ----------------------------------------------------
    congest_random_edge:
      frequency:
        type: exponential
        scale: 200
      impact:
        bw_degradation_factor:
          type: beta
          alpha: 2.0
          beta: 5.0
        latency_multiplier:
          type: uniform
          min: 1.5
          max: 10.0
        distribution_to_clear_edge:
          type: lognormal
          mean: 1.0
          sigma: 0.3
            
    # ----------------------------------------------------
    # Congestión de enlace específico
    # ----------------------------------------------------
    congest_edge:
      frequency:
        type: normal
        mean: 800
        std: 20
      impact:
        edge: [10, 15]
        bw_degradation_factor:
          type: uniform
          min: 0.2
          max: 0.8
        latency_multiplier:
          type: uniform
          min: 2.0
          max: 5.0
        distribution_to_clear_edge:
          type: uniform
          min: 15
          max: 30

    # ----------------------------------------------------
    # Descongestión de enlace
    # ----------------------------------------------------
    # clear_edge: Se autoprograma. No necesita config explícita.
```
