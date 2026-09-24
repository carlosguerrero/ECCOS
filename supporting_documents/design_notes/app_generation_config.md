# Generación de Aplicaciones: SFC y Popularidad

El simulador implementa un modelo de generación de aplicaciones basado en **Cadenas de Funciones de Servicio (SFC - *Service Function Chaining*)**, modelando recursos mediante distribuciones de cola larga, y una distribución de demanda basada en la **Ley de Zipf** con inyección **Geo-Espacial**.

Todo se parametriza mediante el bloque `app` dentro de `attributes` en el archivo de configuración `config_random.yaml`.

---

## 1. Service Function Chaining (SFC) y Perfiles de Recursos

A diferencia de las arquitecturas monolíticas, una aplicación aquí se genera como una cadena lineal de microservicios (de longitud $L$). Cada microservicio consume recursos que se muestrean de una distribución probabilística **Lognormal**. Esto captura la coexistencia de muchas funciones ligeras y unas pocas funciones extremadamente pesadas.

Se pueden definir múltiples "perfiles" (ej. *IoT*, *Video Inference*) para mezclar aplicaciones ligeras con pesadas. El simulador escoge un perfil basado en sus probabilidades ponderadas.

### Configuración YAML
```yaml
app:
  num_apps: 20
  sfc:
    length_range: [2, 6]            # Rango min y max de microservicios por cadena
    profiles:
      iot:                          # Perfil ligero (ej. telemetría)
        prob: 0.6                   # 60% de probabilidad de generarse
        cpu_lognorm: [0.1, 0.5]     # [Media, Desviación Típica] de la Lognormal para CPU
        ram_lognorm: [0.1, 0.5]     # [Media, Desviación Típica] de la Lognormal para RAM
      video:                        # Perfil pesado
        prob: 0.4                   # 40% de probabilidad
        cpu_lognorm: [2.0, 1.0]
        ram_lognorm: [3.0, 1.5]
```

---

## 2. Ley de Zipf y Geo-Popularidad

La popularidad de las aplicaciones no es aleatoria uniforme, sino que se rige por la **Ley de Zipf (Curva de Pareto)**, asegurando que unas pocas "Mega-Apps" acaparen el grueso de las peticiones de los usuarios.

Además, el simulador contempla el concepto de **Aplicaciones Locales**. Una proporción de las apps generadas se atan geográficamente a un lugar del mapa. Cuando un usuario va a emitir una petición, el simulador computa las distancias. Si el usuario se encuentra dentro del radio de influencia de un App Local, la probabilidad original de Zipf de esa aplicación sufre un **incremento exponencial** temporal (Geo-Popularidad), forzando peticiones localizadas.

### Configuración YAML
```yaml
app:
  popularity:
    model: "zipf"
    alpha: 1.2                      # Parámetro alpha de Zipf. Valores cercanos a 1.0 son típicos. Valores >1 empinan la curva.
    local_app_ratio: 0.3            # El 30% de las apps generadas serán de ámbito local. El 70% global.
    local_radius_influence: 0.15    # Radio euclídeo en el cual se inyecta la geo-popularidad a los usuarios.
```

---

## Nota de Arquitectura (Compatibilidad ILP)
Actualmente (Fase Transitoria), aunque la aplicación se genera internamente como un SFC de microservicios, el sistema inyecta un campo genérico `app['ram']` que consiste en la **suma agregada** de la memoria de todos los microservicios. Esto se hace para mantener compatibilidad con el optimizador ILP en su versión *Monolítica* hasta que se refactorice al modelo matemático *VNF-FGE*.
