# Configuración de Eventos de Desconexión Temporal de Usuarios

En entornos de *Far-Edge* (5G/6G, IoT), los usuarios a menudo pierden la conectividad momentáneamente debido a *hand-offs* o puntos ciegos de cobertura. Estos eventos (`suspend_user`) fuerzan al usuario a un estado latente, reduciendo su generación de tráfico a cero. Existen dos causas principales de desconexión.

## 1. Desconexión por Movimiento (Trigger Espacial)

Si un usuario se desplaza (`move_user`) más allá del alcance de las antenas, pierde la conexión automáticamente, entrando en estado `out_of_coverage`. Para habilitar esta mecánica, debes definir un radio máximo de cobertura.

### Configuración del Radio de Cobertura (`coverage_radius`)
Añade el parámetro en la sección `user.mobility`:

```yaml
user:
  mobility:
    model: manhattan
    speed: 0.01
    coverage_radius: 0.2    # Límite de distancia al nodo Edge más cercano
```

> **Efecto Interno:** Cada vez que el usuario se mueva, el simulador calculará la distancia Euclidiana respecto al nodo Edge más próximo. Si supera el `0.2`, automáticamente disparará un evento `suspend_user` interno (marcado como `out_of_coverage`). El usuario **NO recuperará la conexión** de forma mágica ni mediante eventos temporales. Su tráfico de red quedará silenciado. Sin embargo, el usuario seguirá experimentando eventos `move_user` subyacentes. Sólo recuperará su conexión (vía `reconnect_user`) si sus movimientos aleatorios vuelven a introducirlo dentro del radio de una antena Edge.

---

## 2. Desconexión Estocástica Aleatoria (`suspend_random_user`)

Además de la pérdida de señal por alejamiento, los usuarios pueden sufrir interferencias o fallos temporales del dispositivo (un *glitch*). Esto se modela inyectando eventos estocásticos independientes.

### Ejemplo de Configuración en Acciones
```yaml
user:
  actions:
    suspend_random_user:
      # 1. Frecuencia del Evento (Proceso de Poisson / Exponencial)
      frequency:
        type: exponential
        scale: 150               # Promedio de 150 segundos entre suspensiones
      impact:
          
        # 2. Duración de la Desconexión (Lognormal)
        distribution_to_resume_user:
          type: lognormal
          mean: 1.0              # Cuerpo para cortes cortos (hand-offs)
          sigma: 0.5             # Cola larga para cortes muy prolongados
```

> **Efecto Interno:** A diferencia del trigger espacial, un *glitch* pone al usuario en estado `suspended` y **SÍ programa un temporizador de reinicio** (`resume_user`) en el futuro usando la distribución lognormal especificada. Cuando este temporizador salta, el sistema comprobará la posición real del usuario. Si ha caminado fuera de cobertura mientras estaba apagado, transicionará a estado `out_of_coverage`. De lo contrario, recuperará su tráfico con normalidad.

---

## 3. Retención de Estado (Orquestación SFC)

Un punto vital de estos eventos es que la aplicación (SFC) que el usuario estuviera consumiendo **no se destruye**. La aplicación permanecerá residente en el último nodo en el que estuvo activo el usuario, pero no recibirá peticiones (`requestRatio = 0`).

Será responsabilidad de las reglas periódicas del optimizador (ILP solver) detectar cuánto tiempo de "tolerancia" (`Toleration Time`) está dispuesto a mantener la instancia consumiendo RAM inútilmente antes de decidir destruirla y requerir un reinicio en frío (*Cold Start*) cuando el usuario vuelva a tener cobertura.
