# Arquitectura del Sistema: StatsPro Basketball

## 1. Introducción

Para cumplir con los requerimientos de **portabilidad**, **testabilidad** y **ejecución local-first** definidos en el PRD, el sistema adopta una **Arquitectura Limpia (Clean Architecture)** con un enfoque **Hexagonal**.

Esta estructura permite que la lógica de negocio (reglas del básquet y cálculos estadísticos) sea independiente de la base de datos (SQLite), de la interfaz de usuario (GUI de escritorio con Flet) y de las librerías externas (Pandas).

> **Historia:** hasta la US-104 la interfaz era una CLI (`argparse`); en la US-105 se retiró y la reemplazó la GUI. Por qué se tomó esa decisión: `docs/context_ia/2026-10-31-retiro-cli-y-gui-en-hito-1.md`.

!!! note "Nombres reales del proyecto"
    La primera versión de esta guía se escribió como diseño previo y usaba nombres en inglés (`domain`, `use_cases`, `Protocol`).
    El proyecto quedó con **nombres en español** (`dominio`, `casos_uso`) y con clases abstractas `ABC` para los contratos
    (ver [07-protocolos.md](07-protocolos.md) para la comparación). Esta versión describe lo que realmente existe.

---

## 2. Capas de la Aplicación

La regla de oro es que **las dependencias apuntan siempre hacia adentro**:

```text
ui/flet ──►  aplicacion (casos de uso)  ──►  dominio (entidades, contratos, excepciones)
                                                ▲
infraestructura/repositorios (SQLite) ──────────┘  implementan los contratos del dominio
```

### 2.1 Capa de Dominio (`src/dominio`)

Es el corazón del sistema. No tiene dependencias de ninguna librería externa ni de otras capas.

- **Entidades (`entidades/`):** `dataclasses` puras que representan los objetos del negocio y **validan sus datos al construirse** (`__post_init__`):
  `Usuario`, `Club` y `UsuarioClub`, `Jugador` y `JugadorClub`, `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`,
  `Partido` y `JugadorPartido` (el boxscore de un jugador en un partido). Las entidades relacionadas comparten archivo (ej. `competencia.py` tiene cinco).
  Validan **tipos** (`TypeError`, un bug del programa) y **valores** (`DatoInvalidoError`, un error del usuario: nombre vacío o año imposible). También hay un
  *modelo de lectura* sin validación, `PartidoResumen`, que es lo que devuelve la vista `v_partidos_resumen`.
- **Contratos / Puertos (`repositorios/`):** interfaces `ABC` (`ClubRepositorio`, `JugadorRepositorio`, `CompetenciaRepositorio`, `PartidoRepositorio`, `UsuarioRepositorio`).
  Definen **qué** debe poder hacer un repositorio (ej: `JugadorRepositorio.guardar()`), pero no **cómo**.
- **Excepciones (`exceptions.py`):** errores de negocio, todos hijos de `ErrorDeDominio` (ej: `VinculoActivoExistenteError`, `DatoInvalidoError`).
  `DatoInvalidoError` además hereda de `ValueError`, para que el código que ya capturaba `ValueError` siga funcionando.

### 2.2 Capa de Aplicación / Casos de Uso (`src/aplicacion`)

Contiene la lógica de la aplicación y los orquestadores.

- **Casos de uso (`casos_uso/`):** clases con un método `ejecutar()` que realizan una acción del usuario, como `RegistrarJugadorUseCase` o `InscribirClubEnCompetenciaUseCase`.
  Reciben los repositorios **por constructor** (Inyección de Dependencias). Detalle de cada uno en [03-casos-de-uso.md](03-casos-de-uso.md).
- **Servicios (`servicios/`):** `SessionManager`, la sesión (quién inició sesión y con qué club trabaja). Vive en memoria y, con "Recordarme", la copia en un archivo a través del
  **puerto** `SesionAlmacen`, que está en esta capa (y no en el dominio, como `PasswordHasher`) porque su contrato usa `SessionDTO`, un DTO de la aplicación.
- **DTOs (`dtos/`):** objetos planos que viajan entre la GUI y los casos de uso (`CrearJugadorDTO`, `JugadorDTO`, ...).

### 2.3 Capa de Infraestructura (`src/infraestructura`)

Implementaciones técnicas y herramientas externas.

- **Persistencia (`persistencia/`):** `SQLiteManager` (conexión, esquema, vistas, seed) y los scripts SQL en `sql/` (`schema.sql`, `views.sql`, `seed.sql`, `limpieza.sql`).
- **Repositorios (`repositorios/`):** implementaciones `Sqlite*Repositorio` de los contratos del dominio.
- **UI (`ui/flet/`):** adaptador de entrada: la GUI de escritorio con **Flet**. `app.py` es el *Composition Root* (arma las dependencias, la tabla de rutas y la ruta protegida),
  `errores.py` muestra los errores junto al formulario y `screens/` tiene una pantalla por archivo. Detalle en [13-gui-flet-y-eventos.md](13-gui-flet-y-eventos.md).
- **Seguridad (`security/`):** `Pbkdf2PasswordHasher`, la implementación del puerto `PasswordHasher` del dominio.
- **Logger (`logger.py`):** configuración central del logging (ver [01-logger.md](01-logger.md)).
- **Análisis (`analytics/`):** *(todavía no existe)* motor estadístico con **Pandas** para el Hito 2.

### 2.4 Piezas transversales (`src/` raíz)

- **`main.py`:** punto de entrada. Solo llama a `ejecutar()` de `ui/flet/app.py`; el armado vive ahí.
- **`utils.py`:** helpers **puros** que usan todas las capas (`id_persistido`). No importa nada de `infraestructura`: una capa interna nunca puede depender de una externa.
- **`config/rutas.py`:** rutas del proyecto (base de datos, scripts SQL, logs).

---

## 3. Estructura de Directorios

```text
src/
├── main.py                       # Punto de entrada: abre la GUI
├── utils.py                      # Helpers puros compartidos
├── config/
│   └── rutas.py                  # Rutas de la base de datos, scripts SQL y logs
├── dominio/
│   ├── entidades/                # Entidades de básquet (club, jugador, competencia, partido, usuario)
│   ├── repositorios/             # Contratos ABC de los repositorios (puertos)
│   └── exceptions.py             # Excepciones de negocio (ErrorDeDominio y derivadas)
├── aplicacion/
│   ├── casos_uso/                # Lógica de aplicación (un archivo por acción)
│   ├── servicios/                # SessionManager y el puerto SesionAlmacen (sesión recordada)
│   └── dtos/                     # Data Transfer Objects para comunicación con la UI
└── infraestructura/
    ├── logger.py
    ├── persistencia/
    │   ├── database_manager.py   # SQLiteManager
    │   ├── json_sesion_almacen.py # JsonSesionAlmacen: la sesión recordada en ~/.statspro/session.json
    │   └── sql/                  # Scripts .sql (schema, views, seed, limpieza)
    ├── repositorios/             # Implementaciones SQLite de los repositorios
    ├── security/                 # Pbkdf2PasswordHasher
    └── ui/
        └── flet/
            ├── app.py            # Composition root, tabla de rutas y ruta protegida
            ├── errores.py        # Manejador común de errores de la GUI
            ├── barra_superior.py # Barra de las pantallas internas (club activo, navegación)
            └── screens/          # Una pantalla por archivo (login, registro, inicio, clubes)

tests/
├── conftest.py                   # Fixtures compartidas (bases en memoria, fábricas de datos)
├── unit/                         # Tests sin base de datos (entidades, casos de uso, pantallas sin ventana)
└── integration/                  # Tests con SQLite real (repositorios, esquema, casos de uso de punta a punta)
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

- **¿Cómo se aplica?** El composition root de la GUI (`construir_dependencias` en `ui/flet/app.py`) arma una sola vez los repositorios reales y se los pasa al constructor de cada caso
  de uso (`LoginLocalUseCase(repo_usuario, hasher)`). Las pantallas reciben los casos de uso ya armados, así que en los tests se les pasa un mock.
- **Beneficio:** Permite que el Caso de Uso trabaje con una _interfaz_ (`JugadorRepositorio`) y no con una implementación concreta. Si queremos testear, le pasamos un `MagicMock(spec=JugadorRepositorio)` y el código funciona igual.

### 5.2 Repository Pattern

Actúa como una mediación entre el dominio y la persistencia. Provee una interfaz tipo "colección" (guardar, buscar) para acceder a las entidades, ocultando las consultas SQL detrás de métodos limpios.
Ver [el detalle del patrón](../arquitectura/01-repository-pattern.md).

### 5.3 Factory Pattern

*(Todavía no se usa.)* La US-104 resolvió el hasheo sin fábrica: `RegistrarEntrenadorUseCase` recibe un `PasswordHasher` por constructor y hashea antes de crear el `Usuario`.

### 5.4 Una pantalla por archivo y tabla de rutas (antes, Command Pattern)

Cada pantalla vive en su propio archivo dentro de `ui/flet/screens/` y se registra en la tabla de rutas de `app.py` (`{"/login": lambda: crear_login_view(...)}`).
Agregar una pantalla no obliga a tocar las demás ni a escribir un `if/elif` gigante. Cumple el rol que tenía el Command Pattern en la CLI retirada
([06-patron-command.md](06-patron-command.md)); el detalle de la GUI está en [13-gui-flet-y-eventos.md](13-gui-flet-y-eventos.md).

---

## 6. Modelo de Dominio v0.1

Para la primera versión funcional, el foco está en la **Persistencia Robusta** de las siguientes entidades:

### 6.1 Entidades Principales

1. **Usuario (Entrenador):** Posee credenciales y gestiona sus clubes.
2. **Club:** Entidad base. Tiene un nombre y se vincula a un usuario.
3. **Jugador:** Datos básicos (nombre, apellido y nacimiento opcional).
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

## 7. Casos de Uso del Hito 1

Para cumplir con la **US-103** y las siguientes, se implementan estos orquestadores de lógica.
El estado detallado (qué recibe y devuelve cada uno, paso a paso) está en [03-casos-de-uso.md](03-casos-de-uso.md).

### 7.1 Gestión de Identidad (Auth) y sesión — *US-104 a US-106, implementada*

- `RegistrarEntrenador`: Crea un perfil local con password hasheado.
- `LoginLocal`: Valida credenciales; la GUI guarda al usuario en el `SessionManager` (y, con "Recordarme", en el archivo de sesión).
- `SeleccionarClubActivo` *(`CambiarClubActivoUseCase`, que valida)*: Establece el club con el que se trabaja; la pantalla de clubes lo guarda en la sesión (US-106).
- `RestaurarSesionUseCase`: Al abrir la app, restaura la sesión recordada revalidando usuario y club contra la base (US-106).

### 7.2 Gestión Administrativa — *US-103, implementada*

- `CrearClubUseCase`: Registra un nuevo club y vincula al usuario que lo crea, en una sola transacción; no permite nombres repetidos.
- `RegistrarJugadorUseCase`: Crea un jugador en el sistema.
- `VincularJugadorAClubUseCase`: Registra la pertenencia de un jugador a un club en un periodo.
- `CrearCompetenciaUseCase`: Registra ligas o torneos.
- `InscribirClubEnCompetenciaUseCase`: Crea la relación Club-Categoría-Competencia y su lista de buena fe, de forma atómica.
- `CrearCategoriaUseCase`: Registra una categoría (ej. U21); no permite nombres repetidos.
- `AgregarJugadorAListaBuenaFeUseCase`: Habilita a un jugador en la lista de buena fe de una inscripción (debe jugar en el club de la inscripción).
- `ListarClubesUsuarioUseCase`, `ListarJugadoresClubUseCase`, `ListarPartidosPorClubUseCase`, `ListarCategoriasUseCase`, `ListarCompetenciasUseCase`,
  `ListarInscripcionesClubUseCase`, `ListarListaBuenaFeUseCase`: consultas.

### 7.3 Operaciones de Partido — *US-108, pendiente*

- `CargarPartidoManual`: Registra el evento de partido y sus estadísticas básicas por jugador (Boxscore).

---

## 8. Funcionalidades de la Interfaz Gráfica

La GUI (Flet) sigue estas premisas (detalle en [13-gui-flet-y-eventos.md](13-gui-flet-y-eventos.md)):

1. **Navegación por rutas:** cada pantalla tiene una ruta (`/login`, `/registro`, `/inicio`, `/clubes`) y un único router decide qué se dibuja. La **ruta protegida**
   (`resolver_ruta`) impide llegar a una pantalla interna sin sesión.
2. **Errores junto al formulario:** los errores de negocio se muestran debajo del formulario que los causó, sin traceback y sin cerrar la app; un bug muestra un
   mensaje genérico y deja el traceback en `logs/app.log` (`ejecutar_mostrando_errores`).
3. **Pantallas finas:** las pantallas no validan ni calculan: leen los campos, arman el DTO y llaman al caso de uso.
4. **Manejo de Sesión:** vive en memoria (`SessionManager`, US-105). Con "Recordarme" se guarda también en `~/.statspro/session.json` y se restaura al abrir la app,
   junto con el club activo (US-106).
5. **Club activo a la vista:** todas las pantallas internas usan la misma barra superior (`crear_barra_superior`), que muestra el club activo.

---

## 9. Manejo de la Base de Datos y Persistencia

Para gestionar SQLite de forma profesional, se separa la **gestión de la conexión** de la **lógica de datos (CRUD)**.

### 9.1 El SQLiteManager (Infraestructura)

Esta clase (`infraestructura/persistencia/database_manager.py`) es la responsable del ciclo de vida del archivo de base de datos.

- **Responsabilidad:** Crear el archivo `.db`, activar `Foreign Keys` (importante en SQLite), ejecutar `schema.sql` y `views.sql`, y proveer el objeto de conexión.
- **API:** `connect()`, `inicializar_schema()`, `cargar_seed()`, `limpieza()`, `close_connection()`.

```python
manager = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
conexion = manager.connect()      # activa PRAGMA foreign_keys = ON y row_factory = sqlite3.Row
manager.inicializar_schema()      # ejecuta schema.sql y luego views.sql
```

!!! warning "El schema se ejecuta en cada arranque"
    `ejecutar()` de `ui/flet/app.py` llama a `inicializar_schema()` **cada vez que se abre la app**. Por eso `schema.sql` solo usa `CREATE TABLE IF NOT EXISTS` y **nunca** `DROP TABLE`:
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

## 10. Ciclo de Vida de la Aplicación (Orquestación)

`main.py` solo llama a `ejecutar()` de `ui/flet/app.py`, que es el *Composition Root*: el único lugar que conoce las clases concretas.
La app es **un solo proceso que vive mientras la ventana está abierta**, así que todo se arma una sola vez al arrancar:

```python
def ejecutar() -> None:
    db = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
    conexion = db.connect()                                  # 1. Una sola conexión para toda la app
    try:
        db.inicializar_schema()                              # 2. Crea el esquema y las vistas si no existen (idempotente)
        almacen = JsonSesionAlmacen(Path(r.SESSION_FILE))    # ~/.statspro/session.json
        deps = construir_dependencias(conexion, Pbkdf2PasswordHasher(), almacen)  # 3. Repositorios, sesión (restaurada) y casos de uso
        ft.run(lambda page: _main(page, deps))               # 4. Abre la ventana y espera eventos hasta que se cierra
    finally:
        db.close_connection()                                # 5. Se cierra aunque algo falle
```

Y la inyección de dependencias queda en un solo lugar:

```python
def construir_dependencias(conexion, hasher, almacen) -> Dependencias:
    repo_usuario = SqliteUsuarioRepositorio(conexion)
    repo_club = SqliteClubRepositorio(conexion)
    sesion = SessionManager(almacen)
    cambiar_club_uc = CambiarClubActivoUseCase(repo_club)
    # La app "tal como arranca": si había una sesión recordada válida, ya viene abierta.
    RestaurarSesionUseCase(almacen, repo_usuario, cambiar_club_uc, sesion).ejecutar()
    return Dependencias(
        sesion=sesion,
        registrar_uc=RegistrarEntrenadorUseCase(repo_usuario, hasher),
        login_uc=LoginLocalUseCase(repo_usuario, hasher),
        crear_club_uc=CrearClubUseCase(repo_club),
        listar_clubes_uc=ListarClubesUsuarioUseCase(repo_club),
        cambiar_club_uc=cambiar_club_uc,
    )
```

`Dependencias` guarda solo lo que usan las pantallas: `RestaurarSesionUseCase` se ejecuta una vez y no queda ahí.

`_main(page, deps)` arma la tabla de rutas y el router; cada pantalla recibe solo los casos de uso que usa. Una sola conexión alcanza porque en Flet 1.x
los handlers síncronos corren en el mismo hilo que la abrió (ver la sección 8 de [13-gui-flet-y-eventos.md](13-gui-flet-y-eventos.md)).
