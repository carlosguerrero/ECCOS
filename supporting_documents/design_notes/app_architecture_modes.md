# Modos de Arquitectura de Aplicaciones

El simulador permite generar aplicaciones modelando su topología de dos formas distintas. Esta configuración rige globalmente cómo el Optimizador (ILP) percibe la carga computacional en el clúster.

Esta opción se configura en la clave `attributes -> app -> architecture` de tu fichero `config_random.yaml`.

---

## Modos Disponibles

### 1. Modo `microservice` (Por defecto)
Las aplicaciones se generan siguiendo el modelo de cadena de servicios o **Service Function Chaining (SFC)**. 
- Cada aplicación se compone de múltiples dependencias o microservicios interconectados (un grafo lineal por defecto de 2 a 6 componentes).
- **Ventajas**: Alta fidelidad con las arquitecturas *Cloud Native*. El solver ILP calculará la latencia de red exacta entre cada microservicio y evaluará variables de enrutamiento.
- **Desventajas**: Requiere exponenciales variables matemáticas. El tiempo de resolución en problemas NP-difíciles puede tomar varios minutos en infraestructuras densas (más de 50 nodos) para unas pocas decenas de aplicaciones.

### 2. Modo `monolithic`
La aplicación condensa todas sus responsabilidades de cómputo en un único bloque de despliegue.
- Las lógicas de generación de cadenas se comprimen bajo el capó: el simulador calcula las características SFC originalmente, pero suma matemáticamente todas sus CPUs y Memorias RAM en un único gran microservicio con id `..._ms_mono`.
- **Ventajas**: Resolución ultrarrápida del ILP, puesto que omite la creación de miles de variables binarias de enlaces internos. Ideal para pruebas en etapa de configuración, *dry-runs*, o para datasets que buscan predecir colisiones de recursos físicos sin importar la latencia inter-microservicios.
- **Nota sobre el rendimiento**: Aún en modo monolítico, el problema algorítmico sigue siendo un "Bin Packing" NP-Hard. Es **altamente recomendable** definir un umbral de tolerancia o *gap* en el solver para evitar que pase 60 segundos completos evaluando simetrías idénticas en el árbol de búsqueda. Con `gapRel: 0.05` el resultado será casi instantáneo.
- **Desventajas**: Se asume que no existe retardo de propagación local entre componentes, pues todos viven obligatoriamente en el mismo contenedor físico (Mismo nodo de red).

---

## Ejemplo de Configuración en el YAML

```yaml
setup:
  # Opcional pero recomendado: Limitar el tiempo y permitir gap relativo
  # para que el solucionador ILP sea instantáneo en modos como 'monolithic'.
  ilp_solver:
    timeLimit: 60
    gapRel: 0.05  # Detener el solver si encuentra una solución a menos de 5% del óptimo ideal

app:
  num_apps: 20
  saturation_percentage: 15.0
    
  # -------------------------------------------------------------------------
  # OPCIÓN 1: 'microservice' 
  # Múltiples microservicios por App con routing interno (Modo Completo / NP-Hard)
  # 
  # OPCIÓN 2: 'monolithic' 
  # 1 Microservicio por App con la suma de recursos (Modo Rápido / Emplazamiento 1:1)
  # -------------------------------------------------------------------------
  architecture: monolithic  

  num_new_users:
    type: integers
    low: 1
    high: 6
  sfc:
    length_range: [2, 6]  # Ignorado si architecture == monolithic
    ...
```

### Mutaciones Topológicas y Eventos
*Nota de Desarrollo:* Si tu simulación opera en modo `monolithic`, el evento de simulación `update_app_topology` (que se encarga de insertar o borrar microservicios de forma estocástica) será ignorado, garantizando que una aplicación monolítica siga siendo de 1 solo microservicio durante todo su ciclo de vida. Los eventos `update_app_footprint` y `update_app_network` seguirán actuando de forma normal para alterar temporalmente los requisitos de red y computación.
