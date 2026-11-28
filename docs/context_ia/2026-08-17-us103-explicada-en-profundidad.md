# US-103 explicada en profundidad — Gestión de Entidades (Casos de Uso Administrativos)

> Documento de referencia conceptual, no un registro de sesión de trabajo. Responde en detalle
> todas las preguntas que surgieron al leer la US-103 antes de empezar a implementarla. Está
> pensado para consultarse mientras la construyen, no solo para leerse una vez.
>
> **Estado verificado hoy (2026-08-17), para que el documento arranque con la foto real:**
>
> - Las 12 entidades de dominio (`Usuario`, `Club`, `UsuarioClub`, `Jugador`, `JugadorClub`,
>   `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`, `Partido`,
>   `JugadorPartido`) **ya tienen `__post_init__` con validación de tipos** (`isinstance` +
>   `TypeError`) — esto es más de lo que el propio texto de la US-103 asumía como pendiente. Buen
>   avance.
> - `src/dominio/exceptions.py` **ya existe**, con `ErrorDeDominio` (clase base) y
>   `DNIDuplicadoError`. Todavía faltan las otras 4 que pide la US (ver sección 5).
> - `src/aplicacion/` **todavía no existe** — es lo que arranca esta US.

---

## 1. Qué pide la US-103, completa

**Objetivo funcional:** implementar la lógica de negocio pura (casos de uso) y la interfaz de
usuario por comandos (CLI) para gestionar el ciclo de vida de jugadores, clubes, competencias e
inscripciones — validando reglas deportivas reales, no solo tipos de datos.

**Narrativa:** como administrador, quiero casos de uso con lógica de negocio validada para
gestionar jugadores, sus afiliaciones a clubes, y la estructura de competencias.

**Las tres capas que toca, resumidas:**

| Capa            | Qué agrega esta US                                    |
| --------------- | ----------------------------------------------------- |
| Dominio         | Las excepciones de negocio que faltan (sección 5)     |
| Aplicación      | **Se crea por primera vez.** 9 casos de uso + 6 DTOs  |
| Infraestructura | 6 comandos CLI nuevos, usando `argparse` + `tabulate` |

**Los 5 Criterios de Aceptación** (los explico en detalle en la sección 12, acá solo el resumen):

1. Independencia de dominio (ya se cumple)
2. Inyección de dependencias en los casos de uso
3. Validación fail-fast (cortar rápido, sin traceback al usuario)
4. Formato de salida uniforme en tablas
5. Atomicidad en operaciones compuestas (ej. inscripción + lista de buena fe)

**Reglas de negocio que valida esta US específicamente:**

- DNI de jugador numérico y único.
- Un jugador no puede tener dos vínculos activos (sin `fecha_hasta`) al mismo tiempo, ni
  duplicado con el mismo club.
- Porcentajes/totales estadísticos se validan antes de persistir.

---

## 2. Qué conceptos entran en juego acá (mapa general)

Hasta ahora (US-101/102) trabajaron sobre todo con dos patrones: **Repository Pattern**
(interfaces en dominio, implementación SQLite en infraestructura) y **Dependency Injection**
básica (pasar la conexión por constructor). La US-103 suma tres conceptos nuevos, todos
relacionados entre sí:

- **Use Case Pattern** (casos de uso): cómo se organiza la lógica de negocio real, la capa que
  faltaba entre "tengo datos guardados" (repositorios) y "el usuario pidió algo" (CLI).
- **DTO Pattern** (Data Transfer Objects): cómo cruzan datos las fronteras entre capas sin que
  cada capa dependa de la forma interna de la otra.
- **Command Pattern**: cómo se organiza una CLI con muchos subcomandos sin un `if/elif` gigante.

Todo el resto de la sección responde preguntas puntuales sobre estos tres conceptos.

---

## 3. Las entidades que pide la US — ¿son las dataclasses que ya tenemos?

**Sí, son las mismas.** La lista que menciona la US-103 (`Usuario`, `Club`, `Jugador`,
`JugadorClub`, `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`,
`Partido`, `EstadisticaJugador`) ya existe completa en `src/dominio/entidades/` — la única
diferencia es de **nombre**: la US habla de `EstadisticaJugador`, en el código real se llama
`JugadorPartido` (viven en `partido.py`). No hay que crear ninguna entidad nueva para esta US.

Lo que sí es distinto de como lo describe el PRD original es la **organización en archivos**: el
PRD imagina un archivo por entidad; el código real agrupa entidades relacionadas en un mismo
archivo (`competencia.py` tiene 5 dataclasses adentro: `Competencia`, `Categoria`, `Inscripcion`,
`ListaBuenaFe`, `JugadorListaBuenaFe`). Es una decisión válida, ya la tienen tomada — no hace
falta separarlas para esta US.

---

## 4. ¿Hay alguna otra validación que tengamos que hacer en las entidades que ya tenemos?

Acá hay una distinción importante entre **dos tipos de validación** que conviene tener clara,
porque cada una vive en un lugar distinto:

### 4.1 Validación de tipo — ya está hecha ✅

Es la que confirmamos hoy: cada entidad valida en `__post_init__` que sus campos sean del tipo
correcto (`isinstance(self.nombre, str)`, etc.), lanzando `TypeError` si no. Esto ya está en las
12 entidades. No hace falta agregar nada acá para esta US.

### 4.2 Validación de forma/coherencia interna — falta, y sí aplica a esta US

Es distinta de la de tipo: no pregunta "¿es un `int`?", pregunta "¿tiene sentido este dato en
relación a otro campo del mismo objeto?". La propia US-103 la menciona explícitamente como
ejemplo: _"tiros convertidos ≤ lanzados, valores no negativos"_. Hoy `JugadorPartido` valida que
`idJugador`/`idPartido`/`idClub` sean `int` (tipo), pero **no** valida que, por ejemplo,
`t2c <= t2l` (coherencia) — esa regla hoy solo existe como `CHECK` en `schema.sql`, no en Python.
Sería un buen `__post_init__` a sumar, con el mismo estilo que ya tienen:

```python
if self.t2c > self.t2l:
    raise ValueError(f"t2c ({self.t2c}) no puede ser mayor que t2l ({self.t2l})")
if self.t3c > self.t3l:
    raise ValueError(f"t3c ({self.t3c}) no puede ser mayor que t3l ({self.t3l})")
if self.t1c > self.t1l:
    raise ValueError(f"t1c ({self.t1c}) no puede ser mayor que t1l ({self.t1l})")
```

(Usé `ValueError`, no `TypeError`, a propósito — el tipo del dato está bien, `int` es `int`; lo
que está mal es el _valor_ en relación a otro campo. Es la distinción estándar de Python entre
"tipo incorrecto" vs. "valor incorrecto para ese tipo".)

### 4.3 Validación de negocio contra la base — NO va en la entidad, va en el caso de uso

Esta es la tercera categoría, y es importante que quede clara para no intentar meterla en
`__post_init__` por error: **"¿el DNI ya existe en la base?"** o **"¿el jugador ya tiene un
vínculo activo con este club?"** no se pueden validar dentro de la dataclass, porque la entidad
no tiene acceso a la base de datos (ni debería tenerlo — rompería la regla de que `dominio/` no
depende de nada externo). Esta validación vive en los **casos de uso** (sección 6), que sí tienen
acceso al repositorio.

---

## 5. ¿Hay más excepciones que tengamos que crear?

Sí. Hoy `dominio/exceptions.py` tiene solo 2:

```python
class ErrorDeDominio(Exception):
    pass

class DNIDuplicadoError(ErrorDeDominio):
    pass
```

La US-103 pide, además, estas 4 (todas deberían heredar de `ErrorDeDominio`, siguiendo el mismo
patrón que ya empezaron):

| Excepción                     | Cuándo se usa                                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `ClubNoEncontradoError`       | Se intenta operar sobre un `idClub` que no existe                                                                |
| `UsuarioNoEncontradoError`    | Login o búsqueda de usuario que no existe (más relevante en US-104, pero ya se puede dejar creada)               |
| `CredencialesInvalidasError`  | Login con contraseña incorrecta (más relevante en US-104)                                                        |
| `VinculoActivoExistenteError` | Se intenta vincular un jugador a un club cuando ya tiene un vínculo activo (la regla de negocio de la sección 1) |

```python
class ClubNoEncontradoError(ErrorDeDominio):
    pass

class UsuarioNoEncontradoError(ErrorDeDominio):
    pass

class CredencialesInvalidasError(ErrorDeDominio):
    pass

class VinculoActivoExistenteError(ErrorDeDominio):
    pass
```

**¿Por qué excepciones propias y no `ValueError`/`Exception` genérica?** Porque en la capa de CLI
van a necesitar distinguir "esto es un error de negocio esperable, mostrale un mensaje lindo al
usuario" de "esto es un bug real, mostrá el traceback" (ver AC3, sección 12.3). Con excepciones
propias, la CLI puede hacer `except ErrorDeDominio as e:` una sola vez y capturar **todas** las
de negocio (porque heredan de la base común), sin necesidad de listar cada una.

---

## 6. Los casos de uso — ¿qué son, clases o funciones, necesitan interfaz?

### 6.1 Qué es un caso de uso

Es la traducción literal de **una acción concreta que el usuario puede pedir** ("registrar un
jugador", "vincular un jugador a un club") a código. Es el lugar donde vive la lógica de negocio
real — hasta ahora esa lógica no existía en ningún lado del proyecto: los repositorios solo saben
guardar/leer, no saben _cuándo_ está bien guardar algo. Un caso de uso:

1. Recibe los datos de entrada (un DTO, sección 9).
2. Aplica las reglas de negocio (¿el DNI está duplicado? ¿el jugador ya tiene vínculo activo?).
3. Si algo no cumple una regla, lanza una excepción de dominio (sección 5).
4. Si todo está bien, llama al repositorio correspondiente para persistir/leer.
5. Devuelve un DTO de salida.

### 6.2 ¿Son clases o funciones?

**Clases**, por convención de este estilo de arquitectura (y es lo que la propia US-103 da por
sentado en el AC2: _"todos los casos de uso reciben sus repositorios vía **constructor**"_ — eso
ya implica una clase, una función no tiene constructor). El patrón estándar:

```python
class RegistrarJugadorUseCase:
    def __init__(self, jugador_repo: JugadorRepositorio):
        self.jugador_repo = jugador_repo

    def execute(self, dto: CrearJugadorDTO) -> JugadorDTO:
        if self.jugador_repo.buscar_por_dni(dto.dni) is not None:
            raise DNIDuplicadoError(f"Ya existe un jugador con DNI {dto.dni}")

        jugador = Jugador(
            nombre=dto.nombre,
            apellido=dto.apellido,
            dni=dto.dni,
            anioNacimiento=dto.anio_nacimiento,
        )
        jugador_guardado = self.jugador_repo.guardar(jugador)

        return JugadorDTO(
            id=jugador_guardado.idJugador,
            nombre_completo=f"{jugador_guardado.nombre} {jugador_guardado.apellido}",
            dni=jugador_guardado.dni,
        )
```

**Por qué clase y no función:** una función podría, en teoría, hacer lo mismo si le pasás el
repositorio como parámetro cada vez (`registrar_jugador(dto, jugador_repo)`) — pero la clase da
tres cosas que la función suelta no da tan prolijo:

- **Un solo lugar para "armar" las dependencias una vez** (constructor) y reusar la misma
  instancia para múltiples llamadas (`execute()`), en vez de pasar el repositorio en cada
  invocación.
- **Un nombre de tipo propio** (`RegistrarJugadorUseCase`) que se puede usar en type hints,
  loguear, inspeccionar — más difícil de lograr con una función suelta.
- Es el patrón que **ya está implícito en el propio AC2** de la US, así que conviene no pelearse
  con el enunciado.

### 6.3 Si son clases, ¿hace falta armarles una interfaz en el dominio?

**No.** Y esto es importante para no sobre-diseñar: las interfaces (`ABC` con `@abstractmethod`)
sirven cuando **puede haber más de una implementación intercambiable** de la misma idea — por eso
`JugadorRepositorio` tiene interfaz: hoy la implementa `SqliteJugadorRepositorio`, pero mañana
podría existir `PostgresJugadorRepositorio` o `JugadorRepositorioFake` (para tests), y todos
cumplirían el mismo contrato.

Un caso de uso **no tiene ese problema**: `RegistrarJugadorUseCase` no tiene "múltiples
implementaciones" — hay una sola forma de registrar un jugador. No hay nada que intercambiar. Por
eso los casos de uso son clases concretas directas en `src/aplicacion/use_cases/`, sin pasar por
`ABC` ni por el dominio. La única razón por la que SÍ necesitan una interfaz es la que ya tienen
resuelta: el **repositorio que reciben por constructor** (`JugadorRepositorio`, la interfaz) — eso
es lo que les permite testear el caso de uso con un repositorio falso (mock) sin tocar SQLite.

---

## 7. Qué casos de uso hay que crear (los 9 de esta US)

| Caso de uso                         | Qué hace                                                                  | Repositorio(s) que usa                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `RegistrarJugadorUseCase`           | Valida DNI numérico y no duplicado, crea `Jugador`                        | `JugadorRepositorio`                                                                      |
| `CrearClubUseCase`                  | Crea un `Club` nuevo                                                      | `ClubRepositorio`                                                                         |
| `VincularJugadorAClubUseCase`       | Verifica que no haya vínculo activo duplicado, crea `JugadorClub`         | `JugadorRepositorio`                                                                      |
| `CrearCompetenciaUseCase`           | Crea una `Competencia`                                                    | `CompetenciaRepositorio`                                                                  |
| `InscribirClubEnCompetenciaUseCase` | Crea `Inscripcion` + genera automáticamente su `ListaBuenaFe` vacía (1:1) | `CompetenciaRepositorio`                                                                  |
| `ListarClubesUsuarioUseCase`        | Lista los clubes de un usuario                                            | `ClubRepositorio`                                                                         |
| `ListarJugadoresClubUseCase`        | Lista los jugadores de un club                                            | `JugadorRepositorio`                                                                      |
| `ListarPartidosPorClubUseCase`      | Lista partidos de un club (via `v_partidos_resumen`)                      | `JuegoRepositorio`/`PartidoRepositorio`                                                   |
| `CambiarClubActivoUseCase`          | Cambia el club activo en la sesión                                        | (depende de `SessionManager`, que es de US-104 — puede quedar como stub simple por ahora) |

**Bloqueo real a tener en cuenta:** `InscribirClubEnCompetenciaUseCase` depende de que
`SqliteCompetenciaRepositorio.obtener_lista_por_inscripcion` esté corregido (hoy devuelve una
`list`, cuando la relación real es 1:1 y debería devolver un objeto único o `None`) — si arman
este caso de uso contra el comportamiento actual, van a terminar tratando como "lista de listas"
algo que conceptualmente es un solo objeto. Conviene corregir el repositorio primero.

---

## 8. ¿Los casos de uso crecen a medida que pasan las US? — Sí, exactamente así

`src/aplicacion/use_cases/` es una carpeta que se sigue llenando **durante todo el proyecto**, no
solo en esta US. Cada nueva historia de usuario que agrega una acción, agrega (típicamente) un
caso de uso nuevo. Ejemplos ya visibles más adelante en el propio plan:

- **US-104** (la siguiente): suma `RegistrarEntrenadorUseCase`, `LoginLocalUseCase`.
- **US-105**: suma `CargarPartidoUseCase`.
- **Hito 2** (US-201/202/203): suma `ImportarExcelUseCase`, `CalcularEstadisticasAvanzadasUseCase`,
  `GenerarTablaComparativaUseCase`, `CalcularEstadisticasPartidoUseCase`.
- **Hito 3**: `ObtenerLideresTemporadaUseCase`, `GenerarGraficoRendimientoUseCase`,
  `ExportarReporteUseCase`, `GenerarScoutingRivalUseCase`.

Es el patrón esperado — la carpeta nunca "se cierra", crece 1:1 con las funcionalidades que se
van sumando en cada hito.

---

## 9. DTOs vs. las dataclasses de dominio que ya tenemos — ¿cuál es la diferencia?

### 9.1 ¿Qué es un DTO?

**Data Transfer Object**: una clase cuya única responsabilidad es **transportar datos entre
capas**, sin lógica de negocio adentro (sin `__post_init__` con reglas, sin métodos que calculen
nada relevante para el dominio). Técnicamente, en Python, se implementa **con el mismo mecanismo**
que las entidades de dominio — también es un `@dataclass`. La diferencia no es de sintaxis, es de
**rol arquitectónico**.

### 9.2 La diferencia real, con ejemplo concreto

- **`Jugador`** (entidad de dominio): representa el concepto de negocio "jugador" tal como lo
  entiende el sistema — tiene las reglas de validación de tipo (`__post_init__`), y en el futuro
  podría tener métodos de negocio (`calcular_edad()`). Vive en `dominio/entidades/`. Nunca sale
  de la capa de aplicación hacia afuera.
- **`JugadorDTO`** (DTO de salida): representa **lo que la CLI necesita mostrar** — capaz incluye
  cosas que `Jugador` ni sabe (ej. el nombre del club activo, que sale de un `JOIN`, no de la
  tabla `jugador`), y capaz **no** incluye cosas que `Jugador` sí tiene (por ejemplo, si mañana
  `Jugador` guardara un campo interno sensible, el DTO de salida podría decidir no exponerlo).
- **`CrearJugadorDTO`** (DTO de entrada): representa **lo que el comando CLI recibió del
  usuario** — campos sueltos y planos (`nombre`, `apellido`, `dni`, `anio_nacimiento`), sin
  ningún `idJugador` (todavía no existe, porque el jugador no se guardó).

```python
@dataclass
class CrearJugadorDTO:      # entra a RegistrarJugadorUseCase.execute()
    nombre: str
    apellido: str
    dni: int
    anio_nacimiento: int

@dataclass
class JugadorDTO:            # sale de RegistrarJugadorUseCase.execute()
    id: int
    nombre_completo: str     # nombre + apellido combinados, la CLI no debería armar este string
    dni: int
```

### 9.3 ¿Por qué no usar `Jugador` directamente en la CLI, ya que existe?

Porque eso **acoplaría** la CLI a la forma exacta del dominio: si mañana `Jugador` cambia un campo
interno (ej. separan `nombre`/`apellido` en un objeto `NombreCompleto`), todo el código de la CLI
que construya tablas con `jugador.nombre_completo` se rompe. Con un DTO de por medio, el dominio
puede evolucionar libremente mientras el DTO (el "contrato" hacia afuera) se mantenga igual — y
viceversa, la CLI puede pedir un formato de visualización distinto sin tocar el dominio.

**Regla práctica:** las entidades de dominio (`Jugador`, `Club`, etc.) nunca deberían cruzar el
límite entre `aplicacion/` e `infraestructura/ui/`. Lo que cruza esa frontera son siempre DTOs.

---

## 10. Los comandos CLI que hay que crear

Son 6 archivos nuevos en `src/infraestructura/ui/cli/commands/`:

| Archivo          | Subcomando(s) que implementa     |
| ---------------- | -------------------------------- |
| `player_add.py`  | `stats player add`               |
| `club_add.py`    | `stats club add`                 |
| `player_link.py` | `stats player link <id_jugador>` |
| `game_list.py`   | `stats game list`                |
| `player_list.py` | `stats player list`              |
| `club_list.py`   | `stats club list`                |

Cada uno de estos archivos es, en esencia, un traductor en dos direcciones: toma lo que el
usuario tipeó en la terminal → arma el DTO de entrada correspondiente → instancia y ejecuta el
caso de uso → toma el DTO de salida → lo formatea en una tabla con `tabulate` (AC4, sección 12.4).
El comando **nunca** debería tener lógica de negocio adentro — si un comando empieza a validar
reglas por su cuenta, esa lógica se está yendo al lugar equivocado (debería estar en el caso de
uso).

---

## 11. Qué es el Command Pattern con `argparse`

**Command Pattern**, en términos generales (más allá de Python): es un patrón de diseño que
encapsula "una acción a ejecutar" como un objeto/función independiente, en vez de tener un único
bloque gigante de código que decide qué hacer según el input (`if accion == "add": ... elif
accion == "list": ...`). La ventaja: agregar una acción nueva significa **agregar un archivo
nuevo**, no **editar un archivo existente y gigante**.

`argparse` (de la librería estándar de Python) ya tiene soporte nativo para esto con
**subparsers** — cada subcomando (`player add`, `club list`, etc.) se registra como una unidad
independiente, con su propia función "handler" que se ejecuta cuando se elige ese subcomando:

```python
# main_cli.py (composition root)
import argparse
from infraestructura.ui.cli.commands import player_add, club_add, player_list

def construir_parser():
    parser = argparse.ArgumentParser(prog="stats")
    subparsers = parser.add_subparsers(dest="comando")

    parser_player = subparsers.add_parser("player")
    player_subparsers = parser_player.add_subparsers(dest="subcomando")

    parser_player_add = player_subparsers.add_parser("add")
    parser_player_add.set_defaults(func=player_add.ejecutar)

    parser_club = subparsers.add_parser("club")
    club_subparsers = parser_club.add_subparsers(dest="subcomando")

    parser_club_list = club_subparsers.add_parser("list")
    parser_club_list.set_defaults(func=club_list.ejecutar)

    return parser

def main():
    parser = construir_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)   # ← acá está la magia: cada subcomando "sabe" qué función lo maneja
    else:
        parser.print_help()
```

Cada `commands/*.py` expone una función `ejecutar(args)` (o una clase con `__call__`, si
prefieren) que arma el DTO, llama al caso de uso, y formatea la salida. `main_cli.py` (el
composition root, ya mencionado en la arquitectura de la sección 4 del plan) solo se encarga de
**registrar** cada comando — nunca de decidir qué hace cada uno. Eso es lo que hace que agregar
`stats competition add` el día de mañana sea "un archivo nuevo + una línea de registro", no una
reescritura de `main_cli.py`.

---

## 12. Los 5 Criterios de Aceptación, explicados uno por uno

### 12.1 AC1 — Independencia de Dominio

_"Los archivos en `dominio/entidades/` no importan librerías externas."_ Ya se cumple — las
entidades solo importan `dataclasses`, nada de `sqlite3`, `pandas`, ni siquiera
`infraestructura.logger` (ya lo discutimos: el dominio no puede depender de infraestructura, ni
para loguear). No hay nada que hacer para este AC en esta US, solo no romperlo al agregar
validaciones nuevas (sección 4.2).

### 12.2 AC2 — Inyección de Dependencias

_"Todos los casos de uso reciben sus repositorios vía constructor, usando las interfaces."_ Ya lo
mostramos en el ejemplo de la sección 6.2: `RegistrarJugadorUseCase.__init__(self, jugador_repo:
JugadorRepositorio)`. **Inyección de dependencias (DI)** quiere decir: la clase **no crea** sus
propias dependencias (no hace `self.jugador_repo = SqliteJugadorRepositorio(...)` adentro del
caso de uso) — las **recibe ya armadas** desde afuera. ¿Por qué importa? Porque así, en un test,
le podés pasar un repositorio falso (un objeto de prueba que simula la base) en vez de una
conexión SQLite real:

```python
class JugadorRepositorioFalso(JugadorRepositorio):
    def buscar_por_dni(self, dni_jugador):
        return None  # simula "no existe" sin tocar ninguna base real
    # ... resto de los métodos abstractos, con comportamiento controlado

def test_registrar_jugador_dni_no_duplicado():
    repo_falso = JugadorRepositorioFalso()
    caso_de_uso = RegistrarJugadorUseCase(jugador_repo=repo_falso)
    resultado = caso_de_uso.execute(CrearJugadorDTO(nombre="Juan", apellido="Pérez", dni=123, anio_nacimiento=2000))
    assert resultado.dni == 123
```

Sin DI, cada test que quisiera probar `RegistrarJugadorUseCase` necesitaría una base SQLite real
armada — con DI, es una prueba instantánea, sin tocar disco ni memoria de SQLite. ¿Quién es "el
que arma todo desde afuera"? El composition root (`main_cli.py`) — es el único lugar donde sí se
instancian los repositorios reales y se los pasa a los casos de uso reales.

### 12.3 AC3 — Validación Fail-Fast

_"DNI duplicado o datos inválidos cortan el flujo de la CLI con mensajes de error amigables, sin
tracebacks."_ **Fail-fast** significa: apenas se detecta que algo está mal, se corta ahí mismo —
no se sigue procesando con datos potencialmente corruptos, no se difiere el error a más adelante.
En la práctica acá son dos cosas combinadas:

1. El caso de uso valida **antes** de llamar al repositorio (no guarda "por las dudas" y corrige
   después) — el ejemplo de `RegistrarJugadorUseCase` en 6.2 ya lo hace: chequea DNI duplicado
   **antes** de construir el `Jugador` y guardarlo.
2. La CLI atrapa las excepciones de dominio (sección 5) en un solo lugar (el composition root o
   un decorador, como charlamos para el logging) y las traduce a un mensaje legible, en vez de
   dejar que Python muestre el traceback crudo:

```python
try:
    resultado = caso_de_uso.execute(dto)
except ErrorDeDominio as e:
    print(f"Error: {e}")   # mensaje limpio, sin traceback
    return
```

### 12.4 AC4 — Formato de Salida

_"La CLI siempre formatea resultados exitosos y listas con tablas en consola (`tabulate`)."_ Es
una convención de consistencia visual: cualquier comando que devuelva datos (uno o varios
registros) los muestra como tabla, no como texto suelto o un `print(dict)`. `tabulate` es una
librería que arma tablas ASCII prolijas a partir de listas de diccionarios o de tuplas:

```python
from tabulate import tabulate

def formatear_jugadores(jugadores: list[JugadorDTO]) -> str:
    filas = [[j.id, j.nombre_completo, j.dni] for j in jugadores]
    return tabulate(filas, headers=["ID", "Nombre", "DNI"], tablefmt="simple")
```

### 12.5 AC5 — Atomicidad

_"Operaciones complejas (inscripciones que crean listas de buena fe) son atómicas."_ Ya lo
charlamos en detalle a propósito de `guardar_partido`/`guardar_boxscore`/`save_with_boxscore` en
`SqlitePartidoRepositorio`: **atómico** quiere decir "todo o nada" — si `InscribirClubEnCompetenciaUseCase`
necesita crear una `Inscripcion` **y** su `ListaBuenaFe` asociada, o se guardan las dos, o no se
guarda ninguna. Si la inscripción se guarda pero la lista de buena fe falla a mitad de camino,
queda un dato huérfano e inconsistente (una inscripción sin su lista, violando la regla 1:1 ya
documentada). La forma de lograrlo es la misma que ya usaron en `save_with_boxscore`: envolver
ambas operaciones en una sola transacción SQLite (`with self.conexion:`), a nivel del
**repositorio** — el caso de uso no maneja transacciones directamente, delega esa responsabilidad
al método del repositorio (por eso, para este caso de uso en particular, probablemente haga falta
un método nuevo tipo `CompetenciaRepositorio.inscribir_con_lista(inscripcion, lista)` que
internamente sea atómico, en vez de llamar a `guardar_inscripcion()` y `guardar_lista_buena_fe()`
por separado desde el caso de uso).

---

## Resumen ejecutivo (para no perderse en el detalle)

1. Las entidades ya existen y ya validan tipos — no hay que crearlas, solo sumarles la validación
   de coherencia interna que falte (ej. tiros convertidos ≤ lanzados).
2. Faltan 4 excepciones de dominio nuevas, todas heredando de `ErrorDeDominio`.
3. Se crea `src/aplicacion/` por primera vez: 9 casos de uso (clases, sin interfaz propia, con
   repositorios inyectados por constructor) + 6 DTOs (dataclasses simples, sin lógica, distintas
   de las entidades de dominio).
4. Se crean 6 comandos CLI que traducen input de terminal ↔ DTOs ↔ casos de uso ↔ tablas de
   salida, registrados en `main_cli.py` con el patrón de subparsers de `argparse`.
5. Ojo con el bloqueo real: `InscribirClubEnCompetenciaUseCase` necesita que se corrija
   `obtener_lista_por_inscripcion` primero (y probablemente un método atómico nuevo en el
   repositorio para cumplir el AC5).
