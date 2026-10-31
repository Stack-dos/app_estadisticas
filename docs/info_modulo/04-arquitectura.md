# Arquitectura del Sistema: StatsPro Basketball

## 1. Introducción

Para cumplir con los requerimientos de **portabilidad**, **testabilidad** y **ejecución local-first** definidos en el PRD, el sistema adopta una **Arquitectura Limpia (Clean Architecture)** con un enfoque **Hexagonal**.

Esta estructura permite que la lógica de negocio (reglas del básquet y cálculos estadísticos) sea independiente de la base de datos (SQLite), de la interfaz de usuario (CLI hoy, GUI Flet desde la US-105) y de las librerías externas (Pandas).

> **Aviso (2026-10-31):** la CLI se retira en la **US-105** y la interfaz pasa a ser una app de escritorio (Flet). Lo que este documento cuenta sobre la CLI describe el código actual y se reescribe en esa US.

!!! note "Nombres reales del proyecto"
    La primera versión de esta guía se escribió como diseño previo y usaba nombres en inglés (`domain`, `use_cases`, `Protocol`).
    El proyecto quedó con **nombres en español** (`dominio`, `casos_uso`) y con clases abstractas `ABC` para los contratos
    (ver [07-protocolos.md](07-protocolos.md) para la comparación). Esta versión describe lo que realmente existe.

---

## 2. Capas de la Aplicación

La regla de oro es que **las dependencias apuntan siempre hacia adentro**:

```text
ui/cli  ──►  aplicacion (casos de uso)  ──►  dominio (entidades, contratos, excepciones)
                                                ▲
infraestructura/repositorios (SQLite) ──────────┘  implementan los contratos del dominio
```

### 2.1 Capa de Dominio (`src/dominio`)

Es el corazón del sistema. No tiene dependencias de ninguna librería externa ni de otras capas.

- **Entidades (`entidades/`):** `dataclasses` puras que representan los objetos del negocio y **validan sus datos al construirse** (`__post_init__`):
  `Usuario`, `Club` y `UsuarioClub`, `Jugador` y `JugadorClub`, `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`,
  `Partido` y `JugadorPartido` (el boxscore de un jugador en un partido). Las entidades relacionadas comparten archivo (ej. `competencia.py` tiene cinco).
  Validan **tipos** (`TypeError`, un bug del programa) y **valores** (`DatoInvalidoError`, un error del usuario: nombre vacío, DNI negativo, año imposible). También hay un
  *modelo de lectura* sin validación, `PartidoResumen`, que es lo que devuelve la vista `v_partidos_resumen`.
- **Contratos / Puertos (`repositorios/`):** interfaces `ABC` (`ClubRepositorio`, `JugadorRepositorio`, `CompetenciaRepositorio`, `PartidoRepositorio`, `UsuarioRepositorio`).
  Definen **qué** debe poder hacer un repositorio (ej: `JugadorRepositorio.guardar()`), pero no **cómo**.
- **Excepciones (`exceptions.py`):** errores de negocio, todos hijos de `ErrorDeDominio` (ej: `DNIDuplicadoError`, `VinculoActivoExistenteError`, `DatoInvalidoError`).
  `DatoInvalidoError` además hereda de `ValueError`, para que el código que ya capturaba `ValueError` siga funcionando.

### 2.2 Capa de Aplicación / Casos de Uso (`src/aplicacion`)

Contiene la lógica de la aplicación y los orquestadores.

- **Casos de uso (`casos_uso/`):** clases con un método `ejecutar()` que realizan una acción del usuario, como `RegistrarJugadorUseCase` o `InscribirClubEnCompetenciaUseCase`.
  Reciben los repositorios **por constructor** (Inyección de Dependencias). Detalle de cada uno en [03-casos-de-uso.md](03-casos-de-uso.md).
- **DTOs (`dtos/`):** objetos planos que viajan entre la CLI y los casos de uso (`CrearJugadorDTO`, `JugadorDTO`, ...).

### 2.3 Capa de Infraestructura (`src/infraestructura`)

Implementaciones técnicas y herramientas externas.

- **Persistencia (`persistencia/`):** `SQLiteManager` (conexión, esquema, vistas, seed) y los scripts SQL en `sql/` (`schema.sql`, `views.sql`, `seed.sql`, `limpieza.sql`).
- **Repositorios (`repositorios/`):** implementaciones `Sqlite*Repositorio` de los contratos del dominio.
- **UI (`ui/cli/`):** adaptador de entrada. Hoy una **CLI** con `argparse` (comandos en `commands/`, tablas en `formatters/`); en el futuro puede sumarse una GUI (**Flet**).
- **Logger (`logger.py`):** configuración central del logging (ver [01-logger.md](01-logger.md)).
- **Análisis (`analytics/`):** *(todavía no existe)* motor estadístico con **Pandas** para el Hito 2.

### 2.4 Piezas transversales (`src/` raíz)

- **`main.py`:** punto de entrada y *Composition Root* de la CLI (arma el parser, inicializa la base y traduce los errores de negocio).
- **`utils.py`:** helpers **puros** que usan todas las capas (`id_persistido`, `abortar`, `fecha_iso`). No importa nada de `infraestructura`: una capa interna nunca puede depender de una externa.
- **`config/rutas.py`:** rutas del proyecto (base de datos, scripts SQL, logs).

---

## 3. Estructura de Directorios

```text
src/
├── main.py                       # Punto de entrada (parser de la CLI, composición y manejo de errores)
├── utils.py                      # Helpers puros compartidos
├── config/
│   └── rutas.py                  # Rutas de la base de datos, scripts SQL y logs
├── dominio/
│   ├── entidades/                # Entidades de básquet (club, jugador, competencia, partido, usuario)
│   ├── repositorios/             # Contratos ABC de los repositorios (puertos)
│   └── exceptions.py             # Excepciones de negocio (ErrorDeDominio y derivadas)
├── aplicacion/
│   ├── casos_uso/                # Lógica de aplicación (un archivo por acción)
│   └── dtos/                     # Data Transfer Objects para comunicación con la UI
└── infraestructura/
    ├── logger.py
    ├── persistencia/
    │   ├── database_manager.py   # SQLiteManager y abrir_conexion()
    │   └── sql/                  # Scripts .sql (schema, views, seed, limpieza)
    ├── repositorios/             # Implementaciones SQLite de los repositorios
    └── ui/
        └── cli/
            ├── commands/         # Un archivo por comando (club_add.py, jugador_link.py, ...)
            └── formatters/       # Formato de salida (tablas con tabulate)

tests/
├── conftest.py                   # Fixtures compartidas (bases en memoria, fábricas de datos)
├── unit/                         # Tests sin base de datos (entidades, casos de uso, comandos)
└── integration/                  # Tests con SQLite real (repositorios, esquema, CLI de punta a punta)
```

---

## 4. Beneficios para el Proyecto

1. **Testabilidad del Motor Estadístico:** Podemos testear los cálculos de eficiencia (PPP, eFG%) pasando listas de objetos `Partido` sin necesidad de escribir en un archivo `.sqlite`.
2. **Independencia de la Base de Datos:** Si en el futuro se requiere cifrar la DB (SQLCipher) o migrar a una base de datos distribuida, solo se cambia la implementación en `infraestructura/repositorios`.
3. **Evolución de la UI:** Gracias a esta arquitectura, cuando desarrollemos la versión v1.0 (Desktop/Mobile), reutilizaremos el 100% de los Casos de Uso y el Dominio.
4. **Tests rápidos:** los casos de uso se prueban con repositorios falsos (`unittest.mock`), sin base de datos (ver [09-testing.md](09-testing.md)).

---

## 5. Patrones de Diseño e Implementación

Para asegurar un código profesional y mantenible, se utilizan los siguientes patrones:

### 5.1 Inyección de Dependencias (DI)

Es el mecanismo por el cual un objeto recibe sus dependencias de una fuente externa en lugar de crearlas él mismo.

- **¿Cómo se aplica?** Cada comando de la CLI arma el repositorio real (`SqliteJugadorRepositorio(abrir_conexion())`) y se lo pasa al constructor del caso de uso (`RegistrarJugadorUseCase(repo)`).
  Como la función `ejecutar(args, repo=None)` del comando acepta el repositorio como parámetro opcional, en los tests se le pasa uno falso.
- **Beneficio:** Permite que el Caso de Uso trabaje con una _interfaz_ (`JugadorRepositorio`) y no con una implementación concreta. Si queremos testear, le pasamos un `MagicMock(spec=JugadorRepositorio)` y el código funciona igual.

### 5.2 Repository Pattern

Actúa como una mediación entre el dominio y la persistencia. Provee una interfaz tipo "colección" (guardar, buscar) para acceder a las entidades, ocultando las consultas SQL detrás de métodos limpios.
Ver [el detalle del patrón](../arquitectura/01-repository-pattern.md).

### 5.3 Factory Pattern

*(Todavía no se usa.)* La US-104 resolvió el hasheo sin fábrica: `RegistrarEntrenadorUseCase` recibe un `PasswordHasher` por constructor y hashea antes de crear el `Usuario`.

### 5.4 Command Pattern (en la CLI, hasta la US-105)

Cada acción del usuario (ej: `jugador add`, `club list`) se encapsula en su propio archivo dentro de `ui/cli/commands/`, y `main.py` la registra en el parser con `set_defaults(func=...)`.
Esto facilita la extensión de la CLI sin llenar el código de sentencias `if/else` gigantes. Detalle en [06-patron-command.md](06-patron-command.md).
En la GUI (US-105 en adelante) cumple ese rol la convención **una pantalla por archivo** en `ui/flet/screens/`, registrada en la tabla de rutas de `app.py`.

---

## 6. Modelo de Dominio v0.1 (CLI)

Para la primera versión funcional, el foco está en la **Persistencia Robusta** de las siguientes entidades:

### 6.1 Entidades Principales

1. **Usuario (Entrenador):** Posee credenciales y gestiona sus clubes.
2. **Club:** Entidad base. Tiene un nombre y se vincula a un usuario.
3. **Jugador:** Datos básicos (DNI, Nombre, Nacimiento).
4. **Competencia:** Torneos con año y tipo definidos.
5. **Partido:** Evento que vincula dos clubes en una competencia y fecha determinada.
6. **Estadística (Boxscore):** El registro atómico de acciones (puntos, rebotes) de un jugador en un partido específico. En el código es `JugadorPartido`.

### 6.2 Interrelaciones Clave

- **Relación Usuario-Club (N:M):** Un DT puede dirigir varios clubes; un club puede tener varios asistentes vinculados.
- **Relación Jugador-Club (N:M con historial):** Un jugador puede haber pasado por varios clubes. Se gestiona con fechas (`fechaDesde`, `fechaHasta`); un vínculo sin `fechaHasta` es el vigente.
- **Estructura Competitiva:**
  - `Inscripcion` vincula un `Club` + `Categoria` + `Competencia`.
  - La `Lista de Buena Fe` es la lista de jugadores habilitados para esa `Inscripcion` (relación 1:1).
- **El Partido:** Es el eje central. Vincula la `Competencia` con el `Club Local` y el `Club Visitante`. Las estadísticas se cuelgan del `Partido`.

---

## 7. Casos de Uso del Hito 1 (CLI v0.1)

Para cumplir con la **US-103** y las siguientes, se implementan estos orquestadores de lógica.
El estado detallado (qué recibe y devuelve cada uno, paso a paso) está en [03-casos-de-uso.md](03-casos-de-uso.md).

### 7.1 Gestión de Identidad (Auth) — *US-104, pendiente*

- `RegistrarEntrenador`: Crea un perfil local con password hasheado.
- `LoginLocal`: Valida credenciales y mantiene la sesión activa.
- `SeleccionarClubActivo` *(hoy `CambiarClubActivoUseCase`, que solo valida)*: Establece el contexto para los siguientes comandos.

### 7.2 Gestión Administrativa — *US-103, implementada*

- `CrearClubUseCase`: Registra un nuevo club (todavía no lo vincula al usuario: necesita la sesión de la US-104).
- `RegistrarJugadorUseCase`: Crea un jugador en el sistema.
- `VincularJugadorAClubUseCase`: Registra la pertenencia de un jugador a un club en un periodo.
- `CrearCompetenciaUseCase`: Registra ligas o torneos.
- `InscribirClubEnCompetenciaUseCase`: Crea la relación Club-Categoría-Competencia y su lista de buena fe, de forma atómica.
- `CrearCategoriaUseCase`: Registra una categoría (ej. U21); no permite nombres repetidos.
- `AgregarJugadorAListaBuenaFeUseCase`: Habilita a un jugador en la lista de buena fe de una inscripción (debe jugar en el club de la inscripción).
- `ListarClubesUsuarioUseCase`, `ListarJugadoresClubUseCase`, `ListarPartidosPorClubUseCase`, `ListarCategoriasUseCase`, `ListarCompetenciasUseCase`,
  `ListarInscripcionesClubUseCase`, `ListarListaBuenaFeUseCase`: consultas.

### 7.3 Operaciones de Partido — *US-105, pendiente*

- `CargarPartidoManual`: Registra el evento de partido y sus estadísticas básicas por jugador (Boxscore).

---

## 8. Funcionalidades de la Interfaz CLI

La CLI se diseñó para ser rápida y "amigable" bajo las siguientes premisas:

1. **Navegación por Comandos:** Uso de subcomandos claros (ej: `club add`, `jugador list`), con `--help` en cada nivel. La referencia completa está en el [RUNBOOK](../../RUNBOOK.md).
2. **Errores sin traceback:** los errores de negocio se muestran como un mensaje (`Error: ...`) en stderr y terminan con código de salida 1.
3. **Salida Tabulada:** los listados se muestran como tablas de consola con `tabulate` (`formatters/table_formatter.py`).
4. **Formularios:** la carga de partido no se hace en la CLI: es una pantalla de la GUI (US-108).
5. **Manejo de Sesión:** no existe en la CLI; en la GUI la sesión vive en memoria (US-105) y se puede recordar entre aperturas junto con el club activo (US-106, archivo `~/.statspro/session.json`).

---

## 9. Manejo de la Base de Datos y Persistencia

Para gestionar SQLite de forma profesional, se separa la **gestión de la conexión** de la **lógica de datos (CRUD)**.

### 9.1 El SQLiteManager (Infraestructura)

Esta clase (`infraestructura/persistencia/database_manager.py`) es la responsable del ciclo de vida del archivo de base de datos.

- **Responsabilidad:** Crear el archivo `.db`, activar `Foreign Keys` (importante en SQLite), ejecutar `schema.sql` y `views.sql`, y proveer el objeto de conexión.
- **API:** `connect()`, `inicializar_schema()`, `cargar_seed()`, `limpieza()`, `close_connection()`.
- **Atajo `abrir_conexion()`:** función del mismo módulo que abre la base real de la aplicación (`estadisticas.db`); la usan los comandos de la CLI.

```python
manager = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
conexion = manager.connect()      # activa PRAGMA foreign_keys = ON y row_factory = sqlite3.Row
manager.inicializar_schema()      # ejecuta schema.sql y luego views.sql
```

!!! warning "El schema se ejecuta en cada arranque"
    `main()` llama a `inicializar_schema()` **cada vez que se ejecuta la CLI**. Por eso `schema.sql` solo usa `CREATE TABLE IF NOT EXISTS` y **nunca** `DROP TABLE`:
    una versión anterior borraba las tablas al arrancar y destruía todos los datos. Las vistas sí se recrean en cada arranque (`DROP VIEW` + `CREATE VIEW`),
    lo cual es seguro porque una vista no guarda datos y así siempre queda con su definición más reciente.

### 9.2 Repositorios Especializados (S.R.P.)

En lugar de una sola clase con todos los CRUD, hay un repositorio por cada **Agregado** o **Entidad Principal**. Todos reciben la conexión del `SQLiteManager`.

- `SqliteUsuarioRepositorio`: Maneja solo la tabla `usuario`.
- `SqliteClubRepositorio`: Maneja `club` y la relación `usuarioClub`.
- `SqliteJugadorRepositorio`: Maneja `jugador` y su historial en clubes (`jugadorClub`).
- `SqliteCompetenciaRepositorio`: Maneja `competencia`, `categoria`, `inscripcion`, `listaBuenaFe` y `jugadorListaBuenaFe`.
- `SqlitePartidoRepositorio`: Maneja `partido` y las estadísticas de `jugadorPartido`.

**¿Por qué separarlos?**

1. **Mantenibilidad:** Si cambias la lógica de cómo se guarda un Partido, no rompes por error el registro de Usuarios.
2. **Inyección Selectiva:** Un Caso de Uso como `RegistrarJugadorUseCase` solo recibe el `JugadorRepositorio`, no tiene acceso a las funciones de `Login` o `Partidos`. Esto hace el sistema mucho más seguro.

---

## 10. Ciclo de Vida en main.py (Orquestación)

Cada ejecución de la CLI es **un proceso nuevo que corre un único comando**, así que cada comando arma solo las dependencias que necesita.
El `main()` real hace lo siguiente:

```python
def main() -> None:
    inicializar_db()                    # 1. Crea el esquema y las vistas si no existen (idempotente)

    parser = construir_parser()         # 2. Arma el árbol de comandos (subparsers + set_defaults(func=...))
    args = parser.parse_args()          # 3. Valida y convierte los argumentos que escribió el usuario
    if hasattr(args, "func"):
        try:
            args.func(args)             # 4. Ejecuta el comando elegido, sin ningún if/elif
        except ErrorDeDominio as e:     # 5. Un solo lugar traduce los errores de negocio a un mensaje
            abortar(str(e))             #    ("Error: ..." en stderr, código de salida 1, sin traceback)
    else:
        parser.print_help()
```

Y adentro de cada comando (ej. `club_add.ejecutar`) se hace la inyección de dependencias:

```python
def ejecutar(args, repo: ClubRepositorio | None = None) -> None:
    if repo is None:                                              # en producción: repositorio real
        repo = SqliteClubRepositorio(conexion=abrir_conexion())
    club = CrearClubUseCase(repo).ejecutar(CrearClubDTO(nombre=args.nombre))
    ...
```
