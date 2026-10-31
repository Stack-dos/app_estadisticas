# 🏛️ Guía Teórica y Práctica de Arquitectura: App Estadistica

Bienvenidos a la guía definitiva de arquitectura para **App Estadistica**. Como Arquitecto de Software, mi objetivo aquí no es solo dictar reglas, sino explicar el **"porqué"** detrás de cada decisión.

Adoptamos **Clean Architecture** (Arquitectura Limpia) y **Arquitectura Hexagonal** (Puertos y Adaptadores). Estas no son simples modas, son estrategias de supervivencia para que nuestro software no se convierta en código espagueti inantenible a medida que crece.

A lo largo de este documento combinaremos rigor técnico con analogías cotidianas para dominar el diseño en Python.

---

## 1. Casos de Uso (CU): ¿Implementarlos con Clases o con Funciones?

### Concepto Teórico: ¿Qué es un Caso de Uso?
En Clean Architecture, un Caso de Uso (Capa de Aplicación) es el **orquestador del negocio**. Es el director de orquesta que recibe un requerimiento (ej. "Registrar un Jugador"), llama a la base de datos para ver si existe, le pide a la Entidad (Dominio) que valide las reglas, y finalmente le dice a la base de datos que guarde la información.
**Ojo:** El Caso de Uso orquesta, pero *no* contiene la lógica pura de negocio (esa vive en las Entidades del Dominio).

### Comparativa: Funciones vs. Clases
Al implementar un Caso de Uso, podemos usar una función suelta (`def registrar_jugador(...)`) o una Clase (con un método `.execute()` o `__call__`). **En StatsPro, utilizaremos Clases.** Veamos por qué.

#### La Inyección de Dependencias y el *Composition Root*
Imagina que un Caso de Uso es un carpintero. Para hacer una silla (ejecutar su acción), necesita un martillo y clavos (Repositorios y Servicios).

- **Enfoque Funcional (Malo para orquestación compleja):** Le entregas el martillo y los clavos al carpintero **cada vez** que le pides que haga una silla.
  ```python
  # Tienes que pasar las dependencias en CADA llamada
  registrar_jugador(datos, jugador_repo, email_service, logger)
  ```
- **Enfoque Orientado a Objetos (El estándar recomendado):** Al contratar al carpintero (instanciar la clase), le das su caja de herramientas. Luego, cada vez que le pides una silla, él ya tiene lo que necesita.
  ```python
  # Instancias una vez (Composition Root)
  caso_uso = RegistrarJugador(jugador_repo, email_service, logger)

  # Lo usas muchas veces, pasándole SOLO los datos de la acción
  caso_uso.execute(datos1)
  caso_uso.execute(datos2)
  ```

Pasar las dependencias por constructor en el inicio de la app (Inyección de Dependencias) nos permite configurar todo una sola vez. Cuando el controlador (Flet/CLI) necesita usar el CU, simplemente llama al método con los datos, sin tener que saber de qué base de datos viene la información.

#### Impacto en Testing
Usar clases hace que las pruebas unitarias sean un paseo por el parque. Puedes instanciar tu Caso de Uso inyectando *Mocks* o *Fakes* de tus repositorios, y luego probar múltiples escenarios (éxito, fallo) llamando a `.execute()` sin re-enviar los fakes cada vez.

#### 💻 Ejemplo en Código Python

```python
from typing import Protocol
from dataclasses import dataclass

# 1. El Puerto (Interfaz) - Vive en Dominio
class JugadorRepositorio(Protocol):
    def guardar(self, jugador: 'Jugador') -> None: ...
    def existe_email(self, email: str) -> bool: ...

# 2. El Caso de Uso - Vive en Aplicación
class RegistrarJugadorUseCase:
    # Inyección de dependencias por constructor
    def __init__(self, repositorio: JugadorRepositorio):
        self._repositorio = repositorio

    # Solo recibe los datos específicos de la acción
    def execute(self, input_dto: 'RegistrarJugadorInputDTO') -> 'JugadorOutputDTO':
        if self._repositorio.existe_email(input_dto.email):
            raise ValueError("El email ya está registrado")

        # Orquestación: Crea la entidad, llama al repo, devuelve DTO...
        nuevo_jugador = Jugador.crear(input_dto.nombre, input_dto.email)
        self._repositorio.guardar(nuevo_jugador)

        return JugadorOutputDTO(id=nuevo_jugador.id, nombre=nuevo_jugador.nombre)
```

---

## 2. DTOs (Data Transfer Objects) vs. Entidades de Dominio

### El Concepto Teórico
- **Entidad (Dominio):** Es el corazón del sistema. Tiene **identidad** (un ID que lo hace único aunque cambien sus datos), protege sus **invariantes** (reglas que nunca deben romperse, ej. "un jugador no puede tener edad negativa") y contiene **comportamiento** (métodos).
- **DTO (Aplicación):** Es un mensajero tonto. Un **objeto plano** sin lógica ni comportamiento. Su único trabajo es transportar datos de una capa a otra.

### La Diferencia Práctica (Python `@dataclass`)
En Python, solemos usar `@dataclass` para ambos. Entonces, ¿por qué no son lo mismo?
Una `@dataclass` en el dominio encapsula reglas y métodos que validan su integridad. Una `@dataclass` como DTO permite que sus atributos se mapeen y envíen libremente porque solo viajan en el cable (son inmutables por naturaleza transitiva, típicamente `frozen=True`).

### 🛂 La Analogía Cotidiana: El Pasaporte vs. El Formulario
Imagina que la **Entidad** es tu **Pasaporte Original**. Tiene sellos de seguridad, un número de identidad único, hologramas, y nadie puede tachar tu nombre con bolígrafo (tiene reglas de mutación, invariantes).
El **DTO** es una **fotocopia o un formulario impreso** que llenas para el hotel. No tiene valor legal por sí mismo, es solo para mover tus datos de tu bolsillo a la recepción. Si rompes el formulario (DTO), no pasa nada; si alteras el pasaporte (Entidad), vas a la cárcel.

### Peligros del Acoplamiento: ¿Qué pasa si la UI usa Entidades?
Si tu interfaz gráfica (Flet) o CLI importa directamente las Entidades del Dominio:
1. **Acoplamiento Mortal:** Si mañana la regla de negocio cambia y el "nombre" del Jugador se divide en "nombre" y "apellido", tendrás que modificar cada pantalla y botón de tu UI.
2. **Violación de Privacidad:** A veces la Entidad tiene datos sensibles (ej. `password_hash`). Si mandas la Entidad a la UI, podrías exponer datos que la pantalla no necesita, arriesgando fugas de información.

El DTO actúa como un escudo protector (contrato). Si la Entidad cambia, el Caso de Uso adapta la nueva Entidad al mismo DTO viejo, y la UI ni se entera.

#### 💻 Ejemplo en Código

```python
from dataclasses import dataclass
from uuid import UUID, uuid4

# --- EN CAPA DE DOMINIO (Entidad) ---
@dataclass
class Jugador:
    id: UUID
    nombre: str
    email: str
    _lesionado: bool = False # Estado interno protegido

    @classmethod
    def crear(cls, nombre: str, email: str) -> 'Jugador':
        if "@" not in email:
            raise ValueError("Email inválido") # Invariante
        return cls(id=uuid4(), nombre=nombre, email=email)

    def reportar_lesion(self):
        self._lesionado = True # Comportamiento

# --- EN CAPA DE APLICACIÓN (DTOs) ---
@dataclass(frozen=True)
class RegistrarJugadorInputDTO:
    nombre: str
    email: str
    # Datos crudos que vienen de la UI. Sin reglas de negocio.

@dataclass(frozen=True)
class JugadorOutputDTO:
    id: str
    nombre: str
    estado: str
    # Lo que la UI necesita ver, ocultando si "_lesionado" es booleano o no.
```

---

## 3. Catálogo y Mapa Completo de Casos de Uso

Para mantener orden, aquí está el mapa de Casos de Uso orquestadores. Cada uno representa una "acción" o "comando" que nuestro sistema puede realizar.

### 📍 Hito 1: Fundamentos (US-103, US-104, US-105)

| Caso de Uso (Clase) | Dependencias (Constructor) | Input DTO | Output DTO |
| :--- | :--- | :--- | :--- |
| `RegistrarJugadorUseCase` | `JugadorRepositorio` | `RegistrarJugadorInputDTO` | `JugadorOutputDTO` |
| `ActualizarPerfilJugadorUseCase` | `JugadorRepositorio` | `ActualizarJugadorInputDTO` | `JugadorOutputDTO` |
| `CrearEquipoUseCase` | `EquipoRepositorio` | `CrearEquipoInputDTO` | `EquipoOutputDTO` |
| `FicharJugadorEnEquipoUseCase` | `EquipoRepo`, `JugadorRepo` | `FicharJugadorInputDTO` | `bool` (Éxito) |
| `IniciarSesionUseCase` | `UsuarioRepo`, `AuthService` | `LoginInputDTO` | `TokenSessionDTO` |
| `CargarPartidoAtomicoUseCase` | `PartidoRepo`, `EstadisticaRepo` | `CargarPartidoInputDTO` | `ResumenPartidoOutputDTO` |

### 🚀 Hitos Futuros (Hito 2 y 3)

A medida que el proyecto crezca, el diseño orientado a Casos de Uso brilla, porque añadir una nueva funcionalidad es simplemente agregar una nueva clase en la capa de Aplicación, sin tocar las demás.

**Hito 2: Ingesta y Motor Analítico**
*   `ImportarPlanillaPartidoUseCase`: (Dep: parsers de Excel y PDF, `CargarPartidoUseCase`) -> Lee una planilla de partido de Gesdeportiva y la transforma en entidades del dominio.
*   `CalcularMetricasAvanzadasUseCase`: (Dep: `EstadisticasRepo`, `MotorAnaliticoService`) -> Recalcula PER, TS%, USG% tras un partido.
*   `SincronizarDatosNubeUseCase`: (Dep: `NubeSyncPort`) -> Sube el SQLite local a un almacenamiento en la nube.

**Hito 3: Reportes, Líderes y Scouting**
*   `GenerarReportePDFPartidoUseCase`: (Dep: `PartidoRepo`, `PDFGeneratorService`) -> Produce el PDF de cierre de juego.
*   `ObtenerTablaLideresUseCase`: (Dep: `EstadisticasRepo`) -> (Consulta pura / Query) Retorna los top 5 anotadores.
*   `GenerarScoutingRivalUseCase`: (Dep: `EquipoRepo`, `EstadisticasRepo`, `ScoutingService`) -> Agrega tendencias de tiro de un equipo rival.

---

## 4. Interfaces de Casos de Uso: ¿En la Capa de Dominio?

### La Respuesta Definitiva
**NO.** Las interfaces (Protocols/ABCs) de los Casos de Uso **jamás** deben existir en la capa de Dominio.

### La Regla de Dependencias (El flujo unidireccional)
En Clean Architecture, la regla de oro es que **las dependencias siempre apuntan hacia adentro**:
`Infraestructura (UI/BD) ➔ Aplicación (Casos de Uso) ➔ Dominio (Entidades)`

El Dominio es el centro del universo. El Dominio sabe qué es un "Tiro Libre" o un "Jugador", pero **no tiene idea** de que existe un botón en una pantalla, ni sabe que existe un "Caso de Uso" que orquesta cosas, ni le importa si los datos se guardan en SQLite o en un archivo de texto.

Si pones una interfaz como `IRegistrarJugadorUseCase` dentro de la carpeta `src/dominio/`, estás obligando al Dominio a saber sobre la existencia de la orquestación (Aplicación), violando la regla de dependencias.

### Entonces, ¿Qué "Puertos" (Interfaces) SÍ van en el Dominio?
El Dominio necesita hablar con el mundo exterior (ej. guardar en la BD), pero no puede depender de SQL. Para resolverlo, el Dominio define **Interfaces (Puertos de Salida)**.
Es como si el Dominio dijera: *"No sé quién diablos va a guardar esto, pero el que lo haga, tiene que cumplir este contrato estricto"*.

**Interfaces que SÍ pertenecen a `src/dominio/puertos/` o `src/dominio/repositorios/`:**
*   `JugadorRepositorio` (Contrato para guardar/buscar jugadores).
*   `PartidoRepositorio`.
*   `EmailSenderService` (Contrato para enviar correos, si el dominio lo exigiera para alertas críticas).

**¿Dónde van las interfaces de los Casos de Uso?**
Si tu interfaz gráfica (Flet) necesita un contrato para acoplarse a los Casos de Uso sin depender de la implementación concreta (por ejemplo, para mockear la UI en tests), esas interfaces (ej. `IRegistrarJugadorUseCase`) pertenecen a la **Capa de Aplicación** (`src/aplicacion/interfaces/`). Esto es porque Flet (Infraestructura) apunta hacia Aplicación, cumpliendo la regla de dependencias de afuera hacia adentro.

---

## 5. Cómo quedó aplicado en este proyecto

Esta guía explica los conceptos. Los ejemplos de arriba usan nombres genéricos (`execute`, `email`, `UUID`, `Protocol`) para enseñar la idea;
lo que sigue es el mapa entre el concepto y lo que **realmente existe** en el repositorio.

| Concepto de la guía | En este proyecto |
| :--- | :--- |
| Caso de Uso como **clase** con un método | Clases en `src/aplicacion/casos_uso/`; el método se llama **`ejecutar()`** (no `execute`) |
| Inyección de dependencias por constructor | `RegistrarJugadorUseCase(jugador_repo)`, `InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club)` |
| *Composition Root* | Hoy cada **comando de la CLI** arma el repositorio real y se lo pasa al caso de uso (ver [04-arquitectura.md](04-arquitectura.md), sección 10); desde la US-105 lo hace `ui/flet/app.py` una sola vez al arrancar la GUI |
| Puerto de salida (interfaz en el Dominio) | Clases `ABC` en `src/dominio/repositorios/` (`JugadorRepositorio`, `ClubRepositorio`, ...), no `Protocol` (ver [07-protocolos.md](07-protocolos.md)) |
| Entidad con invariantes | `dataclass` en `src/dominio/entidades/` que valida en `__post_init__` (tipos, rangos, reglas del boxscore) |
| DTO de entrada / salida | `dataclass` simples en `src/aplicacion/dtos/` (`CrearJugadorDTO` entra, `JugadorDTO` sale). **No** son `frozen=True` |
| Excepciones de negocio | `src/dominio/exceptions.py`, todas hijas de `ErrorDeDominio` |
| Regla de dependencias hacia adentro | `src/utils.py` es **puro** (no importa `infraestructura`) justamente para que `aplicacion` pueda usarlo sin violarla |

**Dos decisiones que conviene conocer:**

- **Los casos de uso devuelven DTOs, no entidades** (con una excepción hoy: `VincularJugadorAClubUseCase` devuelve la entidad `JugadorClub`). Así la interfaz (hoy la CLI, desde la US-105 la GUI) no queda acoplada a la forma interna del dominio.
- **Las entidades declaran su ID como `int | None`** (antes de guardarse no lo tienen) pero los DTOs de salida exigen `int`. La función `id_persistido()` de `src/utils.py` deja esa garantía explícita en un solo lugar.

El catálogo real de casos de uso (qué recibe y qué devuelve cada uno, paso a paso) está en [03-casos-de-uso.md](03-casos-de-uso.md). La tabla de la sección 3 de esta guía
es el **mapa de diseño original** del proyecto y sus nombres (`CrearEquipoUseCase`, `FicharJugadorEnEquipoUseCase`, ...) no coinciden uno a uno con los implementados.

---
*Documento redactado para el equipo de App Estadistica. La excelencia técnica no se logra copiando código, sino entendiendo los fundamentos.*
