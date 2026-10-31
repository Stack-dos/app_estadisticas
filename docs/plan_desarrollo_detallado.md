# Plan de Desarrollo Detallado: StatsPro Basketball

- **ID de referencia:** PRD-BSKT-2026-001
- **Estado:** Aprobado
- **Producto:** StatsPro Basketball
- **Ingeniería:** equipo de 2 ingenieros
- **Clasificación:** interno
- **Stack principal:** SQLite · Python/Pandas · Flet (UI, ver ADR-002)

> **Qué es este documento:** transcripción completa y fusionada del PRD del proyecto, todas las historias de usuario, épicas e hitos, con sus criterios de aceptación, archivos a crear y funciones/métodos involucrados.
>
> Al final del documento hay una sección **"Estado real del código vs. plan"** con los hallazgos
> e inconsistencias encontrados al hacer esta transcripción — ver sección 20.
>
> **Cambio de rumbo (2026-10-31): la CLI se retira y la interfaz pasa a ser la GUI Flet desde el
> Hito 1.** La CLI fue la interfaz de las US-103 y US-104; la US-105 la reemplaza por una app de
> escritorio. Las historias del Hito 1 se renumeraron:
>
> | Historia                                       | Número anterior | Número nuevo |
> | ---------------------------------------------- | --------------- | ------------ |
> | Interfaz gráfica base y retiro de la CLI       | — (nueva)       | US-105       |
> | Sesión persistente y club activo               | US-105          | US-106       |
> | Pantallas de gestión (antes "CLI con Command") | US-107          | US-107       |
> | Carga atómica de partido                       | US-106          | US-108       |
> | Entorno de desarrollo y CI/CD                  | US-109          | US-109       |
> | Monitoreo y trazabilidad                       | US-108          | US-110       |
>
> Los documentos de `docs/context_ia/` son registros de sesiones pasadas y conservan la
> numeración y la CLI de su fecha.

---

## Tabla de Contenidos

1. [Descripción General del Producto](#1-descripción-general-del-producto)
2. [Perfiles de Usuario](#2-perfiles-de-usuario)
3. [Arquitectura de Datos](#3-arquitectura-de-datos)
4. [Arquitectura de Software (Clean + Hexagonal)](#4-arquitectura-de-software-clean--hexagonal)
5. [Acuerdo de Ingeniería y Estándares](#5-acuerdo-de-ingeniería-y-estándares)
6. [Reglas de Negocio Consolidadas](#6-reglas-de-negocio-consolidadas)
7. [Requisitos No Funcionales (NFR)](#7-requisitos-no-funcionales-nfr)
8. [Registro de Decisiones Arquitectónicas (ADR)](#8-registro-de-decisiones-arquitectónicas-adr)
9. [Hito 1 — Núcleo de Datos e Interfaz Gráfica Base (v0.1)](#9-hito-1--núcleo-de-datos-e-interfaz-gráfica-base-v01)
10. [Hito 2 — Motor de Ingesta y Análisis (v0.2)](#10-hito-2--motor-de-ingesta-y-análisis-v02)
11. [Hito 3 — Visualización Pro y Reporting (v0.3)](#11-hito-3--visualización-pro-y-reporting-v03)
12. [Hito 4 — Interfaz Multiplataforma y Entrega (v1.0)](#12-hito-4--interfaz-multiplataforma-y-entrega-v10)
13. [Definición de "Hecho" (DoD)](#13-definición-de-hecho-dod)
14. [Catálogo Técnico de Criticidad](#14-catálogo-técnico-de-criticidad)
15. [Proceso de Liberación de Versiones](#15-proceso-de-liberación-de-versiones)
16. [Roadmap Futuro (Hitos 5–9, visión de producto)](#16-roadmap-futuro-hitos-59-visión-de-producto)
17. [Estructura de Repositorios](#17-estructura-de-repositorios)
18. [ADRs Pendientes — tabla de bloqueo por hito](#18-adrs-pendientes--tabla-de-bloqueo-por-hito)
19. [Convenciones rápidas](#19-convenciones-rápidas)
20. [Estado real del código vs. plan (hallazgos)](#20-estado-real-del-código-vs-plan-hallazgos)

---

## 1. Descripción General del Producto

### 1.1 Planteamiento del problema

El análisis estadístico en el básquet formativo sufre una brecha crítica entre la recolección de datos y su utilidad táctica. Los entrenadores operan bajo alta presión donde la toma de decisiones basada en datos se ve limitada por herramientas fragmentadas.

| #   | Problema                 | Impacto Operativo                                               | Línea Base                 |
| --- | ------------------------ | --------------------------------------------------------------- | -------------------------- |
| 1   | Carga manual ineficiente | Interferencia táctica; pérdida de foco durante el partido       | >20 min/partido            |
| 2   | Ceguera estadística      | Decisiones por intuición, sin métricas avanzadas (PPP, EFF)     | 0% automatizado            |
| 3   | Fragmentación de datos   | Imposibilidad de seguimiento histórico o comparativo de rivales | Papel / Excel              |
| 4   | Inestabilidad de red     | Apps web fallan en estadios sin conectividad                    | 100% online (competidores) |
| 5   | Rigidez de plataformas   | El DT no puede integrar datos de Gesdeportiva fácilmente       | Ingesta manual             |

Desglose adicional (basado en encuestas reales a DTs):

- **Interferencia en el juego:** la carga manual en tiempo real distrae al entrenador o requiere una persona dedicada exclusivamente a esa tarea.
- **Ritmo frenético:** la velocidad del básquet genera demoras entre la carga de una estadística y la siguiente.
- **Cálculo manual y falta de tendencias:** los DTs pierden tiempo pasando el boxscore a mano y calculando estadísticas avanzadas por su cuenta; no logran identificar numéricamente hacia dónde van las tendencias del juego.
- **Falta de centralización:** no hay un espacio virtual cómodo para el registro histórico, lo que dificulta comparar rivales o evaluar la evolución de los propios jugadores.
- **Herramientas inflexibles:** las apps existentes no se adaptan a los sistemas de competencia locales, y los datos de plataformas externas (Gesdeportiva) no se integran sin trabajo manual.

**Línea base cuantificada:** carga manual >20-40 min; 0% de automatización de importación Excel; 65% de los usuarios encuestados requieren uso offline; datos aislados por partido sin acumulación histórica.

### 1.2 Visión del producto

Desarrollar una aplicación multiplataforma (PC y Mobile) de ejecución local que centralice el conocimiento deportivo en un motor estadístico profesional, permitiendo una gestión integral **sin necesidad de internet**, con un flujo optimizado mediante la carga de planillas de "Gesdeportiva".

Pilares del producto:

1. **Accesibilidad y flexibilidad:** acceso desde cualquier dispositivo — cancha (celular/tablet) o casa (PC/notebook) para análisis más profundo.
2. **Gestión organizativa completa:** perfil de usuario, club, categorías, competencias y listas de buena fe.
3. **Ingesta de datos automatizada y manual:** además de la carga manual partido a partido, el software interpreta automáticamente las planillas Excel o PDF de Gesdeportiva.
4. **Generación de estadísticas avanzadas:** motor de análisis que entrega resúmenes y estadísticas acumuladas, tradicionales y avanzadas, individuales y de equipo.
5. **Visualización y toma de decisiones:** comparación de equipos/jugadores, filtros, gráficos claros para identificar tendencias a corto, mediano y largo plazo.

### 1.3 Metas y no metas

**En el alcance (v1.0):**

- **Ingesta multimodal:**
  - _Automática:_ carga de planillas Excel o PDF de Gesdeportiva (partidos y listados de jugadores).
  - _Manual:_ formulario para carga post-partido (jugador por jugador).
- **Persistencia local:** base de datos SQLite única por instalación de usuario.
- **Motor estadístico:** análisis de tendencias, PPP, estadistica avanzada y eficiencia con Pandas.
- **Multiplataforma:** ejecución en Windows, Linux, macOS y dispositivos móviles.

**Fuera de alcance (v1.0):**

- **Carga en vivo:** toma de datos en tiempo real durante el partido — se posterga a versiones post-estables (ver Hito 7 en el roadmap futuro).
- **Sincronización cloud:** no se contempla almacenamiento en la nube inicialmente.
- **Importación automática/API:** no hay conexión directa con servidores de Gesdeportiva (solo archivos Excel o PDF exportados manualmente por el usuario).
- Adicionalmente: análisis avanzado con IA, integración con sensores, y "no incorporar características demasiado complejas desde el inicio" — se prioriza una primera versión mínima y funcional sobre un sistema definitivo hecho de una sola vez.

### 1.4 Métricas de éxito

- **MTTR (Time to Report):** tiempo desde la carga del archivo hasta el informe completo **< 2 minutos**.
- **Tasa de automatización:** % de estadísticas de partido generadas sin intervención manual **> 95%**.
- **Disponibilidad offline:** **100%** de las funcionalidades críticas operativas sin conexión.
- **North Star Metric:** número de sesiones de análisis táctico realizadas por el DT por semana.
- **Tiempo de carga de datos:** la mayoría de los DTs encuestados solo están dispuestos a dedicar entre "menos de 10 minutos" y "10-20 minutos" por partido — es el techo operativo real.
- **Adopción por usabilidad:** los DTs prefieren explícitamente una app "simple y rápida" por sobre una "completa pero más compleja" — la simplicidad es un requisito de producto, no un nice-to-have.

---

## 2. Perfiles de Usuario

| Perfil                   | Rol y Contexto                                               | Objetivo Principal                             | Problema Actual                                          |
| ------------------------ | ------------------------------------------------------------ | ---------------------------------------------- | -------------------------------------------------------- |
| **Director Técnico**     | Líder táctico, desde categorías formativas hasta profesional | Optimizar rendimiento mediante datos objetivos | El cálculo manual de EFF/PPP es tedioso                  |
| **Analista / Asistente** | Responsable de carga y procesamiento de datos                | Proveer informes rápidos y precisos al DT      | Carga redundante de datos ya existentes en Gesdeportiva |

### Perfil ampliado del usuario principal (Entrenador / Analista Estadístico)

- **Categorías que dirige:** todo el espectro — formativas (Mini, U13, U15, U17), de desarrollo (U21, Reserva), Primera Amateur, Veteranos y básquet Profesional.
- **Tamaño del cuerpo técnico:** variable — solos, en duplas, o equipos de 3+ personas.
- **Momento de análisis:** algunos toman datos durante el partido o en el club, pero la mayoría analiza las estadísticas **de forma diferida en sus casas**, horas o días después del partido.
- **Herramientas actuales:** papel y lápiz o Excel básico; algunos usan apps específicas.
- Satisfacción con los métodos actuales: media a baja.
- **Pain points textuales**:
  - _"pierdo el foco en la mejora"_ del equipo durante el partido por tener que anotar/calcular.
  - El juego es _"demasiado frenético"_ — demoras y pérdida de datos entre una carga y la siguiente.
  - _"tener que pasar el boxscore manualmente y calcular las estadísticas avanzadas por mi cuenta"_ — frustración explícita con el cálculo manual.
  - No pueden _"identificar tendencias de hacia dónde va el básquet, ni identificar numéricamente errores del equipo"_ — faltan datos como porcentajes reales por zona de cancha o situaciones puntuales (ej. goles rivales desde el 1v1).
  - _"no hay un espacio virtual donde se puedan dejar constancia de las estadísticas y que sea cómodo"_ para medir rendimiento a corto/mediano/largo plazo.

---

## 3. Arquitectura de Datos

El sistema usa una base de datos relacional local (**SQLite**) con esquema normalizado.

### Entidades principales

- **Gestión de identidad:** `usuario`, `club`, `usuarioClub` (N:M).
- **Estructura deportiva:** `jugador`, `categoria`, `competencia`, `inscripcion`.
- **Gestión de listas:** `listaBuenaFe`, `jugadorListaBuenaFe`.
- **Eventos y estadísticas:** `partido`, `jugadorPartido` (20+ métricas: puntos, T1/T2/T3, rebotes, asistencias, etc.).

### Reglas de integridad

- Relación **1:1** entre `inscripcion` y `listaBuenaFe`. Una inscripción es club + competencia +
  categoría, y la temporada es el año de la competencia: el Asociativo 2026 y el Asociativo 2027
  son dos competencias, y cada una tiene sus propias listas por categoría y club.
- Un `partido` pertenece a una competencia **y a una categoría** (`idCategoria`, desde la US-108).
- El historial de afiliaciones de un jugador se mantiene vía `jugadorClub` (N:M con fechas).
- `jugadorPartido` actúa como **fact table** para el motor de análisis (Pandas lee desde acá vía las vistas SQL).

### Agregados estadísticos: por jugador (existe) y por club (falta, propuesto)

Hoy solo existe un agregado pre-calculado a nivel **jugador**: `v_jugador_totales_temporada` (suma todas sus filas de `jugadorPartido` agrupadas por año). No existe ningún agregado equivalente a nivel **club/equipo** — todo lo que hay hoy sobre clubes es o bien por-partido (`v_partidos_resumen`, un cruce puntual) o inexistente para series de tiempo/competencias.

Para que la app pueda responder "¿cómo viene mi equipo en toda la competencia?" o "¿cómo viene mi equipo este año, sumando todas las competencias?" (ver Hito 2/3, US-202/203/301), hace falta un agregado análogo, sumando **todos los jugadores de un club** en vez de uno solo. Conceptualmente sería una vista (o un cálculo equivalente en Pandas, ver nota de US-203) con esta forma:

- Agrupada por `idClub` + (`idCompetencia` **o** `anio`, según qué recorte se pida — nunca los dos mezclados, para no repetir el bug ya documentado en sección 20).
- Mismas métricas que `v_jugador_totales_temporada` (puntos, T1/T2/T3, rebotes, asistencias, recuperos, pérdidas, tapones, faltas, porcentajes), sumadas a nivel equipo en vez de individual.
- No requiere ninguna tabla ni columna nueva — sale enteramente de `jugadorPartido` join `club`, igual que el agregado de jugador.

**No se define el SQL exacto acá a propósito** — es una decisión de implementación para cuando se aborde la US-203, no algo a resolver en esta revisión del PRD.

---

## 4. Arquitectura de Software (Clean + Hexagonal)

### Capas y responsabilidades

- **Dominio** (`src/dominio/`): entidades puras, reglas de negocio, excepciones e interfaces (ports), sin dependencias externas.
- **Aplicación** (`src/aplicacion/`): casos de uso (`casos_uso/`) y DTOs (`dtos/`); orquesta reglas mediante inyección de dependencias.
- **Infraestructura** (`src/infraestructura/`): repositorios SQLite, parser Excel (Pandas), GUI (Flet) y generación de reportes.

### Regla de dependencias

```text
dominio  ←  aplicación  ←  infraestructura
```

`dominio` no puede importar `aplicación` ni `infraestructura`. `aplicación` puede importar `dominio`, pero no `infraestructura`.

### Patrones de diseño

- **Repository Pattern:** abstracción de persistencia por agregado (`UsuarioRepositorio`, `JugadorRepositorio`, etc.).
- **Dependency Injection:** los casos de uso reciben puertos (interfaces), no implementaciones concretas, por constructor.
- **Pantallas finas con registro de rutas:** cada pantalla de la GUI vive en su propio archivo de `screens/` y se registra en la tabla de navegación de `app.py`; agregar una pantalla no obliga a tocar las demás. Cumple el rol que tenía el Command Pattern en la CLI retirada (ver `docs/info_modulo/06-patron-command.md`).

### Estructura de directorios de referencia

```mermaid
---
config:
  treeView:
    showIcons: true
---
treeView-beta
  src/
    main.py :::highlight icon(logos:python) ## punto de entrada: abre la GUI (hasta la US-105, parser de la CLI)
    utils.py ## helpers puros compartidos (id_persistido; abortar y fecha_iso se revisan en la US-105)
    config/
      rutas.py ## rutas de la base, scripts SQL y logs
    dominio/
      entidades/ ## @dataclass puras, sin imports externos
      repositorios/ ## interfaces (ABC) de repositorios
      exceptions.py ## excepciones de negocio
      servicios/ ## interfaces (ABC) de servicios que no son repositorios (PasswordHasher, US-104)
    aplicacion/
      dtos/ ## dataclasses de entrada/salida entre capas
      servicios/ ## servicios de aplicación (SessionManager: US-105 en memoria, US-106 persistente)
      casos_uso/ ## orquestadores (reciben repos por DI), un archivo por acción
    infraestructura/
      logger.py ## ✅ configuración central del logging
      repositorios/ ## implementaciones SQLite de las interfaces de dominio
      persistencia/
        database_manager.py ## SQLiteManager y abrir_conexion()
        sql/
          schema.sql
          views.sql
          seed.sql
          limpieza.sql
      analytics/ ## motor Pandas
      ingest/ ## parser Excel
      reports/ ## generador PDF
      security/ ## Pbkdf2PasswordHasher (implementa dominio/servicios/PasswordHasher)
      ui/
        flet/ ## GUI (desde la US-105)
          app.py ## composition root de la GUI: arma repositorios, casos de uso y navegación
          screens/ ## una pantalla por archivo (login_screen.py, clubes_screen.py, ...)
          components/ ## piezas reutilizables (tabla_datos.py, chart_component.py)
tests/
  unit/ ## sin DB, con mocks (entidades, casos de uso, servicios, helpers)
  integration/ ## con SQLite real en memoria (repositorios, esquema, flujos de casos de uso)
  conftest.py ## fixtures compartidas y fábricas de datos (**overrides)
```

> **Convención de la GUI: una pantalla por archivo.** Cada pantalla vive en `screens/`, recibe los casos de uso que necesita
> por constructor y `app.py` la registra en la tabla de navegación. Reemplaza a la convención "un archivo por acción" de la
> CLI (`ui/cli/commands/`), que existió hasta la US-105.

### ¿Qué va en cada capa? Guía práctica

**Capa de Dominio (`src/dominio/`)** — el núcleo del sistema. No depende de ninguna tecnología concreta.

- **`entidades/`** — clases Python puras (`@dataclass`) que modelan los conceptos del básquet. Pueden tener métodos con lógica de negocio simple (validaciones, cálculos derivados). **No importan** `sqlite3`, `pandas` ni ningún framework. Ejemplo real: `Jugador.nombre_completo` y `JugadorPartido`, que en `__post_init__` verifica que los puntos coincidan con los tiros convertidos.
- **`repositorios/`** — interfaces abstractas (`ABC` + `@abstractmethod` en este proyecto — ver nota sobre `Protocol` en sección 19) que definen _qué_ operaciones existen sobre los datos, sin decir _cómo_. Ejemplo real: `JugadorRepositorio` declara `buscar_por_id`,
  `guardar`, sin una sola línea de SQL.
- **`exceptions.py`** — errores propios del negocio deportivo, todos hijos de `ErrorDeDominio`: `VinculoSuperpuestoError`, `EmailYaRegistradoError`, etc. (lista completa en la US-103 y la US-104).

**Capa de Aplicación (`src/aplicacion/`)** — orquesta el dominio para los casos de uso del usuario. No contiene lógica de negocio pura (eso va en dominio) ni detalles técnicos (eso va en infraestructura).

- **`casos_uso/`** — un archivo = una acción del usuario. Cada caso de uso recibe sus dependencias (repositorios, servicios) por constructor y expone un único método `ejecutar(dto)`. Ejemplo: `RegistrarJugadorUseCase.ejecutar(dto)` crea la entidad `Jugador` (que valida sus tipos), la persiste con `repo.guardar` y retorna un `JugadorDTO`. Detalle de los casos de uso implementados (17 de la US-103 y 2 de la US-104) en `docs/info_modulo/03-casos-de-uso.md`.
- **`dtos/`** — dataclasses simples, sin lógica, que viajan entre la GUI y los casos de uso (`CrearJugadorDTO` entra, `JugadorDTO` sale). Un archivo por entidad, con los DTOs de entrada y de salida juntos.
- **`servicios/`** — servicios transversales que no pertenecen a un caso de uso específico, como `SessionManager` (sesión del usuario y club activo) y `ExecutionContext` (propagación de `correlation_id` para logs).

**Capa de Infraestructura (`src/infraestructura/`)** — implementa los contratos del dominio con tecnologías concretas. Es la única capa que puede importar `sqlite3`, `pandas`, `flet`, `bcrypt`, etc.

- **`repositorios/`** — implementaciones SQLite de las interfaces de dominio. Cada clase hereda de su interfaz correspondiente (`SqliteJugadorRepositorio(JugadorRepositorio)`).
- **`persistencia/`** — infraestructura técnica de la base: `database_manager.py` (conexión, inicialización), archivos `.sql` (schema, vistas, seed), migraciones futuras. Sin lógica de negocio.
- **`analytics/`** — `formulas.py` (funciones puras sobre DataFrames), `pandas_analytics_service.py`, `chart_generator.py`.
- **`ingest/`** lectores de los archivos de Gesdeportiva (Excel y PDF) y servicio de ingesta.
- **`reports/`** generadores de PDF.
- **`ui/flet/`** — la GUI: pantallas y componentes. Llaman a casos de uso; nunca acceden a la base de datos directamente.
- **`security/`** — hashing de contraseñas, política de credenciales, adaptador de cifrado de DB.

### Data Transfer Objects (DTOs)

Un **DTO** es una clase simple cuya única responsabilidad es transportar datos entre capas — **no contiene lógica de negocio**.

**¿Por qué se usan?**

- **Desacoplamiento:** la UI no necesita conocer las entidades de dominio, y el dominio no se expone directamente al exterior.
- **Control de la frontera:** el DTO de entrada valida el formato antes de que el caso de uso lo procese; el DTO de salida define exactamente qué información se devuelve.
- **Evolución independiente:** se puede cambiar la entidad de dominio sin romper la UI, y viceversa.

**Patrón de uso:** cada caso de uso recibe un DTO de entrada (datos crudos del usuario) y retorna un DTO de salida (datos procesados para mostrar). Las entidades de dominio **nunca salen** de la capa de aplicación hacia la UI.

**Ejemplo — registrar un jugador:**

- `CrearJugadorDTO` (entrada): `nombre`, `apellido`, `anioNacimiento` (opcional). Solo datos planos, sin métodos.
- `RegistrarJugadorUseCase` recibe este DTO, crea la entidad `Jugador` con las reglas de dominio, y persiste.
- Retorna `JugadorDTO` (salida): `id`, `nombre_completo`, `anioNacimiento`. Solo lo que la interfaz necesita mostrar.

Ubicación: `src/aplicacion/dtos/`. Convención de nombres: `jugador_dto.py` puede contener tanto el DTO de entrada como el de salida para esa entidad.

### Gestión de sesión y club activo

La GUI es un único proceso que queda abierto, así que la sesión vive **en memoria** dentro del `SessionManager` mientras la app está abierta (US-105). Solo si el usuario marca **"Recordarme"** al iniciar sesión, el `SessionManager` además la guarda en `~/.statspro/session.json` para que sobreviva al cierre de la app (US-106). Es el único componente que lee y escribe ese archivo.

**Estructura del archivo de sesión** (`SessionDTO`, US-106):

- `usuario_id`: identificador del usuario autenticado.
- `email`: email del usuario (para mostrar en la UI).
- `club_activo_id`: ID del club seleccionado actualmente (`null` si no se seleccionó ninguno).

Sin token ni expiración en v0.1 (ver las decisiones de la US-106); la expiración configurable llega con el hardening de la US-403.

**¿Cómo se establece el `club_activo_id`?** (US-106)

1. Al iniciar sesión, el `SessionManager` crea la sesión con `club_activo_id = null`.
2. El usuario elige un club en la pantalla de clubes ("Usar este club").
3. La pantalla llama a `CambiarClubActivoUseCase`, que verifica que el club pertenezca al usuario.
4. Si la verificación pasa, el `SessionManager` actualiza el club activo (y el archivo, si hay "Recordarme").
5. Las pantallas operativas (jugadores, inscripciones, carga de partido) leen el club activo al abrirse; si no hay ninguno, llevan a la pantalla de clubes con un aviso.

> **¿Por qué club activo y no elegirlo en cada pantalla?** Un DT trabaja siempre en el contexto de un club. Tener el club activo en la sesión evita elegirlo de nuevo en cada formulario — el mismo patrón que usan los IDEs con el "proyecto activo".

### Composition Root: cómo se ensambla la aplicación

El **Composition Root** es el único lugar del sistema donde se instancian todas las dependencias y se conectan entre sí. Desde la US-105 ese lugar es `src/infraestructura/ui/flet/app.py`; `src/main.py` queda solo como punto de entrada que lo invoca.

> **Cómo era en la CLI (US-103/104, retirada en la US-105):** cada ejecución era un proceso nuevo que corría **un único comando**, así que cada comando armaba las dependencias que necesitaba (`ejecutar(args, repo=None)`). En la GUI el proceso queda abierto: `app.py` abre la conexión una vez al arrancar, arma repositorios, `PasswordHasher`, `SessionManager` y casos de uso, y se los pasa a cada pantalla por constructor. Los errores de negocio (`ErrorDeDominio`) los atrapa un único manejador común de la GUI y los muestra junto al formulario, sin traceback ni cierre de la app.

**¿Por qué es importante?** Porque en todos los demás archivos, las clases reciben sus dependencias como argumentos (nunca las crean con instanciación directa). Esto hace el sistema
testeable: en los tests se pueden pasar repositorios falsos (mocks) sin modificar el código de producción.

**Flujo de ensamblaje esperado en `app.py`** (crece con cada US):

1. **US-101/102:** se instancia `SQLiteManager`, se inicializa el esquema, se crean los repositorios SQLite pasando la conexión.
2. **US-105:** se crean `Pbkdf2PasswordHasher`, `SessionManager` (en memoria) y los casos de uso de autenticación; se registran las pantallas de login, registro e inicio.
3. **US-106/107:** se suma la persistencia de la sesión, la pantalla de clubes y las pantallas de gestión con los casos de uso administrativos de la US-103.
4. **US-108:** se crea `CargarPartidoUseCase` y se registra la pantalla de carga de partido.
5. **US-110:** se inicializa el `ExecutionContext` en cada acción del usuario y se conecta el logging estructurado.
6. **Hitos 2 a 4:** cada historia que suma una pantalla la registra acá, con sus casos de uso como dependencias.

**Regla de oro:** si una clase crea sus dependencias con `NombreClase()` dentro de un método que no sea el composition root, hay un problema de acoplamiento que debe corregirse.

---

## 5. Acuerdo de Ingeniería y Estándares

### Principios de desarrollo

- **Diseño precede a la implementación:** no se escribe código sin un diseño previo aprobado (ADR).
- **Atomicidad:** commits pequeños y lógicos. Formato: `tipo(alcance): descripción`.
- **Gestión de ramas:** `feature/nombre-tarea`, `hotfix/descripción`, `release/vX.Y`.
- **Higiene del repositorio:** prohibido subir binarios, bases SQLite con datos reales, o archivos temporales.

### Calidad de código y pruebas

- **Documentación:** estilo Javadoc/Doxygen (docstrings) para módulos y métodos públicos.
- **Pruebas:** cobertura mínima 80% en lógica de negocio; 95% en componentes críticos (ver Catálogo de Criticidad, sección 14).
- **Análisis estático:** `ruff`.

### Gestión de tareas — prioridad y esfuerzo

| Prioridad | Descripción                                   |
| --------- | --------------------------------------------- |
| Urgente   | Bloqueante; detiene el desarrollo de otras US |
| Alta      | Impacto directo en la entrega del hito        |
| Media     | Importante pero no bloquea el progreso        |
| Baja      | Mejora o refinamiento posterior               |

| Tamaño | Esfuerzo estimado    |
| ------ | -------------------- |
| XS     | Menos de 1 día hábil |
| S      | 1–2 días hábiles     |
| M      | 3–5 días hábiles     |
| L      | 6–10 días hábiles    |

---

## 6. Reglas de Negocio Consolidadas

Centraliza las reglas obligatorias del dominio para que desarrollo y testing sean coherentes en todas las historias de usuario.

**Identidad y Seguridad**:

- Email de usuario único por sistema.
- Contraseña nunca persistida en texto plano ni en logs.
- Sesión requiere usuario autenticado y, para pantallas operativas, club activo.

**Jugadores, Clubes y Afiliaciones**:

- Los jugadores **no tienen DNI** (decisión del 2026-10-31): no aporta a las estadísticas y los
  archivos de la CAB no lo traen. Un jugador se identifica por apellido y nombre **dentro de su
  club**; dos jugadores con el mismo nombre en clubes distintos son dos personas. El año de
  nacimiento es opcional.
- Un jugador no puede tener más de un vínculo activo (con ningún club), ni vínculos con períodos superpuestos.
- Historial de afiliación coherente en fechas: `fecha_hasta >= fecha_desde`.

**Competencias, Inscripciones y Listas**:

- Una inscripción es única por club + competencia + categoría (la temporada es el año de la
  competencia). Un jugador puede estar en varias listas: otra competencia, otra temporada o la
  misma categoría dos años seguidos.
- Cada inscripción tiene una única lista de buena fe asociada (1:1).
- En la carga manual de un partido (US-108), solo pueden figurar jugadores de la lista de buena fe
  de su club para la competencia y categoría del partido. La importación de una planilla de
  partido (US-201) o de un listado de la CAB (US-206) **genera o completa** esas listas en vez de
  rechazar a los jugadores.

**Partidos y Estadísticas**:

- Un partido no puede tener el mismo club como local y visitante.
- Se puede cargar **cualquier partido de la competencia**, aunque el club activo no juegue: cuantos
  más partidos de otros clubes haya, más confiables son las comparaciones (decisión del
  2026-10-31). Un club creado como rival o por importación no queda vinculado al usuario.
- Toda carga de partido y boxscore es atómica (todo o nada).
- Estadísticas de tiro: convertidos ≤ lanzados; todos los valores no negativos.
- Puntos de jugador = T1C + T2C×2 + T3C×3 (coherencia verificada).
- Minutos por jugador no pueden exceder el máximo reglamentario (hoy fijo en 48 en `JugadorPartido` y en el `CHECK` de la base; un máximo por competencia no está implementado).

**Analítica y Reporting**:

- Fórmulas avanzadas deben manejar división por cero y no devolver `NaN`/`inf`.
- Reportes y dashboards se construyen sobre vistas SQL normalizadas y versionadas.
- Toda exportación (PDF/backup) debe ser trazable en logs con timestamp y resultado.
- **Muestra chica** (decisión del 2026-10-31): un promedio sobre uno o dos partidos no dice nada.
  - Toda tabla o comparación muestra los partidos jugados (PJ) al lado de los promedios.
  - Los rankings de líderes exigen un mínimo de partidos (en `settings.py`, por defecto 3); quien
    no llega no entra al ranking.
  - Una comparación en la que alguno no llega al mínimo se muestra igual, con un aviso de muestra
    chica.
  - Además del promedio por partido se ofrece el valor cada 40 minutos jugados, para no castigar a
    quien juega pocos minutos. Solo se calcula para quien llega al mínimo de partidos: con muy
    pocos minutos, el valor cada 40 se dispara.

---

## 7. Requisitos No Funcionales (NFR)

| ID    | Requisito           | Medición / Umbral                                                                        | Severidad  |
| ----- | ------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| NFR-1 | Portabilidad        | Ejecución nativa en Windows 10+, Linux, macOS, Android 9+ (sin iOS — ver nota en US-404) | Bloqueante |
| NFR-2 | Rendimiento Ingesta | Procesamiento de Excel con Pandas < 5 seg                                                | Alta       |
| NFR-3 | Fiabilidad de Datos | Integridad referencial en SQLite (FKs activas)                                           | Bloqueante |
| NFR-4 | Usabilidad          | Carga de partido completo en < 3 clics desde selección de archivo                        | Media      |
| NFR-5 | Arranque            | Tiempo de inicio de la GUI < 3 seg en entorno objetivo                                   | Alta       |
| NFR-6 | Offline             | 100% de funcionalidades críticas sin conexión a internet                                 | Bloqueante |
| NFR-7 | Cobertura de Tests  | ≥80% no críticos; ≥95% en módulos críticos (ver Catálogo de Criticidad)                  | Alta       |

---

## 8. Registro de Decisiones Arquitectónicas (ADR)

| ID      | Título                     | Estado                                                                                    | Decisión                                                                                                                                           | Bloquea         |
| ------- | -------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| ADR-001 | Arquitectura Local-First   | Aprobado (`docs/adr/ADR-001-arquitectura-local-first.md`)                                 | SQLite + offline-first                                                                                                                             | Hito 1          |
| ADR-002 | Framework UI               | Aprobado (`docs/adr/ADR-002-framework-ui.md`)                                             | Flet (Python puro); se descarta Compose Multiplatform. Desde 2026-10-31 es la única interfaz (la CLI se retira)                                    | US-105          |
| ADR-003 | Protocolo de Ingesta       | Pendiente — propuesta con archivos reales (`docs/adr/ADR-003-protocolo-ingesta-excel.md`) | Mapeo fijo en código, buscando encabezados por texto; falta elegir la librería de PDF                                                              | US-201, US-206  |
| ADR-004 | Versionado de DB           | Pendiente — pregunta abierta (`docs/adr/ADR-004-versionado-db.md`)                        | Migraciones manuales vs. Alembic — falta decidir si vale agregar SQLAlchemy solo por el runner                                                     | Hito 2          |
| ADR-005 | Reportes PDF               | Aprobado (`docs/adr/ADR-005-reportes-pdf.md`)                                             | `reportlab`; se descarta `weasyprint`                                                                                                              | US-302          |
| ADR-006 | Seguridad y Cifrado        | Aprobado v0.1 / Pendiente v1.0 (`docs/adr/ADR-006-seguridad-cifrado.md`)                  | Hash de passwords con `pbkdf2_hmac` y salt dinámico; cifrado DB (SQLCipher) y migración a bcrypt/argon2 quedan para Hito 4, con preguntas abiertas | US-104 / Hito 4 |
| ADR-007 | Motor de Visualización     | Aprobado (`docs/adr/ADR-007-motor-visualizacion.md`)                                      | `matplotlib`; se descarta `plotly` para este motor                                                                                                 | US-301          |
| ADR-008 | Estrategia de Backup       | Aprobado (`docs/adr/ADR-008-estrategia-backup.md`)                                        | Exportación/restauración manual con `VACUUM INTO`/backup online de SQLite                                                                          | Hito 4          |
| ADR-009 | Pipeline CI/CD             | Aprobado, ya implementado (`docs/adr/ADR-009-pipeline-cicd.md`)                           | GitHub Actions (hosted) para lint, tests y cobertura automáticos                                                                                   | US-109          |

Estructura canónica de un ADR (ver `docs/documentacion_app_estadistica/ADR/template_adr.md`): Contexto → Alternativas Consideradas → Decisión Tomada → Ventajas y Desventajas. Los ADR escritos viven en `docs/adr/` (no en el submódulo de documentación, que es de otro repositorio). **Estado (2026-10-03): los 9 ADR ya están redactados en `docs/adr/`.** Aprobados sin preguntas
pendientes: ADR-001, ADR-002, ADR-005, ADR-007, ADR-008, ADR-009. Con preguntas abiertas a
resolver antes de cerrarlos del todo: ADR-003 (ya hay archivos reales; falta elegir la librería de PDF),
ADR-004 (manuales vs. Alembic) y ADR-006 (viabilidad de SQLCipher en Android y fuente de la lista
de contraseñas comprometidas, ambas para la parte de v1.0).

---

## 9. Hito 1 — Núcleo de Datos e Interfaz Gráfica Base (v0.1)

**Objetivo del hito:** construir una base técnica funcional con persistencia robusta, autenticación local, casos de uso operativos, validaciones de integridad, una interfaz gráfica de escritorio (Flet) que cubra la gestión completa y la carga de partidos, y un entorno de calidad que garantice reproducibilidad desde el primer commit.

**Épicas:** 3 · **Historias:** 10 (US-101 a US-110; la US-104 original se dividió en Autenticación
y Sesión el 2026-10-03, y el 2026-10-31 se agregó la US-105 de GUI base y se renumeraron las
siguientes — ver la tabla al inicio del documento) · **Esfuerzo total estimado:** ~60 días·persona

**Orden de ejecución:** US-101 → US-102 → US-103 → US-104 (todas ✅) → ajuste previo (quitar el
DNI, en paralelo con el arranque de la US-105) → US-105 → US-106 → US-107 → US-108 → US-110. La US-109 (CI/CD) es transversal: no depende de ninguna y se va completando a lo
largo del hito.

### Plan de trabajo en paralelo (equipo de dos, 2026-10-31)

Las dependencias de cada historia se refieren a la historia **completa**. Casi todas tienen una
parte de backend (casos de uso, repositorios, servicios) que no necesita la GUI y se prueba sola
con mocks o con SQLite en memoria. Por eso el trabajo se reparte en dos **pistas** que avanzan a la
vez. **Todas las historias pendientes salvo la US-105** tienen su bloque "Reparto en dos pistas"
con el detalle. La US-105 es bloqueante para todas las pantallas: la hace la Pista A, y la Pista B
solo aporta el `SessionManager` en memoria mientras avanza con el backend de las US-106 y US-107.

- **Pista A — interfaz:** pantallas, navegación y componentes de `ui/flet/`.
- **Pista B — backend:** casos de uso, DTOs, repositorios y servicios.
- En las historias **sin interfaz** (US-204, US-202, US-203, US-402, US-403) las dos pistas son de
  backend y se dividen por componente; cada bloque dice qué es de cada una.
- Cuando una pista consume lo que produce la otra (un DTO, una firma de función), lo primero de la
  historia es **acordar ese contrato juntos**; después cada uno avanza con un falso del otro lado.

Las pistas se cruzan a propósito en la ronda 2 (B también hace pantallas), para que los dos
integrantes pasen por las dos capas.

| Ronda | Pista A                                                                          | Pista B                                                                                                   |
| ----- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 1     | US-105: esqueleto Flet, pantallas de acceso, retiro de la CLI                    | US-105: `SessionManager` en memoria (**primero**); el ajuste previo (quitar el DNI); después backend de la US-106 y de la US-107 |
| 2     | US-106: pantallas de sesión y clubes; US-107: `tabla_datos.py` (**primero**), jugadores y partidos | US-107: pantallas de competencias, inscripciones y listas de buena fe                       |
| 3     | US-108: `CargaPartidoScreen`                                                     | US-108: categoría del partido, clubes de terceros, `CargarPartidoUseCase` y sus DTOs                      |
| 4     | US-110: conectar los eventos de log a las acciones de las pantallas             | US-204 (migraciones), si el ADR-004 ya está decidido                                                      |

Las rondas marcan orden, no duración: una ronda termina cuando las dos pistas mergearon.

**Trabajo suelto** (sin dependencias con la GUI, para quien termine antes su parte de una ronda):
la Pista A de la US-202 (`formulas.py`), la Pista B de la US-110 (núcleo de logging) y la US-109.

**Hitos 2 a 4 — orden y paralelismo entre historias.** Dentro de cada historia, las dos pistas van
en paralelo. Entre historias se respeta el orden de dependencias, con estas excepciones que permiten
tener dos historias abiertas a la vez si una pista se queda sin trabajo:

- La **US-206** (listado de jugadores de la CAB) va antes que la US-201: fija la librería de PDF
  y el servicio que identifica jugadores sin DNI, que la US-201 reusa. Se pueden solapar: apenas
  se acuerda la firma de `IdentificadorJugadores`, quien termine primero su parte de la US-206
  arranca el `IngestService` de la US-201 con un falso de ese servicio.
- El ADR-003 ya tiene archivos reales (`data/`, 2026-10-31): falta elegir la librería de PDF y
  confirmar el mapeo, pero ya no espera datos. Si igual se traba, la cadena US-201 → US-202 (casos
  de uso) → US-203 → US-205 espera y se adelantan la US-402 y la US-403, que no dependen de ella.
- La **US-402** (backup) solo depende de la US-204: puede hacerse en cualquier momento después.
- La **US-403** (seguridad) solo depende de las US-104 y US-106 y del ADR-006: puede hacerse en
  cualquier momento después del Hito 1.
- La **US-303** (scouting) solo depende de la US-203: puede ir en paralelo con las US-301 y US-302.

**Decisiones que se toman juntos, antes de la ronda que las necesita:**

| Antes de | Decisión                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------ |
| Ronda 1  | Versión de Flet y cómo se testean las pantallas (US-105)                                         |
| Ronda 2  | Si la sesión se guarda a través de un puerto (US-106)                                            |
| Ronda 3  | Los DTOs de carga (US-108), que son el contrato entre las dos pistas                             |
| Ronda 4  | ADR-004 (migraciones manuales o Alembic)                                                         |

**Dónde chocan las dos pistas y cómo evitarlo:**

- `app.py`: los dos registran pantallas en la tabla de rutas → una línea por pantalla y PRs chicos.
- `pyproject.toml` / `uv.lock`: una sola persona agrega dependencias por ronda; si igual chocan,
  se regenera con `uv lock` en vez de resolver el lock a mano.
- `partido_dto.py`: lo tocan la US-107 (`BoxscoreFilaDTO`) y la US-108 → mergea primero la US-107.
- La CLI y los archivos de jugador: el ajuste previo (Pista B) toca la CLI, la entidad `Jugador` y
  sus tests, y la US-105 (Pista A) borra la CLI → la Pista A borra la CLI recién cuando el ajuste
  está mergeado, y mientras tanto avanza con las pantallas.

### Épica H1-E1: Infraestructura y Persistencia

#### US-101 — Esquema SQLite, Vistas y Datos Semilla

**Esfuerzo:** L (6-10 días) · **Prioridad:** Urgente (bloqueante) · **Estado:** ✅ Hecha

**Objetivo Funcional:** habilitar un esquema relacional local verificable y un conjunto de vistas operativas que sirvan de contrato estable para todo el ciclo del producto, garantizando que Pandas y la capa de aplicación consuman datos sin transformaciones ambiguas.

**Narrativa:** Como desarrollador, quiero el esquema relacional completo en SQLite, con sus vistas de análisis y datos de prueba, para tener una base verificable sobre la que construir el sistema.

**Capa de Infraestructura:**

- **Clase `SQLiteManager`** (`src/infraestructura/persistencia/database_manager.py`):
  - `connect()`: retorna una conexión activa con `PRAGMA foreign_keys = ON` y `row_factory = sqlite3.Row`.
  - `inicializar_schema()`: ejecuta de forma atómica los scripts `schema.sql`, `views.sql` (y opcionalmente `seed.sql`) usando `executescript()`.
- **Scripts SQL** (`src/infraestructura/persistencia/sql/`):
  - `schema.sql`: DDL completo, tablas con tipos estrictos, PK, FK, `CHECK` constraints y `CREATE TABLE IF NOT EXISTS`. **Sin `DROP TABLE`:** se ejecuta en cada arranque de la app y no puede borrar datos (se corrigió en la US-103; ver ahí).
  - `views.sql`: las 4 vistas de análisis estadístico.
  - `seed.sql`: datos de prueba (1 usuario, 2 clubes, 10 jugadores, 1 competencia, ≥ 2 partidos con boxscore).

**Vistas a implementar:**

1. `v_partidos_resumen`: une partido con clubes y competencia (reemplaza IDs por nombres).
2. `v_boxscore_completo`: une `jugadorPartido` con jugador y club (fuente principal para Pandas).
3. `v_jugador_totales_temporada`: acumulados históricos por jugador y año de competencia.
4. `v_listas_detalle`: jugadores habilitados por inscripción.

**Criterios de Aceptación:**

- **AC1.** Schema idempotente: `CREATE TABLE IF NOT EXISTS` en toda la DDL.
- **AC2.** FKs activas con reglas `ON DELETE/UPDATE CASCADE` en relaciones críticas.
- **AC3.** `CHECK` constraints en métricas numéricas (ej. `puntos >= 0`, `minutosJugados BETWEEN 0 AND 48`) y en integridad lógica (ej. `idClubLocal != idClubVisitante`).
- **AC4.** El campo `dni` en `jugador` es `UNIQUE` pero permite `NULL`. _(se quita en el ajuste previo a la US-105)_
- **AC5.** Las 4 vistas exponen columnas con nombres y tipos estables, documentados; todas las divisiones usan `NULLIF`/`CASE` para nunca fallar por división por cero.
- **AC6.** `seed.sql` se ejecuta limpiamente sobre un schema vacío y puebla todas las tablas con datos significativos para las vistas.
- **AC7.** Columnas de vistas estables para consumo desde Pandas sin transformaciones adicionales.

**Reglas de Negocio (nivel DB):**

- `CHECK(idClubLocal != idClubVisitante)` en `partido`.
- `fechaHasta >= fechaDesde` en historial de afiliaciones.
- `UNIQUE` en `listaBuenaFe.idInscripcion` (refuerza la relación 1:1).

**Entidades/Modelos implicados:** `usuario`, `club`, `usuarioClub`, `jugador`, `categoria`, `competencia`, `inscripcion`, `listaBuenaFe`, `jugadorListaBuenaFe`, `jugadorClub`, `partido`, `jugadorPartido`.

**Testing Mínimo:**

- _Integración (`test_database.py`):_ existencia de tablas/vistas, FK inexistente → `IntegrityError`, valores negativos → falla, vistas devuelven datos tras el seed, vistas devuelven 0.0, nunca error.

#### US-102 — DatabaseManager y Patrón Repository

**Esfuerzo:** M (3-5 días) · **Prioridad:** Urgente (bloqueante) · **Dependencias:** US-101 · **Estado:** ✅ Hecha

**Objetivo Funcional:** implementar el orquestador de conexión y las interfaces de persistencia bajo Clean Architecture, asegurando que el acceso a datos sea independiente del motor de base de datos y garantizando la integridad referencial.

**Narrativa:** Como desarrollador, quiero una capa de infraestructura que gestione el ciclo de vida de la conexión SQLite y exponga repositorios tipados para cada agregado del dominio.

**Capa de Dominio — Interfaces (`src/dominio/repositorios/`):** las firmas reales ya migraron de "parámetros sueltos" a **recibir la dataclass completa**

- `UsuarioRepositorio`: `encontrar_por_mail(email)`, `encontrar_por_id(id)`, `guardar(usuario: Usuario)`.
- `ClubRepositorio`: `buscar_por_id_usuario`, `buscar_por_id`, `buscar_por_nombre`, `guardar(club: Club)`, `link_user_to_club(us_club: UsuarioClub)`.
- `JugadorRepositorio`: `buscar_por_id`, `buscar_por_dni` _(se quita en el ajuste previo a la US-105)_, `buscar_por_club`, `guardar(jugador: Jugador)`, `link_to_club(jc: JugadorClub)`, `club_activo`.
- `CompetenciaRepositorio`: `guardar_competencia(compe:Competencia)`, `buscar_competencia_por_id`, `obtener_todas_competencias`, `guardar_categoria(cat:Categoria)`, `obtener_categorias`, `guardar_inscripcion(inscripcion: Inscripcion)`, `buscar_inscripcion_por_id`, `obtener_inscripciones_por_club`, `guardar_lista_buena_fe(listaBF: ListaBuenaFe)`, `obtener_lista_por_inscripcion` _(tipada `-> ListaBuenaFe` singular, coherente con la relación 1:1)_, `agregar_jugador_lista(idJugador, idListaBuenaFe)` y `obtener_jugadores_lista`.
- `PartidoRepositorio` (antes `JuegoRepositorio`): `buscar_por_club`, `buscar_por_id`, `guardar_partido(partido: Partido)`, `guardar_boxscore(boxscore: JugadorPartido)`, `save_with_boxscore` (atómico) y `resumen_por_club` (US-103).

**Capa de Infraestructura:**

- **Clase `SQLiteManager`:** administra la conexión; `connect()` activa `PRAGMA foreign_keys` y `row_factory = sqlite3.Row`, retornando la conexión activa si ya existe; `inicializar_schema()` ejecuta `schema.sql` + `views.sql` en una sola llamada atómica.
- **Implementaciones concretas** (`src/infraestructura/repositorios/`): `SqliteUsuarioRepositorio`, `SqliteClubRepositorio`, `SqliteJugadorRepositorio`, `SqliteCompetenciaRepositorio`, `SqlitePartidoRepositorio` (antes `SqliteJuegoRepositorio`). `SqliteCompetenciaRepositorio` maneja competencia, categoria, inscripcion, listaBuenaFe y jugadorListaBuenaFe como un único agregado competitivo. Cada repositorio mapea manualmente `sqlite3.Row` a las dataclasses de dominio mediante un método privado `_row_to_entity()`.

**Criterios de Aceptación:**

- **AC1 — Gestión de Conexión:** `connect()` garantiza integridad referencial y acceso por nombre de columna.
- **AC2 — Abstracción Total:** la capa `dominio/` no importa `sqlite3`, `pandas` ni ninguna librería de infraestructura.
- **AC3 — Mapeo de Datos:** los repositorios retornan objetos `@dataclass` puros, nunca tuplas de SQLite.
- **AC4 — Transaccionalidad:** `SqlitePartidoRepositorio.save_with_boxscore()` (ya implementado) guarda partido y boxscore en una sola transacción multi-tabla, para asegurar la integridad de la carga de partidos.

**Reglas de Negocio:**

- Validación de DNI duplicado al guardar un jugador (lanza excepción de dominio). _(se quita en el ajuste previo a la US-105)_
- Uso de `cursor.lastrowid` para retornar la entidad con el ID asignado por la base de datos.

**Entidades/Modelos implicados:** `Usuario`, `Club`, `Jugador`, `JugadorClub`, `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`, `Partido`, `JugadorPartido`.

**Vistas SQL necesarias:** `v_partidos_resumen` y `v_boxscore_completo` para optimizar las consultas de lectura en los repositorios.

**Testing Mínimo:**

- _Integración (`tests/integration/test_repositorios_*.py`, un archivo por repositorio):_ CRUD completo por repositorio usando DB `:memory:`; `buscar_por_dni` retorna `None` si no existe, sin lanzar excepción; el `save()` de un partido y sus estadísticas es atómico; los repositorios de lectura usan las vistas SQL correctamente.

**Archivos a crear (consolidado, nombres en español):**

```mermaid
---
config:
  treeView:
    showIcons: true
---
src/
  dominio/
    repositorios/
      usuario_repositorio.py
      club_repositorio.py
      jugador_repositorio.py
      competencia_repositorio.py
      partido_repositorio.py
  infraestructura/
    repositorios/
      sqlite_usuario_repositorio.py
      sqlite_club_repositorio.py
      sqlite_jugador_repositorio.py
      sqlite_competencia_repositorio.py
      sqlite_partido_repositorio.py
```

### Épica H1-E2: Lógica de Aplicación e Interfaz

#### US-103 — Gestión de Entidades (Casos de Uso Administrativos)

**Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-101, US-102 · **Estado:** ✅ Hecha

> **La CLI de esta historia se retira en la US-105 (2026-10-31).** Siguen vigentes las entidades,
> los casos de uso, los DTOs, los repositorios y sus tests; los comandos de `ui/cli/`, el
> formatter de `tabulate` y los tests de la CLI se borran y sus funciones pasan a las pantallas
> de las US-106 y US-107. El texto de abajo describe lo que se construyó en su momento.

**Objetivo Funcional:** implementar la lógica de negocio pura y la interfaz de usuario por comandos para la gestión integral de las entidades del sistema (jugadores, clubes, competencias, inscripciones), asegurando la validación de reglas deportivas y la integridad de los datos.

**Narrativa:** Como administrador, quiero disponer de casos de uso con lógica de negocio validada para gestionar el ciclo de vida de los jugadores y sus afiliaciones, así como la estructura de competencias y clubes.

**Capa de Dominio:**

- **Entidades:** `Usuario`, `Club`, `Jugador`, `JugadorClub` (historial N:M jugador-club), `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`, `Partido`, `JugadorPartido`. `@dataclass` puras, serializables, sin dependencias externas.
- **Lógica de validación** (`__post_init__` de entidades): tipos de todos los campos (`TypeError`: bug del programa); y **reglas de valor** (`DatoInvalidoError`: error del usuario, llega a la CLI como mensaje): nombres de `Club`, `Jugador` (nombre y apellido), `Competencia` y `Categoria` no vacíos (ni solo espacios); `Jugador.dni` mayor a 0 _(se quita en el ajuste previo a la US-105)_; `Jugador.anioNacimiento` mayor a 1900 y no posterior al año actual; `Competencia.anio` mayor a 1900 ; en `JugadorPartido`, tiros convertidos ≤ lanzados, minutos entre 0 y 48, valores no negativos y `puntos = T2C·2 + T3C·3 + T1C`.
- **Modelo de lectura:** `PartidoResumen` (dataclass sin validación, es lo que devuelve la vista `v_partidos_resumen`: fecha, estadio, competencia, año y nombres de los dos clubes).
- **Propiedades calculadas:** `Jugador.nombre_completo` y `JugadorPartido.rebotes_totales` (defensivos + ofensivos); no se guardan en la base.
- **Excepciones** (`src/dominio/exceptions.py`), todas hijas de `ErrorDeDominio`: `DNIDuplicadoError` _(se quita en el ajuste previo a la US-105)_, `ClubNoEncontradoError`, `JugadorNoEncontradoError`, `CompetenciaNoEncontradaError`, `CategoriaNoEncontradaError`, `InscripcionDuplicadaError`, `VinculoActivoExistenteError`, `CategoriaDuplicadaError`, `InscripcionNoEncontradaError`, `ListaBuenaFeNoEncontradaError`, `JugadorYaEnListaError`, `JugadorNoPerteneceAlClubError`, `JugadorNoEstaEnListaError`, `JugadorSinVinculoActivoError`, `VinculoSuperpuestoError`, `DatoInvalidoError` (además hereda de `ValueError`, para que el código que ya atrapaba `ValueError` siga funcionando), `UsuarioNoEncontradoError` y `CredencialesInvalidasError`.

**Capa de Aplicación** ✅ (`src/aplicacion/`):

- **Casos de uso** (`casos_uso/`, método `ejecutar()`):
  - `RegistrarJugadorUseCase` (crea la entidad y el repositorio rechaza el DNI duplicado _(se quita en el ajuste previo a la US-105)_),
  - `CrearClubUseCase`,
  - `VincularJugadorAClubUseCase` (verifica que existan jugador y club, evita vínculos activos duplicados y que el vínculo nuevo se superponga con uno anterior),
  - `CrearCompetenciaUseCase`,
  - `InscribirClubEnCompetenciaUseCase` (valida club, competencia y categoría, evita la inscripción duplicada y genera la `listaBuenaFe` vacía asociada, 1:1, **de forma atómica** con `CompetenciaRepositorio.inscribir_con_lista`),
  - `ListarClubesUsuarioUseCase`
  - `ListarJugadoresClubUseCase` (solo vínculos vigentes),
  - `ListarPartidosPorClubUseCase` (devuelve `PartidoResumenDTO` con nombres, desde la vista)
  - `CambiarClubActivoUseCase` (valida que el club exista y pertenezca al usuario; guardar el club en la sesión es de la US-106).
  - `CrearCategoriaUseCase` (no permite nombres repetidos, sin importar mayúsculas ni espacios de los extremos),
  - `ListarCategoriasUseCase`,
  - `ListarCompetenciasUseCase`,
  - `ListarInscripcionesClubUseCase` (devuelve también el id de la lista de cada inscripción),
  - `AgregarJugadorAListaBuenaFeUseCase` (habilita a un jugador en la lista de una inscripción)
  - `ListarListaBuenaFeUseCase` (los jugadores habilitados, con su nombre).
  - `DesvincularJugadorDeClubUseCase` (cierra el vínculo vigente con una fecha de baja no anterior a su inicio)
  - `QuitarJugadorDeListaBuenaFeUseCase` (deshace una habilitación).
- **DTOs** (`dtos/`):
  - `CrearJugadorDTO`
  - `JugadorDTO`
  - `CrearClubDTO`
  - `ClubDTO`
  - `VincularJugadorClubDTO`
  - `CrearCompetenciaDTO`
  - `CompetenciaDTO`
  - `InscribirClubDTO`
  - `InscripcionDTO`
  - `PartidoResumenDTO`
  - `CrearCategoriaDTO`
  - `CategoriaDTO`
  - `AgregarJugadorListaDTO`
  - `JugadorEnListaDTO`
  - `DesvincularJugadorDTO`
  - `VinculoDTO`
  - `QuitarJugadorListaDTO`.
- **`src/utils.py`:** helpers puros compartidos (`id_persistido`, `abortar`, `fecha_iso`), sin dependencias de `infraestructura`.

**Capa de Infraestructura:**

- **`src/main.py`** es el composition root de la CLI (no existe un `main_cli.py` separado): arma el parser raíz con un subparser por entidad (`club`, `jugador`, `competencia`, `partido`), inicializa la base y despacha el comando. Un único `except ErrorDeDominio` en `main()` muestra los errores de negocio como `Error: ...` en stderr, con código de salida 1 y sin traceback.
- **Comandos CLI** (`src/infraestructura/ui/cli/commands/`): **un archivo por acción** con flags de `argparse` (no prompts interactivos): `jugador_add.py`, `jugador_link.py`, `jugador_unlink.py`, `jugador_list.py`, `club_add.py`, `club_list.py` (con `--id-usuario` provisorio hasta que exista la sesión), `competencia_add.py`, `competencia_inscribir.py`, `competencia_list.py`, `categoria_add.py`, `categoria_list.py`, `inscripcion_list.py`, `lista_add.py`, `lista_remove.py`, `lista_list.py` y `game_list.py` (`stats partido list`). Cada uno expone `ejecutar(args, repo=None)`: en producción arma el repositorio real con `abrir_conexion()`; en los tests se le inyecta uno falso.
- **Repositorios:** se agregaron `JugadorRepositorio.historial_vinculos` y `cerrar_vinculo`, `CompetenciaRepositorio.quitar_jugador_lista` y `PartidoRepositorio.resumen_por_club` (lee `v_partidos_resumen`, que ahora también expone `id_club_local` e `id_club_visitante` para poder filtrar por club).
- **`formatters/table_formatter.py`**: wrapper de `tabulate`; todos los listados pasan por acá (AC4).
- **`persistencia/database_manager.py`:** se agregó `abrir_conexion()`. Además se corrigió `schema.sql`, que empezaba con `DROP TABLE` y borraba todos los datos en cada arranque de la CLI.
- **Dependencias:** `tabulate` (runtime), declarada en `pyproject.toml` junto con el resto (versiones fijas, `uv.lock`, sin `requerimientos.txt`).

**Criterios de Aceptación:**

- **AC1 — Independencia de Dominio:** los archivos en `dominio/entidades/` no importan librerías externas.
- **AC2 — Inyección de Dependencias:** todos los casos de uso reciben sus repositorios vía constructor, usando las interfaces (ABC).
- **AC3 — Validación Fail-Fast:** DNI duplicado o datos inválidos cortan el flujo de la CLI con mensajes de error amigables, sin tracebacks (un solo `except ErrorDeDominio` en `main()`; los valores inválidos de una entidad —nombre vacío, DNI negativo, año imposible— llegan como `DatoInvalidoError`, que es un `ErrorDeDominio`, y se muestran igual).
- **AC4 — Formato de Salida:** los listados se formatean como tablas en consola (`tabulate`). Los comandos que crean algo imprimen una línea de confirmación.
- **AC5 — Atomicidad:** la inscripción y su lista de buena fe se guardan en una única transacción (`inscribir_con_lista`).

**Reglas de Negocio:**

- DNI de jugadores numérico, positivo y único _(se quita en el ajuste previo a la US-105)_. Nombre y apellido no vacíos. Año de nacimiento mayor a 1900 y no posterior al año actual.
- Un jugador no puede estar vinculado activamente (sin `fecha_hasta`) a más de un club (ni al mismo club dos veces).
- **Cambio de club:** para pasar a otro club primero se cierra el vínculo vigente (`jugador unlink --fecha-hasta`); la fecha de baja no puede ser anterior al inicio del vínculo, y el vínculo nuevo no puede empezar antes de la baja del anterior (no se superponen períodos). El historial completo queda en `jugadorClub`.
- Un club no puede inscribirse dos veces en la misma competencia y categoría.
- No puede haber dos categorías con el mismo nombre (se compara sin distinguir mayúsculas ni espacios de los extremos).
- **Lista de buena fe:** solo se puede habilitar a un jugador que **existe**, que tiene un **vínculo vigente con el club de la inscripción** y que **todavía no está** en esa lista.
- **Quitar de la lista:** solo se puede quitar a un jugador que **está** en la lista de esa inscripción (si no, `JugadorNoEstaEnListaError`). Quitarlo no lo borra del sistema ni del club: solo deshace la habilitación.
- Porcentajes y totales en estadísticas se validan antes de la persistencia.

**Testing Mínimo**:

- _Unitarios (`tests/unit/`):_ validación de entidades (tipos, valores —vacíos, rangos— y las reglas de `JugadorPartido`), propiedades calculadas, jerarquía de excepciones de dominio, los 17 casos de uso con repositorios falsos (`unittest.mock`) —camino feliz y una prueba por cada excepción—, comandos de la CLI (con `capsys`) y helpers.
- _Integración (`tests/integration/`):_ persistencia real en DB `:memory:` (repositorios, esquema y vistas, atomicidad de la inscripción) y la CLI de punta a punta contra una base temporal.

**Archivos:**

```text
src/dominio/entidades/
├── usuario.py
├── club.py
├── jugador.py
├── jugador_club.py
├── competencia.py
├── categoria.py
├── inscripcion.py
├── lista_buena_fe.py
├── jugador_lista_buena_fe.py
├── partido.py
└── estadistica_jugador.py

src/aplicacion/casos_uso/
├── registrar_jugador.py
├── crear_club.py
├── vincular_jugador_club.py
├── desvincular_jugador_club.py
├── crear_competencia.py
├── inscribir_club_competencia.py
├── listar_clubes_usr.py
├── listar_jugador_club.py
├── partidos_por_club.py
├── cambiar_club_activo.py
├── crear_categoria.py
├── listar_categorias.py
├── listar_competencias.py
├── listar_inscripciones_club.py
├── agregar_jugador_lista.py
├── listar_lista_buena_fe.py
└── quitar_jugador_lista.py

src/infraestructura/ui/cli/
├── commands/
│   ├── jugador_add.py               ✅ stats jugador add
│   ├── jugador_link.py              ✅ stats jugador link
│   ├── jugador_unlink.py            ✅ stats jugador unlink
│   ├── jugador_list.py              ✅ stats jugador list
│   ├── club_add.py                  ✅ stats club add
│   ├── club_list.py                 ✅ stats club list  (--id-usuario provisorio)
│   ├── competencia_add.py           ✅ stats competencia add
│   ├── competencia_inscribir.py     ✅ stats competencia inscribir
│   ├── competencia_list.py          ✅ stats competencia list
│   ├── categoria_add.py             ✅ stats categoria add
│   ├── categoria_list.py            ✅ stats categoria list
│   ├── inscripcion_list.py          ✅ stats inscripcion list
│   ├── lista_add.py                 ✅ stats lista add
│   ├── lista_remove.py              ✅ stats lista remove
│   ├── lista_list.py                ✅ stats lista list
│   └── game_list.py                 ✅ stats partido list
└── formatters/
    └── table_formatter.py
```

#### US-104 — Autenticación de Usuarios

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103 · **Estado:** ✅ Hecha (PR #46)

> **Los comandos `stats auth ...` de esta historia se retiran en la US-105**, que pone el
> registro y el login en pantallas de la GUI usando los mismos casos de uso. El hasher, los casos
> de uso, los DTOs y sus tests no cambian.

**Objetivo Funcional:** permitir el registro y el acceso seguro de entrenadores al sistema, con contraseñas hasheadas y nunca almacenadas en texto plano.

**Narrativa:** Como usuario, quiero poder registrarme y loguearme de forma local, con mis credenciales protegidas.

**Capa de Dominio:**

- **Entidad `Usuario`:** se renombra el campo `pw` a `password_hash` (claridad, sin agregar un campo `salt` separado: el salt va embebido en el propio string que devuelve `PasswordHasher.hash()`, formato estándar de `pbkdf2`/`bcrypt` — no hace falta tocar la columna `contrasenia` de la tabla `usuario`). Se agregan las validaciones de valor que al resto de las entidades (`Club`, `Jugador`, etc.) ya les llegaron en la US-103 y a `Usuario` no: `nombre`/`email` no vacíos (`DatoInvalidoError`), con el mismo `__post_init__` que ya usan las demás entidades.
- **Excepción nueva:** `EmailYaRegistradoError` (hija de `ErrorDeDominio`).

**Capa de Aplicación:**

- **Casos de uso:** `RegistrarEntrenadorUseCase` (rechaza email duplicado con `EmailYaRegistradoError`, usando `UsuarioRepositorio.encontrar_por_mail`), `LoginLocalUseCase` (`CredencialesInvalidasError` si el email no existe o la contraseña no verifica, sin distinguir cuál de los dos pasó, para no filtrar si un email está registrado).
- **DTOs:** `RegistrarDTO`, `LoginDTO`.

**Capa de Infraestructura:**

- **Seguridad:** la interfaz `PasswordHasher` (ABC) vive en `src/dominio/servicios/password_hasher.py` y la implementación `Pbkdf2PasswordHasher` en `src/infraestructura/security/password_hasher.py` (mismo patrón que los repositorios: el caso de uso depende de la interfaz). Solo dos métodos públicos: `hash(password) -> str` y `verify(password, password_hash) -> bool`. El hash guardado tiene el formato `pbkdf2_sha256$iteraciones$salt$hash` (600.000 iteraciones por defecto; `verify` usa las iteraciones guardadas en el propio hash).
  - **Decisión tomada:** v0.1 usa `hashlib.pbkdf2_hmac` con **salt dinámico** (uno distinto por usuario, generado con `os.urandom` al registrarse y guardado junto al hash en el mismo string) — no salt fijo. Migrar a `bcrypt`/`argon2-cffi` queda para v1.0, sin cambiar la interfaz pública de `PasswordHasher`.
- **CLI (retirada en la US-105):** `stats auth register`, `stats auth login`, `stats auth logout` (`auth_register.py`, `auth_login.py`, `auth_logout.py` en `ui/cli/commands/`). `auth_logout` solo informaba "no hay sesión que cerrar".

**Criterios de Aceptación:**

- **AC1 — Seguridad de Credenciales:** las contraseñas NUNCA se almacenan ni se loguean en texto plano. Hashing con salt dinámico por usuario.
- **AC2 — Validaciones:** email único (`EmailYaRegistradoError`); contraseña con requisitos mínimos (≥6 caracteres en v0.1; ≥12 con complejidad en v1.0, ver US-403).

**Testing Mínimo:**

- _Unitarias:_ `hash`/`verify` de `PasswordHasher` (incluye que dos hashes de la misma contraseña sean distintos, por el salt dinámico); `RegistrarEntrenadorUseCase`/`LoginLocalUseCase` con `UsuarioRepositorio` mock (camino feliz + `EmailYaRegistradoError` + `CredencialesInvalidasError`).
- _Integración:_ flujo completo registro → login con DB `:memory:`.

**Archivos a crear:**

```text
src/dominio/servicios/
└── password_hasher.py        ← interfaz PasswordHasher (ABC)

src/infraestructura/security/
└── password_hasher.py        ← Pbkdf2PasswordHasher

src/aplicacion/casos_uso/
├── registrar_entrenador.py
└── login_local.py

src/aplicacion/dtos/
└── auth_dto.py

src/infraestructura/ui/cli/commands/   ← se borran en la US-105
├── auth_register.py
├── auth_login.py
└── auth_logout.py

tests/unit/
├── test_password_hasher.py
├── test_uc_auth.py
└── test_cli_auth.py            ← se borra en la US-105
tests/integration/
└── test_auth_flujo.py
```

#### Ajuste previo a la US-105 — Quitar el DNI de los jugadores

> **No es una historia de usuario:** es un cambio chico sobre código ya terminado (US-101 a US-103)
> que conviene hacer antes de seguir, para no arrastrarlo. Va en su propia rama, por ejemplo
> `feature/quitar-dni-jugador`. No es un `hotfix/`: según la sección 15, esas ramas son para bugs
> en producción y salen de `main`, y todavía no hay ninguna versión entregada.

- **Decisión (2026-10-31):** los jugadores **no tienen DNI**. No aporta a las estadísticas, los
  archivos de la CAB no lo traen (US-201, US-206) y pedirlo obligaba a inventar DNIs para los
  jugadores rivales. Un jugador se identifica por apellido y nombre dentro de su club. El año de
  nacimiento pasa a ser opcional por el mismo motivo.
- **Esfuerzo:** S (1-2 días) · **Dependencias:** ninguna · **Lo hace:** la Pista B en la ronda 1,
  después del `SessionManager` (ver "Plan de trabajo en paralelo").
- **Qué cambia:**
  - **Base de datos:** se quita `jugador.dni` de `schema.sql` y de `seed.sql`. Una base vieja sigue
    funcionando (la columna acepta nulos), así que recrear la base local puede esperar a la US-108,
    que igual lo pide, y hacerse una sola vez.
  - **Dominio:** `Jugador` sin `dni` y con `anioNacimiento: int | None`; se borra
    `DNIDuplicadoError`; `JugadorRepositorio` pierde `buscar_por_dni`.
  - **Aplicación:** `CrearJugadorDTO` sin `dni`; `RegistrarJugadorUseCase` sin la regla de DNI
    duplicado.
  - **Infraestructura:** `SqliteJugadorRepositorio` (`guardar`, el armado de la entidad y
    `buscar_por_dni`). La CLI existe hasta la US-105, así que `jugador add` y `main.py` pierden
    `--dni`.
  - **Tests:** los que arman jugadores con DNI o prueban el duplicado: `conftest.py`,
    `test_entidades.py`, `test_entidades_valores.py`, `test_uc_jugadores.py`,
    `test_repositorios_jugador.py`, `test_repositorios_competencia.py`, `test_database.py`,
    `test_sandbox_sql.py` y los de la CLI.
  - **Documentación del código actual**, en el mismo PR que el código porque describe lo que el
    código hace hoy: `docs/info_modulo/03-casos-de-uso.md`, `04-arquitectura.md`,
    `07-protocolos.md`, `09-testing.md`, `docs/arquitectura/01-repository-pattern.md`, el DER de
    `docs/diagramas/diagramas.md`, `RUNBOOK.md` y `README.md`.
- **Criterios de Aceptación:**
  - **AC1.** No queda ninguna referencia al DNI en `src/` ni en `tests/`
    (`grep -rin dni src tests` no devuelve nada).
  - **AC2.** Se puede dar de alta un jugador sin año de nacimiento; si se informa, se sigue
    validando (mayor a 1900 y no posterior al año actual).
  - **AC3.** Todos los checks del CI pasan.
- **Qué no entra:** evitar jugadores repetidos ahora que no hay DNI. En el alta manual lo resuelve
  la US-107 (buscar por nombre antes de dar de alta) y en la importación, la US-206
  (`IdentificadorJugadores`).

#### US-105 — Interfaz Gráfica Base (Flet) y Retiro de la CLI

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-104, ADR-002

**Objetivo Funcional:** reemplazar la CLI por una aplicación de escritorio Flet como única interfaz del sistema, con su composition root, su navegación y el acceso de usuarios (registro, inicio y cierre de sesión), y retirar todo el código de la CLI.

**Narrativa:** Como entrenador, quiero abrir una aplicación con ventanas y registrarme o iniciar sesión sin escribir comandos.

**Por qué ahora (decisión 2026-10-31):**

- El usuario final es un DT, no alguien que use la terminal (perfiles de la sección 2, NFR-4, narrativa de la US-401).
- Seguir con la CLI obligaba a construir dos veces las mismas pantallas: el formulario de carga de partido (US-108), la consulta de estadísticas (US-205) y los dashboards (US-301) se iban a hacer en consola y después rehacer en Flet.
- El `SessionManager` con archivo JSON obligatorio existía solo porque cada comando de la CLI era un proceso nuevo. En la GUI la sesión vive en memoria y persistirla pasa a ser una opción ("Recordarme", US-106).
- La arquitectura limpia hace barato el cambio: dominio, casos de uso, DTOs y repositorios no se tocan; solo cambia el adaptador de entrada (`ui/`).

**Capa de Aplicación:**

- **Servicio `SessionManager`** (`src/aplicacion/servicios/session_manager.py`), **solo en memoria** en esta US: `iniciar_sesion(usuario: UsuarioDTO)`, `cerrar_sesion()` (idempotente), `is_authenticated()` y `usuario_actual()`. Sin archivo, sin club activo: eso lo agrega la US-106 sobre esta misma clase.

**Capa de Infraestructura (UI):**

- **`src/infraestructura/ui/flet/app.py`** — composition root de la GUI (ver sección 4): abre la conexión, inicializa el esquema, arma repositorios, `Pbkdf2PasswordHasher`, `SessionManager` y casos de uso, y registra las pantallas en una tabla de rutas.
- **`src/main.py`** — queda como punto de entrada que solo llama a `app.py`. Se borran `construir_parser()`, `argparse` y el despacho de comandos.
- **Pantallas** (`screens/`): `LoginScreen` (email + contraseña oculta), `RegistroScreen` (nombre, email, contraseña), `InicioScreen` (pantalla principal con el menú de navegación —todavía sin secciones, las llenan las US-106 y US-107— y el botón "Cerrar sesión").
- **Navegación protegida:** sin sesión, cualquier ruta interna redirige a `LoginScreen`.
- **Errores:** un único manejador común muestra cualquier `ErrorDeDominio` junto al formulario que lo causó, sin traceback y sin cerrar la app (reemplaza al `except ErrorDeDominio` de `main()`).
- **Dependencia:** `flet` con versión exacta en `pyproject.toml` + `uv.lock`.

**Retiro de la CLI (limpieza):**

- Se borran `src/infraestructura/ui/cli/` completo (`commands/` y `formatters/`), los tests `tests/unit/test_cli_main.py`, `test_cli_comandos.py`, `test_cli_comandos_listas.py`, `test_cli_auth.py`, `test_table_formatter.py` y `tests/integration/test_cli_e2e.py`, y la carpeta `scripts/` (scripts de bash que cargaban datos usando la CLI; los datos de prueba ya los da `seed.sql`).
- Se quitan `tabulate` de las dependencias y su override de mypy en `pyproject.toml`; `[project.scripts] statspro` pasa a abrir la GUI.
- Se revisan `abortar()` y `fecha_iso()` de `src/utils.py`: si solo los usaba la CLI, se borran junto con sus tests (`id_persistido()` lo usan los casos de uso y se queda).
- Lo que `test_cli_e2e.py` probaba de punta a punta y no esté cubierto por otro test se pasa a tests de integración de casos de uso con repositorios reales (sin interfaz), como ya hace `test_auth_flujo.py`.
- **Trabajo adelantado de US-109:** el smoke test del CI (`python src/main.py --help`, en las actions de cobertura de Linux y Windows) se reemplaza por un paso que importa `app.py` sin abrir ninguna ventana.
- **Documentación:** se reescriben las secciones de la CLI de `README.md`, `RUNBOOK.md`, `docs/info_modulo/03-casos-de-uso.md` (§7), `04-arquitectura.md`, `05-guia-arquitectura-app.md`, `06-patron-command.md`, `08-vistas-sql.md` y `09-testing.md` (§9); y se borra `docs/spike/spike_build_cli.md` o se lo deja como histórico, que hasta esta US describen la CLI porque es lo que existe en el código.

**Decisiones a tomar al arrancar la US (no bloquean el resto del plan):**

1. **Versión de Flet:** la API cambió de forma incompatible entre la serie 0.x y la 1.0. Se elige la última estable al momento de arrancar y se fija exacta; verificar que `uv sync` en el CI y en Docker no descargue el cliente de escritorio (los tests solo importan módulos).
2. **Cómo se testea la GUI:** Flet no trae un harness de tests maduro. Propuesta: pantallas finas (sin lógica de negocio, AC6 de la US-401 adelantado) y tests sobre lo que no depende de la ventana: `SessionManager`, el manejador de errores y las funciones puras que arman filas o validan campos.

**Criterios de Aceptación:**

- **AC1 — Arranque:** `uv run python src/main.py` abre la ventana en `LoginScreen` en menos de 3 segundos (NFR-5).
- **AC2 — Registro y login desde la GUI:** se registra un entrenador y se inicia sesión con `RegistrarEntrenadorUseCase` y `LoginLocalUseCase` (US-104), sin lógica de negocio en las pantallas. Email repetido, email inválido, contraseña corta y credenciales inválidas se muestran junto al formulario, sin traceback ni cierre de la app.
- **AC3 — Sesión en memoria:** después del login se navega a `InicioScreen`; "Cerrar sesión" vuelve a `LoginScreen`; sin sesión no se puede llegar a ninguna pantalla interna.
- **AC4 — Contraseña protegida:** los campos de contraseña se muestran ocultos y la contraseña nunca se escribe en logs (AC1 de la US-104).
- **AC5 — CLI retirada:** no quedan `ui/cli/`, `scripts/`, `tabulate` ni tests de la CLI; `src/` no importa `argparse`; la suite y el CI están en verde con la cobertura mínima de la US-109.

**Testing Mínimo:**

- _Unitarias:_ `SessionManager` (iniciar, cerrar dos veces sin error, `usuario_actual()` sin sesión); manejador de errores (un `ErrorDeDominio` produce el mensaje esperado).
- _Integración:_ flujo registro → login → `SessionManager.iniciar_sesion` con DB `:memory:` y repositorios reales.
- _Manual guiado:_ en Windows (y en Linux si hay entorno gráfico), abrir la app, registrarse, iniciar sesión, cerrar sesión y probar cada error del AC2.

**Reparto en dos pistas** (ronda 1, ver "Plan de trabajo en paralelo"):

- **Pista B (primero, ~1 día):** `SessionManager` en memoria con sus tests unitarios — la Pista A
  lo necesita para conectar el login. Después, el test de integración registro → login → sesión.
- **Pista A:** esqueleto Flet, `app.py` con la tabla de rutas, `errores.py`, `LoginScreen`,
  `RegistroScreen` e `InicioScreen`; retiro de la CLI y de `scripts/`, smoke test nuevo del CI y
  la documentación que describía la CLI.
- **Juntos, antes de empezar:** versión de Flet y cómo se testean las pantallas.

**Archivos:**

```text
src/main.py                                  ← se reduce a invocar app.py
src/aplicacion/servicios/session_manager.py   ← nuevo (en memoria)
src/infraestructura/ui/flet/
├── app.py                                   ← nuevo: composition root + rutas
├── errores.py                               ← nuevo: manejador común de ErrorDeDominio
└── screens/
    ├── login_screen.py
    ├── registro_screen.py
    └── inicio_screen.py

src/infraestructura/ui/cli/                  ← se borra
scripts/                                     ← se borra
tests/unit/test_cli_*.py, test_table_formatter.py   ← se borran
tests/integration/test_cli_e2e.py            ← se borra (lo no cubierto pasa a tests de casos de uso)
.github/actions/coverage/{linux,windows}/action.yml ← smoke test nuevo
pyproject.toml / uv.lock                     ← + flet, − tabulate, script statspro

tests/unit/test_session_manager.py
tests/integration/test_sesion_flujo.py
```

#### US-106 — Sesión Persistente ("Recordarme") y Club Activo

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-105

> **Antes era la US-105** y estaba pensada para la CLI, donde persistir la sesión era obligatorio
> porque cada comando era un proceso nuevo. En la GUI la sesión ya vive en memoria (US-105); esta
> historia agrega persistirla solo si el usuario lo pide, el club activo y la pantalla de clubes.

**Objetivo Funcional:** que la app recuerde la sesión entre una apertura y la siguiente cuando el usuario lo pide, y que el entrenador trabaje siempre en el contexto de un club activo elegido por él.

**Narrativa:** Como entrenador, quiero que la aplicación recuerde que ya inicié sesión y con qué club estoy trabajando, para no repetir esos pasos cada vez que la abro.

**Decisiones tomadas:**

1. **Persistir es opcional:** solo si el usuario marca "Recordarme" en `LoginScreen`. Sin marcarlo, cerrar la app cierra la sesión.
2. **Dónde se persiste:** archivo **JSON**, no la base SQLite — no compite por locks con la base y permite borrar la sesión a mano sin tocar datos de negocio.
3. **Ruta única:** `~/.statspro/session.json`, resuelta con `pathlib.Path.home()` (funciona igual en Windows y Linux).
4. **Sin token ni expiración en v0.1:** `SessionDTO` tiene solo `usuario_id`, `email` y `club_activo_id`. Un token tiene sentido cuando cliente y servidor están en procesos distintos; acá el mismo proceso lee su propio archivo. El archivo **nunca** guarda la contraseña ni su hash. **Riesgo aceptado para v0.1:** con "Recordarme", cualquiera con acceso a esa cuenta del sistema operativo abre la app sin contraseña; la expiración configurable llega con la US-403 (AC7).
5. **Configurable, no hardcodeado:** loader mínimo `src/config/settings.py` + `.env.example` (idea de `docs/ideas-aprendizaje.md`, sección 4) con `STATSPRO_SESSION_PATH` (default `~/.statspro/session.json`) y `STATSPRO_DB_PATH` (default: lo que ya calcula `config/rutas.py`), para que los tests apunten a archivos temporales sin parchear código.

**Decisión a tomar al arrancar la US:** si el `SessionManager` (capa de aplicación) escribe el JSON directamente o a través de un puerto — una interfaz `SesionAlmacen` en `dominio/servicios/` y una implementación `JsonSesionAlmacen` en `infraestructura/` —, igual que se hizo con `PasswordHasher` en la US-104. El puerto respeta la regla de capas (la aplicación no hace I/O) y permite testear el `SessionManager` sin archivos.

**Gap real encontrado y su corrección (bug de una pieza ya cerrada de la US-103):** `CrearClubUseCase` crea el club pero **nunca inserta en `usuarioClub`** — la tabla N:M que vincula usuario y club con `rolEntrenador`. Sin ese vínculo, `ListarClubesUsuarioUseCase` (que hace `JOIN usuarioClub`) y `CambiarClubActivoUseCase` no encuentran ningún club para ningún usuario real. Se corrige acá, **documentado explícitamente como fix**: `CrearClubUseCase` pasa a recibir el `idUsuario` de la sesión y lo vincula como entrenador al crear el club.

**Capa de Aplicación:**

- **Servicio:** `SessionManager` (US-105) se extiende con `set_active_club(id_club)` (falla si no hay sesión), `club_activo()` y la persistencia opcional (guardar al iniciar sesión con "Recordarme", cargar al arrancar la app, borrar al cerrar sesión).
- **DTO:** `SessionDTO` (`usuario_id`, `email`, `club_activo_id`).
- **Caso de uso extendido:** `CrearClubUseCase` (US-103) recibe `idUsuario` y vincula en `usuarioClub` — no se crea un caso de uso nuevo para esto. **Ojo con la US-108:** los clubes rivales no son del usuario, así que el alta de un rival no puede pasar por este mismo camino sin más: la US-108 hace opcional el `idUsuario` (club sin vínculo).

**Capa de Infraestructura (UI):**

- `LoginScreen` suma la casilla "Recordarme".
- `ClubesScreen`: alta de club, listado de "mis clubes" (`ListarClubesUsuarioUseCase` con el usuario de la sesión) y botón "Usar este club" (`CambiarClubActivoUseCase` + `SessionManager.set_active_club`).
- El club activo se muestra siempre en la barra superior.
- Guard de navegación `requiere_club_activo`: las pantallas operativas (US-107 y US-108) sin club activo llevan a `ClubesScreen` con un aviso.

**Criterios de Aceptación:**

- **AC1 — Persistencia de sesión:** con "Recordarme", al cerrar y reabrir la app se entra directo con el mismo usuario; sin marcarlo, la app pide login (y un inicio de sesión sin marcarlo borra la sesión guardada antes). "Cerrar sesión" borra el archivo.
- **AC2 — Club activo:** el club elegido en `ClubesScreen` se ve en la barra superior y, con "Recordarme", sigue activo al reabrir la app.
- **AC3 — Club realmente vinculado:** un club creado desde la GUI aparece en "mis clubes" del mismo usuario y se puede elegir como activo (cierra el gap de `usuarioClub`).
- **AC4 — Archivo dañado:** un `session.json` ilegible o con un usuario que ya no existe se ignora y se pide login, sin traceback.

**Reglas de Negocio:**

- `cerrar_sesion()` es idempotente.
- `set_active_club()` falla si no hay sesión previa.
- Solo se puede elegir como activo un club vinculado al usuario.

**Testing Mínimo:**

- _Unitarias:_ `SessionManager` con archivo temporal (`tmp_path`) — guardar, cargar, borrar, archivo dañado; `CrearClubUseCase` vincula al usuario (repositorio mock).
- _Integración:_ registro → login con "Recordarme" → crear club → elegirlo → un `SessionManager` nuevo leyendo el mismo archivo (simula reabrir la app) recupera usuario y club activo, y el club aparece en `ListarClubesUsuarioUseCase`. DB `:memory:` y archivo temporal.
- _Manual guiado:_ el mismo flujo cerrando y abriendo la app de verdad.

**Reparto en dos pistas:**

- **Pista B (ronda 1, en paralelo con la US-105):** `settings.py` + `.env.example` +
  `python-dotenv`; persistencia del `SessionManager` (`set_active_club`, `club_activo`, guardar,
  cargar y borrar); fix de `CrearClubUseCase`; tests unitarios y de integración.
- **Pista A (ronda 2):** casilla "Recordarme", `ClubesScreen`, club activo en la barra superior y
  guard `requiere_club_activo`.
- **Juntos, antes de la ronda 2:** si la sesión se guarda a través de un puerto.

**Archivos:**

```text
src/config/
└── settings.py            ← nuevo: lee .env (python-dotenv) y expone STATSPRO_SESSION_PATH/STATSPRO_DB_PATH

src/aplicacion/
├── servicios/session_manager.py   ← se extiende (club activo + persistencia)
├── dtos/session_dto.py           ← SessionDTO (usuario_id, email, club_activo_id)
└── casos_uso/crear_club.py       ← fix: vincula en usuarioClub

src/infraestructura/ui/flet/screens/
├── login_screen.py        ← + "Recordarme"
└── clubes_screen.py       ← nuevo

.env.example
pyproject.toml / uv.lock   ← + python-dotenv (versión exacta)

tests/unit/test_session_manager.py          ← se extiende
tests/integration/test_sesion_club_activo_flujo.py
```

#### US-107 — Pantallas de Gestión Administrativa

**Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-106

> **Antes era "CLI con Command Pattern"**: completaba la CLI (`partido boxscore`, DNI y club en
> `jugador list`) y aplicaba los guards de sesión. Con la CLI retirada, esta historia cumple el
> mismo papel en la GUI: que todas las entidades se puedan gestionar desde la interfaz. Puede
> entregarse en dos PRs (jugadores; competencias, inscripciones, listas y partidos) si conviene.

**Objetivo Funcional:** gestionar desde la GUI todo lo que la US-103 dejó resuelto en casos de uso (jugadores, competencias, categorías, inscripciones, listas de buena fe y partidos), siempre en el contexto del club activo.

**Narrativa:** Como entrenador, quiero cargar y consultar mis jugadores, competencias, inscripciones y listas de buena fe desde pantallas con formularios y tablas, sin tener que conocer IDs.

**Nota de reuso (no se pisa con otras US):** las pantallas envuelven casos de uso que **ya existen** desde la US-103 — no se agrega lógica de negocio. Las piezas nuevas de aplicación son chicas y de lectura: el boxscore de un partido (antes previsto como comando `partido boxscore` de esta misma US), y la búsqueda de jugadores por nombre. La US-205 le agrega métricas avanzadas a esa misma pantalla de detalle; no crea otra.

**Capa de Aplicación:**

- **Casos de uso nuevos:** `ObtenerBoxscorePartidoUseCase` (devuelve una lista de `BoxscoreFilaDTO`) y `BuscarJugadoresPorNombreUseCase` (usa `JugadorRepositorio.buscar_por_nombre`, nuevo: busca por apellido o nombre en todos los clubes, sin distinguir mayúsculas). Sin él no hay forma de elegir en pantalla a un jugador que todavía no está en el club activo, ni de avisar que un jugador ya existe antes de darlo de alta.
- **Repositorio extendido:** `JugadorRepositorio.buscar_por_nombre(texto)` y su versión SQLite.
- **Repositorio:** método nuevo `PartidoRepositorio.boxscore_por_partido(id_partido)`, que lee `v_boxscore_completo` (mismo patrón que `resumen_por_club` con `v_partidos_resumen`).

**Capa de Infraestructura (UI):**

- **Componente compartido:** `components/tabla_datos.py` — tabla reutilizable (encabezados + filas a partir de DTOs) que usan todos los listados. Reemplaza a `formatters/table_formatter.py` de la CLI.
- **Pantallas** (`screens/`):
  - `JugadoresScreen` — alta (`RegistrarJugadorUseCase`; antes de guardar muestra los jugadores con el mismo nombre, para vincular uno existente en vez de duplicarlo), listado del club activo (`ListarJugadoresClubUseCase`), buscar por nombre un jugador que todavía no está en el club (`BuscarJugadoresPorNombreUseCase`) para vincularlo al club activo (`VincularJugadorAClubUseCase`), y dar de baja (`DesvincularJugadorDeClubUseCase`).
  - `CompetenciasScreen` — alta y listado de competencias y de categorías (`CrearCompetenciaUseCase`, `ListarCompetenciasUseCase`, `CrearCategoriaUseCase`, `ListarCategoriasUseCase`).
  - `InscripcionesScreen` — inscribir al club activo en una competencia y categoría (`InscribirClubEnCompetenciaUseCase`) y listar sus inscripciones (`ListarInscripcionesClubUseCase`).
  - `ListaBuenaFeScreen` — habilitar y quitar jugadores de la lista de una inscripción y verla (`AgregarJugadorAListaBuenaFeUseCase`, `QuitarJugadorDeListaBuenaFeUseCase`, `ListarListaBuenaFeUseCase`).
  - `PartidosScreen` — listado de partidos del club activo (`ListarPartidosPorClubUseCase`, con nombres desde `v_partidos_resumen`) y detalle con el boxscore (`ObtenerBoxscorePartidoUseCase`).

**Criterios de Aceptación:**

- **AC1 — Pantallas desacopladas:** agregar una pantalla solo requiere crear su archivo en `screens/` y registrarla en la tabla de rutas de `app.py`, sin modificar otras pantallas (el equivalente del AC1 de la vieja US-107 para la CLI).
- **AC2 — Sin IDs a mano:** competencia, categoría, inscripción y jugadores del club se eligen de listas desplegables cargadas desde los casos de uso de listado; un jugador que todavía no está en el club se busca por nombre; el club es siempre el club activo (US-106).
- **AC3 — Visualización con vistas SQL:** el listado de partidos usa `v_partidos_resumen` (nombres, no IDs); el detalle usa `v_boxscore_completo`.
- **AC4 — Errores de negocio:** toda excepción de dominio (vínculo superpuesto, jugador ya en lista, inscripción duplicada, etc.) se muestra junto al formulario con el manejador común de la US-105.
- **AC5 — Sesión:** todas las pantallas de esta US exigen sesión y club activo (guards de las US-105 y US-106).

**Testing Mínimo:**

- _Unitarias:_ `ObtenerBoxscorePartidoUseCase` y `BuscarJugadoresPorNombreUseCase` con repositorio mock; las funciones puras que convierten DTOs en filas de `tabla_datos`.
- _Integración:_ `ObtenerBoxscorePartidoUseCase` contra `v_boxscore_completo` con `seed.sql`. Los demás casos de uso ya tienen sus tests desde la US-103.
- _Manual guiado:_ recorrido completo club → jugador → vínculo → competencia → categoría → inscripción → lista de buena fe → partidos → boxscore, probando al menos un error de negocio en cada pantalla.

**Reparto en dos pistas:**

- **Pista B, ronda 1:** `buscar_por_nombre` y `BuscarJugadoresPorNombreUseCase`,
  `boxscore_por_partido` y `ObtenerBoxscorePartidoUseCase`, con sus tests.
- **Pista A, ronda 2:** `tabla_datos.py` **primero** (la Pista B la necesita), después
  `JugadoresScreen` y `PartidosScreen`.
- **Pista B, ronda 2:** `CompetenciasScreen`, `InscripcionesScreen` y `ListaBuenaFeScreen`.

**Archivos:**

```text
src/aplicacion/
├── casos_uso/obtener_boxscore_partido.py
├── casos_uso/buscar_jugadores_nombre.py
└── dtos/partido_dto.py             ← + BoxscoreFilaDTO

src/dominio/repositorios/partido_repositorio.py                ← + boxscore_por_partido
src/infraestructura/repositorios/sqlite_partido_repositorio.py ← + boxscore_por_partido
src/dominio/repositorios/jugador_repositorio.py                ← + buscar_por_nombre
src/infraestructura/repositorios/sqlite_jugador_repositorio.py ← + buscar_por_nombre

src/infraestructura/ui/flet/
├── components/tabla_datos.py
└── screens/
    ├── jugadores_screen.py
    ├── competencias_screen.py
    ├── inscripciones_screen.py
    ├── lista_buena_fe_screen.py
    └── partidos_screen.py

tests/unit/test_uc_boxscore.py
tests/unit/test_uc_buscar_jugador.py
tests/unit/test_tabla_datos.py
tests/integration/test_boxscore_vista.py
```

#### US-108 — Carga Atómica de Partido (CargarPartido)

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-106, US-107
- **Antes era la US-106.** Pasó de S a M porque el formulario de varios pasos ahora es una pantalla de la GUI, no un flujo de consola.
- **Objetivo Funcional:** registrar un partido de una competencia y categoría, con las estadísticas individuales de los dos equipos, garantizando la integridad de los datos mediante una transacción atómica (todo o nada).
- **Narrativa:** Como DT, quiero registrar un partido completo —de mi club o de otros clubes de la competencia— con todas las estadísticas de los jugadores en una única operación; si falla una sola estadística, nada se persiste.

> **Decisiones tomadas el 2026-10-31** (cierran las dos decisiones pendientes que tenía esta historia):
>
> 1. **Cualquier partido de la competencia.** Se puede cargar un partido aunque el club activo no
>    juegue; el club activo (US-106) solo viene **preseleccionado** como local y el usuario puede
>    cambiar los dos equipos. Motivo: si solo se cargan los partidos propios, el club activo tiene
>    N partidos y cada rival 0 o 1, y el promedio de un rival con un solo partido no dice nada.
> 2. **El partido guarda la categoría.** Un partido es de una categoría que juega una competencia.
>    Las categorías se repiten (U13 juega el Asociativo 2026, el Asociativo 2027 y el Provincial
>    2026) y cada combinación tiene su inscripción y su lista de buena fe por club; sin la
>    categoría no se sabe contra qué lista validar.
> 3. **Clubes rivales o de terceros.** `ClubRepositorio.listar_todos` para elegir cualquier club, y
>    `CrearClubUseCase` con `idUsuario` opcional: sin usuario, el club se crea **sin** vínculo en
>    `usuarioClub`.

- **Capa de Dominio:** `Partido` suma `idCategoria: int` (obligatorio). `JugadorPartido` no cambia.
- **Capa de Aplicación:**
  - **Caso de uso:** `CargarPartidoUseCase` — orquesta: para **cada uno de los dos equipos** busca la inscripción del club en la competencia y categoría del partido, valida que su boxscore solo tenga jugadores de esa lista (`CompetenciaRepositorio.obtener_jugadores_lista`, ya existe de US-103) y llama a `PartidoRepositorio.save_with_boxscore` con los dos boxscores juntos.
  - **Caso de uso nuevo:** `ListarClubesUseCase` (todos los clubes, para elegir local y visitante).
  - **Caso de uso extendido:** `CrearClubUseCase` con `idUsuario` opcional (decisión 3).
  - **DTOs:** `PartidoDTO` (de carga, con la categoría — el de solo lectura que ya existe se llama `PartidoResumenDTO`), `BoxscoreDTO`, `EstadisticaInputDTO`.
- **Capa de Infraestructura:**
  - **Base de datos:** columna `partido.idCategoria` (FK a `categoria`); `v_partidos_resumen` suma el nombre de la categoría; `SqlitePartidoRepositorio` la guarda y la lee; `SqliteClubRepositorio.listar_todos`.
  - **`CargaPartidoScreen`** — formulario de varios pasos: (1) competencia, categoría, fecha, local y visitante, con el club activo preseleccionado como local; (2) el boxscore de cada equipo, una fila por jugador de su lista de buena fe; (3) resumen y confirmación. Si un equipo no tiene inscripción o lista en esa competencia y categoría, la pantalla lo avisa y lleva a `ListaBuenaFeScreen` (US-107) para cargarla — desde la US-206 también se puede importar del listado de la CAB. Los errores de validación se marcan en el campo o la fila que los causó.
- **Decisión tomada (2026-10-31) — cómo llega `partido.idCategoria` a las bases que ya existen:**
  `schema.sql` usa `CREATE TABLE IF NOT EXISTS`, así que agregar la columna ahí no cambia una base
  ya creada. Se cambia `schema.sql` y cada integrante borra y recrea su base local: todavía no hay
  ninguna versión entregada, así que solo se pierden datos de prueba. Se descartó adelantar la
  US-204 (migraciones) solo para esto.
- **Criterios de Aceptación:**
  - **AC1 — Atomicidad Garantizada (ya cumplido a nivel repositorio, falta ejercitarlo desde el caso de uso):** si falla la inserción del boxscore en cualquier punto, no se guarda el partido huérfano. `save_with_boxscore` ya lo garantiza; falta el test desde `CargarPartidoUseCase`.
  - **AC2 — Validaciones Pre-persistencia:** la validación de los dos boxscores contra la lista de cada club ocurre ANTES de llamar al repositorio; el mensaje de error dice qué jugador de qué equipo la causó.
  - **AC3 — Independencia:** el caso de uso no contiene SQL embebido — se delega totalmente al repositorio.
  - **AC4 — Formulario:** si el guardado falla, el formulario conserva lo cargado para corregirlo, sin perder los datos de los demás jugadores.
  - **AC5 — Partidos de otros clubes:** se puede cargar un partido entre dos clubes que no son el club activo ni están vinculados al usuario.
  - **AC6 — Categoría:** un jugador que está en la lista del club para otra categoría u otra competencia (por ejemplo, el Asociativo 2025) no puede figurar en el boxscore.
- **Reglas de Negocio (las cuatro primeras ya están en `JugadorPartido.__post_init__` y la quinta en `save_with_boxscore`; se listan para trazabilidad):**
  - `(T1C×1) + (T2C×2) + (T3C×3)` = puntos totales.
  - `convertidos ≤ lanzados` para T1, T2, T3.
  - Todos los campos numéricos `≥ 0`.
  - `minutosJugados` entre 0 y 48.
  - No se puede cargar un partido si los clubes involucrados no existen en la DB (ya lo valida `save_with_boxscore`).
  - **En el boxscore de cada equipo solo figuran jugadores de la lista de buena fe de ese club para la competencia y categoría del partido** (regla de la sección 6). Las listas se cargan desde `ListaBuenaFeScreen` (US-107) o se importan (US-206, US-201); si un jugador no está, se lanza una excepción de dominio.
  - **Nota (campo propuesto, no implementado todavía):** si se agrega a `Partido` un resultado final (`puntosLocalFinal`/`puntosVisitanteFinal`, ver sección 20 y el DER en `docs/diagramas/diagramas.md`), esta US sería el lugar natural para completarlo, con una regla que valide que la suma de puntos del boxscore por club coincide con ese resultado. La importación (US-201) ya no lo necesita: valida contra la fila `TOTALES` del archivo.
- **Testing Mínimo:**
  - _Unitarias:_ `CargarPartidoUseCase` rechaza un jugador que no está en la lista de su club (en cualquiera de los dos equipos) y uno que está en la lista de otra categoría (mock de `CompetenciaRepositorio`); camino feliz llama a `save_with_boxscore` con los DTOs traducidos. `CrearClubUseCase` sin usuario no vincula.
  - _Integración:_ flujo completo (partido + dos boxscores) en DB `:memory:` con repositorios reales, incluido un partido entre dos clubes sin vínculo con el usuario — puede reusar el fixture de `tests/integration/test_repositorios_partido.py`.
  - _Manual guiado:_ cargar un partido completo desde la pantalla, uno de otros dos clubes, y uno con un jugador fuera de la lista para ver el error y que nada se guardó.

**Reparto en dos pistas** (ronda 3):

- **Juntos, antes de empezar:** los DTOs de carga (`PartidoDTO`, `BoxscoreDTO`,
  `EstadisticaInputDTO`), que son el contrato entre las dos pistas.
- **Pista B:** `idCategoria` en el esquema, la entidad, el repositorio y la vista;
  `listar_todos`, `ListarClubesUseCase` y `CrearClubUseCase` con usuario opcional; DTOs,
  `CargarPartidoUseCase` y sus tests unitarios y de integración.
- **Pista A:** `CargaPartidoScreen`, programada contra los DTOs acordados (puede arrancar con un
  caso de uso falso hasta que la Pista B mergee el real).

**Archivos a crear o modificar:**

```text
src/dominio/entidades/partido.py              ← Partido + idCategoria
src/infraestructura/persistencia/sql/
├── schema.sql                                ← partido.idCategoria (cada uno recrea su base local)
└── views.sql                                 ← v_partidos_resumen + categoría
src/infraestructura/repositorios/
├── sqlite_partido_repositorio.py             ← guarda y lee idCategoria
└── sqlite_club_repositorio.py                ← + listar_todos
src/aplicacion/
├── dtos/partido_dto.py     ← se extiende: PartidoDTO (carga), BoxscoreDTO, EstadisticaInputDTO
└── casos_uso/
    ├── cargar_partido.py
    ├── listar_clubes.py
    └── crear_club.py       ← idUsuario opcional

src/infraestructura/ui/flet/screens/
└── carga_partido_screen.py

tests/unit/
└── test_uc_cargar_partido.py
tests/integration/
└── test_cargar_partido_flujo.py
```

#### US-110 — Monitoreo y Trazabilidad Operativa

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Dependencias:** US-107, US-108
- **Antes era la US-108.** El "comando" como unidad de trazabilidad pasa a ser la **acción del usuario** en la GUI (un botón que invoca un caso de uso).
- **Objetivo Funcional:** proveer observabilidad transversal estructurada para depuración y soporte, con correlación de eventos extremo-a-extremo por acción del usuario.
- **Reparto en dos pistas:**
  - **Pista B (trabajo suelto, cualquier ronda):** núcleo — `ExecutionContext`, formato JSON,
    redacción de secretos (AC3) y selección de sink (AC4), con sus tests unitarios.
  - **Pista A (ronda 4):** conectar los eventos a las acciones de las pantallas y a los casos de
    uso de la lista de eventos obligatorios, y el test de integración del `correlation_id`.
  - **Juntos, antes:** los nombres de los campos del evento (`accion`, `correlation_id`,
    resultado, duración), que son el contrato entre las dos pistas.
- **Archivos a crear:**

```text
src/infraestructura/logging/
├── logger_config.py       ← configuración de sinks (local-file / Seq)
└── seq_handler.py         ← handler HTTP para Seq (opcional)

src/aplicacion/servicios/
└── execution_context.py   ← genera correlation_id UUIDv4 y propaga contexto

docker-compose.yml          ← perfil "observabilidad" con Seq (opcional)

tests/unit/
├── test_execution_context.py
└── test_logging_redaction.py
```

- **Eventos de log obligatorios:** inicio/fin de cada acción del usuario (pantalla, acción, resultado y duración); `LoginLocalUseCase`/cierre de sesión, `SessionManager.set_active_club` (US-104/106), fallos de autenticación; inicio/fin de transacciones críticas (`CargarPartidoUseCase` de US-108; importación Excel y backup/restore cuando existan, US-201 y US-402); creación/actualización de entidades principales; excepciones de dominio y errores de infraestructura, clasificados por severidad.
- **Criterios de Aceptación:**
  - **AC1.** Niveles DEBUG/INFO/WARNING/ERROR en formato JSON estructurado.
  - **AC2.** `correlation_id` UUIDv4 generado al inicio de cada acción del usuario y propagado hasta repositorios.
  - **AC3.** Secretos (passwords, tokens, hashes sensibles) redactados en todos los niveles de log.
  - **AC4.** Selección de sink (local-file o Seq) por configuración, sin cambiar código de negocio.
  - **AC5.** En modo Seq, eventos filtrables por `correlation_id`, `accion` (pantalla + acción) y nivel.
- **Testing Mínimo:**
  - _Unitario:_ creación y propagación de `execution_context`; redacción de secretos en campos conocidos.
  - _Integración:_ una acción completa (por ejemplo, crear un club con sesión iniciada) → verificar que todos sus eventos tienen el mismo `correlation_id` y que otra acción tiene uno distinto.

> **Estado real:** el proyecto ya tiene un logger funcional (`src/infraestructura/logger.py`,
> rotación 10MB/5 backups, formato `asctime - name - levelname - message`) — es más simple que lo
> que pide esta US (sin JSON estructurado, sin `correlation_id`, sin redacción de secretos, sin
> Seq). Es un buen punto de partida, no un reemplazo completo de la US-110. Ver
> `docs/info_modulo/01-logger.md`.

### Épica H1-E3: Entorno de Calidad y Pipeline CI/CD

> **Regla de alcance para US-104 a US-110 (agregada el 2026-10-03; ampliada a la US-110 al renumerar el 2026-10-31):** si al implementar cualquiera
> de estas historias hace falta tocar algo que no está declarado en su propia sección — en
> particular, cualquier cambio de CI/CD o de Docker, que es responsabilidad de la US-109 — se
> anota explícitamente en la sección de esa US como **"trabajo adelantado de US-109"**, en vez de
> mezclarse en el mismo PR sin dejar rastro. Es la corrección directa a lo que ya pasó una vez: ver
> la nota de "Estado real" de la US-109 más abajo.

#### US-109 — Entorno de Desarrollo y Pipeline CI/CD

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Dependencias:** —
- **Objetivo Funcional:** garantizar que todo nuevo commit sea verificado automáticamente con linting, tests y cobertura, haciendo del pipeline la única fuente de verdad sobre el estado de calidad del proyecto.
- **Archivos a crear/existentes:**

```text
.github/workflows/MainAction.yml  ✅ existe (jobs: check_dep [pip-audit], gitleaks, lint [ruff], static [mypy],
                                     tests-linux, tests-windows, tests-docker, ci-ok [agregador];
                                     matriz de Python 3.12–3.14 solo en tests-linux (Windows y Docker: una corrida con 3.13;
                                     mypy: una corrida contra 3.12); se dispara en PR, push a main/develop y manual;
                                     con concurrency, permissions y timeout-minutes)
.github/actions/style/{ruff,mypy}/action.yml                   ✅ existen (versión de ruff/mypy = la de pyproject.toml/uv.lock;
                                     ruff corre `ruff check .` + `ruff format --check .` con las reglas de pyproject.toml)
.github/actions/coverage/{linux,windows,docker}/action.yml     ✅ existen (todas reciben `python-version`;
                                     la de Linux exige cobertura ≥ 85 % y guarda el reporte HTML)
.github/dependabot.yml          ✅ existe (uv, github-actions y docker; semanal)
pytest.ini / .coveragerc        ➡️ migrados a pyproject.toml ([tool.pytest.ini_options] y [tool.coverage.*], 2026-10-17;
                                     de paso se corrigió branch=True, que estaba mal ubicado y no medía ramas)
.pre-commit-config.yaml         ✅ existe (check-yaml, end-of-file-fixer, trailing-whitespace y ruff check/format
                                     ejecutados con `uv run`: misma versión de ruff que el CI)
pyproject.toml                  ✅ existe (dependencias con versión fija + config de ruff/mypy/pytest/coverage + comando `statspro`; uv.lock; sin requerimientos.txt)
Makefile                        ✅ existe (instalar_dependencias [uv sync], run_test, run_linter_ruf, corregir_linter, pre_commit, docker_test, static_check)
docs/info_modulo/11-flujo-de-trabajo-git.md  ❌ no existe
docs/catalogo-criticidad.md     ❌ no existe (lo pide la sección 14; se inicializa en esta US)
```

- **Criterios de Aceptación:**
  - **AC1.** `make run_test` ejecuta la suite completa y falla si la cobertura baja del piso de `[tool.coverage.report]` de `pyproject.toml` (`fail_under = 60`). El job de Linux del CI exige además **85 %** (parámetro `cobertura-minima`; cumple el ≥ 80 % pedido) y guarda el reporte HTML como _artifact_.
  - **AC2.** `make run_linter_ruf` falla ante cualquier infracción de estilo o de formato.
  - **AC3.** El pipeline CI falla el PR ante test fallido, cobertura insuficiente (Linux), error de linting o de tipos, dependencias con vulnerabilidades conocidas o secretos en el historial.
  - **AC4.** `pre-commit install` configura hooks locales en un único comando (los hooks de ruff se ejecutan con `uv run`: usan la versión fijada en `pyproject.toml`, la misma del CI).
  - _(La numeración salta de AC4 a AC6; se conserva porque ADR-009 y la sección de estado citan AC6–AC8.)_
  - **AC6 — Job agregador y required status checks (nuevo, antes solo vivía en `ideas-aprendizaje.md` §8.9):** un job final `ci-ok` que depende de todos los demás y falla si alguno falló; registrado como _required status check_ de la rama, para que un PR con el CI en rojo no se pueda mergear.
  - **AC7 — `ruff format --check` (nuevo, antes §8.2):** el job `lint` también falla si algún archivo no está formateado con `ruff format`, no solo si viola reglas de estilo.
  - **AC8 — Smoke test de la app (nuevo, antes §8.14):** un paso que falla si el punto de entrada no se puede importar. Con la CLI era `uv run python src/main.py --help`; desde la US-105 es un paso que importa el composition root de la GUI (`app.py`) sin abrir ninguna ventana.
- **Testing Mínimo:** manual — push a rama feature dispara el workflow; error de lint intencional hace fallar CI; cobertura por debajo del umbral hace fallar CI con mensaje explicativo; un PR con un job en rojo no puede mergearse (AC6).
- **Reparto en dos pistas** (trabajo suelto, para quien termine antes su parte de una ronda):
  - **Pista A:** documentación — `docs/catalogo-criticidad.md` (sección 14) y
    `docs/info_modulo/11-flujo-de-trabajo-git.md`.
  - **Pista B:** pipeline — fijar las actions de terceros por hash (8.13) y marcar `ci-ok` como
    _required status check_ en GitHub (AC6). El smoke test nuevo ya lo hace la US-105.
> **Estado real:** ver `docs/ideas-aprendizaje.md` sección 8 (informe de CI) para el detalle
> técnico de cada punto. Ya aplicado (2026-09-20): `mypy`, `pip-audit`, build de Docker, una sola
> versión de ruff/mypy (`pyproject.toml`) en CI y pre-commit, matriz de Python 3.11–3.14 (Windows
> solo 3.13), disparo en `push`, `concurrency`/`permissions`/`timeout-minutes`, cobertura mínima de
> 85 % con reporte guardado (Linux), Dependabot y `gitleaks`.
>
> **Importante — esto es exactamente el ejemplo de historias pisándose entre sí que motivó esta
> revisión completa del 2026-10-03:** todo lo anterior se hizo **durante el PR de la US-103**
> (commits `f5c4386` y `938c93f` de ese branch), no en un PR dedicado a esta US. El trabajo quedó
> bien hecho, pero no quedó registrado como tal en su momento — de ahí la "Regla de alcance para
> US-104 a US-110" agregada al principio de esta épica.
>
> **Aplicado el 2026-10-11 (trabajo adelantado de US-109, hecho en la rama de la US-104 antes de
> abrir su PR — ver la "Regla de alcance" de arriba):**
>
> - **AC6:** job agregador `ci-ok` (falla si algún job falló, se canceló o se salteó). **Falta un
>   paso manual en GitHub:** marcarlo como _required status check_ en Settings → Branches.
> - **AC7:** el job `lint` corre también `ruff format --check .`.
> - **AC8:** smoke test `python src/main.py --help` en los jobs de tests de Linux y Windows (lo
>   reemplaza la US-105 por el import de `app.py`, como trabajo adelantado de esta US).
> - **8.4:** se sacó `submodules: recursive` de `check_dep`, `lint` y `static`.
> - **Matriz reducida:** las versiones de Python (3.12, 3.13 y 3.14) se prueban solo en
>   `tests-linux`; Docker y Windows corren una vez (3.13) y mypy una vez (contra 3.12). La 3.11
>   dejó de probarse en el CI aunque `pyproject.toml` sigue declarando `requires-python >= 3.11`.
> - **Ruff más estricto:** las reglas viven solo en `pyproject.toml` (`E`, `W`, `F`, `I`, `B`,
>   `UP`, `SIM`, `C4`, `RUF`; antes `E501` + `I`, y el CI pasaba `--select E --select I` por su
>   cuenta). CI, pre-commit y Makefile corren `ruff check` sin `--select`. `docs/` queda excluido.
>   Al activarlas se corrigió el código existente; entre otras cosas apareció un test duplicado en
>   `test_repositorios_competencia.py` (mismo nombre dos veces: el primero nunca se ejecutaba).
> - **mypy** ya era `--strict`; no cambió.
>
> **Sigue pendiente:** fijar las actions de terceros por hash (8.13, prioridad baja).

---

## 10. Hito 2 — Motor de Ingesta y Análisis (v0.2)

**Objetivo del hito:** automatizar la carga desde Gesdeportiva, producir métricas avanzadas
confiables, exponerlas en pantallas de la GUI y asegurar la evolución controlada del esquema de
base de datos.

**Épicas:** 3 · **Historias:** 6 (la US-206 se agregó el 2026-10-31) · **Esfuerzo total estimado:** ~34 días·persona

**Decisión previa requerida:** ninguna sobre ADR-002 — la GUI Flet ya existe desde la US-105 y
este hito le suma pantallas (importación en la US-201, consulta estadística en la US-205). _Nota
(2026-10-31): hasta esta fecha el plan decía que el Hito 2 era 100 % CLI; con la CLI retirada,
sus salidas pasan a ser pantallas._ **Sí hay dos
decisiones previas reales todavía sin cerrar para este hito:** ADR-003 (protocolo de ingesta,
bloquea las US-201 y US-206 — ya hay archivos reales en `data/`; falta elegir la librería de PDF) y ADR-004 (versionado de DB,
bloquea la US-204 — falta decidir si vale agregar SQLAlchemy solo por el runner de Alembic). Ver
`docs/adr/`._

### Épica H2-E1: Integración "Gesdeportiva" y Gobernanza de Esquema

> **Nota de reordenamiento (2026-10-03):** la US-204 (Versionado de Esquema y Migraciones) vivía
> antes en la Épica H2-E3, mezclada sin ninguna relación temática con el motor analítico
> (US-203/US-205) — además aparecía físicamente _después_ de la US-205 en el documento, pese a
> tener un número menor. Se la mueve acá, antes de la US-201, porque esta última la necesita de
> verdad: el AC3 de la US-201 (verificar que la suma de puntos del boxscore coincida con el
> resultado final del partido) requiere agregar un campo nuevo a `Partido` que hoy no existe en
> el schema, y agregar una columna a una tabla existente sin perder datos es exactamente el
> problema que resuelve la US-204. La Épica H2-E3 quedó renombrada a solo "Inteligencia Deportiva
> (Pandas Engine)" — ver más abajo.
>
> **Actualización (2026-10-31):** con los archivos reales, el AC3 de la US-201 se valida contra la
> fila `TOTALES` del archivo y ya no necesita una columna de resultado final, así que la US-201 dejó
> de depender de la US-204. La US-204 se sigue haciendo al principio del hito. Se suma a esta épica la **US-206** (listado de
> jugadores de la CAB), que va antes que la US-201.

#### US-204 — Versionado de Esquema y Migraciones

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-101, ADR-004
- **Objetivo Funcional:** asegurar la evolución controlada del esquema de base de datos entre
  versiones sin pérdida de datos, con un runner que aplique migraciones en orden y registre cada
  resultado. La primera migración real que corra sobre una base con datos será el primer cambio
  de esquema posterior a esta historia (la categoría del partido entra antes, en la US-108,
  recreando las bases locales).
- **Reparto en dos pistas** (sin interfaz; arranca en la ronda 4 del Hito 1 si el ADR-004 ya está
  decidido):
  - **Juntos, antes:** el ADR-004 y la convención de nombres y formato de las migraciones (AC5).
  - **Pista A:** `migration_runner.py` — tabla `schema_version` (AC1), aplicar solo las pendientes
    (AC2), bloquear el arranque si el esquema es incompatible (AC4).
  - **Pista B:** pasar `schema.sql` a `001_init.sql`, la primera migración real (`002_*.sql`, la que
    haga falta primero), el rollback de la última (AC3), los tests de upgrade
    multi-versión y la guía `12-como-agregar-una-migracion.md`.
- **Archivos a crear:**

```text
src/infraestructura/persistencia/sql/migrations/
├── 001_init.sql          ← schema completo de v0.1; desde acá el schema no se toca directo
└── 002_*.sql              ← migraciones incrementales, NNN_descripcion_corta.sql, idempotentes

src/infraestructura/persistencia/migration_runner.py

tests/integration/test_migrations.py (upgrade multi-versión y rollback)
docs/info_modulo/12-como-agregar-una-migracion.md
```

- **Criterios de Aceptación:**
  - **AC1.** Tabla `schema_version` creada y mantenida automáticamente (número de versión,
    nombre, timestamp).
  - **AC2.** El runner ejecuta solo migraciones pendientes (idempotente en las ya aplicadas).
  - **AC3.** Soporte de rollback controlado para la última migración aplicada (script `down`
    opcional).
  - **AC4.** Si el schema es incompatible con la versión del código al arrancar, la ejecución se
    bloquea con mensaje claro.
  - **AC5.** Scripts versionados con el mismo estándar de nomenclatura, registrados en el
    changelog técnico.
- **Testing Mínimo:** upgrade multi-versión sobre base con datos reales (cardinalidad
  conservada); rollback de la última migración (integridad post-rollback); dataset de versión
  anterior conserva todas las relaciones tras migrar.

#### US-206 — Importación de Lista de Buena Fe desde el Listado de la CAB

> **Nueva (2026-10-31).** Va antes que la US-201 aunque tenga un número mayor: fija la librería de
> PDF y el servicio que identifica jugadores sin DNI, que la US-201 reusa.

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-107, ADR-003
- **Objetivo Funcional:** cargar la lista de buena fe de un club para una competencia y categoría
  desde el listado "Jugadores" que exporta Gesdeportiva (CAB), en Excel o PDF, sin tipear nombres.
  Sirve para el club propio y para los rivales, y es lo que permite después cargar a mano partidos
  de otros clubes (US-108).
- **Narrativa:** Como DT, quiero importar el listado de jugadores que publica la CAB para tener la
  lista de buena fe de cualquier club sin cargarla jugador por jugador.

**Formato real del listado** (`data/jugadores_*.xlsx` y su PDF, revisados el 2026-10-31):

- Una sola hoja (`Jugadores-Equipo`). Título en celdas combinadas:
  `Jugadores - UNIVERSITARIO - INFANTILES MIXTO - CORDOBA - ASOCIACIÓN - 2026 - FEDERACION DE BASQUETBOL DE LA PROVINCIA DE CORDOBA - 2026`
  → club, categoría, ciudad, competencia, temporada, organizador, año.
- Columnas: `Apellidos y Nombre`, `Partidos jugados`, `Minutos partido`, `Puntos partido` (estas
  dos son promedios con coma decimal: `21,2`). Todas las celdas son texto.
- Nombres en formato `APELLIDOS, NOMBRES`, a veces con espacios al final. Incluye jugadores con 0
  partidos (están en la lista pero no jugaron).
- **No trae DNI ni año de nacimiento.** La categoría se nombra distinto que en la planilla de
  partido (`INFANTILES MIXTO` acá, `U13MX` allá).

- **Capa de Dominio:**
  - `Jugador` no cambia: el ajuste previo a la US-105 ya quitó el DNI y dejó opcional el año de
    nacimiento, que los archivos tampoco traen.
  - **Excepción:** `FormatoArchivoInvalidoError` (la reusa la US-201).
- **Capa de Aplicación:**
  - **Servicio `IdentificadorJugadores`** (`aplicacion/servicios/`) — recibe un nombre
    `APELLIDOS, NOMBRES` y un club y devuelve el jugador. Normaliza el nombre (sin tildes,
    mayúsculas ni espacios de más) y busca **solo entre los jugadores de ese club** (vínculos y
    listas). Sin coincidencias → jugador nuevo vinculado al club; una → ese jugador; más
    de una → ambiguo, lo resuelve el usuario en la vista previa. **Nunca** empareja con jugadores de
    otro club: dos chicos con el mismo nombre en clubes distintos son dos personas. La US-201 lo
    reusa.
  - **Caso de uso `ImportarListaBuenaFeUseCase`** con `preview()`: el club viene sugerido del título
    (si no existe, se crea sin vínculo con el usuario, US-108); competencia y categoría se eligen en
    la pantalla. Crea la inscripción con su lista si no existe (`inscribir_con_lista`, con la fecha
    de importación como fecha de presentación) y agrega los jugadores que faltan. No quita de la
    lista a los que no vienen en el archivo: los informa.
- **Capa de Infraestructura:**
  - **Parsers:** `ListadoJugadoresExcelParser` (`pd.read_excel`, necesita `openpyxl`) y
    `ListadoJugadoresPdfParser` (librería a elegir en el ADR-003). Los dos devuelven un
    `ListadoJugadoresDTO` (título + nombres) y buscan el encabezado `Apellidos y Nombre` por texto,
    no por posición.
  - **UI:** botón "Importar desde archivo" en `ListaBuenaFeScreen` (US-107), con vista previa.
- **Criterios de Aceptación:**
  - **AC1 — Formato:** un archivo sin el título o sin el encabezado `Apellidos y Nombre` lanza
    `FormatoArchivoInvalidoError` antes de procesar, diciendo qué faltó.
  - **AC2 — Idempotencia:** importar dos veces el mismo listado no duplica jugadores ni filas en la
    lista.
  - **AC3 — Vista previa:** muestra los jugadores nuevos, existentes y ambiguos sin persistir nada.
  - **AC4 — Mismo resultado en los dos formatos:** el Excel y el PDF del mismo listado producen el
    mismo `ListadoJugadoresDTO`.
  - **AC5 — Listas separadas:** el mismo jugador puede estar en la lista de U13 del Asociativo 2026
    y en la del Provincial 2026 (o del Asociativo 2027); importar una no toca las otras.
- **Fuera de alcance en v0.2:** `Partidos jugados`, `Minutos partido` y `Puntos partido` son los
  datos oficiales de la temporada y no se guardan. Más adelante servirían para mostrar cuánto de la
  temporada de un jugador está cargado (partidos cargados contra jugados; ver "Muestra chica" en la
  sección 6).
- **Testing Mínimo:**
  - _Unitarias:_ parsers contra fixtures (tildes, espacios de más, coma decimal);
    `IdentificadorJugadores` con 0, 1 y 2 coincidencias, y el mismo nombre en otro club no
    empareja.
  - _Integración:_ importar el fixture dos veces; el mismo jugador en las listas de dos
    competencias.
  - _Manual guiado:_ importar el Excel y el PDF del mismo listado y comparar.
  - Fixtures anonimizados (ver la US-201).

**Reparto en dos pistas:**

- **Juntos, antes:** la librería de PDF (ADR-003), el `ListadoJugadoresDTO` y la firma de
  `IdentificadorJugadores` (la reusa la US-201).
- **Pista A:** los dos parsers (AC1, AC4) y la importación en `ListaBuenaFeScreen`.
- **Pista B:** `IdentificadorJugadores` e `ImportarListaBuenaFeUseCase` (AC2, AC3, AC5).

**Archivos a crear o modificar:**

```text
src/dominio/exceptions.py                     ← + FormatoArchivoInvalidoError
src/aplicacion/servicios/identificador_jugadores.py
src/aplicacion/casos_uso/
└── importar_lista_buena_fe.py
src/aplicacion/dtos/ingest_dto.py             ← ListadoJugadoresDTO
src/infraestructura/ingest/
├── listado_jugadores_excel.py
└── listado_jugadores_pdf.py
src/infraestructura/ui/flet/screens/lista_buena_fe_screen.py  ← se extiende
pyproject.toml / uv.lock                      ← + openpyxl y la librería de PDF (versiones exactas)

tests/unit/test_listado_jugadores_parsers.py
tests/unit/test_identificador_jugadores.py
tests/integration/test_importar_lista_buena_fe.py
tests/integration/fixtures/listado_jugadores_anonimo.xlsx (y .pdf)
```

#### US-201 — Importación de Planillas de Partido (Excel y PDF)

- **Esfuerzo:** L (6-10 días) · **Prioridad:** Urgente (bloqueante) · **Dependencias:** US-108,
  US-206, ADR-003
- **Antes se llamaba "Parseo de Planillas Excel con Pandas".** El 2026-10-31 se revisaron archivos
  reales y se sumó el PDF, que trae el mismo contenido (más titulares y capitán).
- **Objetivo Funcional:** convertir la planilla de estadísticas de un partido que exporta Gesdeportiva (CAB), en Excel o PDF, en un partido con el boxscore de los dos equipos, sin
  transcripción manual, con vista previa sin efecto secundario y reporte de calidad. De paso genera
  o completa las listas de buena fe de los dos clubes para esa competencia y categoría.
- **Narrativa:** Como analista, quiero importar las planillas de partido de Gesdeportiva —de mi
  club y de los demás— para eliminar el error humano de la transcripción y tener una base con
  partidos de toda la competencia.

**Formato real de la planilla de partido** (`data/estadisticaPartido_*.xlsx` y su PDF, revisados
el 2026-10-31):

- Una sola hoja (`Estadísticas-`). Título en celdas combinadas:
  `Estadísticas - UNIVERSITARIO vs DEPORTIVO NORTE - U13MX - CORDOBA - ASOCIACIÓN - 2026 - CABB - 2026`
  → local, visitante, categoría, ciudad, competencia, temporada, organizador, año.
- Un bloque por equipo: el nombre del club, una fila de grupos (`TC 2P`, `TC 3P`, `TL`, `Rebotes`,
  `TAP`, `FAL`), una fila de encabezados y una fila final `TOTALES`. Los bloques no están en filas
  fijas (en el ejemplo, el segundo encabezado está en la fila 33 y su primer jugador en la 35): el
  parser busca los encabezados por su texto.
- **Todas las celdas son texto**, incluso los números. `MIN` viene como `mm:ss` (`16:30` → 16,5);
  los tiros como `convertidos/lanzados` en una celda (`1/8`); los `%` son redundantes y se ignoran.
  Hay nombres con espacios al final.
- Nombres en formato `APELLIDOS, NOMBRES`. **No trae DNI, año de nacimiento, fecha del partido ni
  estadio.**
- El **PDF** tiene lo mismo y además marca titulares (`*`), capitán (`(CAP)`) y entrenador; el
  Excel no.
- En el ejemplo, `TOTALES` de minutos es `200:00` por equipo: partido de 40 minutos (U13). El
  máximo de 48 minutos por jugador del esquema no choca.

Mapeo a `jugadorPartido`:

| Columna del archivo       | Campo                                                  |
| ------------------------- | ------------------------------------------------------ |
| `MIN`                     | `minutosJugados` (`mm:ss` → minutos con decimales)     |
| `PTS`                     | `puntos`                                               |
| `TC 2P` `A/I`             | `T2C` / `T2L`                                          |
| `TC 3P` `A/I`             | `T3C` / `T3L`                                          |
| `TL` `A/I`                | `T1C` / `T1L`                                          |
| `DEF`, `OF`               | `rebotesDef`, `rebotesOf` (`Tot.` se ignora)            |
| `AST`, `REC`, `PER`       | `asistencias`, `recuperos`, `perdidas`                 |
| `TAP` `TC` / `TR`         | `taponesRealizados` / `taponesRecibidos`               |
| `FAL` `FC` / `FR`         | `faltasCometidas` / `faltasRecibidas`                  |
| `Num.`, `VAL`, `+/-`      | no se guardan en v0.2 (ver decisiones)                 |

- **Capa de Dominio:** reusa `FormatoArchivoInvalidoError` (US-206).
- **Capa de Aplicación:**
  - **Caso de uso:** `ImportarPlanillaPartidoUseCase` con `preview()`. Para guardar reusa
    `CargarPartidoUseCase` (US-108), y para los jugadores, `IdentificadorJugadores` (US-206).
  - **DTOs:** `PlanillaPartidoDTO` (lo que entregan los dos parsers: título y filas de cada equipo,
    ya tipadas) e `IngestReportDTO` (`creados`, `existentes`, `ambiguos`, `rechazados` con causa, y
    totales).
- **Capa de Infraestructura:**
  - **Parsers:** `PlanillaPartidoExcelParser` y `PlanillaPartidoPdfParser`. Los dos devuelven un
    `PlanillaPartidoDTO`, así el resto no sabe de qué formato vino el archivo.
  - **`IngestService`** — resuelve clubes, jugadores, inscripciones y listas, y arma el partido.
  - **UI:** `ImportScreen` — elegir el archivo (`FilePicker` de Flet), completar lo que el archivo
    no trae (la fecha), confirmar competencia y categoría, ver la vista previa con el reporte y
    confirmar.
- **Base de Datos:** afecta `club`, `jugador`, `jugadorClub`, `inscripcion`, `listaBuenaFe`,
  `jugadorListaBuenaFe`, `partido`, `jugadorPartido`.
- **Criterios de Aceptación:**
  - **AC1 — Formato:** si faltan el título o los encabezados esperados, se lanza
    `FormatoArchivoInvalidoError` antes de procesar, diciendo qué faltó.
  - **AC2 — Identificación de jugadores:** los jugadores se identifican por nombre dentro de su
    club (`IdentificadorJugadores`, US-206); los que no existen se crean y los ambiguos se resuelven
    en la vista previa.
  - **AC3 — Consistencia:** para cada equipo, la suma de las filas de jugadores coincide con la
    fila `TOTALES` del archivo en cada columna; si no, se rechaza el partido indicando la columna.
    Los puntos de `TOTALES` son el resultado final. _(Antes este AC pedía una columna de resultado
    final en `partido`, y por eso dependía de la US-204.)_
  - **AC4 — Transaccionalidad:** partido y boxscore se guardan en una sola transacción
    (`save_with_boxscore`). Lo que se crea antes (clubes, jugadores, inscripciones) queda
    aunque el partido falle, y reimportar no lo duplica (ver decisiones).
  - **AC5 — Vista Previa:** `preview()` valida el archivo y muestra qué se crearía (clubes,
    jugadores, inscripciones) sin persistir nada.
  - **AC6 — Logs:** reporte con registros procesados, jugadores creados/existentes/ambiguos y
    errores.
  - **AC7 — Usabilidad (NFR-4):** todo en una pantalla: elegir archivo → completar la fecha y
    confirmar competencia y categoría en la vista previa → confirmar.
  - **AC8 — Mismo resultado en los dos formatos:** el Excel y el PDF del mismo partido producen el
    mismo `PlanillaPartidoDTO`.
  - **AC9 — Sin duplicados:** importar de nuevo un partido ya cargado (misma competencia,
    categoría, fecha, local y visitante) se rechaza con un aviso.
- **Reglas de Negocio:**
  - El primer club del título (`A vs B`) se toma como local — **supuesto a confirmar** con más
    archivos; la vista previa permite invertirlo.
  - Club que no existe → se crea **sin** vínculo con el usuario (US-108). Se busca por nombre
    normalizado (sin tildes, mayúsculas ni espacios de más).
  - Competencia y categoría **no** se crean solas: se eligen en la pantalla, sugeridas cuando el
    nombre coincide. Los dos archivos de la CAB nombran distinto la misma categoría (`U13MX` y
    `INFANTILES MIXTO`), así que crearlas automáticamente generaría duplicados.
  - Si un club no tiene inscripción en esa competencia y categoría, se crea con su lista
    (`inscribir_con_lista`, con la fecha del partido); los jugadores de la planilla que no están en
    la lista se agregan. Así se cumple la regla de la sección 6 sin rechazar el archivo.
- **Decisiones tomadas (2026-10-31):**
  - **Datos sin lugar en el esquema** (dorsal, titular, capitán, entrenador, `VAL` y `+/-`): no se
    guardan en v0.2. `VAL` se puede recalcular (US-202); el resto se puede agregar más adelante con
    una migración (US-204), si hace falta. `+/-` no se puede recalcular: necesita el minuto a minuto.
  - **Lo que se crea antes del partido** (clubes, jugadores, inscripciones) se guarda con otros
    métodos, cada uno con su propio commit. Si el partido falla, eso queda creado; a cambio,
    reimportar no lo duplica (AC2 y AC9). Se descartó una unidad de trabajo que abarque todo: hoy
    cada método del repositorio hace su propio commit, y cambiarlo es más trabajo del que ahorra.
- **Testing Mínimo:**
  - _Unitarias:_ los dos parsers contra fixtures (`mm:ss`, `A/I`, espacios de más, bloques en filas
    distintas); `IngestService` con repositorios falsos (club nuevo, jugador ambiguo, lista
    inexistente, `TOTALES` que no coincide).
  - _Integración:_ importar el fixture a SQLite en memoria; `preview` no cambia nada; reimportar se
    rechaza.
  - _Manual guiado:_ importar el Excel y el PDF del mismo partido desde `ImportScreen` y comparar.
  - **Fixtures anonimizados:** los archivos de `data/` tienen nombres reales de jugadores menores
    de edad y no se suben al repositorio. Los fixtures son copias con el mismo formato y nombres
    inventados.

**Reparto en dos pistas:**

- **Juntos, antes:** el `PlanillaPartidoDTO` (lo que entregan los parsers) y el `IngestReportDTO`
  (lo que muestra la pantalla).
- **Pista A:** `ImportScreen` (AC7) y los dos parsers (AC1, AC8); el de PDF reusa la librería que
  fijó la US-206.
- **Pista B:** `IngestService` (AC2, AC3, AC9), `ImportarPlanillaPartidoUseCase` con `preview()`
  (AC5) y el reporte (AC6), con los fixtures y los tests de integración.

**Archivos a crear:**

```text
src/infraestructura/ingest/
├── planilla_partido_excel.py
├── planilla_partido_pdf.py
└── ingest_service.py

src/infraestructura/ui/flet/screens/import_screen.py

src/aplicacion/
├── casos_uso/importar_planilla_partido.py
└── dtos/ingest_dto.py                        ← + PlanillaPartidoDTO, IngestReportDTO

tests/unit/test_planilla_partido_parsers.py
tests/integration/
├── test_importar_planilla_partido.py
└── fixtures/planilla_partido_anonima.xlsx (y .pdf; casos borde: TOTALES que no coincide, jugador ya existente, club nuevo)
```

### Épica H2-E2: Motor Estadístico Avanzado

#### US-202 — Cálculo de Métricas Avanzadas

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-201
- **Objetivo Funcional:** implementar el motor lógico de analítica deportiva para transformar
  datos crudos del boxscore en indicadores avanzados de rendimiento (eficiencia, porcentajes
  ajustados, ritmos de juego), mediante funciones puras determinísticas.
- **Narrativa:** Como DT, quiero ver métricas como eFG%, EFF, PPP y PER para evaluar el impacto
  real de mis jugadores y comparar el rendimiento de mi equipo contra el rival en cada partido.
- **Capa de Dominio:** **Excepciones:** `CalculationError` (datos inconsistentes, ej. lanzamientos
  negativos).
- **Capa de Aplicación:**
  - **Casos de uso:** `CalcularEstadisticasAvanzadasUseCase` (aplica fórmulas sobre DataFrames),
    `GenerarTablaComparativaUseCase` (agrupa por club, "Equipo vs Rival" — **ampliado**: además de
    la comparativa de un único `idPartido`, acepta agregar por `idCompetencia` o por año, para
    comparar el rendimiento acumulado de dos equipos en toda una competencia/temporada, no solo en
    un cruce puntual), `GenerarComparativaJugadoresUseCase` (**nuevo** — compara dos jugadores en
    la misma "situación" elegida: un partido, una competencia, un año, o global/toda su carrera; y
    también compara un jugador contra el promedio de su categoría/competencia, para saber si está
    por encima o por debajo del resto).
  - **DTOs:** `MetricasAvanzadasDTO`, `ComparativaEquipoDTO`, `MetricasDTO`,
    `ComparativaJugadoresDTO` (**nuevo**).
- **Capa de Infraestructura:** `src/infraestructura/analytics/formulas.py` — funciones puras que
  reciben un `DataFrame` y retornan serie/escalar; **sin acceso a DB, sin efectos secundarios**.
- **Fórmulas mínimas requeridas:**
  - **eFG% (Effective Field Goal Percentage):** `(T2C + 1.5 × T3C) / (T2L + T3L)`.
  - **EFF (Efficiency Index):** `PTS + REB + AST + REC + TAP_R − (T2L−T2C) − (T3L−T3C) − (T1L−T1C) − PERD`.
  - **PPP (Puntos por Posesión):** `Puntos / Posesiones`.
  - **Posesiones (estimación FIBA):** `(T2L + T3L) + 0.44 × T1L + PERD − REB_OF`.
  - **% de Rebotes:** proporción de rebotes totales capturados sobre el total disponible.
- **Criterios de Aceptación:**
  - **AC1.** Disponibilidad de eFG%, EFF, PPP, PER (simplificado) y % de Rebotes.
  - **AC2.** Reporte comparativo "Equipo vs Rival" para un `idPartido` dado, **o agregado para un
    `idCompetencia`/año completo** (no solo partido a partido).
  - **AC3.** Los cálculos aceptan parámetros de filtro por Temporada e `idCompetencia`
    directamente en los DataFrames.
  - **AC4.** División por cero → 0.0; exclusión de `NaN` en resultados finales.
  - **AC5.** Cada fórmula documentada con su fuente/referencia técnica.
  - **AC6.** `formulas.py` no contiene ningún acceso a base de datos ni I/O externo.
  - **AC7 (nuevo).** `GenerarComparativaJugadoresUseCase` soporta comparar dos jugadores (mismo
    recorte: partido/competencia/año/global) y comparar un jugador contra el promedio de su
    categoría/competencia.
  - **AC8 (2026-10-31) — Muestra chica:** los resultados traen los partidos jugados (PJ) y los
    minutos; una comparación marca la muestra chica cuando alguno no llega al mínimo de partidos
    (sección 6). `formulas.py` suma el valor cada 40 minutos.
- **Testing Mínimo:**
  - _Unitarias (`tests/unit/test_formulas.py`):_ cobertura del **100%** de las funciones matemáticas, con
    valores calculados a mano y casos límite (ceros).
  - _Integración:_ `GenerarTablaComparativaUseCase` con datos de dos equipos en un mismo partido
    (semilla), verificando que los totales coinciden con el resultado final; y con datos de dos
    equipos a lo largo de una competencia completa, verificando el agregado.
  - _Integración:_ `GenerarComparativaJugadoresUseCase` jugador vs. jugador y jugador vs. promedio
    de categoría, con datos semilla de al menos 3 jugadores.

> **Por qué se agregó esto:** surge de revisar casos de uso reales de un DT (¿cómo viene mi
> jugador vs. otro de mi equipo? ¿mi equipo mejoró de una competencia a otra?) contrastados contra
> apps de analítica deportiva existentes (Hudl Assist, Hoopsalytics, Viziball, Basketball Stats
> Assistant) — comparar jugadores/equipos con distintos recortes de tiempo (partido, temporada,
> período personalizado) y contra un promedio de referencia es un feature estándar de la
> categoría, no un agregado innecesario. Ver también sección 20.

**Reparto en dos pistas** (sin interfaz):

- **Juntos, antes:** las firmas de las funciones de `formulas.py`, que la Pista B consume.
- **Pista A:** `formulas.py` con cobertura del 100 % (AC1, AC4, AC5, AC6). No depende de la US-201
  ni de la GUI — funciones puras sobre DataFrames que se prueban con datos a mano —, así que es
  trabajo suelto que se puede adelantar en el Hito 1.
- **Pista B:** `CalcularEstadisticasAvanzadasUseCase`, `GenerarTablaComparativaUseCase` y
  `GenerarComparativaJugadoresUseCase` con sus DTOs (AC2, AC3, AC7) y los tests de integración.
  Esta parte sí espera a tener datos importados (US-201) o semilla suficiente.

**Archivos a crear:**

```text
src/infraestructura/analytics/formulas.py

src/aplicacion/
├── casos_uso/calcular_estadisticas_avanzadas.py
├── casos_uso/generar_tabla_comparativa.py
├── casos_uso/generar_comparativa_jugadores.py    ← nuevo
└── dtos/metricas_dto.py

tests/unit/test_formulas.py
```

### Épica H2-E3: Inteligencia Deportiva (Pandas Engine)

#### US-203 — Integración de Motor Estadístico (Pandas Engine)

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-202
- **Objetivo Funcional:** conectar las Vistas SQL con DataFrames de Pandas para calcular métricas
  avanzadas automáticamente a partir de los datos cargados, sin acoplar fórmulas y persistencia.
- **Capa de Dominio:** **Interfaz:** `AnalyticsService` (`src/dominio/servicios/analytics_service.py`, junto a `PasswordHasher`: es un servicio, no un repositorio)
  — declara `get_boxscore_partido(partido_id)`, `get_totales_temporada(club_id, temporada)`, y los
  métodos nuevos que cubren los recortes multi-dimensionales pedidos (ver AC5):
  `get_totales_jugador(jugador_id, *, competencia_id=None, anio=None)` (si no se pasa ningún
  filtro, devuelve el acumulado global/de toda la carrera del jugador),
  `get_totales_club(club_id, *, competencia_id=None, anio=None)` (**nuevo** — agregado a nivel
  equipo, análogo al de jugador pero sumando a todos los jugadores del club; ver también sección
  3), y `get_evolucion_jugador(jugador_id, metrica)` (**nuevo** — serie temporal partido a partido
  de una métrica puntual, para ver tendencia/progreso, no solo un total acumulado).
- **Capa de Aplicación:**
  - **Caso de uso:** `CalcularEstadisticasPartidoUseCase`.
  - **DTOs:** `MetricasPartidoDTO`, `MetricasJugadorDTO`, `MetricasClubDTO` (**nuevo**),
    `EvolucionJugadorDTO` (**nuevo**).
- **Capa de Infraestructura:** `PandasAnalyticsService`
  (`src/infraestructura/analytics/pandas_analytics_service.py`) — lee desde las vistas SQL vía
  `pandas.read_sql()`, aplica las fórmulas de `formulas.py`, retorna DataFrames con columnas
  estandarizadas. Los filtros por competencia/año/global (AC5) se resuelven **acá, con `pandas`**
  (agrupando/filtrando el DataFrame ya cargado), no creando una vista SQL nueva por cada
  combinación posible — es la forma en que esta capa ya estaba pensada para poder cubrir estos
  recortes sin explotar la cantidad de vistas.
- **Vistas SQL requeridas:** `v_boxscore_completo`, `v_jugador_totales_temporada`, y el agregado
  por club nuevo (ver sección 3 — todavía sin definir el SQL exacto, queda para cuando se
  implemente esta US).
- **Criterios de Aceptación:**
  - **AC1 — `formulas.py` puro:** ninguna función accede a la DB; todas aceptan `pd.DataFrame` y
    retornan resultados. Cobertura 100%.
  - **AC2 — División por cero protegida:** retorna 0.0 (no NaN/inf) en casos límite.
  - **AC3 — Uso de Vistas SQL:** `AnalyticsService` lee exclusivamente de las vistas, nombres de
    columnas consistentes.
  - **AC4 — Integridad de Datos:** porcentajes expresados como float entre 0-100 o como ratio
    según corresponda.
  - **AC5 (nuevo) — Recortes multi-dimensionales:** tanto para jugador como para club, el motor
    soporta obtener totales por partido individual, por competencia específica, por año, y
    global/toda la carrera — sin mezclar competencias distintas jugadas en un mismo año (ver el
    bug de `v_jugador_totales_temporada` documentado en sección 20, a corregir antes o durante
    esta US).
  - **AC6 (nuevo) — Evolución/tendencia:** `get_evolucion_jugador` devuelve la serie ordenada por
    fecha de una métrica elegida, partido a partido, para poder graficar si un jugador está
    mejorando o empeorando (consumido después por `GenerarGraficoRendimientoUseCase` en US-301).
- **Testing Mínimo:**
  - _Unitarias:_ fórmulas con DataFrames en memoria.
  - _Integración:_ vistas reales en DB `:memory:` con datos semilla, comparadas con valores
    esperados.
  - _Integración:_ `get_totales_jugador`/`get_totales_club` con un jugador/club que participó en
    dos competencias distintas dentro del mismo año — confirmar que **no** se mezclan si se pide
    por competencia, y que sí se suman si se pide por año o global.
  - _Regresión:_ test que falla si se renombra una columna consumida.

- **Reparto en dos pistas** (sin interfaz):
  - **Juntos, antes:** la interfaz `AnalyticsService` (nombres de métodos y columnas que devuelve).
  - **Pista A:** datos — corregir el agrupamiento de `v_jugador_totales_temporada` (sección 20) y
    el agregado por club (sección 3), con la prueba de regresión de columnas.
  - **Pista B:** `PandasAnalyticsService`, `CalcularEstadisticasPartidoUseCase` y sus DTOs, con los
    tests de recortes por competencia/año/global (AC5) y de evolución (AC6).

#### US-205 — Consulta Estadística en Pantalla

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Dependencias:** US-203, US-107
- **Objetivo Funcional:** mostrar en la GUI las métricas del motor analítico, para que el DT
  consulte líderes, las estadísticas avanzadas de un partido y la comparativa de equipo.
  _Antes (hasta 2026-10-31) eran comandos de consola: `stats show partido`, `stats leaders` y
  `stats compare`._
- **Pantallas:**
  - **Detalle de partido** — la `PartidosScreen` de la US-107 ya muestra el boxscore; esta US le
    suma las métricas avanzadas del partido (`CalcularEstadisticasPartidoUseCase`). No se crea una
    pantalla nueva.
  - **`LideresScreen`** — top-N por PTS, REB, AST y EFF de una temporada, con filtros de temporada
    y competencia, sobre `ObtenerLideresTemporadaUseCase` en su **versión básica** (se crea acá).
    La US-301 (Hito 3) amplía ese mismo caso de uso y esta misma pantalla con filtros multi-año y
    local/visitante — no es una pantalla nueva que compita con esta.
  - **`ComparativaScreen`** — comparativa equipo vs. rival de un partido
    (`GenerarTablaComparativaUseCase`, US-202).
- **Criterios de Aceptación:**
  - **AC1.** Cada pantalla muestra tablas legibles (`components/tabla_datos.py`, US-107) con
    alineación numérica correcta.
  - **AC2.** Los filtros de temporada y competencia funcionan en `LideresScreen`.
  - **AC3.** Partido o temporada sin datos → mensaje descriptivo en pantalla, no traceback.
  - **AC4.** Todos los valores consistentes con los calculados por `formulas.py`.
  - **AC5 — Muestra chica:** `LideresScreen` muestra PJ y deja afuera a quien no llega al mínimo de
    partidos; `ComparativaScreen` muestra el aviso de muestra chica (sección 6).
- **Testing Mínimo:** integración — los casos de uso detrás de cada pantalla con datos semilla,
  verificando columnas y valores; partido/temporada inexistente → error de dominio controlado.
  Manual guiado: recorrer las tres pantallas con los datos semilla.

- **Reparto en dos pistas:**
  - **Pista A:** `LideresScreen`, `ComparativaScreen` y las métricas avanzadas en el detalle de
    `PartidosScreen`.
  - **Pista B:** `ObtenerLideresTemporadaUseCase` en versión básica y los tests de integración de
    los casos de uso detrás de cada pantalla (AC2, AC3, AC4).

**Archivos a crear (US-203 + US-205):**

```text
src/dominio/servicios/analytics_service.py
src/infraestructura/analytics/pandas_analytics_service.py
src/aplicacion/casos_uso/calcular_estadisticas_partido.py
src/aplicacion/casos_uso/obtener_lideres_temporada.py   ← versión básica (la amplía la US-301)

src/infraestructura/ui/flet/screens/     # una pantalla por archivo, misma convención del Hito 1 (AC1 de la US-107)
├── partidos_screen.py                    ← se extiende: métricas avanzadas en el detalle
├── lideres_screen.py
└── comparativa_screen.py

tests/integration/
└── test_analytics_service.py
```

> **Nota sobre las tablas:** se reutiliza `components/tabla_datos.py` (US-107) — no se crea un
> componente de tabla aparte salvo que aparezca una necesidad real que no cubra (ej. una
> comparativa lado a lado); si eso pasa, se extiende `tabla_datos.py` en vez de duplicarlo.

---

## 11. Hito 3 — Visualización Pro y Reporting (v0.3)

**Objetivo del hito:** convertir las estadísticas en tableros, gráficos e informes consumibles
por el DT para tomar decisiones tácticas antes, durante y después del partido.

**Épicas:** 3 · **Historias:** 3 · **Esfuerzo total estimado:** ~22 días·persona

**Decisiones previas requeridas:** ninguna. _Nota (2026-10-03): ADR-005 (librería PDF) y ADR-007
(motor de visualización) ya están aprobados y redactados en `docs/adr/` — `reportlab` y
`matplotlib` respectivamente, sin preguntas abiertas._

> **Hallazgo de transcripción:** el `.md` del submódulo solo tenía **US-301 y US-302** para este
> hito — **le faltaba por completo la Épica H3-E3 (Scouting) con US-303**, que sí está en el
> LaTeX. Se completa acá con la fuente que sí la tiene. Ver sección 20.

### Épica H3-E1: Dashboards e Informes (GUI & Engine)

#### US-301 — Dashboards e Informes Interactivos

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-203, US-205
- **Objetivo Funcional:** proveer en la GUI un tablero con líderes y gráficos de tendencia, y el
  motor de generación de gráficos que lo alimenta.
- **Narrativa:** Como DT, quiero ver tablas de líderes y gráficos de tendencia en un tablero para
  analizar el rendimiento del equipo de un vistazo.
- **Nota de reuso (no se pisa con la US-205):** `ObtenerLideresTemporadaUseCase` y `LideresScreen`
  ya existen en versión básica desde la US-205; acá se amplían (mismo archivo, más filtros), no se
  crea un caso de uso ni una pantalla nuevos.
- **Capa de Aplicación:**
  - **Casos de uso:** `ObtenerLideresTemporadaUseCase` (**ampliado**: además de filtrar por
    temporada/año, acepta filtrar por `idCompetencia` específica y por múltiples años a la vez,
    para comparar cómo cambió el liderazgo de una métrica entre competencias o a lo largo de
    varias temporadas), `GenerarGraficoRendimientoUseCase` (usa `get_evolucion_jugador` de
    `AnalyticsService`, US-203, para graficar la tendencia de un jugador en el tiempo — no solo un
    promedio estático), `VerTrayectoriaJugadorUseCase` (**nuevo** — vista longitudinal de un mismo
    jugador a través de distintas categorías/temporadas, ej. cómo rindió en U15 vs. cómo le va en
    U17 este año; usa el historial de `jugadorClub` que ya existe).
  - **DTOs:** `LiderDTO`, `GraficoDTO`, `TrayectoriaJugadorDTO` (**nuevo**).
- **Capa de Infraestructura:**
  - **Motor de Gráficos:** `ChartGenerator` (`src/infraestructura/analytics/chart_generator.py`)
    — genera figuras a partir de DataFrames con `matplotlib` (ADR-007).
  - **UI:** `DashboardScreen` (top-5 de líderes por rubro + gráfico de tendencia) y
    `ChartComponent` (`components/chart_component.py`, muestra en pantalla las figuras de
    `ChartGenerator`). Ambos estaban previstos en la US-401; nacen acá porque es donde aparecen
    los gráficos. Se descartan `rich`/`textual`, que eran para la consola.
- **Vistas SQL requeridas:** `v_jugador_totales_temporada`, `v_partidos_resumen`.
- **Criterios de Aceptación:**
  - **AC1 — Dashboard:** `DashboardScreen` muestra el top-5 de líderes por rubro (puntos,
    rebotes, EFF) y al menos un gráfico de tendencia.
  - **AC2 — Generación de Figuras:** `ChartGenerator` produce gráficos (PNG o interactivos) en
    **menos de 2 segundos** para un dataset de referencia (3 temporadas, 20 equipos, 1200 filas
    de boxscore).
  - **AC3 — Interactividad:** filtro por temporada **y por competencia** en `LideresScreen` y
    `DashboardScreen`.
  - **AC4.** Valores graficados coinciden con los calculados por las vistas SQL.
  - **AC5 (nuevo) — Split local/visitante:** los reportes de líderes y de rendimiento aceptan un
    filtro opcional de condición (local o visitante) para ver si un jugador/equipo rinde distinto
    según de local o de visitante (dato ya disponible en `partido.idClubLocal`/`idClubVisitante`,
    no requiere cambios de schema).
  - **AC6 — Muestra chica:** el dashboard y los gráficos muestran PJ y respetan el mínimo de
    partidos y el aviso de la sección 6.
- **Implementación requerida:** elegir una temporada en `LideresScreen` invoca a
  `ObtenerLideresTemporadaUseCase` y muestra los resultados en `tabla_datos`.
- **Testing Mínimo:**
  - _Unitario:_ ordenamiento de líderes y desempate por criterio secundario; transformación de
    DataFrame a serie temporal para gráficos.
  - _Integración:_ `ChartGenerator` con datos semilla (figura generada, valores coherentes con
    las vistas).
  - _Manual guiado:_ `DashboardScreen` y `LideresScreen` con filtros.
  - _Integración:_ `VerTrayectoriaJugadorUseCase` con un jugador que participó en más de una
    categoría/temporada en el dataset semilla.

> **Por qué se agregó esto:** la investigación de mercado (sección 20) confirma que el
> "performance trend" — aislar un jugador/métrica y ver su evolución con el tiempo, no solo un
> promedio fijo — es un feature estándar en apps de analítica deportiva (Hudl Assist,
> Hoopsalytics), y ya encaja con `GenerarGraficoRendimientoUseCase` que esta US ya tenía planeado;
> solo faltaba conectarlo explícitamente con un método de evolución en `AnalyticsService`.

- **Reparto en dos pistas:**
  - **Juntos, antes:** qué devuelve `ChartGenerator` (imagen en memoria o archivo) para que
    `ChartComponent` la muestre.
  - **Pista A:** `DashboardScreen`, `ChartComponent` y los filtros nuevos de `LideresScreen` (AC1,
    AC3, AC5 en pantalla).
  - **Pista B:** `ChartGenerator` con su prueba de rendimiento (AC2), la ampliación de
    `ObtenerLideresTemporadaUseCase`, `GenerarGraficoRendimientoUseCase` y
    `VerTrayectoriaJugadorUseCase`.

### Épica H3-E2: Reportería y Exportación

#### US-302 — Exportación Profesional a PDF

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-301, ADR-005
- **Objetivo Funcional:** emitir un reporte formal de partido o temporada en formato PDF para
  análisis y difusión interna del cuerpo técnico.
- **Narrativa:** Como DT, quiero exportar el boxscore a PDF para compartirlo con mi cuerpo técnico
  o imprimirlo.
- **Capa de Aplicación:**
  - **Caso de uso:** `ExportarReporteUseCase`.
  - **DTOs:** `ExportarReporteDTO`, `ReporteResponseDTO`.
- **Capa de Infraestructura:** `PDFReportGenerator`
  (`src/infraestructura/reports/pdf_generator.py`), librería según ADR-005. En la UI, un botón
  "Exportar PDF" en el detalle de partido (`PartidosScreen`) que invoca `ExportarReporteUseCase`.
- **Criterios de Aceptación:**
  - **AC1 — Formato Profesional:** encabezado con nombres de clubes, fecha, metadata; tablas de
    boxscore y métricas avanzadas con alineación numérica y cabeceras claras.
  - **AC2 — Convención de Nombres:** `boxscore_YYYY-MM-DD_Local_vs_Visitante.pdf`.
  - **AC3 — Robustez:** creación automática del directorio `exports/` si no existe; errores de
    I/O (ruta sin permisos, disco lleno) producen mensaje de recuperación, no crash.
- **Testing Mínimo:** generación exitosa de un PDF completo desde un `idPartido` con datos
  semilla (válido, no corrupto, abre con lector estándar); nombre de archivo y ruta esperados;
  ruta sin permisos → excepción controlada.

- **Reparto en dos pistas:**
  - **Pista A:** el diseño del PDF en `PDFReportGenerator` (AC1) y el botón "Exportar PDF" en
    `PartidosScreen`, con los errores de I/O mostrados en pantalla.
  - **Pista B:** `ExportarReporteUseCase`, convención de nombres (AC2), carpeta `exports/` y manejo
    de errores de I/O (AC3), con los tests de integración.

**Archivos a crear (US-301 + US-302):**

```text
src/aplicacion/casos_uso/
├── obtener_lideres_temporada.py   ← se extiende (creado en la US-205)
├── generar_grafico_rendimiento.py
├── ver_trayectoria_jugador.py
└── exportar_reporte.py

src/aplicacion/dtos/reporte_dto.py

src/infraestructura/analytics/chart_generator.py
src/infraestructura/reports/
└── pdf_generator.py

src/infraestructura/ui/flet/
├── screens/dashboard_screen.py
├── screens/lideres_screen.py      ← se extiende (filtros multi-año, local/visitante)
└── components/chart_component.py

tests/unit/test_leaderboard.py
tests/integration/
├── test_chart_generator.py
└── test_pdf_export.py
```

### Épica H3-E3: Inteligencia de Scouting

#### US-303 — Scouting de Rival Pre-Partido

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Dependencias:** US-203
- **Objetivo Funcional:** entregar al DT un reporte táctico detallado del rival antes del
  encuentro, basado en el historial de partidos de la temporada.
- **Capa de Infraestructura:** `src/infraestructura/persistencia/sql/views_scouting.sql` —
  vistas de análisis histórico por rival.
- **Capa de Aplicación:**
  - **Caso de uso:** `GenerarScoutingRivalUseCase`.
  - **DTOs:** `ScoutingDTO`.
- **UI:** `ScoutingScreen` — elegir rival, ventana de _N_ partidos y filtros; muestra el reporte
  y permite exportarlo.
- **Criterios de Aceptación:**
  - **AC1.** Ventana de análisis de últimos _N_ partidos configurable por parámetro.
  - **AC2.** Detección de patrones: rachas (victorias/derrotas consecutivas), tendencia de tiro,
    pérdidas recurrentes.
  - **AC3.** Filtros por competencia y categoría producen resultados consistentes con las vistas
    SQL.
  - **AC4.** Reporte exportable (texto/PDF) con conclusiones destacadas y datos fuente citados.
- **Testing Mínimo:**
  - _Unitario:_ agregaciones históricas y funciones de detección de rachas.
  - _Integración:_ vistas de scouting con dataset histórico de ejemplo (mínimo 10 partidos del
    rival); consistencia de filtros por competencia y ventana N.

> **Nota de reuso (evitar duplicar lógica):** el pedido de "comparar mi equipo contra otro equipo
> dentro de la misma competencia" (agregado, no un partido puntual — ver US-202 AC2 ampliado) es
> conceptualmente el mismo problema que resuelve el Scouting acá, solo que orientado hacia el
> propio equipo en vez de hacia el rival de un próximo partido. Conviene que
> `GenerarTablaComparativaUseCase` (US-202) y `GenerarScoutingRivalUseCase` (esta US) compartan la
> misma función de agregación histórica por club (`get_totales_club` de `AnalyticsService`,
> US-203) en vez de construir dos caminos separados para calcular lo mismo.

**Reparto en dos pistas:**

- **Pista A:** `views_scouting.sql` y `ScoutingScreen` (filtros, ventana de _N_ partidos,
  exportar).
- **Pista B:** `GenerarScoutingRivalUseCase`, detección de rachas y tendencias (AC2) y
  `ScoutingDTO`, reutilizando `get_totales_club` de la US-203 (ver la nota de reuso).

**Archivos a crear:**

```text
src/infraestructura/persistencia/sql/views_scouting.sql
src/aplicacion/casos_uso/generar_scouting_rival.py
src/aplicacion/dtos/scouting_dto.py
src/infraestructura/ui/flet/screens/scouting_screen.py
tests/integration/test_scouting_rival.py
```

---

## 12. Hito 4 — Interfaz Multiplataforma y Entrega (v1.0)

**Objetivo del hito:** completar la GUI Flet (perfil de jugador, tema, adaptación a mobile),
cerrar el hardening de seguridad, garantizar continuidad operativa mediante backup/restore y distribuir la aplicación
como binario autónomo para las plataformas objetivo.

**Épicas:** 4 · **Historias:** 4 · **Esfuerzo total estimado:** ~35 días·persona

**Decisión previa requerida:** ninguna — ✅ **ADR-002 ya aprobado** (Flet confirmado como
framework de UI, ver `docs/adr/ADR-002-framework-ui.md`). Desde el 2026-10-31 la GUI existe desde
la US-105, así que este hito ya no "migra" a Flet: completa lo que falta.

> **Hallazgo de transcripción:** el `.md` del submódulo solo tenía **US-401** para este hito —
> **le faltaban por completo las épicas H4-E2 (Resiliencia/Backup, US-402), H4-E3
> (Seguridad, US-403) y H4-E4 (Empaquetado, US-404)**, que sí están en el LaTeX. Se completa con
> esa fuente. Ver sección 20.

### Épica H4-E1: Interfaz de Usuario Adaptable (GUI)

#### US-401 — Interfaz Adaptable a Mobile y Pantallas Finales

- **Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-301, US-302, US-402,
  ADR-002
- **Objetivo Funcional:** completar la GUI que existe desde la US-105 — perfil de jugador,
  backup, tema claro/oscuro — y adaptarla a mobile, sin modificar la lógica de negocio.
- **Narrativa:** Como DT, quiero usar la misma aplicación desde mi PC o mi celular, con una
  experiencia fluida y visual.
- **Cambio de alcance (2026-10-31):** esta US era la que creaba la GUI. Con la GUI adelantada al
  Hito 1, las pantallas que listaba ya nacen en otras historias y acá **no se reimplementan**:
  `GameEntryScreen` → `CargaPartidoScreen` (US-108); `ImportScreen` (US-201); `StatsTableComponent`
  → `tabla_datos.py` (US-107); `DashboardScreen` y `ChartComponent` (US-301). Queda lo que todavía
  no tiene dueño.
- **Nota de reuso:** el botón de backup del AC4 envuelve `ExportarBackupUseCase`/
  `RestaurarBackupUseCase` (US-402, por eso es dependencia); `PlayerProfileScreen` usa
  `VerTrayectoriaJugadorUseCase` y `GenerarGraficoRendimientoUseCase` (US-301). Nada de eso se
  reimplementa acá.
- **Capa de Infraestructura (UI):**
  - **Pantallas nuevas:** `PlayerProfileScreen` (trayectoria y evolución de un jugador),
    `AcercaDeScreen` (versión de la app, ver AC4 de la US-404).
  - **Transversal:** tema claro/oscuro y diseño adaptable (responsive) en todas las pantallas
    existentes.
- **Criterios de Aceptación:**
  - **AC1 — Performance:** tiempo de arranque **< 3 segundos** también en mobile (en desktop ya
    lo exige la US-105).
  - **AC2 — UX:** soporte de Modo Oscuro/Claro basado en preferencias del sistema.
  - **AC3 — Responsividad:** adaptación automática a resoluciones de PC (1080p) y Mobile (720p)
    en todas las pantallas.
  - **AC4 — Gestión de Datos:** botón de "Backup" que invoca
    `ExportarBackupUseCase`/`RestaurarBackupUseCase` (**ya creados en la US-402** — esta US solo
    le agrega el botón, no reimplementa el backup).
  - **AC5.** Formularios con validación visual (mensajes de error en campo, sin modal genérico)
    en todas las pantallas — repaso de las creadas desde la US-105.
  - **AC6.** La UI no contiene lógica de negocio; invoca casos de uso vía inyección de
    dependencias.
- **Testing Mínimo:**
  - _Unitario:_ validadores de formularios, reglas de navegación de estado de pantalla.
  - _Manual guiado:_ flujo Dashboard → carga de partido → perfil de jugador en desktop y mobile;
    importación de Excel desde `ImportScreen` en mobile.

**Reparto en dos pistas** (las dos de interfaz):

- **Pista A:** pantallas nuevas — `PlayerProfileScreen`, `AcercaDeScreen` y el botón de backup
  (AC4).
- **Pista B:** lo transversal — tema claro/oscuro (AC2), diseño adaptable en todas las pantallas
  existentes (AC3) y repaso de la validación visual de formularios (AC5), con la prueba manual en
  mobile.

**Archivos a crear:**

```text
src/infraestructura/ui/flet/screens/
├── player_profile_screen.py
└── acerca_de_screen.py

tests/unit/test_flet_validators.py
```

### Épica H4-E2: Resiliencia y Backup

#### US-402 — Backup y Restauración de Base de Datos

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-204, ADR-008
- **Objetivo Funcional:** proteger la continuidad operativa mediante un mecanismo de exportación
  e importación de la base de datos completa, con verificación automática de integridad
  post-restauración.
- **Criterios de Aceptación:**
  - **AC1.** Exportación completa incluye metadata: versión del schema, fecha/hora, hash de
    integridad.
  - **AC2.** Restauración funciona tanto sobre instancia vacía como sobre instancia con datos
    existentes.
  - **AC3.** Verificación automática post-restore: conteo de filas en tablas críticas y checksum
    lógico de datos clave.
  - **AC4.** Checklist de estabilización ejecutada y documentada (rendimiento, errores críticos,
    regresión).
- **Testing Mínimo:** ciclo completo exportar → restaurar → verificar igualdad de datos clave;
  restauración desde backup de versión anterior con migraciones aplicadas automáticamente;
  regresión de casos críticos tras restore (auth, carga partido, exportación PDF).

**Reparto en dos pistas** (sin interfaz; el botón lo agrega la US-401):

- **Juntos, antes:** el formato del backup y de su metadata (versión de esquema, fecha, hash; AC1).
- **Pista A:** exportar — `ExportarBackupUseCase` y la parte de exportación de `backup_service.py`.
- **Pista B:** restaurar — `RestaurarBackupUseCase`, verificación post-restore (AC3) y restauración
  de un backup de versión anterior con migraciones (US-204).

**Archivos a crear:**

```text
src/aplicacion/casos_uso/
├── exportar_backup.py
└── restaurar_backup.py

src/infraestructura/persistencia/backup_service.py
tests/integration/test_backup_restore.py
```

### Épica H4-E3: Seguridad de Datos Local

#### US-403 — Hardening de Seguridad Local

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-104, US-106, ADR-006
- **Objetivo Funcional:** endurecer credenciales, política de sesión y almacenamiento local para
  que la aplicación cumpla con un nivel de seguridad adecuado al contexto de datos deportivos
  personales.
- **Criterios de Aceptación:**
  - **AC1.** Contraseñas mínimo **12 caracteres**, con validación de complejidad (mayúscula,
    número, símbolo).
  - **AC2.** Lista local de contraseñas comprometidas bloquea efectivamente su uso en registro y
    cambio.
  - **AC3.** Procedimiento de actualización mensual documentado en `docs/security/`, con pasos
    reproducibles.
  - **AC4.** CI valida versión vigente y checksum de la lista de comprometidas en cada PR.
  - **AC5.** Hashing robusto (bcrypt o Argon2) con salt único por usuario; migración de hashes
    legados.
  - **AC6.** Cifrado de base de datos local configurable (SQLCipher) sin romper la API del
    `DatabaseManager`.
  - **AC7.** Política de sesión: expiración configurable de la sesión recordada (US-106, que en
    v0.1 no expira), revocación inmediata en logout, limpieza idempotente.
  - **AC8.** Eventos de seguridad (fallos de login, cambios de contraseña) trazados en log sin
    exponer datos sensibles.
- **Testing Mínimo:** política de contraseñas (longitud, complejidad, lista comprometidas); ciclo
  hash → verificación, migración de hash legado; expiración y revocación de sesión; acceso a DB
  con y sin cifrado según configuración.

**Reparto en dos pistas** (sin interfaz):

- **Pista A:** credenciales y sesión — `credential_policy.py` (AC1), lista de contraseñas
  comprometidas con su procedimiento y control en el CI (AC2–AC4) y política de sesión de la
  sesión recordada (AC7).
- **Pista B:** almacenamiento — migración a bcrypt/Argon2 sin cambiar la interfaz `PasswordHasher`
  y migración de hashes legados (AC5), adaptador SQLCipher (AC6) y eventos de seguridad en el log
  (AC8).

**Archivos a crear:**

```text
src/infraestructura/security/
├── credential_policy.py
├── compromised_password_store.py
└── db_encryption_adapter.py (adaptador SQLCipher, opcional)

docs/security/password_compromised_update_procedure.md
tests/unit/test_credential_policy.py
```

### Épica H4-E4: Empaquetado y Distribución

#### US-404 — Empaquetado y Distribución Multiplataforma

> **Adelanto (2026-10-17, actualizado el 2026-10-31):** el paquete ya se instala en modo editable
> (`uv tool install --editable .`, comando `statspro`); hasta la US-105 ese comando es la CLI y
> desde ahí abre la GUI. El spike `docs/spike/spike_build_cli.md` investigaba el build de la CLI:
> sus hallazgos sobre el paquete raíz `statspro`, la DB en la carpeta de datos del usuario y los
> `.sql` como datos del paquete siguen sirviendo para esta US; lo específico de la CLI quedó
> obsoleto.

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-401, US-109
- **Objetivo Funcional:** generar binarios autónomos distribuibles para cada plataforma objetivo
  (Windows, Linux, macOS, Android) sin requerir instalación de Python ni dependencias externas
  por parte del usuario final.

> **iOS fuera de alcance (decisión 2026-10-03):** el NFR-1 pedía también iOS 14+, pero esta US
> nunca tuvo ningún AC para IPA y el propio plan listaba `build_ios.py` sin más contexto.
> Compilar y firmar una app iOS exige una Mac + Xcode, y distribuirla fuera de un entorno de
> desarrollo exige una cuenta de Apple Developer (u$s99/año) con certificados de firma — un costo
> real que nadie había evaluado explícitamente. Se decidió sacar iOS del alcance y corregir el
> NFR-1 en consecuencia (ver sección 7), en vez de completar esta US para una plataforma con un
> costo no asumido. Si se retoma en el futuro, es un hito/roadmap aparte, no un AC suelto acá.

- **Criterios de Aceptación:**
  - **AC1.** Binario desktop lanza la aplicación sin Python instalado en el sistema del usuario.
  - **AC2.** APK de Android instalable en dispositivos Android 9+ sin dependencias adicionales.
  - **AC3.** El pipeline de release genera artefactos para las 3 plataformas desktop en cada tag
    de versión.
  - **AC4.** Versión embebida en la aplicación (`AcercaDeScreen`, US-401) coincide con el tag de
    release.
  - **AC5.** `CHANGELOG.md` actualizado siguiendo formato _Keep a Changelog_ en cada release.
- **Testing Mínimo:** instalar binario desktop en máquina limpia (sin Python) y ejecutar flujo
  completo; instalar APK en dispositivo/emulador Android y verificar arranque; el pipeline de
  release ejecuta tests completos antes de generar artefactos.

**Reparto en dos pistas:**

- **Pista A:** desktop — `build_desktop.py` (AC1), versión embebida (AC4) y la guía de instalación.
- **Pista B:** Android y release — `build_android.py` (AC2), `release.yml` (AC3) y `CHANGELOG.md`
  (AC5).

**Archivos a crear:**

```text
build/
├── build_desktop.py   ← flet build (Windows/Linux/macOS) o PyInstaller, a decidir en la US
└── build_android.py   ← flet build apk

.github/workflows/release.yml   ← se activa con tag v*.*.*
CHANGELOG.md                    ← formato Keep a Changelog
docs/install-guide.md           ← instrucciones de instalación por plataforma
```

---

## 13. Definición de "Hecho" (DoD)

> **Nota de transcripción importante:** las dos fuentes tenían **tres versiones distintas** de la
> Definición de "Hecho" (una en el LaTeX, y **dos** dentro del mismo `.md` del submódulo — una
> etiquetada "v2" a mitad de documento y otra al final, más corta y parcialmente contradictoria
> entre sí). Se consolidan en una sola versión, la más completa, marcando esto como hallazgo en
> la sección 20.

Una Historia de Usuario se considera **Hecha** cuando cumple TODOS los siguientes puntos:

1. **Código integrado:** merge a la rama principal sin conflictos; commits con formato
   `tipo(alcance): descripción`.
2. **Tests pasan:** cobertura ≥80% en lógica de negocio general; ≥95% en componentes críticos
   (autenticación, persistencia transaccional, rollback, fórmulas estadísticas — ver Catálogo de
   Criticidad). Todos los tests corren sin errores en CI.
3. **Arquitectura respetada:** ninguna clase en `dominio/` importa de `infraestructura/` ni de
   librerías externas (`sqlite3`, `pandas`). Verificable con grep o una herramienta de análisis
   de imports.
4. **SQL verificado:** si la US crea o modifica una vista SQL, la vista está en `views.sql` y
   existe un test de integración que la consulta con datos de `seed.sql`.
5. **Transacciones:** si la US persiste múltiples tablas (ej. partido + estadísticas), existe un
   test que verifica que un fallo parcial hace rollback completo.
6. **ADR documentado:** si la US requirió una decisión arquitectónica, el ADR correspondiente
   está aprobado y en el repositorio.
7. **Sin imports cruzados:** verificado con una herramienta de linting de arquitectura.
8. **Docstring mínimo:** todos los métodos públicos tienen docstring de una línea; los métodos
   complejos documentan sus parámetros.
9. **Si incluye UI:** validada manualmente en desktop (Windows, y Linux si hay entorno gráfico);
   desde la US-401 (Hito 4), también en mobile.
10. **Trazabilidad:** eventos de log relevantes implementados con `correlation_id` (desde la
    US-110; las historias anteriores usan el logger actual).
11. **Pipeline CI en verde:** lint + tests + cobertura.

**El repositorio del agregado tiene su propia interfaz en el dominio**, y **la persistencia fue
validada mediante una prueba de integración con SQLite** son, además, dos condiciones que ambas
fuentes repiten como base mínima innegociable — se mantienen implícitas en los puntos 3 y 4
de arriba.

---

## 14. Catálogo Técnico de Criticidad

Artefacto vivo del backlog de arquitectura donde se lista cada módulo con: nivel de criticidad,
justificación, owner técnico y cobertura objetivo.

**Ubicación:** `docs/catalogo-criticidad.md` (❌ no existe todavía — se inicializa en US-109).

**Estructura mínima de la tabla:** `Módulo | Criticidad | Justificación | Owner | Cobertura
objetivo | Evidencia`.

**Criterios de clasificación (crítico si cumple al menos uno):**

- Controla acceso, autenticación o autorización.
- Persiste datos en múltiples tablas con transacciones.
- Impacta la integridad histórica del dato deportivo.
- Implementa cálculos estadísticos oficiales usados en decisiones tácticas.

**Gobernanza:** owner primario Arquitecto Técnico; co-owner QA Lead. Revisión obligatoria en
kickoff de hito y en cada planificación de sprint.

---

## 15. Proceso de Liberación de Versiones

### Versionado semántico

`vMAJOR.MINOR.PATCH` (Semantic Versioning 2.0):

- **MAJOR** — cambios incompatibles con versiones anteriores (ej. rediseño del schema que
  requiere migración manual).
- **MINOR** — nuevas funcionalidades compatibles. **Cada hito completado incrementa el MINOR**
  (H1 → v0.1.0, H2 → v0.2.0, H4 → v1.0.0).
- **PATCH** — corrección de bugs sin nuevas funcionalidades (ej. v0.1.1).

> Mientras `MAJOR = 0`, la API no se considera estable — cualquier hito puede cambiar el schema o
> los contratos internos. La versión `1.0.0` se alcanza al completar el Hito 4.

### Estrategia de ramas

| Rama                 | Propósito                                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------- |
| `main`               | Solo commits de merge desde `release/`. Cada commit tiene un tag de versión. Nunca se trabaja directo acá. |
| `develop`            | Rama de integración; las `feature/` se mergean acá.                                                        |
| `feature/nombre`     | Una rama por US o tarea, desde `develop`, mergeada por PR. Ej. `feature/us-101-sqlite-schema`.             |
| `release/vX.Y.Z`     | Se crea desde `develop` cuando el hito está feature-complete. Solo acepta fixes y bump de versión.         |
| `hotfix/descripcion` | Para bugs críticos en producción; desde `main`, se mergea a `main` y a `develop`.                          |

### Proceso de release paso a paso

1. **Preparar la rama:** `git checkout -b release/v0.1.0 develop`; actualizar `version` en
   `pyproject.toml`; mover `[Unreleased]` a `[0.1.0] - YYYY-MM-DD` en `CHANGELOG.md`; correr
   `make test` (debe pasar); solo corregir bugs críticos, sin features nuevas.
2. **Mergear a `main` y taggear:** merge `--no-ff`; el tag describe el contenido del hito, no
   solo el número; `git push origin main --tags`.
3. **Mergear de vuelta a `develop`:** para que los fixes del release lleguen a desarrollo; borrar
   la rama de release.
4. **Crear el GitHub Release:** con `gh release create v0.1.0 --title "..." --notes-file
CHANGELOG.md`; adjuntar binarios con `gh release upload`; o automatizado por
   `.github/workflows/release.yml` (US-404) al detectar el tag.
5. **Verificar el release:** confirmar tag/notas/artefactos en GitHub; instalar el binario en
   máquina limpia y correr el smoke-test de instalación.

### Formato del `CHANGELOG.md`

Estándar **Keep a Changelog** (keepachangelog.com): sección `[Unreleased]` al tope para cambios en
desarrollo; una sección `[vX.Y.Z] - YYYY-MM-DD` por release con subsecciones `Added`, `Changed`,
`Fixed`, `Removed`, `Security`.

> **Buena práctica:** actualizar `[Unreleased]` en cada PR mergeado, no solo al momento del
> release.

### Hotfix — corregir un bug en producción

1. `git checkout -b hotfix/descripcion-breve main`.
2. Aplicar la corrección mínima; un test de regresión que falla sin el fix.
3. Actualizar `PATCH` en `pyproject.toml` (ej. 0.1.0 → 0.1.1) y `CHANGELOG.md`.
4. Merge `--no-ff` a `main`; tag `v0.1.1`.
5. Mergear también a `develop` para no perder el fix.
6. Crear GitHub Release con la nota del bug corregido.

---

## 16. Roadmap Futuro (Hitos 5–9, visión de producto)

> Los hitos 5–9 son **visión de producto, no compromisos de entrega**. Se refinan y priorizan
> según feedback real de usuarios al cierre de v1.0. Se transcriben completos porque forman parte
> del PRD original, aunque no son parte del plan de trabajo actual.

- **Hito 5 · Ecosistema Conectado y Colaborativo (v1.5):** romper el aislamiento local.
  Sincronización cloud híbrida (FastAPI + PostgreSQL, manteniendo la app 100% funcional
  offline); exportación de "Match Cards" para redes sociales; base de datos compartida de
  scouting entre DTs (con consentimiento explícito). Investigación previa de la sincronización
  (local-first con Supabase como alternativa): ver `docs/spike/spike_supabase.md`.
- **Hito 6 · Inteligencia Táctica con IA (v2.0):** pasar de análisis descriptivo a prescriptivo.
  Motor de recomendación de quinteto (scikit-learn/XGBoost); detección automática de patrones
  (rachas de tiro, degradación defensiva por fatiga, pérdidas en momentos de presión — z-score,
  ARIMA); explicabilidad con SHAP values; integración de video scouting; marco de
  experimentación A/B de estrategias.
- **Hito 7 · Live Stats y Cancha Digital (v3.0):** captura de datos en tiempo real. Módulo de
  captura en vivo en tablet (<200ms por acción); dashboard en vivo para el banco (PPP por
  posesión, eFG% acumulado, +/- por jugador); mapa de tiro interactivo por zonas; control de
  carga/fatiga con alertas.
- **Hito 8 · Plataforma Federativa y Competición Multi-Liga (v4.0):** escalar de club a
  federación. Integración con APIs federativas (CABB, FIBA); vista multi-club para oficiales de
  liga; reportería regulatoria automatizada; benchmarking anónimo inter-club; gestión de árbitros
  y planilleros.
- **Hito 9 · Multi-Deporte y Ecosistema de Formación (v5.0):** extender más allá del básquet.
  Motor estadístico multi-deporte configurable (voleibol, fútbol sala, handball); seguimiento de
  desarrollo a largo plazo entre categorías; modelado de riesgo de lesión por carga acumulada;
  módulo de formación para entrenadores; portal de seguimiento para familias (solo lectura,
  opt-in).

---

## 17. Estructura de Repositorios

Cada módulo de datos se divide siguiendo el S.R.P. (Single Responsibility Principle):

| Entidad / Agregado | Repositorio                    | Vistas Relacionadas                         | Estado real                                                              |
| ------------------ | ------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------ |
| **Identidad**      | `SqliteUsuarioRepositorio`     | N/A                                         | ✅ funcional y testeado                                                  |
| **Clubes**         | `SqliteClubRepositorio`        | `v_listas_detalle`                          | ✅ funcional y testeado                                                  |
| **Jugadores**      | `SqliteJugadorRepositorio`     | `v_jugador_totales_temporada`               | ✅ funcional y testeado (el bug de `link_to_club` se corrigió)           |
| **Competencia**    | `SqliteCompetenciaRepositorio` | `v_listas_detalle`                          | ✅ funcional y testeado (bugs corregidos, ver sección 20)                |
| **Partidos/Stats** | `SqlitePartidoRepositorio`     | `v_partidos_resumen`, `v_boxscore_completo` | ✅ funcional y testeado (reescrito, ver sección 20)                      |

> **Corrección respecto a ambas fuentes originales:** tanto el LaTeX como el `.md` del submódulo
> listan esta tabla con **solo 4 filas**, omitiendo el repositorio de Competencia — pese a que el
> propio texto de la US-102 en ambas fuentes lo describe en detalle. Es la inconsistencia
> original que motivó esta revisión completa del documento.

---

## 18. ADRs Pendientes — tabla de bloqueo por hito

(Duplicado intencional de la sección 8, en el formato de tabla de bloqueo que traían ambas
fuentes, por si se prefiere consultar esta vista en vez de la de "Registro de Decisiones":)

| ADR     | Título                     | Bloquea       | Decisión recomendada                                                                                                                                                              |
| ------- | -------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-001 | Arquitectura Local-First   | Hito 1        | ✅ SQLite + offline-first (ya definido)                                                                                                                                           |
| ADR-002 | Framework UI               | US-105        | ✅ Flet, se descarta Compose Multiplatform; única interfaz desde el 2026-10-31 (ver `docs/adr/ADR-002-framework-ui.md`)                                                          |
| ADR-003 | Protocolo de Ingesta       | US-201/US-206 | ⏳ Propuesta con archivos reales: mapeo fijo buscando encabezados por texto; falta elegir la librería de PDF (ver `docs/adr/ADR-003-protocolo-ingesta-excel.md`)                  |
| ADR-004 | Versionado de DB           | Hito 2        | ⏳ Migraciones manuales vs. `alembic` — pregunta abierta sobre agregar SQLAlchemy solo por el runner (ver `docs/adr/ADR-004-versionado-db.md`)                                    |
| ADR-005 | Reportes PDF               | US-302        | ✅ `reportlab` (ya definido, ver `docs/adr/ADR-005-reportes-pdf.md`)                                                                                                              |
| ADR-006 | Seguridad y Cifrado        | US-104/US-403 | ✅ v0.1: `pbkdf2_hmac` con salt **dinámico** (ver `docs/adr/ADR-006-seguridad-cifrado.md`). v1.0: SQLCipher + bcrypt/argon2, con preguntas abiertas de viabilidad multiplataforma |
| ADR-007 | Motor de Visualización     | US-301        | ✅ `matplotlib` (ya definido, ver `docs/adr/ADR-007-motor-visualizacion.md`)                                                                                                      |
| ADR-008 | Estrategia de Backup       | Hito 4        | ✅ Export manual con `VACUUM INTO`/backup online de SQLite (ya definido, ver `docs/adr/ADR-008-estrategia-backup.md`)                                                             |
| ADR-009 | Pipeline CI/CD             | US-109        | ✅ GitHub Actions hosteados por GitHub, ya implementado (ver `docs/adr/ADR-009-pipeline-cicd.md`)                                                                                 |

---

## 19. Convenciones rápidas

- **Commits:** `tipo: descripción corta` (`FEAT`, `FIX`, `DOCS`, `STYLE`, `REFACTOR`, `PERF`,
  `TEST`) — ver `docs/info_modulo/02-reglas.md`. _(El LaTeX propone el formato `tipo(alcance):
descripción` con alcance entre paréntesis — ambos formatos conviven en las fuentes, el equipo
  debería fijar uno solo.)_
- **Interfaces de repositorio:** el proyecto usa `ABC`/`@abstractmethod` en la práctica, **no**
  `typing.Protocol` como sugiere `docs/info_modulo/07-protocolos.md` (que compara ambas). Ambas son válidas — vale un ADR corto
  para dejarlo asentado.
- **Logging:** `infraestructura/logger.py` ya implementado (rotación 10MB, 5 backups, nivel
  INFO+ a archivo) — ver `docs/info_modulo/01-logger.md`. Es la base sobre la que debería crecer
  la US-110 (JSON estructurado + `correlation_id`), no un reemplazo.
- **Análisis estático:** el proyecto usa `ruff` en la práctica (`pyproject.toml`,
  `.github/workflows/MainAction.yml`), no `flake8`/`pylint` como sugería el borrador original del
  Acuerdo de Ingeniería (sección 5) — ya reflejado arriba.

---

## 20. Estado real del código vs. plan (hallazgos)

> **Reescrita el 2026-08-17.** Las revisiones anteriores (2026-08-09 y siguientes) catalogaron una
> cantidad grande de bugs en los 5 repositorios. **Se hizo una auditoría fresca hoy** —
> `mypy --strict` (**0 errores**, antes 50) y `pytest -q` (**53 passed, 0 failed**), más relectura
> completa de `sqlite_jugador_repositorio.py`, `sqlite_competencia_repositorio.py` y
> `sqlite_partido_repositorio.py` — y **prácticamente todo lo de código quedó resuelto**. Se saca
> de acá lo ya corregido (queda como historial en el propio historial de git, no hace falta
> repetirlo en el plan) y se deja solo lo que sigue vigente + lo nuevo de esta revisión.

### Resuelto desde la última auditoría (ya no requiere acción — solo para que quede constancia)

Confirmado hoy, con lectura completa de cada archivo, no solo con `mypy`/`pytest` en verde:

- Los 5 repositorios usan `sqlite3.Connection` crudo, de forma uniforme (patrón de conexión ya
  unificado).
- `SqliteCompetenciaRepositorio`: los 3 bugs (`guardar_inscripcion` con conteo de `?` mal,
  `obtener_categorias` con `fetchall` sin invocar, y los 2 métodos sin implementar) están
  corregidos — las 12 funciones completas y funcionales.
- `sqlite_partido_repositorio.py` (renombrado desde `sqlite_juego_repositorio.py`): reescrito por
  completo — tabla/columna correctas, sin el método de conexión inexistente, `INSERT` de boxscore
  con columnas/valores alineados, `guardar_partido`/`guardar_boxscore` ya reciben la dataclass
  completa (Liskov resuelto), y sumaron `save_with_boxscore()` — el método atómico multi-tabla que
  pide la carga atómica de partido (hoy US-108; ese trabajo de repositorio ya está hecho).
- `sqlite_jugador_repositorio.py`: `buscar_por_club` devuelve `[]` (no `None`); `link_to_club` ya
  usa `jc.idJugador`/`jc.idClub` (el bug de atributos está resuelto); `guardar()` ya valida DNI
  duplicado y lanza `DNIDuplicadoError` — regla de negocio implementada, no solo documentada.
- El patrón sistémico "`None` en vez de `[]`" en los métodos de listado: resuelto en las 5
  implementaciones.
- El manejo de errores silencioso: las 5 implementaciones ya loguean (`logger.error`/
  `logger.critical`) en cada `except`, con el patrón de dos bloques (`sqlite3.Error` → log +
  `None`; `TypeError` post-commit → log crítico + `raise`) acordado en sesiones anteriores.
- Las 12 entidades de dominio ya tienen `__post_init__` con validación de tipos, y
  `dominio/exceptions.py` ya existe (`ErrorDeDominio`, `DNIDuplicadoError`).
- El typo `SquliteJugadorRepositorio` está corregido (`SqliteJugadorRepositorio`).
- Cobertura de tests: ya no hay archivos de test vacíos — la suite completa (53 tests) cubre los 5
  repositorios.
- **CI evolucionó bastante desde la última auditoría:** ahora corre `pip-audit`, `gitleaks`,
  `mypy --strict`, `ruff` (lint) y tests en Linux/Windows/Docker con una matriz de Python 3.11 a
  3.14 (desde el 2026-10-11: 3.12 a 3.14 y solo en Linux; Windows y Docker solo con 3.13; `Dockerfile.test` + `.dockerignore` ya armados y correctos), y Dependabot vigila las
  dependencias. Ruff y mypy usan en todos lados (CI, pre-commit y local) la versión de
  `pyproject.toml`. Ver `docs/ideas-aprendizaje.md` sección 8 para el informe detallado de qué
  falta. Las dependencias ya están fijadas en `pyproject.toml` + `uv.lock` (se eliminó
  `requerimientos.txt`) y auditadas con `pip-audit`.

### Todavía vigente — vistas SQL

- ❌ **`obtener_lista_por_inscripcion` — ya no es un bug de tipos, pero revisar si sigue el AC de
  la interfaz.** (Verificar en el próximo repaso de `competencia_repositorio.py` vs. su
  implementación — el resto de la clase ya está limpio, este punto puntual conviene reconfirmarlo
  cuando se use desde un caso de uso real en US-103.)
- ❌ **Bug de diseño en `v_jugador_totales_temporada` (`views.sql`), confirmado hoy releyendo el
  archivo:** agrupa `GROUP BY j.idJugador, comp.anio` — **por año, no por competencia**. Si un
  club juega dos competencias distintas en el mismo año (ej. "Liga Provincial" y "Copa de
  Verano"), esta vista **mezcla ambas en una sola fila**, perdiendo la granularidad "por
  competencia específica". Cobra más relevancia ahora que se documentaron explícitamente los
  filtros por competencia en US-202/203/301 (ver más abajo) — hay que corregir esta vista (o
  reemplazarla por agregación en Pandas, ver nota de US-203) antes de construir esos filtros
  encima.
- ❌ **No existe ningún agregado estadístico a nivel club/equipo** — solo existe el de jugador
  (`v_jugador_totales_temporada`). Ya se documentó el concepto en la sección 3 (Arquitectura de
  Datos) y se referenció en US-203; falta implementarlo cuando se llegue a esa US.
- **Campo/tabla que falta para que el propio PRD sea implementable:** no existe ningún campo que
  guarde el resultado final oficial del partido (ej. `puntosLocalFinal`/`puntosVisitanteFinal`).
  Importa porque la propia **US-201 AC3** pide verificar que "la suma de puntos individuales
  coincida con el resultado final del partido cargado", pero hoy no hay dónde guardar ese
  resultado para comparar. Propuesta ya volcada (marcada como tal, no implementada) en el DER de
  `docs/diagramas/diagramas.md` y anotada en US-108. **Actualización (2026-10-31):** el AC3 de la
  US-201 ya no lo necesita, porque valida contra la fila `TOTALES` del archivo; el campo queda como
  mejora opcional para la carga manual.
- Tampoco existe todavía la tabla `schema_version` que pide US-204 (Hito 2, no arrancado —
  esperable).

### Nuevo — investigación de mercado para las estadísticas multi-dimensionales (2026-08-17)

Antes de sumar las ideas de estadísticas de jugador/equipo con distintos recortes (partido,
competencia, año, global, comparativas) a US-202/203/301/303, se investigaron apps reales de
analítica de básquet para no proponer a ciegas — confirma que estos ejes son estándar en la
categoría, no sobrealcance: filtros por partido/temporada/período personalizado, comparativas
jugador vs. jugador y equipo vs. equipo con distintos operadores (promedio, mediana, total), y
"performance trends" (evolución de una métrica en el tiempo, vía media móvil). Fuentes:
[Hudl Assist — Basketball](https://www.hudl.com/products/assist/basketball),
[Hoopsalytics](https://hoopsalytics.com/), [Viziball](https://viziball.app/nba/en),
[Basketball Stats Assistant](https://basketballstatsassistant.com/en/). El detalle de qué se
agregó a cada US está en las propias US-202, US-203, US-301 y US-303 (Hito 2 y 3).

### Hallazgos de organización de código

- **Entidades agrupadas en un mismo archivo:** el PRD prevé un archivo por entidad; el código real
  agrupa varias entidades relacionadas en un mismo archivo (ej. `competencia.py` contiene 5
  dataclasses). Razonable para el tamaño actual — conviene un acuerdo explícito del equipo sobre
  si se mantiene así.
- ✅ **Capa de aplicación implementada** (`src/aplicacion/`): los 17 casos de uso de la US-103 y sus DTOs,
  con la CLI correspondiente (retirada en la US-105). Ver `docs/info_modulo/03-casos-de-uso.md` y
  `docs/context_ia/2026-08-17-us103-explicada-en-profundidad.md` para el detalle.
- ✅ **Huecos de alcance detectados y cerrados (2026-09-20):** el PRD prometía "categorías y listas de buena fe" en el pilar 2, pero ninguna US planificaba crear/listar categorías, listar competencias
  ni administrar la lista de buena fe, aunque las tablas y los métodos del repositorio existían. Se incorporaron a la US-103 (ver el recuadro "Alcance ampliado" de esa US).
  ✅ **Auditoría de cierre de la US-103 (2026-09-20):** se cerró también el ciclo de vida del vínculo jugador-club (`jugador unlink`, regla de no superposición), **quitar un jugador de la lista** (`lista remove`),
  las validaciones de valor de las entidades (`DatoInvalidoError`) y `partido list` con nombres (vista `v_partidos_resumen`).
  **Decisiones que siguen abiertas:** (1) **cómo valida la US-108 la lista cuando el partido no guarda la categoría** (ver la regla agregada en la US-108); (2) si la regla "el jugador debe tener vínculo vigente
  con el club" para habilitarlo admite excepciones (préstamos); (3) **editar o borrar** clubes, competencias y jugadores no está en ninguna US (el PRD solo pide crear, listar y vincular), por lo que un dato
  mal cargado hoy solo se corrige en la base; (4) **`jugador historial`** (ver todos los clubes por los que pasó un jugador): el repositorio ya expone `historial_vinculos`, falta el caso de uso y la pantalla si se los necesita.

### Hallazgos de documentación (inconsistencias entre las fuentes del PRD — no cambian con el código)

- **El submódulo (`.md`) tenía Hito 3 y 4 incompletos.** Le faltaba la Épica H3-E3 (US-303,
  Scouting de Rival) completa, y las épicas H4-E2, H4-E3, H4-E4 (US-402 Backup, US-403 Seguridad,
  US-404 Empaquetado) completas. Solo estaban en el LaTeX. Ya se completó en este documento
  usando esa fuente.
- **Tres versiones distintas de la Definición de "Hecho" (DoD).** Una en el LaTeX (la más
  completa) y **dos** dentro del mismo archivo del submódulo. Se consolidaron en la sección 13.
- **El `.md` del submódulo no tenía sección de Requisitos No Funcionales (NFR)** — solo estaba en
  el LaTeX. Se agregó en la sección 7.
- **El `.md` del submódulo no tenía el Proceso de Liberación de Versiones** — solo estaba en el
  LaTeX. Se agregó en la sección 15.
- **ADR-002 y ADR-008 tenían bloqueo de hito contradictorio entre fuentes** (texto narrativo dice
  un hito, la tabla de ADRs dice otro). **Ambos ya se resolvieron (2026-10-03):** ADR-002 bloquea
  el Hito 4 (`docs/adr/ADR-002-framework-ui.md` — el Hito 2 no tiene ninguna tarea de GUI);
  ADR-008 también bloquea el Hito 4 (`docs/adr/ADR-008-estrategia-backup.md` — todo el contenido
  de backup, US-402, vive en la Épica H4-E2, nada en el Hito 3).
- **El estándar de análisis estático documentado no coincidía con el real** (`flake8`/`pylint` vs.
  `ruff` real) — ya corregido en la transcripción.
- **La tabla "Estructura de Repositorios"** (sección 17) le faltaba la fila de Competencia en
  ambas fuentes originales — corregida acá.
- **US-103, US-104 y US-106 se contradecían sobre `src/infraestructura/ui/cli/`**: US-103 listaba
  archivos de comando por verbo (`player_add.py`, `club_add.py`...) mientras US-106 usaba
  convención por entidad (`player_commands.py`, `club_commands.py`...) para la misma carpeta, y
  las tres historias daban a entender que creaban `main_cli.py` desde cero pese a que US-106
  depende de que US-103 y US-104 ya estén terminadas. Corregido: `main_cli.py`, `commands/` y
  `formatters/table_formatter.py` nacen en US-103 (que ya necesita `argparse`/`tabulate` para su
  propio AC4), con convención por entidad en las tres historias; US-104 y US-106 quedan
  documentadas como extensión sobre lo existente, no como creación nueva.
  **Decisión posterior (2026-09-20):** finalmente se adoptó **un archivo por acción** (`club_add.py`,
  `jugador_link.py`…), tal como se construyó el 29/08, y el composition root de la CLI es `src/main.py`
  (no existe `main_cli.py`). Las tres historias ya reflejan esa convención.
  **Nota de numeración (2026-10-03):** este hallazgo se escribió cuando la US-104 era una sola
  historia ("Autenticación y Sesión Local") y la US-106 era "CLI con Command Pattern". Desde la
  revisión de esa fecha, la autenticación/sesión quedó dividida en US-104 (Autenticación) y US-105
  (Sesión y Club Activo), y la vieja "CLI con Command Pattern" pasó a ser **US-107**. El hallazgo
  en sí sigue siendo válido tal como está contado (es historia), solo cambió la numeración vigente.
  **Segunda renumeración (2026-10-31):** con el retiro de la CLI, la sesión pasó a US-106, la US-107
  pasó a ser "Pantallas de Gestión", la carga de partido pasó a US-108 y el monitoreo a US-110 (ver
  la tabla al inicio del documento). Toda la carpeta `ui/cli/` de este hallazgo se borra en la
  US-105.

### Lo que ya está sólido

- ✅ `SQLiteManager` (`database_manager.py`): conexión, `PRAGMA foreign_keys`, `row_factory`,
  inicialización de schema/vistas/seed/limpieza, con manejo de errores y logging.
- ✅ Las 4 vistas SQL (`views.sql`) funcionan y están probadas, incluyendo protección contra
  división por cero (salvo el bug de agrupación de `v_jugador_totales_temporada` ya anotado).
- ✅ Los 5 repositorios SQLite funcionales y testeados, con manejo de errores logueado
  consistentemente.
- ✅ `mypy --strict` y la suite completa en verde (lo verifica el CI en cada PR).
- ✅ Pipeline CI real: `pip-audit`, `gitleaks`, `ruff` (lint), `mypy --strict` y tests en
  Linux/Windows/Docker (matriz de Python 3.12–3.14 solo en Linux; Windows y Docker con 3.13; cobertura ≥ 85 % en
  Linux) y job agregador `ci-ok`. Falta marcar `ci-ok` como _required status check_ en GitHub (ver US-109).
- ✅ Suite de tests dividida por repositorio (`test_repositorios_*.py`), más fácil de mantener que el archivo único anterior.
