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
>
> **Cambio de forma de trabajo (2026-11-27), al cerrar el Hito 1:** desaparece `develop`; cada
> historia se toma como un ticket y va en una PR chica a `main` (secciones 5 y 15). Las versiones se
> atan a hitos y épicas (Hito 1 → v1.0.0, cada épica sube el MINOR y la última de cada hito, el
> MAJOR). Las historias de los Hitos 2 a 4 se dividieron en historias chicas sin pistas A/B. Desde
> la v1.0.0 la base de un usuario solo cambia con migraciones aditivas (sección 3).

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
9. [Hito 1 — Núcleo de Datos e Interfaz Gráfica Base (v1.0.0)](#9-hito-1--núcleo-de-datos-e-interfaz-gráfica-base-v100)
10. [Hito 2 — Motor de Ingesta y Análisis (v2.0.0)](#10-hito-2--motor-de-ingesta-y-análisis-v200)
11. [Hito 3 — Visualización Pro y Reporting (v3.0.0)](#11-hito-3--visualización-pro-y-reporting-v300)
12. [Hito 4 — Interfaz Multiplataforma y Entrega (v4.0.0)](#12-hito-4--interfaz-multiplataforma-y-entrega-v400)
13. [Definición de "Hecho" (DoD)](#13-definición-de-hecho-dod)
14. [Proceso de Liberación de Versiones](#15-proceso-de-liberación-de-versiones)
15. [Roadmap Futuro (Hitos 5–9, visión de producto)](#16-roadmap-futuro-hitos-59-visión-de-producto)
16. [ADRs Pendientes — tabla de bloqueo por hito](#18-adrs-pendientes--tabla-de-bloqueo-por-hito)
17. [Convenciones rápidas](#19-convenciones-rápidas)

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
| 5   | Rigidez de plataformas   | El DT no puede integrar datos de Gesdeportiva fácilmente        | Ingesta manual             |

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

**En el alcance (hasta el Hito 4, v4.0.0):**

- **Ingesta multimodal:**
  - _Automática:_ carga de planillas Excel o PDF de Gesdeportiva (partidos y listados de jugadores).
  - _Manual:_ formulario para carga post-partido (jugador por jugador).
- **Persistencia local:** base de datos SQLite única por instalación de usuario.
- **Motor estadístico:** análisis de tendencias, PPP, estadistica avanzada y eficiencia con Pandas.
- **Multiplataforma:** ejecución en Windows, Linux, macOS y dispositivos móviles.

**Fuera de alcance (hasta el Hito 4, v4.0.0):**

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

| Perfil                   | Rol y Contexto                                               | Objetivo Principal                             | Problema Actual                                         |
| ------------------------ | ------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------- |
| **Director Técnico**     | Líder táctico, desde categorías formativas hasta profesional | Optimizar rendimiento mediante datos objetivos | El cálculo manual de EFF/PPP es tedioso                 |
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

### Evolución del esquema desde v1.0.0 (regla de producción)

Desde la v1.0.0 hay usuarios con datos reales en `~/.statspro/`. **Una versión nueva nunca puede
hacerles perder datos.** Por eso, a partir del Hito 2:

- **Prohibido modificar la base, salvo con migraciones aditivas** (agregados en caliente, como las
  migraciones de Supabase). Las aplica yoyo-migrations (US-204, ADR-004) al abrir la app, una sola
  vez cada una y en orden.
- **Permitido en una migración:** `CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE … ADD COLUMN` (que
  acepte `NULL` o tenga `DEFAULT`; SQLite no deja agregar una columna `PRIMARY KEY`, `UNIQUE` ni
  `NOT NULL` sin default) e `INSERT` de datos de referencia nuevos.
- **Prohibido:** `DROP TABLE`, `DROP COLUMN`, `RENAME`, `DELETE`, `UPDATE`, y reconstruir una tabla
  para cambiarle tipos o restricciones. El CI lo controla (US-209). Si algún día un cambio no
  aditivo es indispensable, primero va un ADR que lo justifique; recién después se escribe la
  historia.
- **Una migración que ya está en `main` no se edita ni se borra:** se corrige con otra migración.
- **`schema.sql` queda congelado en la v1.0.0** y la US-204 lo convierte en `0001_base_v1_0_0.sql`.
  Hasta que la US-204 se mergee, ninguna historia toca tablas. Hoy `schema.sql` usa
  `CREATE TABLE IF NOT EXISTS`: no borra datos, pero un cambio a una tabla que ya existe se ignora en
  silencio en la base de un usuario, y el código nuevo falla contra ella. Por eso los cambios van por
  migración.
- **Las vistas sí se pueden cambiar:** no guardan datos y `views.sql` se recrea en cada arranque,
  después de las migraciones. Una vista solo usa columnas que ya existen por migración, y quien la
  cambia ajusta a sus consumidores.
- **El código tolera filas viejas:** una columna agregada vale `NULL` o su default en las filas
  anteriores a la migración.
- **Se terminó "borrar y recrear la base local"** para probar un cambio de tablas (así se hizo en
  el Hito 1, por ejemplo en las US-107 y US-108): también en desarrollo se hace con una migración.
- **Antes de migrar se copia la base** (US-208). Una versión vieja de la app nunca toca una base
  que ya migró una versión más nueva.
- **Lo mismo vale para los otros archivos del usuario** (sesión, configuración): una versión nueva
  lee el formato viejo o lo descarta sin error (ej. US-415).

### Agregados estadísticos: por jugador (existe) y por club (falta, propuesto)

Hoy solo existe un agregado pre-calculado a nivel **jugador**: `v_jugador_totales_temporada` (suma todas sus filas de `jugadorPartido` agrupadas por año). No existe ningún agregado equivalente a nivel **club/equipo** — todo lo que hay hoy sobre clubes es o bien por-partido (`v_partidos_resumen`, un cruce puntual) o inexistente para series de tiempo/competencias.

Para que la app pueda responder "¿cómo viene mi equipo en toda la competencia?" o "¿cómo viene mi equipo este año, sumando todas las competencias?" (ver Hito 2/3, US-221, US-227, US-307), hace falta un agregado análogo, sumando **todos los jugadores de un club** en vez de uno solo. Conceptualmente sería una vista (o un cálculo equivalente en Pandas, ver nota de US-203) con esta forma:

- Agrupada por `idClub` + (`idCompetencia` **o** `anio`, según qué recorte se pida — nunca los dos mezclados, para no repetir el bug ya documentado en sección 20).
- Mismas métricas que `v_jugador_totales_temporada` (puntos, T1/T2/T3, rebotes, asistencias, recuperos, pérdidas, tapones, faltas, porcentajes), sumadas a nivel equipo en vez de individual.
- No requiere ninguna tabla ni columna nueva — sale enteramente de `jugadorPartido` join `club`, igual que el agregado de jugador.

**Decidido en el rearmado del 2026-11-27 (US-221):** no se crea una vista nueva. El agregado sale con pandas de `v_totales_equipo_partido` (US-113), que ya junta los totales de cada equipo en cada partido, se haya cargado con boxscore o solo con totales (ADR-010).

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
    main.py :::highlight icon(logos:python) ## punto de entrada: solo llama a ejecutar() de ui/flet/app.py
    utils.py ## helpers puros compartidos (id_persistido)
    config/
      rutas.py ## rutas de la base, scripts SQL y logs
    dominio/
      entidades/ ## @dataclass puras, sin imports externos
      repositorios/ ## interfaces (ABC) de repositorios
      exceptions.py ## excepciones de negocio
      servicios/ ## interfaces (ABC) de servicios que no son repositorios (PasswordHasher, US-104)
    aplicacion/
      dtos/ ## dataclasses de entrada/salida entre capas
      servicios/ ## servicios de aplicación (SessionManager: US-105 en memoria, US-106 persistente) y el puerto SesionAlmacen
      casos_uso/ ## orquestadores (reciben repos por DI), un archivo por acción
    infraestructura/
      logger.py ## ✅ configuración central del logging
      repositorios/ ## implementaciones SQLite de las interfaces de dominio
      persistencia/
        database_manager.py ## SQLiteManager
        json_sesion_almacen.py ## JsonSesionAlmacen: la sesión recordada en ~/.statspro/session.json (US-106)
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
          errores.py ## manejador común de errores de los handlers
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
- **`servicios/`** — servicios transversales que no pertenecen a un caso de uso específico, como `SessionManager` (sesión del usuario y club activo). El contexto de cada acción (`correlation_id`) **no** quedó acá: vive en `infraestructura/observabilidad.py` y la aplicación solo usa `logging` de la biblioteca estándar (US-110, ADR-011).

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

La GUI es un único proceso que queda abierto, así que la sesión vive **en memoria** dentro del `SessionManager` mientras la app está abierta (US-105). Solo si el usuario marca **"Recordarme"** al iniciar sesión, el `SessionManager` además la guarda en `~/.statspro/session.json` para que sobreviva al cierre de la app (US-106). Es el único que decide cuándo se guarda o se borra; quien escribe el archivo es el adaptador `JsonSesionAlmacen`, a través del puerto `SesionAlmacen`.

**Estructura del archivo de sesión** (`SessionDTO`, US-106):

- `usuario_id`: identificador del usuario autenticado.
- `email`: email del usuario (para mostrar en la UI).
- `club_activo_id`: ID del club seleccionado actualmente (`null` si no se seleccionó ninguno).

Sin token ni expiración en v1.0.0 (ver las decisiones de la US-106); la expiración configurable llega con la US-415 (Hito 4).

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
5. **US-110:** `logger.py` arma el handler JSON (sink y nivel por variables de entorno); cada acción del usuario abre su `correlation_id` en `ejecutar_mostrando_errores`, cada cambio de pantalla en `al_cambiar_ruta` ("navegar") y el arranque en `ejecutar()` ("arranque").
6. **Hitos 2 a 4:** cada historia que suma una pantalla la registra acá, con sus casos de uso como dependencias.

**Regla de oro:** si una clase crea sus dependencias con `NombreClase()` dentro de un método que no sea el composition root, hay un problema de acoplamiento que debe corregirse.

---

## 5. Acuerdo de Ingeniería y Estándares

### Principios de desarrollo

- **Diseño precede a la implementación:** no se escribe código sin un diseño previo aprobado (ADR).
- **Atomicidad:** commits pequeños y lógicos. Formato: `tipo(alcance): descripción`.
- **Gestión de ramas:** `feature/usNNN-descripcion` desde `main` → PR a `main` (_squash_); tag `vX.Y.Z` en `main` al cerrar cada épica, y `hotfix/descripción` desde el último tag. Detalle en la sección 15.

### Cómo trabajamos (desde el 2026-11-27)

Somos dos y cada historia se toma como un **ticket**: la hace una sola persona, de punta a punta.

- **Qué historia tomar:** cualquiera cuyas dependencias estén todas mergeadas en `main`. Cada hito
  tiene un **mapa de dependencias** al principio. Antes de arrancar, cada uno se asigna la issue
  (Project: _En curso_), así los dos no toman la misma.
- **Rama y PR:** `feature/usNNN-descripcion` desde `main` actualizado; el número de la rama vincula
  la PR con su issue (US-109 AC18). PR a `main` con _squash_, revisada por el otro integrante.
- **PR chicas:** una historia apunta a una PR que se lee en una sentada. Si mientras se hace aparece
  más trabajo del previsto, la parte nueva se anota como una **historia nueva** en este PRD (número
  nuevo, con objetivo y dependencias) en vez de agrandar la PR.
- **`main` siempre publicable:** cada PR deja la app andando y los tests en verde. Lo que no está
  terminado no se ve (una pantalla a medias no entra al menú).
- **Las historias no se pisan:** cada una dice qué deja hecho para otras (**Entrega**) y de qué
  depende. Si una historia necesita algo que no existe, se agrega como dependencia o se crea una
  historia nueva, nunca se hace "de paso" dentro de otra. Dos historias en paralelo solo comparten
  los puntos de registro: el composition root, el menú lateral y `pyproject.toml`/`uv.lock` (una
  línea cada una; si el lock choca, se regenera con `uv lock` en vez de resolverlo a mano).
- **Forma de una historia:** encabezado con _Esfuerzo · Prioridad · Depende de · Toca la base_,
  después **Objetivo** (una oración), **Entrega**, **Criterios de Aceptación**, **Testing Mínimo** y
  **Archivos**. "Toca la base" dice si cambia el esquema (solo con una migración aditiva, sección 3)
  o una vista.
- **Tamaño:** XS o S de preferencia, M como máximo. Una historia L se divide antes de empezar.
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

**Seguimiento en GitHub (desde el 2026-11-22).** Este documento es la fuente de verdad; las issues lo reflejan:

- **Una issue por hito, épica e historia**, con el título `[H1]`, `[H1-E2]` o `[US-107]` y el texto de su sección de este PRD.
  Jerarquía con **sub-issues** (hito → épica → historia) y **milestone** = hito (`M1 - v1.0.0` … `M4 - v4.0.0`; la versión de cada épica está en la sección 15).
- **Labels:** tipo (`hito`, `epica`, `historia`, `tarea`, `bug`), épica (`H1-E1` … `H4-E4`), capa (`capa:dominio`,
  `capa:aplicacion`, `capa:infraestructura`, `capa:ui`) y `tests`, `ci`, `docs`, `dependencias`. Los de capa y los `US-NNN`
  los ponen solos los workflows en las PRs (US-109 AC18).
- **Project "StatsPro – Roadmap"** (de la organización): campos _Status_ (Backlog / Todo / En curso / En review / Hecho),
  _Prioridad_ y _Esfuerzo_ con los valores de las tablas de arriba.
- Si cambia una historia acá (alcance, AC, estado), se actualiza su issue.

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
- **Una competencia tiene sus categorías** (decisión del 2026-11-08, US-107): la categoría sigue
  siendo un catálogo común (U13 Mixto, U15, U17...), pero cada competencia habilita las que juega
  (`competenciaCategoria`). Un club solo se puede inscribir en una categoría habilitada en esa
  competencia, y no se puede quitar una categoría que ya tiene clubes inscriptos.
- En la carga manual de un partido (US-108), solo pueden figurar jugadores de la lista de buena fe
  de su club para la competencia y categoría del partido. La importación de una planilla de
  partido (US-201) o de un listado de la CAB (US-206) **genera o completa** esas listas en vez de
  rechazar a los jugadores.
- **Desde la US-113 (2026-11-27) la regla anterior vale solo para el club propio.** Del rival se cargan
  sus totales (o solo el resultado) o su boxscore por jugador. Si se carga su boxscore, en la misma
  transacción del partido se crean su inscripción, su lista de buena fe y los jugadores que no
  existían, y se habilitan en la lista los de su plantel que faltaban: el rival nunca frena la carga.

**Partidos y Estadísticas**:

- Un partido no puede tener el mismo club como local y visitante.
- Se puede cargar **cualquier partido de la competencia**, aunque el club activo no juegue: cuantos
  más partidos de otros clubes haya, más confiables son las comparaciones (decisión del
  2026-10-31). Un club creado como rival o por importación no queda vinculado al usuario.
  **Revisada por la US-113 (2026-11-27):** la pantalla de carga es del club activo (su boxscore y el
  del rival). **Cerrada por la US-114:** los partidos entre dos clubes ajenos no se cargan a mano; van a
  entrar por la importación de planillas (US-201) y la carga masiva (US-207).
- **Jugadores por partido (US-114):** como máximo **12 por equipo** (`MAX_JUGADORES_PARTIDO`), y se
  rechaza en el caso de uso. Con menos de **5** del club propio (`MIN_JUGADORES_PARTIDO`) la pantalla
  solo avisa y deja guardar igual: puede faltar cargar a alguno, o el equipo terminó con menos.
- **No hay empates (US-114):** si los dos equipos suman los mismos puntos, el partido no se guarda
  (si hubo prórroga, va sumada en el total).
- **Partido repetido (US-114):** mismo día, mismo torneo y mismo rival se avisa y se puede guardar
  igual (dos partidos el mismo día son raros, pero posibles en un torneo corto).
- **El rival nuevo se crea con el partido (US-114):** el club que se escribe y no existe se inserta en
  la misma transacción que el partido; si el partido falla, el club no queda.
- **Editar y eliminar (US-114):** editar un partido lo reemplaza entero conservando su id (mismos
  datos, boxscore, cuartos y totales, todo en una transacción). Eliminarlo borra sus filas; lo que se
  dio de alta del rival (inscripción, lista, jugadores) se conserva.
- **Clubes rivales (US-114):** un club sin usuario se puede renombrar; se puede eliminar solo si no
  tiene partidos. Los clubes propios no se tocan desde ahí.
- **Totales de un equipo (US-113):** convertidos ≤ lanzados y todo ≥ 0. Si se cargan tiros, los
  puntos tienen que dar `2×T2C + 3×T3C + T1C`; si no se carga ningún tiro, alcanza con los puntos
  (solo el resultado). Los totales cargados a mano y la suma del boxscore se leen juntos en
  `v_totales_equipo_partido`.
- **Fila vacía = no jugó (US-113):** en la planilla, la fila de un jugador sin ningún dato no se
  guarda; un jugador que entró y no hizo nada se registra con sus minutos.
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
- **Puntos por cuarto** (decisión del 2026-11-08, US-108): son **opcionales**. Si no se tienen,
  el partido se carga igual, sin error ni aviso.
  - Se cargan para los dos equipos o para ninguno, con la misma cantidad de períodos: 4 cuartos y,
    si hubo, las prórrogas (período 5, 6...).
  - Los puntos por cuarto de cada club suman sus puntos del boxscore.
  - Un promedio por cuarto se calcula solo sobre los partidos que los tienen y dice sobre cuántos
    («sobre 4 de 9 partidos»); la regla de muestra chica se aplica a esos 4, no a los 9.
- **Filtros de estadísticas** (decisión del 2026-11-08): todas las pantallas de estadísticas
  (Líderes, Comparativa, Tablero, Scouting y Perfil de jugador) usan la misma barra de filtros,
  `components/filtros_estadisticas.py` (nace en la US-225).
  - Tres desplegables encadenados: **Año** → **Competencia** → **Categoría**. Cada uno arranca con
    «Todos/Todas». Elegir un año achica la lista de competencias; elegir una competencia achica la
    de categorías a las habilitadas en ella (`competenciaCategoria`, US-107).
  - El año **no se guarda aparte**: sale de `competencia.anio` (la lista de años es
    `SELECT DISTINCT anio FROM competencia`). Alcanza mientras cada competencia sea de un solo año
    calendario, que es como se juegan las formativas.
  - Cada partido cuenta en la competencia y la categoría **en que se jugó** (`partido.idCompetencia`
    y `partido.idCategoria`), no en una categoría «actual» del jugador. Quien jugó en U17 y U19
    en la misma temporada suma por separado en cada una, y en «Todas» suma los dos.
  - Lo que el filtro deja pasar se suma y recién después se calcula: los porcentajes salen de los
    totales (aciertos sobre intentos), **nunca promediando porcentajes** de filas distintas.
  - Cada pantalla agrega a la barra su propio selector: Club y Contra (Comparativa), Rival y
    ventana de partidos (Scouting), Jugador (Perfil).
  - En **Líderes** y **Comparativa** la categoría es **obligatoria** (no tiene «Todas»): un ranking
    o una comparación entre chicos de edades distintas no dice nada. Año y competencia sí pueden
    ir en «Todos» (por ejemplo, el máximo anotador histórico de U17). Un jugador que pasó de U15 a
    U17 aparece en el ranking de cada categoría con los partidos que jugó en ella; su recorrido
    completo está en el Perfil y en el Tablero, donde la categoría sí puede ser «Todas». El
    componente lo recibe como parámetro (`categoria_obligatoria`).

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
| NFR-8 | Compatibilidad de datos | Actualizar la app nunca pierde ni rompe los datos del usuario: solo migraciones aditivas (sección 3) | Bloqueante |

---

## 8. Registro de Decisiones Arquitectónicas (ADR)

| ID      | Título                   | Estado                                                                                    | Decisión                                                                                                                                           | Bloquea         |
| ------- | ------------------------ | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| ADR-001 | Arquitectura Local-First | Aprobado (`docs/adr/ADR-001-arquitectura-local-first.md`)                                 | SQLite + offline-first                                                                                                                             | Hito 1          |
| ADR-002 | Framework UI             | Aprobado (`docs/adr/ADR-002-framework-ui.md`)                                             | Flet (Python puro); se descarta Compose Multiplatform. Desde 2026-10-31 es la única interfaz (la CLI se retira)                                    | US-105          |
| ADR-003 | Protocolo de Ingesta     | Pendiente — propuesta con archivos reales (`docs/adr/ADR-003-protocolo-ingesta-excel.md`) | Mapeo fijo en código, buscando encabezados por texto; falta elegir la librería de PDF                                                              | US-201, US-206  |
| ADR-004 | Versionado de DB         | Decidido en el PRD (2026-11-27); se formaliza en la US-204 (`docs/adr/ADR-004-versionado-db.md`) | `yoyo-migrations`: SQL plano, sin SQLAlchemy; solo migraciones aditivas (sección 3)                                                                | US-204          |
| ADR-005 | Reportes PDF             | Aprobado (`docs/adr/ADR-005-reportes-pdf.md`)                                             | `reportlab`; se descarta `weasyprint`                                                                                                              | US-302          |
| ADR-006 | Seguridad y Cifrado      | Aprobado v1.0.0 / Pendiente Hito 4 (`docs/adr/ADR-006-seguridad-cifrado.md`)              | Hash de passwords con `pbkdf2_hmac` y salt dinámico; cifrado DB (SQLCipher) y migración a bcrypt/argon2 quedan para Hito 4, con preguntas abiertas | US-104 / Hito 4 |
| ADR-007 | Motor de Visualización   | Aprobado (`docs/adr/ADR-007-motor-visualizacion.md`)                                      | `matplotlib`; se descarta `plotly` para este motor                                                                                                 | US-301          |
| ADR-008 | Estrategia de Backup     | Aprobado (`docs/adr/ADR-008-estrategia-backup.md`)                                        | Exportación/restauración manual con `VACUUM INTO`/backup online de SQLite                                                                          | Hito 4          |
| ADR-009 | Pipeline CI/CD           | Aprobado, ya implementado (`docs/adr/ADR-009-pipeline-cicd.md`)                           | GitHub Actions (hosted) para lint, tests y cobertura automáticos                                                                                   | US-109          |
| ADR-010 | Carga del rival          | Aprobado, ya implementado (`docs/adr/ADR-010-carga-rival-y-totales.md`)                   | Boxscore completo solo del club propio; del rival, totales en `estadisticaEquipoPartido` o boxscore con alta automática en la misma transacción   | US-113          |
| ADR-011 | Logs estructurados       | Aprobado, ya implementado (`docs/adr/ADR-011-logs-estructurados.md`)                      | `logging` de la biblioteca estándar con formatter JSON propio y `ContextVar` para el `correlation_id`; sin structlog ni servicio externo           | US-110          |

Estructura canónica de un ADR (ver `docs/documentacion_app_estadistica/ADR/template_adr.md`): Contexto → Alternativas Consideradas → Decisión Tomada → Ventajas y Desventajas. Los ADR escritos viven en `docs/adr/` (no en el submódulo de documentación, que es de otro repositorio). **Estado (2026-10-03): los 9 ADR ya están redactados en `docs/adr/`.** Aprobados sin preguntas
pendientes: ADR-001, ADR-002, ADR-005, ADR-007, ADR-008, ADR-009. Con preguntas abiertas a
resolver antes de cerrarlos del todo: ADR-003 (ya hay archivos reales; falta elegir la librería de PDF)
y ADR-006 (viabilidad de SQLCipher en Android y fuente de la lista
de contraseñas comprometidas, ambas para el Hito 4).

---

## 9. Hito 1 — Núcleo de Datos e Interfaz Gráfica Base (v1.0.0)

**Objetivo del hito:** construir una base técnica funcional con persistencia robusta, autenticación local, casos de uso operativos, validaciones de integridad, una interfaz gráfica de escritorio (Flet) que cubra la gestión completa y la carga de partidos, y un entorno de calidad que garantice reproducibilidad desde el primer commit.

**Épicas:** 3 · **Historias:** 14 (US-101 a US-114; la US-104 original se dividió en Autenticación
y Sesión el 2026-10-03, el 2026-10-31 se agregó la US-105 de GUI base y se renumeraron las
siguientes — ver la tabla al inicio del documento —, el 2026-11-08 se agregó la US-111 de base
visual, que va antes de la US-107 aunque tenga número más alto, y ese mismo día la US-107 se
dividió en US-107 (competencias, inscripciones y listas) y US-112 (jugadores y partidos); el
2026-11-27 se agregó la US-113, que rehace la carga de partido después de probar la app con datos
reales, y después la US-114, con lo que salió de simular el uso de un entrenador) · **Esfuerzo total estimado:** ~65 días·persona

**Orden de ejecución:** US-101 → US-102 → US-103 → US-104 (todas ✅) → ajuste previo (quitar el
DNI, en paralelo con el arranque de la US-105) → US-105 → US-106 → US-111 → US-107 → US-112 → US-108 → US-113 → US-114 → US-110. La US-109 (CI/CD) es transversal: no depende de ninguna y se va completando a lo
largo del hito.

### Cómo se trabajó el Hito 1 (historia)

Hasta el 2026-11-27 cada historia se repartía en dos **pistas** que avanzaban a la vez (interfaz y
backend), ordenadas en rondas. Se abandonó: en la práctica cada integrante tomaba una historia
entera, y las PR pasaban las 1000 líneas, imposibles de revisar. Desde el Hito 2 rige la forma de
trabajo de la sección 5: historias chicas e independientes, una persona por historia y PR directo a
`main`. Los bloques "Reparto en dos pistas" de las historias ya hechas se sacaron; el detalle quedó
en las PR de cada una.

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

- _Integración (`tests/integration/test_repositorios_\*.py`, un archivo por repositorio):_ CRUD completo por repositorio usando DB `:memory:`; `buscar_por_dni`retorna`None`si no existe, sin lanzar excepción; el`save()` de un partido y sus estadísticas es atómico; los repositorios de lectura usan las vistas SQL correctamente.

### Épica H1-E2: Lógica de Aplicación e Interfaz

#### US-103 — Gestión de Entidades (Casos de Uso Administrativos)

**Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-101, US-102 · **Estado:** ✅ Hecha

> **La CLI de esta historia se retira en la US-105 (2026-10-31).** Siguen vigentes las entidades, los casos de uso, los DTOs, los repositorios y sus tests; los comandos de `ui/cli/`, el formatter de `tabulate` y los tests de la CLI se borran y sus funciones pasan a las pantallas de las US-106 y US-107. El texto de abajo describe lo que se construyó en su momento.

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
- **`persistencia/database_manager.py`:** se agregó `abrir_conexion()` (se borró en la US-105: solo la usaba la CLI). Además se corrigió `schema.sql`, que empezaba con `DROP TABLE` y borraba todos los datos en cada arranque de la CLI.
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

#### US-104 — Autenticación de Usuarios

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103 · **Estado:** ✅ Hecha (PR #46)

> **Los comandos `stats auth ...` de esta historia se retiran en la US-105**, que pone el registro y el login en pantallas de la GUI usando los mismos casos de uso. El hasher, los casos de uso, los DTOs y sus tests no cambian.

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
  - **Decisión tomada:** la v1.0.0 usa `hashlib.pbkdf2_hmac` con **salt dinámico** (uno distinto por usuario, generado con `os.urandom` al registrarse y guardado junto al hash en el mismo string) — no salt fijo. Migrar a `bcrypt`/`argon2-cffi` queda para la US-414 (Hito 4), sin cambiar la interfaz pública de `PasswordHasher`.
- **CLI (retirada en la US-105):** `stats auth register`, `stats auth login`, `stats auth logout` (`auth_register.py`, `auth_login.py`, `auth_logout.py` en `ui/cli/commands/`). `auth_logout` solo informaba "no hay sesión que cerrar".

**Criterios de Aceptación:**

- **AC1 — Seguridad de Credenciales:** las contraseñas NUNCA se almacenan ni se loguean en texto plano. Hashing con salt dinámico por usuario.
- **AC2 — Validaciones:** email único (`EmailYaRegistradoError`); contraseña con requisitos mínimos (≥6 caracteres en v1.0.0; ≥12 con complejidad desde la US-403, Hito 4).

**Testing Mínimo:**

- _Unitarias:_ `hash`/`verify` de `PasswordHasher` (incluye que dos hashes de la misma contraseña sean distintos, por el salt dinámico); `RegistrarEntrenadorUseCase`/`LoginLocalUseCase` con `UsuarioRepositorio` mock (camino feliz + `EmailYaRegistradoError` + `CredencialesInvalidasError`).
- _Integración:_ flujo completo registro → login con DB `:memory:`.

#### Ajuste previo a la US-105 — Quitar el DNI de los jugadores

- **Decisión (2026-10-31):** los jugadores **no tienen DNI**. No aporta a las estadísticas, los archivos de la CAB no lo traen (US-201, US-206) y pedirlo obligaba a inventar DNIs para los jugadores rivales. Un jugador se identifica por apellido y nombre dentro de su club. El año de nacimiento pasa a ser opcional por el mismo motivo.
- **Esfuerzo:** S (1-2 días) · **Dependencias:** ninguna
- **Qué cambia:**
  - **Base de datos:** se quita `jugador.dni` de `schema.sql` y de `seed.sql`. Una base vieja sigue funcionando (la columna acepta nulos), así que recrear la base local puede esperar a la US-108, que igual lo pide, y hacerse una sola vez.
  - **Dominio:** `Jugador` sin `dni` y con `anioNacimiento: int | None`; se borra `DNIDuplicadoError`; `JugadorRepositorio` pierde `buscar_por_dni`.
  - **Aplicación:** `CrearJugadorDTO` sin `dni`; `RegistrarJugadorUseCase` sin la regla de DNI duplicado.
  - **Infraestructura:** `SqliteJugadorRepositorio` (`guardar`, el armado de la entidad y `buscar_por_dni`). La CLI existe hasta la US-105, así que `jugador add` y `main.py` pierden `--dni`.
  - **Tests:** los que arman jugadores con DNI o prueban el duplicado: `conftest.py`, `test_entidades.py`, `test_entidades_valores.py`, `test_uc_jugadores.py`, `test_repositorios_jugador.py`, `test_repositorios_competencia.py`, `test_database.py`, `test_sandbox_sql.py` y los de la CLI.
  - **Documentación del código actual**, en el mismo PR que el código porque describe lo que el código hace hoy: `docs/info_modulo/03-casos-de-uso.md`, `04-arquitectura.md`, `07-protocolos.md`, `09-testing.md`, `docs/arquitectura/01-repository-pattern.md`, el DER de `docs/diagramas/diagramas.md`, `RUNBOOK.md` y `README.md`.
- **Criterios de Aceptación:**
  - **AC1.** No queda ninguna referencia al DNI en `src/` ni en `tests/` (`grep -rin dni src tests` no devuelve nada).
  - **AC2.** Se puede dar de alta un jugador sin año de nacimiento; si se informa, se sigue validando (mayor a 1900 y no posterior al año actual).
  - **AC3.** Todos los checks del CI pasan.
- **Qué no entra:** evitar jugadores repetidos ahora que no hay DNI. En el alta manual lo resuelve la US-112 (buscar por nombre antes de dar de alta) y en la importación, la US-211 (`IdentificadorJugadores`).

#### US-105 — Interfaz Gráfica Base (Flet) y Retiro de la CLI

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-104, ADR-002 · **Estado:** ✅ Hecha (PR #48)

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
- **Pantallas** (`screens/`): `LoginScreen` (email + contraseña oculta), `RegistroScreen` (nombre, email, contraseña), `InicioScreen` (saluda al usuario y tiene el botón "Cerrar sesión" en la barra superior, `ft.AppBar`; el menú de navegación se agrega cuando haya secciones, en las US-106 y US-107).
- **Navegación protegida:** sin sesión, cualquier ruta interna redirige a `LoginScreen`.
- **Errores:** un único manejador común muestra cualquier `ErrorDeDominio` junto al formulario que lo causó, sin traceback y sin cerrar la app (reemplaza al `except ErrorDeDominio` de `main()`).
- **Dependencia:** `flet[desktop]==1.1.2` en `pyproject.toml` + `uv.lock` (el extra `desktop` fija también el cliente de escritorio; sin él, Flet lo instala solo al arrancar, fuera del lock).

**Retiro de la CLI (limpieza):**

- Se borran `src/infraestructura/ui/cli/` completo (`commands/` y `formatters/`), los tests `tests/unit/test_cli_main.py`, `test_cli_comandos.py`, `test_cli_comandos_listas.py`, `test_cli_auth.py`, `test_table_formatter.py` y `tests/integration/test_cli_e2e.py`, y la carpeta `scripts/` (scripts de bash que cargaban datos usando la CLI; los datos de prueba ya los da `seed.sql`).
- Se quitan `tabulate` de las dependencias y su override de mypy en `pyproject.toml`; `[project.scripts] statspro` pasa a abrir la GUI.
- `abortar()` y `fecha_iso()` de `src/utils.py` solo los usaba la CLI: se borraron junto con sus tests (`id_persistido()` lo usan los casos de uso y se queda). También se borró `abrir_conexion()` de `database_manager.py`, por el mismo motivo.
- Lo que `test_cli_e2e.py` probaba de punta a punta y no estaba cubierto por otro test pasó a `tests/integration/test_flujo_casos_de_uso.py`: casos de uso con repositorios reales sobre un archivo SQLite temporal, sin interfaz (persistencia entre arranques, flujo completo, cambio de club, nombres en `listar_partidos` y que cada error de negocio llegue como `ErrorDeDominio`). De `test_auth_flujo.py` se borró el test que llamaba a `main.main()` (con la GUI abría la ventana real); su caso de login fallido pasó a `test_sesion_flujo.py`.
- **Trabajo adelantado de US-109:** el smoke test del CI (`python src/main.py --help`, en las actions de cobertura de Linux y Windows) se reemplazó por `uv run --locked python -c "import main"`, que importa toda la app sin abrir ninguna ventana ni crear la base.
- **Documentación:** se reescriben las secciones de la CLI de `README.md`, `RUNBOOK.md`, `docs/info_modulo/03-casos-de-uso.md` (§7), `04-arquitectura.md`, `05-guia-arquitectura-app.md`, `06-patron-command.md`, `08-vistas-sql.md`, `09-testing.md` (§9) e `ideas-aprendizaje.md` (§8.14); y `docs/spike/spike_build_cli.md` queda como histórico, que hasta esta US describen la CLI porque es lo que existe en el código. Guía nueva: `docs/info_modulo/13-gui-flet-y-eventos.md` (Flet, programación por eventos, rutas, composition root y cómo agregar una pantalla).

**Decisiones a tomar al arrancar la US (no bloquean el resto del plan):**

1. **Versión de Flet:** la API cambió de forma incompatible entre la serie 0.x y la 1.0. Se elige la última estable al momento de arrancar y se fija exacta; verificar que `uv sync` en el CI y en Docker no descargue el cliente de escritorio (los tests solo importan módulos).
   **Decidido:** `flet[desktop]==1.1.2`.
2. **Cómo se testea la GUI:** Flet no trae un harness de tests maduro. Propuesta: pantallas finas (sin lógica de negocio, AC6 de la US-401 adelantado) y tests sobre lo que no depende de la ventana: `SessionManager`, el manejador de errores y las funciones puras que arman filas o validan campos.
   **Decidido:** eso, y además cada pantalla se testea sin ventana: recibe `page` por parámetro (en el test, `MagicMock(spec=ft.Page)`), el test completa los campos y llama al handler del botón. El router se testea con una `page` falsa y una fixture automática de `conftest.py` impide que un test abra la ventana. Detalle en `docs/info_modulo/09-testing.md` (§9) y `13-gui-flet-y-eventos.md` (§13).
3. **Python mínimo:** pasó de 3.11 a **3.12** (`requires-python`, mypy, actions, `Dockerfile.test`, `Makefile`): los _stubs_ de numpy que trae la cadena de dependencias usan la sentencia `type` de 3.12 y mypy fallaba al chequear contra 3.11.

**Criterios de Aceptación:**

- **AC1 — Arranque:** `uv run python src/main.py` abre la ventana en `LoginScreen` en menos de 3 segundos (NFR-5).
- **AC2 — Registro y login desde la GUI:** se registra un entrenador y se inicia sesión con `RegistrarEntrenadorUseCase` y `LoginLocalUseCase` (US-104), sin lógica de negocio en las pantallas. Email repetido, email inválido, contraseña corta y credenciales inválidas se muestran junto al formulario, sin traceback ni cierre de la app.
- **AC3 — Sesión en memoria:** después del login se navega a `InicioScreen`; "Cerrar sesión" vuelve a `LoginScreen`; sin sesión no se puede llegar a ninguna pantalla interna.
- **AC4 — Contraseña protegida:** los campos de contraseña se muestran ocultos y la contraseña nunca se escribe en logs (AC1 de la US-104).
- **AC5 — CLI retirada:** no quedan `ui/cli/`, `scripts/`, `tabulate` ni tests de la CLI; `src/` no importa `argparse`; la suite y el CI están en verde con la cobertura mínima de la US-109.

**Testing Mínimo:**

- _Unitarias:_ `SessionManager` (iniciar, cerrar dos veces sin error, `usuario_actual()` sin sesión); manejador de errores (un `ErrorDeDominio` produce el mensaje esperado); ruta protegida y router; cada pantalla sin ventana (camino feliz, error de negocio, error inesperado).
- _Integración:_ flujo registro → login → `SessionManager.iniciar_sesion` con DB `:memory:` y repositorios reales.
- _Manual guiado:_ en Windows (y en Linux si hay entorno gráfico), abrir la app, registrarse, iniciar sesión, cerrar sesión y probar cada error del AC2.

#### US-106 — Sesión Persistente ("Recordarme") y Club Activo

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-105 · **Estado:** ✅ Hecha (PR #49)

**Objetivo Funcional:** que la app recuerde la sesión entre una apertura y la siguiente cuando el usuario lo pide, y que el entrenador trabaje siempre en el contexto de un club activo elegido por él.

**Narrativa:** Como entrenador, quiero que la aplicación recuerde que ya inicié sesión y con qué club estoy trabajando, para no repetir esos pasos cada vez que la abro.

**Decisiones tomadas:**

1. **Persistir es opcional:** solo si el usuario marca "Recordarme" en `LoginScreen`. Sin marcarlo, cerrar la app cierra la sesión.
2. **Dónde se persiste:** archivo **JSON**, no la base SQLite — no compite por locks con la base y permite borrar la sesión a mano sin tocar datos de negocio.
3. **Ruta única:** `~/.statspro/session.json`, resuelta con `pathlib.Path.home()` (funciona igual en Windows y Linux).
4. **Sin token ni expiración en v1.0.0:** `SessionDTO` tiene solo `usuario_id`, `email` y `club_activo_id`. Un token tiene sentido cuando cliente y servidor están en procesos distintos; acá el mismo proceso lee su propio archivo. El archivo **nunca** guarda la contraseña ni su hash. **Riesgo aceptado para v1.0.0:** con "Recordarme", cualquiera con acceso a esa cuenta del sistema operativo abre la app sin contraseña; la expiración configurable llega con la US-415.
5. **Configurable, no hardcodeado:** loader mínimo `src/config/settings.py` + `.env.example` (idea de `docs/ideas-aprendizaje.md`, sección 4) con `STATSPRO_SESSION_PATH` (default `~/.statspro/session.json`) y `STATSPRO_DB_PATH` (default: lo que ya calcula `config/rutas.py`), para que los tests apunten a archivos temporales sin parchear código.~~ **Cambiado al arrancar la US:** sin `settings.py`, `.env` ni `python-dotenv`. La ruta del archivo se **inyecta por constructor** (`JsonSesionAlmacen(ruta)`), así los tests usan `tmp_path` sin variables de entorno; el default vive en `config/rutas.py` (`SESSION_FILE`). Si se necesita cambiarla sin tocar código, se suma una variable de entorno en `ejecutar()` (paso 6); `python-dotenv` no se agrega por tres líneas.

**Decisión a tomar al arrancar la US:** si el `SessionManager` (capa de aplicación) escribe el JSON directamente o a través de un puerto — una interfaz `SesionAlmacen` en `dominio/servicios/` y una implementación `JsonSesionAlmacen` en `infraestructura/` —, igual que se hizo con `PasswordHasher` en la US-104. El puerto respeta la regla de capas (la aplicación no hace I/O) y permite testear el `SessionManager` sin archivos.

**Decidido:** con puerto. Pero el puerto va en **`aplicacion/servicios/sesion_almacen.py`**, no en `dominio/servicios/`: su contrato usa `SessionDTO`, que es de la capa de aplicación, y el dominio no puede importar de la aplicación (`PasswordHasher` sí está en el dominio porque solo usa `str`). El adaptador es `infraestructura/persistencia/json_sesion_almacen.py`.

**Otras decisiones tomadas al arrancar:**

- **Rehidratar la sesión al abrir la app** (leer el archivo, volver a buscar el usuario en la base y revalidar el club con `CambiarClubActivoUseCase`) es un caso de uso propio, `RestaurarSesionUseCase`, y no lógica del `SessionManager`: revalidar es una regla de negocio, y el `SessionManager` sigue siendo un guardador simple.
- **Club activo en memoria como `ClubDTO`** (la barra superior necesita el nombre); en el archivo, solo el `id`.
- **El guard `requiere_club_activo` se posterga a la US-107**, cuando exista la primera pantalla que lo necesite (hoy no hay ninguna ruta que lo use).
- **Una función compartida arma la barra superior** (título, club activo, "Clubes", "Cerrar sesión") para todas las pantallas internas.
- **Al restaurar se compara el id _y_ el email** del usuario guardado: si la base se recreó, ese id puede ser de otra persona, y sin el email se entraría con su cuenta.
- **`construir_dependencias` restaura la sesión antes de devolver** ("la app tal como arranca"): `ejecutar()` no cambia y el router manda directo a `/inicio`. `RestaurarSesionUseCase` no entra en `Dependencias` (lo usa el arranque, no una pantalla).
- **El registro no tiene "Recordarme":** se registra una vez; si quiere que lo recuerde, lo marca en el próximo login.
- **Nombre de club repetido → `ClubYaExisteError`** (`ErrorDeDominio`, mensaje claro en la pantalla) que lanza `CrearClubUseCase` antes de guardar, sin distinguir mayúsculas. `club.nombre` sigue siendo `UNIQUE` en toda la base; si debería ser único por usuario se discute en la US-108 (rivales).
- **"Usar este club" navega al inicio:** elegir club es "me pongo a trabajar", y al navegar la barra se redibuja con el club nuevo.
- **El adaptador JSON es "mejor esfuerzo":** `cargar` nunca lanza (archivo inexistente, dañado o con tipos incorrectos → `None` + warning, sin loguear el contenido); `guardar` y `borrar` atrapan `OSError` y lo loguean, porque no poder recordar la sesión no debe impedir iniciarla ni cerrarla. Sin escritura atómica: un archivo a medias es un JSON roto y solo obliga a loguearse de nuevo.

**Gap real encontrado y su corrección (bug de una pieza ya cerrada de la US-103):** `CrearClubUseCase` crea el club pero **nunca inserta en `usuarioClub`** — la tabla N:M que vincula usuario y club con `rolEntrenador`. Sin ese vínculo, `ListarClubesUsuarioUseCase` (que hace `JOIN usuarioClub`) y `CambiarClubActivoUseCase` no encuentran ningún club para ningún usuario real. Se corrige acá, **documentado explícitamente como fix**: `CrearClubUseCase` pasa a recibir el `idUsuario` de la sesión y lo vincula como entrenador al crear el club.

**Capa de Aplicación:**

- **Servicio:** `SessionManager` (US-105) se extiende con `set_active_club(club: ClubDTO)` (falla si no hay sesión), `club_activo() -> ClubDTO | None` y la persistencia opcional: recibe un `SesionAlmacen` por constructor; `iniciar_sesion(usuario, recordar=False)` guarda la sesión (con "Recordarme") o borra la guardada antes (sin él); `set_active_club` vuelve a guardar si la sesión se recuerda; `cerrar_sesion` borra. Iniciar sesión deja el club activo en `None`. **Hecho (pasos 2 a 4).**
- **Puerto y adaptador:** `SesionAlmacen` (`guardar`, `cargar`, `borrar`) y `JsonSesionAlmacen(ruta)`. **Hecho (paso 2).**
- **DTO:** `SessionDTO` (`usuario_id`, `email`, `club_activo_id`). **Hecho (paso 2).**
- **Caso de uso nuevo:** `RestaurarSesionUseCase` (rehidratar al abrir la app: vuelve a buscar el usuario, exige que coincida el email y revalida el club con `CambiarClubActivoUseCase`; si algo no cierra, borra el archivo o deja la sesión sin club). **Hecho (paso 5).**
- **Caso de uso extendido:** `CrearClubUseCase` (US-103) recibe `idUsuario` y vincula en `usuarioClub` en la misma transacción (`ClubRepositorio.guardar_con_entrenador`) — no se crea un caso de uso nuevo para esto. Además lanza `ClubYaExisteError` si el nombre ya existe. **Hecho (pasos 1 y 9).** **Ojo con la US-108:** los clubes rivales no son del usuario, así que el alta de un rival no puede pasar por este mismo camino sin más: la US-108 hace opcional el `idUsuario` (club sin vínculo).

**Capa de Infraestructura (UI):**

- `LoginScreen` suma la casilla "Recordarme" (`ft.Checkbox`). **Hecho (paso 7).**
- `ClubesScreen` (ruta `/clubes`): alta de club, listado de "mis clubes" (`ListarClubesUsuarioUseCase` con el usuario de la sesión, un `ft.ListTile` por club, el activo marcado "✓ En uso") y botón "Usar este club" (`CambiarClubActivoUseCase` + `SessionManager.set_active_club`, y va al inicio). Al crear un club la lista se rehace en el lugar, sin navegar. **Hecho (paso 9).**
- El club activo se muestra siempre en la barra superior: `crear_barra_superior` (`ui/flet/barra_superior.py`) arma la `AppBar` de todas las pantallas internas ("StatsPro · club", Inicio, Clubes, Cerrar sesión). Sin club, el inicio invita a elegir uno. **Hecho (paso 8).**
- Guard de navegación `requiere_club_activo`: las pantallas operativas (US-107, US-112 y US-108) sin club activo llevan a `ClubesScreen` con un aviso. **Se posterga a la US-107** (ver las decisiones).

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

- _Unitarias:_ `SessionManager` (con almacén mock: cuándo guarda y cuándo borra); `JsonSesionAlmacen` con archivo temporal (`tmp_path`) — guardar, cargar, borrar, archivo dañado, disco que falla; `RestaurarSesionUseCase`; `CrearClubUseCase` vincula al usuario y rechaza nombres repetidos (repositorio mock); pantallas de login, inicio y clubes, y la barra superior, sin ventana.
- _Integración:_ registro → login con "Recordarme" → crear club → elegirlo → un `SessionManager` nuevo leyendo el mismo archivo (simula reabrir la app) recupera usuario y club activo, y el club aparece en `ListarClubesUsuarioUseCase`. DB `:memory:` y archivo temporal. **Hecho** en `tests/integration/test_sesion_club_activo_flujo.py`: "reabrir" es volver a llamar a `construir_dependencias` con la misma base y el mismo archivo; cubre también sin "Recordarme", cerrar sesión, archivo dañado, usuario borrado y club desvinculado.
- _Manual guiado:_ el mismo flujo cerrando y abriendo la app de verdad.

#### US-111 — Base Visual de la GUI (tema, página y formularios)

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-105, US-106 · **Agregada:** 2026-11-08 · **Estado:** ✅ Hecha (PR #50)

**Objetivo Funcional:** definir **una sola vez** cómo se ven las pantallas (colores, tipografía, espaciados, ancho del contenido, cómo se arma un formulario) en un tema y unos pocos componentes compartidos, y aplicarlo a las pantallas que ya existen, para que todas las que vienen (US-107, US-108, US-205, US-301...) nazcan acomodadas y parejas.

**Narrativa:** Como entrenador, quiero que todas las pantallas se vean ordenadas y se usen igual (dónde están los campos, dónde los botones, dónde aparecen los errores), para no tener que aprender cada una de nuevo.

**Por qué ahora (decisión 2026-11-08):** hasta la US-106 las pantallas se armaron para que funcionen, apilando controles sin un criterio común. El único repaso visual previsto era el de la US-401 (Hito 4); para entonces habría unas 15 pantallas para rehacer, y las versiones de los Hitos 1 a 3 saldrían con pantallas sin acomodar. Es el mismo patrón que ya usan `crear_barra_superior` y `crear_etiqueta_error`, llevado a todo lo visual.

**Fuera de alcance (US-401):** elegir el modo oscuro a mano y revisarlo pantalla por pantalla, adaptación a celular (responsive), pantallas finales. Esta US sí define `page.dark_theme` con la misma semilla: sin eso, con Windows en oscuro Flet usaba su paleta por defecto y el tema propio no se veía. El logo en pantalla **sí** entra acá (AC6); el ícono del ejecutable y de la ventana (`.ico`, `.png`) queda en la US-404. Esta US deja todo en el tema para que esos cambios sean de un solo lugar.

**Decisión tomada (2026-11-09): combinación elegida en el muestrario** — propuesta «Pizarra», modificada:

| Perilla         | Elección                                                                                                               |
| --------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Color           | Semilla `#4A5866`, variante **tonal** (la de Flet por defecto; el principal sale más azul que la semilla)              |
| Formato         | **Menú lateral** (`ft.NavigationRail`) con el logo arriba; la barra superior conserva el club activo y "Cerrar sesión" |
| Densidad        | Cómoda: espacios 8 / 16 / 24, título 24, campo de 56 px                                                                |
| Tablas          | Filas alternadas (lo aplica `tabla_datos.py`, US-107)                                                                  |
| Campos          | Con relleno                                                                                                            |
| Botón principal | Ancho completo                                                                                                         |
| Esquinas        | Suaves: 8 px en botones, campos y tarjetas                                                                             |
| Letra           | IBM Plex Sans, empaquetada en `src/assets/fuentes/` (licencia OFL)                                                     |

Se revisó en modo oscuro. Login y registro usan el formato del muestrario para el menú lateral: panel de marca a la izquierda (logo blanco, nombre y lema sobre el color principal) y el formulario centrado a la derecha. Imágenes y letra viven en `src/assets/` (`assets_dir` absoluta, desde `config/rutas.py`); `public/logo_statpro.jpg` queda solo como referencia.

**Opciones que se compararon:**

- **Muestrario en lugar de bocetos (2026-11-08):** las combinaciones se comparan en un muestrario interactivo: 9 propuestas aplicadas a 23 pantallas del PRD (las de hoy, gestión, carga e importación de partidos con su vista previa, estadísticas, gráficos, scouting, perfil y los informes PDF). Se elige ahí y la elección queda escrita en esta US y en la guía 13:
  - **Color:** semilla de Material 3 (`ft.Theme(color_scheme_seed=...)`) y su **variante**: «tonal» (lo que hace Flet por defecto, baja la saturación) o «fiel a la semilla» (mantiene el color tal cual; en Flet probablemente con `ft.ColorScheme(primary=...)`, a confirmar). Con el naranja del logo, «tonal» da botones color ladrillo.
  - **Formato** (tarjetas, columna limpia o menú lateral con `ft.NavigationRail`), **densidad**, **estilo de tablas** (lo usa `tabla_datos.py`, US-107), **campos**, **botón principal**, **esquinas** y **letra**.
- **Dónde viven las imágenes:** Flet sirve imágenes desde la carpeta que se pasa como `assets_dir`, y `flet build` (US-109 para escritorio, US-404 para Android) la busca en `src/assets/`. Recomendado: mover ahí `public/logo/` y dejar en `public/` solo el original de referencia.

**Capa de Infraestructura (UI):**

- **Tema:** `ui/flet/estilo.py` — colores, tamaños de letra, espaciados (por ejemplo `ESPACIO_CHICO`, `ESPACIO`, `ESPACIO_GRANDE`), ancho máximo del contenido y ancho de los formularios, y el `ft.Theme` que `ejecutar()` asigna a `page.theme`. Tamaño inicial y mínimo de la ventana.
- **Componentes** (`ui/flet/components/`):
  - `pagina.py` — `crear_pagina(...)`: el contenido de cada pantalla. Título, subtítulo, márgenes, ancho máximo y un panel lateral opcional. Lo envuelven `crear_vista_interna(...)` (barra superior, menú lateral y _scroll_) y `crear_vista_acceso(...)` (login y registro: marca y formulario centrado).
  - `menu_lateral.py` — `crear_menu_lateral(...)`: `ft.NavigationRail` con el logo y un destino por sección (`DESTINOS`); reemplaza a los botones "Inicio" y "Clubes" de la barra superior. Cada US que suma una sección agrega su fila.
  - `formulario.py` — `crear_formulario(...)`: campos en columna con el ancho del tema, la etiqueta de error de `errores.py` debajo, el botón principal destacado (`ft.FilledButton`) y los secundarios como texto, siempre en el mismo lugar.
- **Repaso:** `login_screen.py`, `registro_screen.py`, `inicio_screen.py` y `clubes_screen.py` pasan a usar el tema y los componentes, sin cambiar su comportamiento.
- **Logo (decidido el 2026-11-08):** el isotipo de `public/logo/` (pelota, flecha que sube y barras), redibujado en vector a partir del logo generado con IA (`public/logo_statpro.jpg`, que queda solo como referencia: es un JPG sin transparencia y su texto dice «Basketball Stats Pro»). El nombre visible sigue siendo **StatsPro**. Hay tres versiones: a color (`statspro-isotipo.svg`), en blanco para fondos de color (`statspro-isotipo-blanco.svg`) e ícono de app sobre fondo azul noche (`src/assets/icon.svg`: desde la US-109 vive ahí, con el nombre que busca `flet build`). Las tres salen del mismo dibujo; si se toca, se regeneran juntas.

**Criterios de Aceptación:**

- **AC1 — Tema en un solo lugar:** colores, tamaños de letra y espaciados salen de `estilo.py`; ninguna pantalla escribe un color ni un número de espaciado propio.
- **AC2 — Página común:** todas las pantallas usan `crear_pagina`; en una ventana de 1366×768 y en una maximizada, el contenido no se corta ni se estira de borde a borde.
- **AC3 — Formularios iguales:** login, registro y alta de club usan `crear_formulario`: mismo ancho, error debajo de los campos, botón principal en el mismo lugar, y **Enter** envía el formulario.
- **AC4 — Sin cambios de comportamiento:** los tests de las pantallas existentes siguen pasando sin tocar lo que verifican (buscan controles por su texto, no por su posición).
- **AC5 — Guía visual:** las reglas (qué componente usar, dónde va cada cosa) y la combinación elegida en el muestrario quedan en la guía `docs/info_modulo/13-gui-flet-y-eventos.md`, junto con los conceptos de Flet nuevos (`ft.Theme`, `ft.Container`, `ft.Image`, alineación y _scroll_).
- **AC6 — Logo:** el login muestra el isotipo junto al nombre «StatsPro», y todas las pantallas internas lo muestran arriba del menú lateral (con el formato elegido, el menú es lo primero que se ve; antes de elegirlo, este AC decía «la barra superior»). Se ve nítido en 1366×768 y maximizado, y la app arranca aunque falte el archivo (Flet muestra el hueco, no lanza error).

**Testing Mínimo:**

- _Unitarias:_ `crear_pagina` incluye el título y respeta el ancho máximo; `crear_formulario` ubica la etiqueta de error y el botón principal; Enter en el último campo dispara la acción; el menú marca la pantalla actual y navega; el tema usa la misma semilla y letra en claro y en oscuro.
- _Las existentes:_ toda la suite de pantallas sigue en verde (AC4). Los ayudantes de `tests/unit/ayudantes_flet.py` recorren el árbol de controles completo, así los tests no dependen de cómo está anidada la pantalla; lo único que cambió en ellos es cómo encuentran la lista de clubes (por su `key`) y que la navegación se prueba en el menú, no en la barra.
- _Manual guiado:_ recorrer login → registro → inicio → clubes en 1366×768 y maximizada, en claro y en oscuro, y comparar con el muestrario.

#### US-107 — Competencias, Inscripciones y Listas de Buena Fe en Pantalla

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-106, US-111 · **Estado:** 🔧 En review (PR #52)

> **Dividida el 2026-11-08.** La US-107 original creció con las categorías por competencia y se partió en dos: esta, con todo lo del torneo (competencias, categorías, inscripciones y listas de buena fe), y la **US-112**, con jugadores y partidos. Esta va primero porque crea `tabla_datos.py` y el guard `requiere_club_activo`, que la US-112 reusa.

**Objetivo Funcional:** gestionar desde la GUI las competencias, sus categorías, las inscripciones del club activo y sus listas de buena fe, sobre los casos de uso de la US-103.

**Narrativa:** Como entrenador, quiero cargar las competencias con sus categorías, inscribir a mi club y armar las listas de buena fe desde pantallas con formularios y tablas, sin tener que conocer IDs.

**Nota de reuso:** las pantallas envuelven casos de uso que **ya existen** desde la US-103. La única lógica de negocio nueva es la de categorías por competencia.

**Ampliada (2026-11-08): categorías por competencia.** Hasta ahora la categoría era un catálogo suelto y la relación con la competencia solo existía a través de las inscripciones: al inscribir, el desplegable mostraba todas las categorías y nada impedía inscribir a un club en una categoría que esa competencia no juega. Se agrega la tabla `competenciaCategoria` (la competencia habilita las categorías que juega) y esta US suma esa lógica de negocio, además de las pantallas. Es una regla nueva de la sección 6.

**Capa de Aplicación:**

- **Categorías por competencia (2026-11-08):**
  - **Repositorio:** `CompetenciaRepositorio` (que ya maneja categorías e inscripciones) suma `habilitar_categoria(idCompetencia, idCategoria)`, `obtener_categorias_de_competencia(idCompetencia)`, `quitar_categoria(idCompetencia, idCategoria)` y `guardar_competencia_con_categorias(competencia, idCategorias)`, que guarda la competencia y sus categorías en **una transacción** (mismo patrón que `guardar_con_entrenador` de la US-106). ✅ (2026-11-14) Se suma un quinto método, `tiene_inscripciones(idCompetencia, idCategoria)`, para que `QuitarCategoriaDeCompetenciaUseCase` lance `CategoriaConInscripcionesError` consultando antes de borrar (misma convención que `InscripcionDuplicadaError`: el repositorio devuelve `bool` o `None` y el caso de uso lanza la excepción), en vez de adivinar el motivo del `False` de `quitar_categoria`.
  - **Casos de uso nuevos:** `HabilitarCategoriaEnCompetenciaUseCase`, `ListarCategoriasDeCompetenciaUseCase` y `QuitarCategoriaDeCompetenciaUseCase` (rechaza si la categoría ya tiene clubes inscriptos en esa competencia).
  - **Casos de uso extendidos:** `CrearCompetenciaUseCase` acepta las categorías al crear (`CrearCompetenciaDTO.idCategorias`, lista que puede venir vacía); `InscribirClubEnCompetenciaUseCase` rechaza una categoría no habilitada en la competencia.
  - **Excepciones nuevas** (`ErrorDeDominio`): `CategoriaNoHabilitadaError` (inscribir en una categoría que la competencia no juega), `CategoriaYaHabilitadaError` y `CategoriaConInscripcionesError` (quitar una categoría con clubes inscriptos).
  - **Base de datos:** tabla `competenciaCategoria (idCompetencia, idCategoria)`, con clave primaria compuesta y FK a las dos tablas. Además, `inscripcion` suma una **FK compuesta** `(idCompetencia, idCategoria) → competenciaCategoria`, para que la base tampoco acepte una inscripción en una categoría no habilitada aunque alguien se saltee el caso de uso. `seed.sql` habilita sus categorías antes de inscribir. Como en la US-108 con `partido.idCategoria`: se cambia `schema.sql` y cada integrante borra y recrea su base local (todavía no hay versión entregada; las migraciones son de la US-204).
- **Bajas seguras y vaciado (ampliación 2026-11-23):**
  - **Repositorio:** `CompetenciaRepositorio` suma `competencia_tiene_inscripciones(idCompetencia)`, `competencia_tiene_partidos(idCompetencia)`, `eliminar_competencia(idCompetencia)`, `categoria_en_uso(idCategoria)`, `eliminar_categoria(idCategoria)`, `inscripcion_tiene_partidos(idInscripcion)`, `eliminar_inscripcion(idInscripcion)` y `vaciar_lista_buena_fe(idListaBuenaFe)`.
  - **Casos de uso nuevos:** `EliminarCompetenciaUseCase` (rechaza si tiene inscripciones o partidos), `EliminarCategoriaUseCase` (rechaza si está habilitada en alguna competencia o tiene inscripciones), `EliminarInscripcionUseCase` (da de baja la inscripción y en cascada su lista 1:1, rechazando si el club ya tiene partidos cargados en esa competencia) y `VaciarListaBuenaFeUseCase` (quita todos los jugadores habilitados de una lista sin dar de baja la inscripción).
  - **Excepciones nuevas** (`ErrorDeDominio`): `CompetenciaEnUsoError`, `CategoriaEnUsoError` e `InscripcionEnUsoError`.

**Capa de Infraestructura (UI):**

- **Componentes compartidos:**
  - `components/tabla_datos.py` — tabla reutilizable (encabezados + filas a partir de DTOs) que usan todos los listados, también los de la US-112. Reemplaza a `formatters/table_formatter.py` de la CLI. Toma colores y espaciados de `estilo.py` (US-111), con **filas alternadas** (lo elegido en el muestrario): una fila sí y otra no con fondo `SURFACE_CONTAINER_LOW`.
  - `components/subnav_torneos.py` — barra de sub-navegación por ruta entre `/competencias`, `/inscripciones` y `/listas`, manteniendo las tres pantallas desacopladas (AC1).
  - `components/confirmacion.py` — diálogo modal de confirmación (`pedir_confirmacion`) para acciones destructivas (bajas y vaciado de listas).
- **Menú lateral:** cada sección nueva suma su fila a `DESTINOS` en `components/menu_lateral.py` (US-111): «Torneos» lleva a `/competencias` y se mantiene marcado en `/inscripciones` y `/listas`.
- **Guard `requiere_club_activo`** (postergado desde la US-106): las pantallas de esta US y de las US-112 y US-108 sin club activo llevan a `ClubesScreen` con un aviso.
- **Base visual:** todas las pantallas usan `crear_pagina` y sus formularios `crear_formulario` (US-111), siguiendo la guía visual de la guía 13.
- **Pantallas** (`screens/`):
  - `CompetenciasScreen` — alta, listado, filtros en memoria por **Año** y **Categoría**, y eliminación con confirmación de competencias y de categorías (`CrearCompetenciaUseCase`, `ListarCompetenciasUseCase`, `CrearCategoriaUseCase`, `ListarCategoriasUseCase`, `EliminarCompetenciaUseCase`, `EliminarCategoriaUseCase`). Al crear una competencia se eligen sus categorías del catálogo; en la pantalla se muestran sus categorías habilitadas y permite habilitar otra o quitar una (`HabilitarCategoriaEnCompetenciaUseCase`, `QuitarCategoriaDeCompetenciaUseCase`).
  - `InscripcionesScreen` — inscribir al club activo en una competencia y categoría (`InscribirClubEnCompetenciaUseCase`), listar sus inscripciones (`ListarInscripcionesClubUseCase`), filtrarlas en memoria por **Año** y **Categoría**, y dar de baja inscripciones con confirmación (`EliminarInscripcionUseCase`). El desplegable de categoría muestra solo las habilitadas en la competencia elegida (`ListarCategoriasDeCompetenciaUseCase`).
  - `ListaBuenaFeScreen` — habilitar y quitar jugadores de la lista de una inscripción, verla, vaciar la lista o dar de baja la inscripción con confirmación (`AgregarJugadorAListaBuenaFeUseCase`, `QuitarJugadorDeListaBuenaFeUseCase`, `ListarListaBuenaFeUseCase`, `VaciarListaBuenaFeUseCase`, `EliminarInscripcionUseCase`). Los jugadores se eligen entre los del club activo (`ListarJugadoresClubUseCase`).

**Criterios de Aceptación:**

- **AC1 — Pantallas desacopladas:** agregar una pantalla solo requiere crear su archivo en `screens/` y registrarla en la tabla de rutas de `app.py`, sin modificar otras pantallas (el equivalente del AC1 de la vieja US-107 para la CLI). Vale también para la US-112 y las siguientes.
- **AC2 — Sin IDs a mano:** competencia, categoría, inscripción y jugadores del club se eligen de listas desplegables cargadas desde los casos de uso de listado; el club es siempre el club activo (US-106).
- **AC3 — Errores de negocio:** toda excepción de dominio (jugador ya en lista, inscripción duplicada, categoría no habilitada, baja rechazada por datos asociados, etc.) se muestra junto al formulario o tabla con el manejador común de la US-105.
- **AC4 — Sesión:** todas las pantallas de esta US exigen sesión y club activo (guard de la US-105 y `requiere_club_activo`).
- **AC5 — Categorías por competencia:** una competencia se crea con sus categorías en una sola transacción; se puede habilitar otra o quitar una sin inscriptos; inscribir en una categoría no habilitada lanza `CategoriaNoHabilitadaError` desde el caso de uso, y la FK compuesta la rechaza también desde la base.
- **AC6 — Bajas seguras y filtros:** eliminar competencias, categorías o inscripciones y vaciar listas pide confirmación previa; los casos de uso rechazan la baja si existen inscripciones, partidos o usos vinculados; los listados de competencias e inscripciones se pueden filtrar en memoria por año y categoría.

**Testing Mínimo:**

- _Unitarias:_ las funciones puras que convierten DTOs en filas de `tabla_datos` y las funciones puras de filtrado por año y categoría; los casos de uso de categorías por competencia y de baja/vaciado; la validación nueva de `InscribirClubEnCompetenciaUseCase`; y cada pantalla sin ventana (incluyendo confirmaciones y filtros).
- _Integración:_ `guardar_competencia_con_categorias` guarda todo o nada; un `INSERT` directo en `inscripcion` con una categoría no habilitada falla por la FK compuesta; flujo completo con bajas y errores de uso sobre SQLite real. Los tests de integración de la US-103 que insertan inscripciones directo tienen que habilitar antes la categoría (la FK compuesta los rompería).
- _Manual guiado:_ recorrido club → competencia con sus categorías → filtros → inscripción → lista de buena fe → bajas/vaciado con confirmación, probando al menos un error de negocio en cada pantalla.

#### US-112 — Jugadores y Partidos en Pantalla

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-107

> **Nueva (2026-11-08), sale de dividir la US-107.** Usa `tabla_datos.py` y `requiere_club_activo`, que crea la US-107. Va antes que la US-108: el alta de jugadores de esta US es la que llena las listas de buena fe contra las que la US-108 valida.

**Objetivo Funcional:** dar de alta, buscar, vincular y desvincular jugadores del club activo, y consultar sus partidos con el boxscore, sobre los casos de uso de la US-103.

**Narrativa:** Como entrenador, quiero manejar el plantel de mi club y ver los partidos cargados con su boxscore, sin duplicar jugadores ni conocer IDs.

**Nota de reuso:** las pantallas envuelven casos de uso que **ya existen** desde la US-103. Las piezas nuevas de aplicación son chicas y de lectura: el boxscore de un partido (antes previsto como comando `partido boxscore`) y la búsqueda de jugadores por nombre. La US-205 le agrega métricas avanzadas a esa misma pantalla de detalle; no crea otra.

**Capa de Aplicación:**

- **Casos de uso nuevos:** `ObtenerBoxscorePartidoUseCase` (devuelve una lista de `BoxscoreFilaDTO`) y `BuscarJugadoresPorNombreUseCase` (usa `JugadorRepositorio.buscar_por_nombre`, nuevo: busca por apellido o nombre en todos los clubes, sin distinguir mayúsculas). Sin él no hay forma de elegir en pantalla a un jugador que todavía no está en el club activo, ni de avisar que un jugador ya existe antes de darlo de alta.
- **Repositorio extendido:** `JugadorRepositorio.buscar_por_nombre(texto)` y su versión SQLite.
- **Repositorio:** método nuevo `PartidoRepositorio.boxscore_por_partido(id_partido)`, que lee `v_boxscore_completo` (mismo patrón que `resumen_por_club` con `v_partidos_resumen`).
- **Edición y baja segura de jugadores (ampliación 2026-11-23):**
  - **Repositorio:** `JugadorRepositorio` suma `actualizar(jugador)`, `jugador_en_uso(id_jugador)` y `eliminar(id_jugador)`.
  - **Casos de uso nuevos:** `EditarJugadorUseCase` (`EditarJugadorDTO`: corrige nombre, apellido y año de nacimiento validando reglas de dominio) y `EliminarJugadorUseCase` (elimina el jugador si no tiene partidos cargados ni figura en listas de buena fe; en caso contrario lanza `JugadorEnUsoError`).
  - **Excepción nueva** (`ErrorDeDominio`): `JugadorEnUsoError`.

**Capa de Infraestructura (UI):**

- Usa `tabla_datos.py`, `requiere_club_activo` (US-107), `crear_pagina`, `crear_vista_interna` y `crear_formulario` (US-111), y suma «Jugadores» y «Partidos» a `DESTINOS` del menú lateral.
- **Pantallas** (`screens/`):
  - `JugadoresScreen` — alta (`RegistrarJugadorUseCase`; antes de guardar muestra los jugadores con el mismo nombre, para vincular uno existente en vez de duplicarlo), listado del club activo (`ListarJugadoresClubUseCase`), buscar por nombre un jugador que todavía no está en el club (`BuscarJugadoresPorNombreUseCase`) para vincularlo al club activo (`VincularJugadorAClubUseCase`), editar sus datos (`EditarJugadorUseCase`), dar de baja del club (`DesvincularJugadorDeClubUseCase` con confirmación) y eliminar de forma segura (`EliminarJugadorUseCase` con confirmación).
  - `PartidosScreen` — listado de partidos del club activo (`ListarPartidosPorClubUseCase`, con nombres desde `v_partidos_resumen`) y detalle con el boxscore (`ObtenerBoxscorePartidoUseCase`). Dos desplegables filtran el listado (2026-11-08): **Competencia** (solo aquellas en las que el club activo está inscripto, de `ListarInscripcionesClubUseCase`) y **Categoría** (solo las inscriptas en la competencia elegida); los dos arrancan en «Todas». El filtro se aplica sobre la lista ya cargada: los partidos de un club son pocos y no hace falta otra consulta. Desde la US-108, si el partido tiene puntos por cuarto, el detalle los muestra en una línea arriba del boxscore; si no, no muestra nada.

**Criterios de Aceptación:**

- **AC1 — Sin IDs a mano:** un jugador que todavía no está en el club se busca por nombre; el club es siempre el club activo (US-106).
- **AC2 — Sin duplicados:** el alta avisa si ya hay jugadores con ese nombre y ofrece vincular uno de ellos en vez de crear otro.
- **AC3 — Visualización con vistas SQL:** el listado de partidos usa `v_partidos_resumen` (nombres, no IDs); el detalle usa `v_boxscore_completo`.
- **AC4 — Errores y sesión:** las excepciones de dominio (vínculo superpuesto, etc.) se muestran junto al formulario con el manejador común de la US-105; las dos pantallas exigen sesión y club activo.

**Testing Mínimo:**

- _Unitarias:_ `ObtenerBoxscorePartidoUseCase` y `BuscarJugadoresPorNombreUseCase` con repositorio mock.
- _Integración:_ `ObtenerBoxscorePartidoUseCase` contra `v_boxscore_completo` con `seed.sql`; `buscar_por_nombre` sin distinguir mayúsculas ni tildes de más.
- _Manual guiado:_ alta de un jugador con un nombre que ya existe (vincular en vez de duplicar) → baja → partidos filtrados por competencia y categoría → boxscore.

#### US-108 — Carga Atómica de Partido (CargarPartido)

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-106, US-107, US-112
- **Antes era la US-106.** Pasó de S a M porque el formulario de varios pasos ahora es una pantalla de la GUI, no un flujo de consola.
- **Objetivo Funcional:** registrar un partido de una competencia y categoría, con las estadísticas individuales de los dos equipos, garantizando la integridad de los datos mediante una transacción atómica (todo o nada).
- **Narrativa:** Como DT, quiero registrar un partido completo —de mi club o de otros clubes de la competencia— con todas las estadísticas de los jugadores en una única operación; si falla una sola estadística, nada se persiste.

> **Decisiones tomadas el 2026-10-31** (cierran las dos decisiones pendientes que tenía esta historia):
>
> 1. **Cualquier partido de la competencia.** Se puede cargar un partido aunque el club activo no juegue; el club activo (US-106) solo viene **preseleccionado** como local y el usuario puede cambiar los dos equipos. Motivo: si solo se cargan los partidos propios, el club activo tiene N partidos y cada rival 0 o 1, y el promedio de un rival con un solo partido no dice nada.
> 2. **El partido guarda la categoría.** Un partido es de una categoría que juega una competencia. Las categorías se repiten (U13 juega el Asociativo 2026, el Asociativo 2027 y el Provincial 2026) y cada combinación tiene su inscripción y su lista de buena fe por club; sin la categoría no se sabe contra qué lista validar.
> 3. **Clubes rivales o de terceros.** `ClubRepositorio.listar_todos` para elegir cualquier club, y `CrearClubUseCase` con `idUsuario` opcional: sin usuario, el club se crea **sin** vínculo en `usuarioClub`.
>
> **Revisada el 2026-11-27 por la US-113:** la decisión 1 y el AC5 ya no valen para la pantalla (carga
> los partidos del club activo), y la validación contra la lista de buena fe es solo para el club
> propio. El formulario de varios pasos se reemplazó por una sola pantalla. El resto sigue igual.

- **Puntos por cuarto (2026-11-08):** opcionales (regla de la sección 6). Van en una tabla aparte y
  no en columnas de `partido`: así entran las prórrogas sin columnas vacías y "no se cargaron" es
  simplemente que no hay filas.
- **Capa de Dominio:** `Partido` suma `idCategoria: int` (obligatorio). `JugadorPartido` no cambia. Excepción nueva `CuartosInconsistentesError` (`ErrorDeDominio`): cuartos de un solo equipo, distinta cantidad de períodos, o una suma que no da los puntos del boxscore.
- **Capa de Aplicación:**
  - **Caso de uso:** `CargarPartidoUseCase` — orquesta: para **cada uno de los dos equipos** busca la inscripción del club en la competencia y categoría del partido, valida que su boxscore solo tenga jugadores de esa lista (`CompetenciaRepositorio.obtener_jugadores_lista`, ya existe de US-103) y llama a `PartidoRepositorio.save_with_boxscore` con los dos boxscores juntos.
  - **Caso de uso nuevo:** `ListarClubesUseCase` (todos los clubes, para elegir local y visitante).
  - **Caso de uso extendido:** `CrearClubUseCase` con `idUsuario` opcional (decisión 3).
  - **DTOs:** `PartidoDTO` (de carga, con la categoría y `cuartos: list[CuartoDTO]`, vacía si no se cargaron — el de solo lectura que ya existe se llama `PartidoResumenDTO`), `BoxscoreDTO`, `EstadisticaInputDTO`, `CuartoDTO (idClub, nroCuarto, puntos)`.
  - **Validación de cuartos:** `CargarPartidoUseCase` la hace antes de guardar, junto con la de las listas (AC2).
- **Capa de Infraestructura:**
  - **Base de datos:** columna `partido.idCategoria` (FK a `categoria`); `v_partidos_resumen` suma el nombre de la categoría; `SqlitePartidoRepositorio` la guarda y la lee; `SqliteClubRepositorio.listar_todos`. Tabla `partidoCuarto (idPartido, idClub, nroCuarto, puntos)` con clave primaria `(idPartido, idClub, nroCuarto)`, FK a `partido` con `ON DELETE CASCADE`, `nroCuarto ≥ 1` y `puntos ≥ 0`. `save_with_boxscore` recibe los cuartos (opcional) y los guarda **en la misma transacción** que el partido y los boxscores.
  - **`CargaPartidoScreen`** — formulario de varios pasos: (1) competencia, categoría, fecha, local y visitante, con el club activo preseleccionado como local; (2) el boxscore de cada equipo, una fila por jugador de su lista de buena fe; (3) resumen y confirmación, con un bloque opcional **Puntos por cuarto** (4 casilleros por equipo y un botón para agregar prórroga; es `components/puntos_por_cuarto.py`, que reusa la vista previa de la US-201). Si un equipo no tiene inscripción o lista en esa competencia y categoría, la pantalla lo avisa y lleva a `ListaBuenaFeScreen` (US-107) para cargarla — desde la US-206 también se puede importar del listado de la CAB. Los errores de validación se marcan en el campo o la fila que los causó.
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
  - **AC7 — Puntos por cuarto opcionales:** un partido sin cuartos se guarda igual, sin aviso. Con cuartos, se guardan solo si están los dos equipos con la misma cantidad de períodos y cada suma da los puntos de su boxscore; si no, `CuartosInconsistentesError` dice qué equipo y cuánto falta o sobra, y no se guarda nada.
- **Reglas de Negocio (las cuatro primeras ya están en `JugadorPartido.__post_init__` y la quinta en `save_with_boxscore`; se listan para trazabilidad):**
  - `(T1C×1) + (T2C×2) + (T3C×3)` = puntos totales.
  - `convertidos ≤ lanzados` para T1, T2, T3.
  - Todos los campos numéricos `≥ 0`.
  - `minutosJugados` entre 0 y 48.
  - No se puede cargar un partido si los clubes involucrados no existen en la DB (ya lo valida `save_with_boxscore`).
  - **En el boxscore de cada equipo solo figuran jugadores de la lista de buena fe de ese club para la competencia y categoría del partido** (regla de la sección 6). Las listas se cargan desde `ListaBuenaFeScreen` (US-107) o se importan (US-206, US-201); si un jugador no está, se lanza una excepción de dominio.
  - **Nota (campo propuesto, no implementado todavía):** si se agrega a `Partido` un resultado final (`puntosLocalFinal`/`puntosVisitanteFinal`, ver sección 20 y el DER en `docs/diagramas/diagramas.md`), esta US sería el lugar natural para completarlo, con una regla que valide que la suma de puntos del boxscore por club coincide con ese resultado. La importación (US-201) ya no lo necesita: valida contra la fila `TOTALES` del archivo.
    **Resuelto distinto en la US-113:** el resultado no es una columna de `partido`; sale de
    `v_totales_equipo_partido` (suma del boxscore o totales cargados), así no hay dos fuentes que
    puedan contradecirse.
- **Testing Mínimo:**
  - _Unitarias:_ `CargarPartidoUseCase` rechaza un jugador que no está en la lista de su club (en cualquiera de los dos equipos) y uno que está en la lista de otra categoría (mock de `CompetenciaRepositorio`); camino feliz llama a `save_with_boxscore` con los DTOs traducidos. `CrearClubUseCase` sin usuario no vincula. Cuartos (AC7): sin cuartos, con 4 cuartos válidos, con prórroga, de un solo equipo y con una suma que no coincide.
  - _Integración:_ flujo completo (partido + dos boxscores, con y sin cuartos) en DB `:memory:` con repositorios reales, incluido un partido entre dos clubes sin vínculo con el usuario — puede reusar el fixture de `tests/integration/test_repositorios_partido.py`.
  - _Manual guiado:_ cargar un partido completo desde la pantalla, uno de otros dos clubes, y uno con un jugador fuera de la lista para ver el error y que nada se guardó.

#### US-113 — Carga de Partido Centrada en el Club Propio y Pantallas Más Cómodas

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-108, US-111, US-112
- **Nueva (2026-11-27).** Sale de probar la app con los datos reales de una temporada (la planilla de
  Excel del club): no se podía escribir el rival, había que crearlo en "Mis clubes" como si fuera
  propio, se le exigía inscripción y lista, y el formulario desperdiciaba el espacio.
- **Objetivo Funcional:** cargar un partido como lo anota un entrenador: el boxscore completo de su
  equipo y, del rival, lo que tenga (sus totales, solo el resultado o su boxscore). De paso, que las
  pantallas usen todo el ancho y que las tareas repetidas (armar una lista) se hagan de una vez.
- **Narrativa:** Como DT, quiero cargar el partido de mi equipo en una sola pantalla parecida a mi
  planilla, escribir el rival aunque no exista y no tener que armarle una lista de buena fe.

> **Decisiones tomadas el 2026-11-27:**
>
> 1. **Rival: totales o boxscore (D1 = C).** Del rival se cargan sus totales en una fila (como la fila
>    "Equipo Rival" de la planilla) o, si se tiene, su boxscore por jugador. Con boxscore, sus
>    jugadores van a la base: en la misma transacción se crean su inscripción, su lista y los
>    jugadores nuevos (se reconocen por nombre y apellido sin tildes ni mayúsculas, entre su plantel
>    vigente).
> 2. **El rival es un club sin usuario (D2 = A).** Se elige de la lista o se escribe; si no existe se
>    crea con `CrearClubUseCase` sin usuario y no aparece en "Mis clubes". "Mis clubes" muestra solo
>    los clubes propios.
> 3. **Rival + Local/Visitante (D3).** En vez de elegir local y visitante, se elige el rival y si se
>    jugó de local o de visitante.
> 4. **Ancho completo y una sola pantalla (D4 = A-A).** `crear_pagina` deja de limitar el ancho; la
>    carga es una sola pantalla con una planilla tipo Excel.
> 5. **Dónde quedan los totales del rival (2 = A).** Tabla nueva `estadisticaEquipoPartido` y vista
>    `v_totales_equipo_partido`, que une la suma del boxscore con los totales cargados a mano.
> 6. **Encabezados T2C/T2L** como en la planilla (no se traducen a "Dobles").
> 7. **Alta masiva en la lista de buena fe, no "todo o nada":** se agregan los válidos y se informa
>    qué jugadores no entraron y por qué.

- **Capa de Dominio:**
  - `EstadisticaEquipo` (totales de un equipo, con las reglas de la sección 6), `AltaPlantelRival` y
    `JugadorRivalNuevo` (qué hay que crear del rival), `TotalesEquipoFila` y `LiderClub` (lectura).
    `PartidoResumen` suma `puntosLocal`/`puntosVisitante`.
  - `PartidoRepositorio.save_with_boxscore(partido, boxscore, cuartos, totales, alta_rival)`;
    métodos nuevos `totales_por_partido` y `lideres_por_club`.
- **Capa de Aplicación:**
  - `CargarPartidoUseCase(repo_partido, repo_competencia, repo_jugador).ejecutar(partido, boxscore_propio, rival)`,
    donde `rival` es un `BoxscoreDTO` o un `TotalesEquipoDTO`. Valida todo antes de guardar: fecha
    ISO, clubes distintos, el club propio inscripto y con todos sus jugadores en la lista, el rival
    con jugadores de su club (por id) o nuevos (con nombre y apellido), sin repetidos, y los cuartos
    contra los puntos de cada equipo. `EstadisticaInputDTO.idJugador` pasa a ser opcional y suma
    `nombre`/`apellido` para los jugadores nuevos del rival.
  - Casos de uso nuevos: `ObtenerTotalesPartidoUseCase`, `ListarLideresClubUseCase` (5 por defecto) y
    `AgregarJugadoresAListaBuenaFeUseCase` (reusa el alta individual para cada jugador).
- **Capa de Infraestructura:**
  - **Base de datos:** tabla `estadisticaEquipoPartido` (PK `(idPartido, idClub)`, `ON DELETE CASCADE`
    desde `partido`, CHECK de no negativos y convertidos ≤ lanzados); vistas `v_totales_equipo_partido`
    (origen `boxscore` o `totales`), `v_lideres_club`, y `v_partidos_resumen` con los puntos de cada
    equipo. Es una tabla nueva: `CREATE TABLE IF NOT EXISTS` la agrega sola a una base existente.
  - **Componentes:** `planilla_boxscore.py` (`PlanillaBoxscore`: una fila por jugador con PTS y la fila
    Equipo calculados solos, filas a mano para el rival; `FilaTotalesEquipo`: los puntos se calculan
    si hay tiros y se escriben si no). `crear_pagina` sin ancho máximo.
  - **Pantallas:**
    - `CargaPartidoScreen` — tarjeta de datos (competencia y categoría en un solo desplegable,
      preelegido si hay una sola inscripción; fecha con calendario; estadio; rival escribible;
      Local/Visitante), planilla propia, bloque del rival («Solo totales o resultado» o «Boxscore por
      jugador»), puntos por cuarto opcionales, marcador en vivo y Guardar. El club rival nuevo se crea
      recién después de validar la planilla.
    - `PartidosScreen` — columna Resultado y, en el detalle, la tabla «Totales por equipo».
    - `InicioScreen` — accesos rápidos, último partido y líderes del club.
    - `JugadoresScreen` — tabla a todo el ancho, alta en un diálogo, acciones con íconos y la fecha
      de baja dentro del diálogo de baja.
    - `ListaBuenaFeScreen` — casillas con el plantel que no está en la lista, «Seleccionar todos» y
      «Agregar seleccionados (n)».
    - `CompetenciasScreen` — las categorías de cada competencia se eligen desde su fila (diálogo con
      casillas); el catálogo pasa a `CategoriasScreen` (ruta `/categorias`, pestaña nueva de Torneos).
- **Criterios de Aceptación:**
  - **AC1 — Rival escribible:** se puede escribir un rival que no existe; se crea sin usuario y no
    aparece en "Mis clubes". Si se escribe igual que uno existente (sin importar tildes ni
    mayúsculas), se usa ese.
  - **AC2 — Rival sin lista:** con totales, el rival no necesita inscripción ni lista; con boxscore,
    se le crean en la misma transacción. Si algo falla, no queda nada de ese alta (atomicidad).
  - **AC3 — Solo el resultado:** del rival alcanza con los puntos.
  - **AC4 — Totales coherentes:** con tiros cargados, los puntos tienen que cerrar.
  - **AC5 — Un solo lugar para el resultado:** listado, detalle e inicio leen el resultado de
    `v_totales_equipo_partido`.
  - **AC6 — Alta masiva:** varios jugadores a la lista en un paso, con el motivo de cada rechazo.
  - **AC7 — Sin pérdida de datos:** si el guardado falla, la planilla conserva lo cargado.
- **Testing Mínimo:**
  - _Unitarias:_ `CargarPartidoUseCase` con totales, solo resultado, totales incoherentes, de
    visitante, rival inscripto, rival reconocido por nombre, rival nuevo, jugador de otro club,
    repetidos y cuartos; `AgregarJugadoresAListaBuenaFeUseCase`; planilla y fila de totales; cada
    pantalla con mocks.
  - _Integración:_ rival nuevo con boxscore (y segundo partido sin duplicar jugadores), totales en la
    vista, rollback del alta del rival, líderes.
  - _Manual guiado:_ el flujo de un entrenador de punta a punta (registro → club → jugadores →
    competencia → inscripción → lista masiva → partido con totales → partido con boxscore del rival).
- **Pendiente de decisión (para cerrar el hito):** _resuelto en la US-114 (los tres puntos)._
  - **Partidos entre dos clubes ajenos** (antes AC5 de la US-108): hoy no se pueden cargar desde la
    pantalla. Opciones: (a) dejarlo fuera de la v1.0.0; (b) un modo «Partido de otros» en la misma
    pantalla con los dos equipos en totales; (c) esperar a la importación (US-201).
  - **Empates:** en básquet no hay empates, pero hoy se puede guardar un partido empatado.
  - **Crear el rival y guardar el partido no son atómicos:** si el guardado falla después de crear el
    club rival, el club queda (vacío y sin usuario).

#### US-114 — Editar Partidos, Convocados y Guía de Uso

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-113
- **Nueva (2026-11-27).** Sale de simular el flujo completo de un entrenador sobre la US-113: no se
  podía corregir un partido ya cargado, la planilla mostraba toda la lista de buena fe, se guardaban
  empates, un error de la planilla aparecía dos veces, el rival mal escrito quedaba para siempre y no
  había ayuda dentro de la app.
- **Objetivo Funcional:** que el entrenador pueda corregir lo que cargó, cargue solo a los que fueron
  al partido y tenga a mano una guía simple de cómo se usa la aplicación.
- **Narrativa:** Como DT, quiero marcar los convocados, corregir o borrar un partido mal cargado y
  arreglar el nombre de un rival, y tener una guía a mano cuando no sé cómo seguir.

> **Decisiones tomadas el 2026-11-27:**
>
> 1. **Editar (D1 = a):** todo el partido se puede editar, reusando la pantalla de carga llena con lo
>    guardado (ruta `/partidos/editar/{id}`). Se suma «Eliminar partido» con confirmación.
> 2. **Cantidad de jugadores (D2 = a y b):** máximo 12, fijo y obligatorio; el mínimo (5, como en el
>    reglamento FIBA) solo avisa.
> 3. **Convocados (D3 = a):** casillas con la lista de buena fe; la planilla muestra solo los
>    marcados. Si la lista tiene 12 o menos vienen todos marcados; si tiene más, ninguno.
> 4. **Guía (D4 = a):** pantalla `/guia` que muestra `src/assets/guia.md` con `ft.Markdown`; botón
>    «Guía» abajo del menú lateral y link «¿Cómo se usa?» en el login (se abre sin sesión).
> 5. **Partidos de otros clubes:** quedan fuera: la US-201 importa planillas de cualquier club y la
>    US-207 hace la carga masiva.
> 6. **Recomendaciones de la simulación:** rechazar empates; mostrar el error de la planilla una sola
>    vez (abajo solo se dice dónde mirar); crear el rival nuevo en la misma transacción del partido;
>    avisar si el partido ya existe; «Agregar todo el plantel a la lista» al inscribirse (marcado por
>    defecto); sección «Clubes rivales» en «Mis clubes» para renombrar o borrar rivales sin partidos.

- **Capa de Dominio:**
  - Constantes `MAX_JUGADORES_PARTIDO = 12`, `MIN_JUGADORES_PARTIDO = 5` e `ID_CLUB_NUEVO = 0` (id
    provisorio del rival que todavía no existe). Excepción nueva `ClubEnUsoError`.
  - `PartidoRepositorio.save_with_boxscore(..., club_rival_nuevo)`: con `partido.idPartido` hace UPDATE
    y reemplaza sus filas; métodos nuevos `eliminar` y `cuartos_por_partido`.
  - `ClubRepositorio`: `listar_sin_usuario`, `actualizar`, `eliminar`, `tiene_partidos`, `tiene_usuarios`.
- **Capa de Aplicación:**
  - `CargarPartidoUseCase.ejecutar(partido, boxscore_propio, rival, nombre_rival_nuevo=None)`: valida
    el máximo de 12 por equipo y que no haya empate; con `nombre_rival_nuevo` el rival viene con
    `ID_CLUB_NUEVO` y el repositorio lo crea en la misma transacción; con `PartidoDTO.idPartido`, edita.
  - Casos de uso nuevos: `ObtenerPartidoUseCase`, `EliminarPartidoUseCase`, `ListarClubesRivalesUseCase`,
    `RenombrarClubUseCase` (`RenombrarClubDTO`) y `EliminarClubUseCase`.
- **Capa de Infraestructura:**
  - **Base de datos:** sin cambios de esquema. Editar hace UPDATE de `partido` y vuelve a insertar sus
    filas; eliminar borra a mano `jugadorPartido` (es `ON DELETE RESTRICT`), `partidoCuarto` y
    `estadisticaEquipoPartido`, y después el partido.
  - **Rutas:** `/partidos/editar/{id}` (ruta con id: `separar_ruta`, con club activo) y `/guia` (con o
    sin sesión).
  - **Componentes:** `PlanillaBoxscore.cargar_jugadores` conserva lo cargado de cada jugador;
    `poner_valores` en la planilla y en `FilaTotalesEquipo`; `BloquePuntosPorCuarto.cargar_cuartos`;
    `crear_boton_guia` abajo del menú lateral.
  - **Pantallas:**
    - `CargaPartidoScreen` — convocados con contador «Convocados: n/12», avisos con «¿Guardar igual?»
      (menos de 5 jugadores, partido repetido) y modo edición (título «Editar partido», botón
      «Guardar cambios»; avisa si un jugador del partido ya no está en la lista).
    - `PartidosScreen` — «Editar partido» y «Eliminar partido» en el detalle.
    - `InscripcionesScreen` — casilla «Agregar todo el plantel a la lista».
    - `ClubesScreen` — sección «Clubes rivales» (renombrar en un diálogo, eliminar con confirmación).
    - `GuiaScreen` — el manual de uso; `LoginScreen` suma el link «¿Cómo se usa?».
- **Criterios de Aceptación:**
  - **AC1 — Editar:** desde el detalle se abre el partido con todo lo cargado; guardar lo reemplaza sin
    crear otro.
  - **AC2 — Eliminar:** pide confirmación y borra el partido con su boxscore, cuartos y totales.
  - **AC3 — Convocados:** no se pueden marcar más de 12; la planilla muestra solo los marcados.
  - **AC4 — Avisos:** con menos de 5 jugadores o un partido repetido, se pregunta antes de guardar.
  - **AC5 — Sin empates:** un empate no se guarda y se explica por qué.
  - **AC6 — Rival atómico:** si el partido no se guarda, el rival nuevo no queda en la base.
  - **AC7 — Rivales:** se renombran; se eliminan solo si no tienen partidos.
  - **AC8 — Guía:** se abre desde el menú (con sesión) y desde el login (sin sesión).
  - **AC9 — Pantallas como la maqueta (agregado el 2026-11-27, al compararlas con el muestrario):**
    - _Mis clubes:_ cada club con un círculo con sus iniciales y «n categorías · n jugadores».
    - _Jugadores:_ buscador y «Del club» / «En todos los clubes» (este último solo de consulta, con el
      club actual de cada jugador; nuevo `ListarJugadoresTodosUseCase` y
      `JugadorRepositorio.listar_con_club_actual`). Se quita «Vincular jugador existente»: un jugador se
      crea siempre con club y no se trae de otro club; solo un homónimo **sin club** se ofrece sumar.
    - _Partidos:_ columnas Cat. y G/P; el filtro de categoría ofrece todo el catálogo; «Ver» abre el
      partido en su pantalla (`/partidos/ver/{id}`) con marcador destacado, cuartos en tabla, totales y
      un boxscore por equipo, todas las tablas al mismo ancho.
    - _Inscripciones:_ «Jugadores en la lista» en vez de «Lista #n».
    - _Carga de partido:_ asistente de tres pasos (Datos → Boxscore → Confirmar); los avisos se ven en
      el resumen y reemplazan al diálogo «¿Guardar igual?».
    - _Tablas:_ encabezado con fondo de color en toda la app.
- **Testing Mínimo:**
  - _Unitarias:_ empate, más de 12, rival nuevo (id provisorio y nombre juntos), edición con
    `idPartido`, obtener/eliminar partido, renombrar/eliminar/listar rivales; convocados, avisos, error
    único y edición en la pantalla de carga; editar/eliminar en partidos; plantel al inscribirse;
    clubes rivales; rutas con id y guía; botón Guía; iniciales y resumen de clubes; buscador y «En
    todos los clubes»; G/P y detalle del partido; jugadores por lista; pasos del asistente de carga.
  - _Integración:_ rival nuevo con el partido y su rollback, edición que reemplaza filas y conserva el
    id, edición de un partido inexistente, eliminación, métodos nuevos del repositorio de clubes,
    `listar_con_club_actual` (club vigente o ninguno, sin repetir jugadores).
  - _Manual guiado:_ simulación del flujo del entrenador (guía sin sesión → club → 14 jugadores →
    inscripción con plantel → partido con convocados → duplicado y empate → editar → eliminar →
    renombrar rival → guía con sesión).

#### US-110 — Monitoreo y Trazabilidad Operativa

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Dependencias:** US-107, US-108 · **Estado:** ✅ Hecha (2026-11-27)
- **Antes era la US-108.** El "comando" como unidad de trazabilidad pasa a ser la **acción del usuario** en la GUI (un botón que invoca un caso de uso).
- **Objetivo Funcional:** proveer observabilidad transversal estructurada para depuración y soporte, con correlación de eventos extremo-a-extremo por acción del usuario.
> **Decisiones tomadas (2026-11-27, ver ADR-011):**
>
> - **Nombre explícito de cada acción:** `ejecutar_mostrando_errores(accion, etiqueta, nombre="clubes.crear")`, con el formato
>   `pantalla.que_hace`. Es obligatorio (keyword-only): una pantalla nueva no puede olvidarse de nombrar su acción.
> - **JSON con la biblioteca estándar:** `FormateadorJson` propio (`json.dumps`), sin `structlog` ni `python-json-logger`.
> - **Sink por variables de entorno:** `STATSPRO_LOG_SINK=archivo|consola` (default `archivo`, `~/.statspro/logs/app.log`) y
>   `STATSPRO_LOG_NIVEL` (default `INFO`). Un valor desconocido usa el default: un error de tipeo no impide abrir la app. Sin Seq,
>   SigNoz ni otro servicio: se evaluó un `docker compose` para desarrollo y se descartó (con `consola` + `jq` alcanza).
> - **Eventos de entidades en los casos de uso**, con `logging.getLogger(__name__)` de la biblioteca estándar: la aplicación no
>   importa infraestructura. El `correlation_id` lo agrega el handler, no el que loguea.
> - **Arranque y navegación también son acciones:** el esquema y la sesión recordada salen con `accion="arranque"`; cada cambio de
>   pantalla, con `accion="navegar"`. Si una acción abre otra (Guardar navega), sigue el `correlation_id` de la de afuera.
> - **Los filtros van en el handler**, no en el logger raíz: los filtros de un logger no ven lo que propagan sus hijos.
> - **Emails tapados** además de los secretos: son dato personal (y los mensajes de dominio a veces los incluyen). El login fallido
>   se loguea sin el email.
> - Fuera de alcance por ahora: importación Excel y backup/restore (no existen todavía; se suman en la US-216 y las US-402 y US-410).

- **Eventos de log obligatorios:** inicio/fin de cada acción del usuario (pantalla, acción, resultado y duración); `LoginLocalUseCase`/cierre de sesión, `SessionManager.set_active_club` (US-104/106), fallos de autenticación; inicio/fin de transacciones críticas (`CargarPartidoUseCase` de US-108; importación Excel y backup/restore cuando existan, US-201 y US-402); creación/actualización de entidades principales; excepciones de dominio y errores de infraestructura, clasificados por severidad.
- **Criterios de Aceptación:**
  - **AC1.** Niveles DEBUG/INFO/WARNING/ERROR en formato JSON estructurado.
  - **AC2.** `correlation_id` UUIDv4 generado al inicio de cada acción del usuario y propagado hasta repositorios.
  - **AC3.** Secretos (passwords, tokens, hashes sensibles) redactados en todos los niveles de log.
  - **AC4.** Selección de sink (local-file) por configuración, sin cambiar código de negocio.
- **Testing Mínimo:**
  - _Unitario:_ creación y propagación de `execution_context`; redacción de secretos en campos conocidos.
  - _Integración:_ una acción completa (por ejemplo, crear un club con sesión iniciada) → verificar que todos sus eventos tienen el mismo `correlation_id` y que otra acción tiene uno distinto.
  - _Implementado:_ `tests/unit/test_observabilidad.py` (contexto, anidado, JSON, redacción, sink y nivel, inicio/fin de acción),
    eventos de login/logout/club activo en `test_uc_auth.py` y `test_session_manager.py`, y
    `tests/integration/test_observabilidad_flujo.py` (crear un club con SQLite real: pantalla, repositorio y caso de uso con el mismo
    `correlation_id`; otra acción, otro). La fixture `registros_log` de `tests/conftest.py` captura los registros con los filtros reales.

### Épica H1-E3: Entorno de Calidad y Pipeline CI/CD

#### US-109 — Entorno de Desarrollo y Pipeline CI/CD

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-105 (los binarios empaquetan la GUI) · **Estado:** ✅ Hecha (PR #51), probada con el pre-release `v0.1.0-rc.2`
- **Objetivo Funcional:** garantizar que todo nuevo commit sea verificado automáticamente con linting, tests y cobertura, haciendo del pipeline la única fuente de verdad sobre el estado de calidad del proyecto; y que **publicar una versión** (desde la v0.1) sea un proceso automático y repetible: tag → tests → binarios → GitHub Release con changelog.

> **Ampliada (2026-11-08):** se le suma todo el **release** de escritorio (Windows y Linux), que antes era de la US-404, para que la
> v1.0.0 ya salga con binarios descargables; más el chequeo del título de los PR, actionlint y SAST (Bandit vía ruff y CodeQL).
> Lo que quedaba de la US-404 se dividió el 2026-11-27: Android (US-404), macOS (US-417), la versión visible en la app (US-409) y la guía de instalación (US-418). Decisiones tomadas:
>
> _Nota (2026-11-27): `develop` y las ramas de épica e hito ya no existen, y se publica al cerrar cada épica; el flujo vigente está en la sección 15. Lo que sigue es la decisión tal como se tomó._
>
> - **Tag a mano en `main` + git-cliff**, no Release Please: se publica una vez por hito, y Release Please suma dos PR por release
>   (su "Release PR" y el de `main` de vuelta a `develop`). Si los releases se vuelven frecuentes, se migra.
> - **El tag va en `main`**, después de mergear `develop`: marca exactamente el código publicado (un tag en `develop` apunta a otro commit).
> - **Estrategia de merge mixta** (ver la sección 15): _squash_ en los PR de trabajo y _merge commit_ en los de promoción. Con
>   _squash_ en todos los niveles, a `main` llegaría un solo commit por hito y el changelog tendría una línea.
> - **Matriz de runners** (`windows-latest` para el `.exe` y el `.zip`, `ubuntu-latest` para el `.deb`): `flet build` no compila
>   para otro sistema operativo (no hay compilación cruzada, tampoco con Wine).
> - **El `.zip` es la app portable, no el código:** el código ya lo agrega GitHub ("Source code (zip/tar.gz)") a cada release.
>
> **Decisiones tomadas al arrancar (2026-11-09):**
>
> - **Empaquetado con `flet build windows|linux`** (basado en Flutter), no `flet pack` (PyInstaller): es la misma herramienta que
>   arma el APK de la US-404 y toma sola la carpeta `src/assets/` (letra y logo de la US-111). `flet build windows` no genera un solo
>   `.exe` sino una carpeta (el `.exe` más sus bibliotecas). PyInstaller "a secas" ni siquiera sirve: no incluye el cliente de
>   escritorio de Flet y el binario no abre ninguna ventana.
> - **Tres artefactos por release:** `.exe` = **instalador** de Windows armado con Inno Setup a partir de esa carpeta (acceso directo
>   en el menú Inicio, desinstalador); `.zip` = la misma carpeta comprimida, **portable** (se descomprime y se abre, sin instalar);
>   `.deb` = paquete de Linux (`dpkg-deb`). El `.apk` de Android se suma al release en la US-404.
> - **Base y logs en `~/.statspro/`** (la carpeta del usuario, donde ya vive `session.json`), siempre, también en desarrollo. Hoy
>   `config/rutas.py` los pone junto al código, y una app instalada en `Program Files` o `/opt` no puede escribir ahí. La
>   `estadisticas.db` actual se mueve a mano una sola vez (el RUNBOOK dice cómo).
> - **Sin gitleaks, a propósito:** se sacó del CI y no vuelve. El AC3 ya no pide detectar secretos en el historial.
>
> **Spike de `flet build` (2026-11-09, workflow temporal `spike-build.yml`, ya borrado: lo reemplazó `release.yml`):** compila en
> `windows-latest` y `ubuntu-latest` sin instalar nada a mano (Flet baja Flutter solo con `--yes`; Linux necesita `clang cmake
ninja-build pkg-config libgtk-3-dev liblzma-dev libstdc++-12-dev`). El `.exe` probado en Windows abre, crea `~/.statspro/` con la base y
> funciona. Hallazgos para `release.yml`: (1) `PYTHONUTF8=1` en el paso del build, si no flet-cli se cae en Windows al reenviar el `√`
> de Flutter (`UnicodeEncodeError` con cp1252) y no copia el resultado; (2) el paquete lleva **su propio Python 3.14**, no el del runner
> (ya probado por la matriz de `tests-linux`); (3) va todo compilado a `.pyc`, con `src/assets/` y los `.sql` adentro; (4) se excluye
> `statspro_basketball.egg-info` (`[tool.flet.app] exclude`); (5) nada de `| head` en los pasos de bash (con `pipefail`, el
> "Broken pipe" hace fallar el paso).

- **Criterios de Aceptación:**
  - **AC1.** `make run_test` ejecuta la suite completa y falla si la cobertura baja del piso de `[tool.coverage.report]` de `pyproject.toml` (`fail_under = 60`). El job de Linux del CI exige además **85 %** (parámetro `cobertura-minima`; cumple el ≥ 80 % pedido) y guarda el reporte HTML como _artifact_.
  - **AC2.** `make run_linter_ruf` falla ante cualquier infracción de estilo o de formato.
  - **AC3.** El pipeline CI falla el PR ante test fallido, cobertura insuficiente (Linux), error de linting o de tipos o dependencias con vulnerabilidades conocidas. (Hasta el 2026-11-09 también pedía detectar secretos en el historial con gitleaks; se sacó a propósito.)
  - **AC4.** `pre-commit install` configura hooks locales en un único comando (los hooks de ruff se ejecutan con `uv run`: usan la versión fijada en `pyproject.toml`, la misma del CI).
  - **AC6 — Job agregador y required status checks (nuevo, antes solo vivía en `ideas-aprendizaje.md` §8.9) ✅ (ruleset configurado el 2026-11-09, junto con `titulo-pr`):** un job final `ci-ok` que depende de todos los demás y falla si alguno falló; registrado como _required status check_ de la rama, para que un PR con el CI en rojo no se pueda mergear.
  - **AC7 — `ruff format --check` (nuevo, antes §8.2):** el job `lint` también falla si algún archivo no está formateado con `ruff format`, no solo si viola reglas de estilo.
  - **AC8 — Smoke test de la app (nuevo, antes §8.14):** un paso que falla si el punto de entrada no se puede importar. Con la CLI era `uv run python src/main.py --help`; desde la US-105 es un paso que importa el composition root de la GUI (`app.py`) sin abrir ninguna ventana.
  - **AC9 — Release por tag (antes AC3 de la US-404):** `release.yml` se dispara con `push: tags: ["v*.*.*"]` y, en orden:
    1. corre la suite de tests (si falla, no se publica nada);
    2. falla si la versión de `pyproject.toml` no coincide con el tag (`v0.1.0` ↔ `version = "0.1.0"`);
    3. compila con `flet build` en una matriz de runners: `windows-latest` arma el instalador `.exe` (Inno Setup) y el `.zip` portable, `ubuntu-latest` el `.deb` (`dpkg-deb`; la versión del paquete va sin la `v`). Ningún artefacto lleva `data/` ni una base: la app arranca con la base vacía;
    4. crea el GitHub Release con los binarios y, como notas, la sección de esa versión del `CHANGELOG.md`.
       Un tag con sufijo (`v0.1.0-rc.1`) crea un _pre-release_: sirve para probar el workflow sin publicar una versión de verdad. Permisos: `contents: write` solo en el job que publica.
       ✅ Implementado (2026-11-09): los tests corren en Linux y en Windows con **Python 3.14**, el que `flet build` mete en el paquete. En un pre-release se compara la versión sin el sufijo (`v0.1.0-rc.1` ↔ `0.1.0`). Las notas salen de la sección `## [X.Y.Z]` del `CHANGELOG.md` (un pre-release usa la de su versión final si ya está; si no, un texto de prueba); una versión final sin su sección falla sin publicar. Nombres: `StatsPro-X.Y.Z-windows-x64-instalador.exe`, `StatsPro-X.Y.Z-windows-x64-portable.zip` y `statspro_X.Y.Z_amd64.deb` (en Debian el `-rc.1` pasa a `~rc.1`, para que la versión final quede por encima). Desinstalar no borra `~/.statspro/`.
  - **AC10 — Changelog (antes AC5 de la US-404):** `CHANGELOG.md` en formato _Keep a Changelog_, generado con git-cliff (`make changelog VERSION=X.Y.Z`, que corre `uvx git-cliff@2.14.2 --tag vX.Y.Z -o CHANGELOG.md`) a partir de los Conventional Commits, con la configuración en `cliff.toml`. Se genera en el PR de release (`chore(release): vX.Y.Z`, sección 15), junto con el cambio de versión. ✅ (2026-11-09) Secciones en castellano: `feat` → Agregado; `refactor`, `perf` y `revert` → Cambiado; `fix` → Corregido; `fix(seguridad)` → Seguridad. Quedan afuera `docs`, `test`, `ci`, `build` (incluye Dependabot), `chore`, `style` y los commits que no siguen Conventional Commits. Los _pre-release_ (`-rc.N`) no abren sección propia: sus commits quedan en la versión final. El archivo se regenera entero: no se edita a mano.
  - **AC11 — Título del PR:** un job falla si el título del PR no sigue Conventional Commits (`amannn/action-semantic-pull-request`). Con _squash_, el título del PR es el mensaje del commit que llega a la rama, y de ahí sale el changelog. El repo se configura para que el _squash_ use siempre el título del PR. Va en un workflow aparte (`titulo-pr.yml`) porque necesita el evento `edited`: corregir el título vuelve a correr el chequeo sin relanzar los tests; por eso es un _required status check_ propio, además de `ci-ok`. También valida el mensaje del commit en los PR de un solo commit (`validateSingleCommit`), porque ahí GitHub propone ese mensaje en vez del título.
  - **AC12 — Workflows revisados:** actionlint en pre-commit, en `make run_linter_ruf` y en el job `lint` (detecta, por ejemplo, una expresión mal escrita como `${{ github.evnt_name }}`, y con shellcheck, que viene en `ubuntu-latest`, errores en los scripts de los `run:`). Su versión sale de `uv.lock` (paquete `actionlint-py` del grupo `dev`), igual que ruff. Los inputs de un `with:` los valida solo para las acciones que conoce: con versiones más nuevas que su catálogo (por ejemplo `actions/checkout@v7`) no los revisa.
  - **AC13 — SAST ✅ (2026-11-09):** reglas `S` (Bandit) de ruff activadas en `pyproject.toml`, con excepciones justificadas para `tests/` (`assert`, contraseñas de prueba); y CodeQL con la _default setup_ (Settings → Code security; gratis porque el repo es público).
  - **AC14 — Binario probado:** antes de publicar la v1.0.0, el instalador `.exe`, el `.zip` portable y el `.deb` de un _pre-release_ se abren en una máquina sin Python (o una VM limpia, como Windows Sandbox): la app arranca, se registra un usuario y se crea un club.
  - **AC15 — Datos fuera de la carpeta de instalación (nuevo, 2026-11-09):** la base (`estadisticas.db`) y los logs viven en `~/.statspro/` (junto a `session.json`), con la app instalada y también en desarrollo; la carpeta se crea si no existe. La app instalada nunca escribe en su propia carpeta. ✅ (2026-11-09: `config/rutas.py` con `DATOS_DIR`; `ejecutar()` crea la carpeta antes de abrir la base; `tests/unit/test_rutas.py`.)
  - **Ampliación (2026-11-22, rama `feature/mejora-ci`): resumen de la PR y labels.** Decisiones: **un solo comentario**
    editable (tabla de semáforo arriba y un desplegable por tema), no uno por herramienta; la cobertura y los tests que se
    reportan son los de **Linux 3.13** (no se combinan las cinco corridas); los benchmarks son **informativos** (no están en `ci-ok`).
  - **AC16 — Resumen de la PR:** el job `resumen-pr` publica y edita un comentario con: el resultado de cada job; cobertura total
    con el delta contra la última corrida de la rama base; cobertura de las líneas cambiadas (diff-cover); tests fallidos y los 5
    más lentos (`--junitxml`); errores de ruff y mypy; una línea con el resumen de los benchmarks; la HU vinculada; y un
    aviso si cambia `src/` sin cambiar `docs/`. No comenta en las PRs de Dependabot ni de forks (token de solo
    lectura): ahí el resumen queda en la página de la corrida. No está en `ci-ok`.
  - **AC17 — Anotaciones y dependency review:** ruff (`--output-format=github`) y mypy (problem matcher) marcan cada error sobre
    la línea del diff; `dependency-review-action` falla si la PR agrega una dependencia con vulnerabilidad moderada o peor
    (está en `ci-ok`).
  - **AC18 — Labels automáticos** (`pr-meta.yml`): por capa según las carpetas (`.github/labeler.yml`), y la épica (`H1-E2`), la
    US (`US-107`) y el milestone de la HU, encontrada por `Closes #N` o por el número de la rama.
  - **AC19 — Benchmarks de consultas:** `pytest-benchmark` en `tests/benchmarks/`, fuera de la suite normal (`-m "not
    benchmark"` en `pyproject.toml`); el job `benchmark` los corre en cada PR y en cada push a una rama base. Miden 19
    consultas (las lecturas de los cinco repositorios, las vistas de `views.sql` y las dos escrituras transaccionales) sobre
    datos de volumen en dos escalas (`temporada`: 240 partidos; `x10`: 2.400) y guardan el `EXPLAIN QUERY PLAN` de cada una.
    El reporte va en un **segundo comentario** editable (`<!-- resumen-benchmark -->`): tabla por repositorio con la mediana
    en cada escala, el crecimiento entre escalas, el cambio de la mediana contra la base (⚠️ si sube más de 20 %) y los
    `SCAN` de tabla completa (🆕 si son nuevos respecto de la base); más los planes y las estadísticas completas en
    desplegables. Informativo: no está en `ci-ok`. Guía e informe de los primeros resultados:
    `docs/info_modulo/14-benchmarks.md`.
- **Testing Mínimo:** manual — push a rama feature dispara el workflow; error de lint intencional hace fallar CI; cobertura por debajo del umbral hace fallar CI con mensaje explicativo; un PR con un job en rojo no puede mergearse (AC6); un PR con título `arreglos varios` falla (AC11); un tag `v0.1.0-rc.1` genera un _pre-release_ con el `.exe`, el `.zip` y el `.deb` y sus notas (AC9); un tag que no coincide con `pyproject.toml` falla sin publicar nada (AC9); el binario abre en una máquina limpia (AC14); tests de `config/rutas.py`: la base y los logs apuntan a `~/.statspro/` (AC15).

---

## 10. Hito 2 — Motor de Ingesta y Análisis (v2.0.0)

**Objetivo del hito:** automatizar la carga desde Gesdeportiva, producir métricas avanzadas
confiables, exponerlas en pantallas de la GUI y asegurar la evolución del esquema de la base
**sin perder nunca los datos de un usuario** (sección 3, "Evolución del esquema desde v1.0.0").

**Versiones:** H2-E1 → **v1.1.0** · H2-E2 → **v1.2.0** · H2-E3 → **v2.0.0** (cierra el hito).

**Épicas:** 3 · **Historias:** 30 · **Esfuerzo total estimado:** ~50 días·persona

> **Rearmado (2026-11-27).** Las 7 historias que tenía el hito (US-201 a US-207) se dividieron en
> historias chicas, cada una con un objetivo, sus dependencias y lo que deja hecho para las demás
> (campo **Entrega**). Las pistas A/B desaparecen: cada historia la toma una sola persona, como un
> ticket (sección 5). El número viejo queda con la pieza central de la historia original; las
> piezas que se separaron tienen números nuevos (US-208 en adelante). La columna "Sale de" del mapa
> dice de qué historia vieja viene cada una. Además:
>
> - La **US-204** (migraciones) es la primera del hito y se convierte en regla: desde la v1.0.0 la
>   base solo cambia con migraciones aditivas (sección 3).
> - El **`IngestService`** de la vieja US-201 se fusiona con su caso de uso: resolver clubes,
>   jugadores e inscripciones es lógica de aplicación, no de infraestructura.
> - Los casos de uso de comparativas se mueven de la H2-E2 a la H2-E3: necesitan leer datos, y en el
>   plan viejo la lectura (`AnalyticsService`, US-203) dependía de ellos, al revés de lo necesario.
>   La H2-E2 queda con las fórmulas y la lectura de datos, y cierra con métricas visibles en el
>   detalle de partido.
> - Aparece una pantalla para la comparativa de jugadores (US-230): el caso de uso existía en el
>   plan, pero ninguna pantalla lo mostraba.

**Decisiones previas:** ADR-003 (protocolo de ingesta) sigue abierto solo en la librería de PDF y
bloquea únicamente las US-210 y US-214; lo cierra quien tome la US-210. ADR-004 (versionado de la
base) quedó decidido en este PRD: **yoyo-migrations** (sección 8); la US-204 lo pasa al ADR.

### Mapa de dependencias del Hito 2

Se puede tomar cualquier historia cuyas dependencias estén todas mergeadas en `main`. Las que no
dependen de nada se pueden tomar desde el primer día.

| US     | Qué deja hecho                                             | Depende de              | Tamaño | Sale de |
| ------ | ---------------------------------------------------------- | ----------------------- | ------ | ------- |
| US-204 | Migraciones con yoyo; la base de v1.0.0 como punto de partida | v1.0.0 publicada        | M      | US-204  |
| US-208 | Copia de la base antes de migrar; bloqueo de bases más nuevas | US-204                  | S      | US-204  |
| US-209 | El CI rechaza migraciones destructivas o editadas           | US-204                  | S      | nueva   |
| US-206 | Lectura del listado de jugadores de la CAB en Excel         | —                       | S      | US-206  |
| US-210 | Lectura del listado en PDF                                  | US-206, ADR-003         | S      | US-206  |
| US-211 | `IdentificadorJugadores` (nombre → jugador del club)        | —                       | S      | US-206  |
| US-212 | Caso de uso para importar una lista de buena fe             | US-206, US-211          | M      | US-206  |
| US-213 | Importar lista desde archivo en `ListaBuenaFeScreen`        | US-212                  | S      | US-206  |
| US-201 | Lectura de la planilla de partido en Excel                  | US-206                  | M      | US-201  |
| US-214 | Lectura de la planilla de partido en PDF                    | US-201, US-210          | S      | US-201  |
| US-215 | Validación de la planilla contra la fila `TOTALES`          | US-201                  | XS     | US-201  |
| US-216 | Caso de uso para importar una planilla de partido           | US-201, US-211, US-215  | M      | US-201  |
| US-217 | `ImportScreen`: importar una planilla con vista previa      | US-216                  | M      | US-201  |
| US-207 | Carga masiva de planillas                                   | US-217                  | S      | US-207  |
| US-202 | `formulas.py`: tiro y eficiencia                            | —                       | S      | US-202  |
| US-218 | Promedio de puntos por cuarto                               | —                       | S      | US-202  |
| US-219 | Valores cada 40 minutos y aviso de muestra chica            | —                       | XS     | US-202  |
| US-203 | `AnalyticsService` (interfaz completa) y boxscore de un partido | —                    | S      | US-203  |
| US-220 | Totales de jugador por competencia, categoría y año         | US-203                  | M      | US-203  |
| US-221 | Partidos y totales de un club (a favor y en contra)         | US-203                  | M      | US-203  |
| US-222 | Puntos por cuarto de un club                                | US-203                  | S      | US-203  |
| US-223 | Evolución de un jugador partido a partido                   | US-203, US-202          | S      | US-203  |
| US-224 | Métricas avanzadas en el detalle de partido                 | US-202, US-203          | M      | US-203  |
| US-225 | Barra común de filtros de estadísticas                      | —                       | S      | US-205  |
| US-226 | Caso de uso de líderes de una competencia                   | US-220, US-202, US-219  | S      | US-205  |
| US-205 | `LideresScreen`                                             | US-225, US-226          | S      | US-205  |
| US-227 | Caso de uso de comparativa entre dos clubes                 | US-221, US-222, US-202, US-218, US-219 | M | US-202 |
| US-228 | `ComparativaScreen`                                         | US-227, US-225          | S      | US-205  |
| US-229 | Caso de uso de comparativa de jugadores                     | US-220, US-202, US-219  | S      | US-202  |
| US-230 | Pantalla de comparativa de jugadores                        | US-229, US-225          | S      | nueva   |

**Puntos donde dos historias en paralelo pueden chocar** (se resuelven con una línea cada una):
`pyproject.toml`/`uv.lock` (US-204, US-206, US-210 suman dependencias; si chocan, `uv lock`), el
composition root y el menú lateral (cada pantalla nueva suma su línea), y
`pandas_analytics_service.py`, donde las US-220 a US-223 completan métodos distintos de la misma
clase (la US-203 deja la interfaz entera definida para que ninguna cambie la de otra).

### Formatos reales de los archivos de la CAB (referencia para las US-206 a US-214)

**Listado "Jugadores"** (`data/jugadores_*.xlsx` y su PDF, revisados el 2026-10-31):

- Una sola hoja (`Jugadores-Equipo`). Título en celdas combinadas:
  `Jugadores - UNIVERSITARIO - INFANTILES MIXTO - CORDOBA - ASOCIACIÓN - 2026 - FEDERACION DE BASQUETBOL DE LA PROVINCIA DE CORDOBA - 2026`
  → club, categoría, ciudad, competencia, temporada, organizador, año.
- Columnas: `Apellidos y Nombre`, `Partidos jugados`, `Minutos partido`, `Puntos partido` (estas
  dos son promedios con coma decimal: `21,2`). Todas las celdas son texto.
- Nombres en formato `APELLIDOS, NOMBRES`, a veces con espacios al final. Incluye jugadores con 0
  partidos (están en la lista pero no jugaron).
- **No trae DNI ni año de nacimiento.** La categoría se nombra distinto que en la planilla de
  partido (`INFANTILES MIXTO` acá, `U13MX` allá).

**Planilla de estadísticas de partido** (`data/estadisticaPartido_*.xlsx` y su PDF):

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

| Columna del archivo  | Campo                                              |
| -------------------- | -------------------------------------------------- |
| `MIN`                | `minutosJugados` (`mm:ss` → minutos con decimales) |
| `PTS`                | `puntos`                                           |
| `TC 2P` `A/I`        | `T2C` / `T2L`                                      |
| `TC 3P` `A/I`        | `T3C` / `T3L`                                      |
| `TL` `A/I`           | `T1C` / `T1L`                                      |
| `DEF`, `OF`          | `rebotesDef`, `rebotesOf` (`Tot.` se ignora)       |
| `AST`, `REC`, `PER`  | `asistencias`, `recuperos`, `perdidas`             |
| `TAP` `TC` / `TR`    | `taponesRealizados` / `taponesRecibidos`           |
| `FAL` `FC` / `FR`    | `faltasCometidas` / `faltasRecibidas`              |
| `Num.`, `VAL`, `+/-` | no se guardan (ver la US-214)                      |

**Fixtures anonimizados (vale para todas las US de ingesta):** los archivos de `data/` tienen
nombres reales de jugadores menores de edad y no se suben al repositorio. Los fixtures de
`tests/integration/fixtures/` son copias con el mismo formato y nombres inventados; cada US crea
los que usa.

### Épica H2-E1: Integración "Gesdeportiva" y Gobernanza de Esquema (v1.1.0)

#### US-204 — Migraciones de Esquema con yoyo y Base v1.0.0

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Urgente (es la primera del hito) · **Depende de:**
  v1.0.0 publicada · **Toca la base:** sí, solo agrega las tablas de control de yoyo; no cambia
  ninguna tabla de datos
- **Objetivo:** que una versión nueva de la app pueda agregar tablas o columnas a la base de un
  usuario sin perder sus datos, aplicando las migraciones pendientes al abrir.
- **Entrega:** la carpeta `migrations/` con `0001_base_v1_0_0.sql`, la función que aplica las
  migraciones pendientes al arrancar y la guía para escribir una. La usan la US-208, la US-209,
  la US-410 y toda historia futura que agregue algo a la base.
- **Por qué yoyo-migrations (ADR-004):** las migraciones son archivos `.sql` planos como los que ya
  usa el proyecto. No necesita SQLAlchemy (Alembic sí, y el proyecto no tiene ORM). Registra lo
  aplicado en una tabla propia y corre cada migración en una transacción. Es el mismo modelo que las
  migraciones de Supabase: archivos numerados que se aplican una vez y en orden.
- **Alcance:**
  - `0001_base_v1_0_0.sql` es **copia exacta** del `schema.sql` del tag `v1.0.0`. `schema.sql` se
    borra: desde acá las tablas solo existen por migraciones. `views.sql`, `seed.sql` y
    `limpieza.sql` siguen como están.
  - `DatabaseManager.inicializar_schema` pasa a aplicar las migraciones pendientes y después
    recrear las vistas (`views.sql`). Los tests que creaban la base con `schema.sql` la crean igual
    que la app.
- **Criterios de Aceptación:**
  - **AC1 — ADR:** `docs/adr/ADR-004-versionado-db.md` queda aprobado con yoyo-migrations y la regla
    de migraciones aditivas de la sección 3.
  - **AC2 — Base nueva:** sobre una base vacía se aplican todas las migraciones y la app abre.
  - **AC3 — Base de un usuario de v1.0.0:** una base con las tablas de v1.0.0 y sin las tablas de
    yoyo se reconoce como v1.0.0. La `0001` se marca como aplicada **sin ejecutarse** y se aplican
    solo las siguientes. No se pierde ni cambia ninguna fila.
  - **AC4 — Al día:** si no hay pendientes, no se hace nada (abrir dos veces da el mismo resultado).
  - **AC5 — Falla:** una migración que falla no deja cambios (su transacción se deshace), la app no
    abre y muestra un mensaje claro. Se registra en el log. Hoy `inicializar_schema` registra el
    error y sigue de largo: eso se cambia, porque abrir con una base a medio migrar rompe después.
  - **AC6 — Binario:** el instalador de un _pre-release_ abre una base creada con la v1.0.0 y la
    migra (yoyo se instala con `flet build`; se prueba como el AC14 de la US-109).
- **Testing Mínimo:** _integración_ con una base v1.0.0 con datos (armada con la `0001` y
  `seed.sql`) más una migración de prueba (`tests/.../migraciones_prueba/0002_agrega_columna.sql`,
  una columna con `DEFAULT`): la cantidad de filas de cada tabla no cambia y la columna existe. Base
  vacía, base al día y una migración rota que se deshace entera.
- **Archivos:**

```text
src/infraestructura/persistencia/sql/migrations/0001_base_v1_0_0.sql
src/infraestructura/persistencia/migraciones.py          ← aplicar_migraciones(ruta_db) sobre yoyo
src/infraestructura/persistencia/database_manager.py     ← inicializar_schema usa migraciones.py
src/infraestructura/persistencia/sql/schema.sql          ← se borra
pyproject.toml / uv.lock                                 ← + yoyo-migrations (versión exacta)
docs/adr/ADR-004-versionado-db.md
docs/info_modulo/12-como-agregar-una-migracion.md
tests/integration/test_migraciones.py
```

#### US-208 — Copia de la Base Antes de Migrar y Bloqueo de Bases Más Nuevas

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-204 · **Toca la base:** no
  (copia el archivo)
- **Objetivo:** que si una migración sale mal haya una copia de la base de antes, y que una versión
  vieja de la app nunca toque una base que ya migró una versión más nueva.
- **Entrega:** `crear_copia(conexion, destino)` en `persistencia/backup_service.py` (con
  `VACUUM INTO`, ADR-008) y la carpeta `~/.statspro/backups/` en `config/rutas.py`. Las usan la
  US-402, la US-410 y la US-416.
- **Criterios de Aceptación:**
  - **AC1:** si hay migraciones pendientes, antes de aplicarlas se crea
    `~/.statspro/backups/antes-de-migrar-AAAAMMDD-HHMMSS.db`. Si la copia falla, no se migra y la
    app no abre (mensaje claro).
  - **AC2:** se conservan las últimas 5 copias de este tipo; las más viejas se borran.
  - **AC3:** si la base tiene migraciones aplicadas que esta versión no conoce, la app no abre:
    explica que hay que actualizarla y no toca la base.
- **Testing Mínimo:** _integración_: con una migración pendiente se crea la copia y abre igual que
  el original; sin pendientes no se copia nada; la sexta copia borra la más vieja; una base con
  una migración desconocida bloquea sin modificar el archivo (mismo hash antes y después).
- **Archivos:** `src/infraestructura/persistencia/backup_service.py`, `src/config/rutas.py`,
  `src/infraestructura/persistencia/migraciones.py`, `tests/integration/test_copia_antes_de_migrar.py`.

#### US-209 — Guardia de Migraciones en el CI

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-204 · **Toca la base:** no
- **Objetivo:** que el CI frene un PR que rompa la regla de la sección 3, en vez de depender de
  que alguien lo vea en la revisión.
- **Entrega:** un test y un paso del CI que tiene que pasar toda migración nueva.
- **Criterios de Aceptación:**
  - **AC1 — Solo sentencias aditivas:** un test recorre `migrations/` y falla si encuentra
    `DROP TABLE`, `DROP COLUMN`, `RENAME`, `DELETE` o `UPDATE`, y dice el archivo y la línea.
  - **AC2 — Migraciones inmutables:** el CI falla si un PR modifica, renombra o borra un archivo
    de `migrations/` que ya está en `main` (solo se pueden agregar archivos nuevos).
  - **AC3:** los dos chequeos están en la guía `12-como-agregar-una-migracion.md`.
- **Testing Mínimo:** el test con una migración de ejemplo prohibida (en `tests/`) falla, y con una
  permitida pasa; un PR de prueba que edita la `0001` queda en rojo.
- **Archivos:** `tests/unit/test_migraciones_permitidas.py`, `.github/workflows/MainAction.yml`
  (paso de `git diff --diff-filter=MDR` contra `main`), `docs/info_modulo/12-como-agregar-una-migracion.md`.

#### US-206 — Lectura del Listado de Jugadores de la CAB en Excel

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — (usa el mapeo por texto que
  propone el ADR-003) · **Toca la base:** no
- **Objetivo:** convertir el listado "Jugadores" que exporta Gesdeportiva en Excel en datos
  tipados, sin tocar la base.
- **Entrega:** `ListadoJugadoresDTO` (título desarmado y nombres), `FormatoArchivoInvalidoError`,
  el paquete `infraestructura/ingest/` y `leer_listado(ruta)`, que elige el lector según la
  extensión. La US-210 le suma el PDF sin cambiar a quien lo llama. Los usan la US-210, la US-212,
  la US-213 y la US-201.
- **Criterios de Aceptación:**
  - **AC1 — Formato:** un archivo sin el título o sin el encabezado `Apellidos y Nombre` lanza
    `FormatoArchivoInvalidoError` antes de procesar y dice qué faltó. Una extensión que ningún
    lector conoce lanza el mismo error ("formato no soportado").
  - **AC2 — Título:** se separa en club, categoría, ciudad, competencia, temporada, organizador y
    año.
  - **AC3 — Nombres:** salen sin espacios de más y en el orden del archivo, incluidos los que
    tienen 0 partidos. El encabezado se busca por texto, no por posición.
- **Fuera de alcance:** `Partidos jugados`, `Minutos partido` y `Puntos partido` son los datos
  oficiales de la temporada y no se guardan. Más adelante servirían para mostrar cuánto de la
  temporada de un jugador está cargado (ver "Muestra chica" en la sección 6).
- **Testing Mínimo:** _unitarias_ contra el fixture (tildes, espacios de más, jugador con 0
  partidos, título incompleto, encabezado faltante, extensión desconocida).
- **Archivos:**

```text
src/dominio/exceptions.py                         ← + FormatoArchivoInvalidoError
src/aplicacion/dtos/ingest_dto.py                 ← ListadoJugadoresDTO
src/infraestructura/ingest/__init__.py            ← leer_listado(ruta): lector por extensión
src/infraestructura/ingest/listado_jugadores_excel.py
pyproject.toml / uv.lock                          ← + openpyxl (versión exacta)
tests/unit/test_listado_jugadores_excel.py
tests/integration/fixtures/listado_jugadores_anonimo.xlsx
```

#### US-210 — Lectura del Listado de Jugadores en PDF

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-206, ADR-003 (la elección
  de la librería de PDF es el primer paso de esta US) · **Toca la base:** no
- **Objetivo:** aceptar también el PDF del listado, con el mismo resultado que el Excel.
- **Entrega:** la librería de PDF fijada en `pyproject.toml` (la reusa la US-214) y `.pdf`
  registrado en `leer_listado`. La pantalla de la US-213 lo acepta sin cambios.
- **Criterios de Aceptación:**
  - **AC1:** ADR-003 aprobado con la librería elegida.
  - **AC2 — Mismo resultado:** el Excel y el PDF del mismo listado producen el mismo
    `ListadoJugadoresDTO`.
  - **AC3:** los errores de formato son los mismos del AC1 de la US-206.
- **Testing Mínimo:** _unitaria_ que compara el DTO de los dos fixtures; PDF sin encabezado.
- **Archivos:** `src/infraestructura/ingest/listado_jugadores_pdf.py`,
  `src/infraestructura/ingest/__init__.py`, `pyproject.toml`/`uv.lock`, `docs/adr/ADR-003-*.md`,
  `tests/unit/test_listado_jugadores_pdf.py`, `tests/integration/fixtures/listado_jugadores_anonimo.pdf`.

#### US-211 — Identificación de Jugadores por Nombre Dentro del Club

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — · **Toca la base:** no (solo
  lee)
- **Objetivo:** decidir, para un nombre `APELLIDOS, NOMBRES` y un club, si es un jugador que ya
  existe, uno nuevo o un caso ambiguo, sin guardar nada.
- **Entrega:** el servicio `IdentificadorJugadores`. Lo usan la US-212 y la US-216.
- **Reglas:** normaliza el nombre (sin tildes, mayúsculas ni espacios de más) y busca **solo entre
  los jugadores de ese club** (vínculos y listas). **Nunca** empareja con jugadores de otro club:
  dos chicos con el mismo nombre en clubes distintos son dos personas.
- **Criterios de Aceptación:**
  - **AC1:** devuelve `Existente(jugador)`, `Nuevo` o `Ambiguo(candidatos)` según haya 1, 0 o más de
    una coincidencia. No crea jugadores: los crea el caso de uso al confirmar, así la vista previa
    no persiste nada.
  - **AC2:** el mismo nombre en otro club da `Nuevo`.
  - **AC3:** si `JugadorRepositorio` no tiene cómo listar los jugadores de un club por vínculos y
    listas, el método se agrega en esta US, con su test de integración.
- **Testing Mínimo:** _unitarias_ con repositorio falso: 0, 1 y 2 coincidencias, tildes y espacios,
  y el mismo nombre en otro club.
- **Archivos:** `src/aplicacion/servicios/identificador_jugadores.py`,
  `tests/unit/test_identificador_jugadores.py` (y el repositorio, si aplica el AC3).

#### US-212 — Caso de Uso para Importar una Lista de Buena Fe

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-206, US-211 · **Toca la
  base:** no (inserta datos con los repositorios existentes)
- **Objetivo:** cargar la lista de buena fe de un club para una competencia y categoría a partir de
  un `ListadoJugadoresDTO`, con vista previa sin efectos.
- **Narrativa:** Como DT, quiero importar el listado de jugadores que publica la CAB para tener la
  lista de buena fe de cualquier club (propio o rival) sin cargarla jugador por jugador. Es lo que
  después permite cargar a mano partidos de otros clubes.
- **Entrega:** `ImportarListaBuenaFeUseCase` con `preview()` y `confirmar()`. Lo usa la US-213.
- **Reglas:**
  - El club viene sugerido del título; si no existe, se crea **sin** vínculo con el usuario
    (como en la US-108).
  - Competencia y categoría las elige el usuario (llegan como parámetros). Si la categoría no está
    habilitada en la competencia, la vista previa lo avisa y al confirmar se habilita
    (`HabilitarCategoriaEnCompetenciaUseCase`, regla de la sección 6).
  - Si no hay inscripción, se crea con su lista (`inscribir_con_lista`, con la fecha de importación
    como fecha de presentación). Se agregan los jugadores que faltan. Los que están en la lista y no
    vienen en el archivo **no se quitan**: se informan.
- **Criterios de Aceptación:**
  - **AC1 — Vista previa:** `preview()` devuelve jugadores nuevos, existentes y ambiguos, y lo que
    se crearía (club, habilitación, inscripción), sin persistir nada.
  - **AC2 — Ambiguos:** `confirmar()` recibe la elección del usuario para cada ambiguo; sin elección
    no confirma.
  - **AC3 — Idempotencia:** importar dos veces el mismo listado no duplica jugadores ni filas en la
    lista.
  - **AC4 — Listas separadas:** el mismo jugador puede estar en la lista de U13 del Asociativo 2026
    y en la del Provincial 2026 (o del Asociativo 2027); importar una no toca las otras.
- **Testing Mínimo:** _integración_ en SQLite en memoria: `preview` no cambia nada; importar el
  fixture dos veces; el mismo jugador en las listas de dos competencias; categoría no habilitada.
- **Archivos:** `src/aplicacion/casos_uso/importar_lista_buena_fe.py`,
  `tests/integration/test_importar_lista_buena_fe.py`.

#### US-213 — Importar la Lista desde un Archivo en Pantalla

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-212 · **Toca la base:** no
- **Objetivo:** que el DT importe un listado desde `ListaBuenaFeScreen` sin tipear nombres.
- **Criterios de Aceptación:**
  - **AC1:** botón "Importar desde archivo" en `ListaBuenaFeScreen` (US-107). El `FilePicker`
    acepta las extensiones que conoce `leer_listado`: cuando se mergea la US-210 aparece el PDF sin
    tocar esta pantalla.
  - **AC2:** la vista previa muestra nuevos, existentes y ambiguos; cada ambiguo se resuelve
    eligiendo un candidato o "es otro jugador". Confirmar o descartar.
  - **AC3:** un error de formato se muestra en pantalla con lo que faltó, sin traceback.
- **Testing Mínimo:** _manual guiado:_ importar el fixture, resolver un ambiguo y volver a importar
  (no duplica). Pantalla construida sin ventana, como las del Hito 1.
- **Archivos:** `src/infraestructura/ui/flet/screens/lista_buena_fe_screen.py`.

#### US-201 — Lectura de la Planilla de Partido en Excel

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-206
  (`FormatoArchivoInvalidoError` y el patrón de lector por extensión) · **Toca la base:** no
- **Objetivo:** convertir la planilla de estadísticas de partido que exporta Gesdeportiva en Excel
  en un `PlanillaPartidoDTO` con el título y las filas de los dos equipos ya tipadas.
- **Entrega:** `PlanillaPartidoDTO` y `leer_planilla(ruta)`. Los usan la US-214, la US-215, la
  US-216 y la US-207.
- **Criterios de Aceptación:**
  - **AC1 — Formato:** si faltan el título o los encabezados esperados, se lanza
    `FormatoArchivoInvalidoError` antes de procesar y se dice qué faltó.
  - **AC2 — Bloques:** encuentra los dos bloques por texto aunque estén en filas distintas, cada uno
    con su club, sus jugadores y su fila `TOTALES`.
  - **AC3 — Valores:** `mm:ss` → minutos con decimales, `A/I` → convertidos y lanzados, según el
    mapeo de arriba. Las columnas `%`, `Tot.`, `Num.`, `VAL` y `+/-` se ignoran.
- **Testing Mínimo:** _unitarias_ contra el fixture: `mm:ss`, `A/I`, espacios de más, bloques en
  filas distintas, encabezado faltante.
- **Archivos:** `src/infraestructura/ingest/planilla_partido_excel.py`,
  `src/infraestructura/ingest/__init__.py` (+ `leer_planilla`), `src/aplicacion/dtos/ingest_dto.py`
  (+ `PlanillaPartidoDTO`), `tests/unit/test_planilla_partido_excel.py`,
  `tests/integration/fixtures/planilla_partido_anonima.xlsx`.

#### US-214 — Lectura de la Planilla de Partido en PDF

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-201, US-210 (librería de
  PDF) · **Toca la base:** no
- **Objetivo:** aceptar también el PDF de la planilla, con el mismo resultado que el Excel.
- **Criterios de Aceptación:**
  - **AC1 — Mismo resultado:** el Excel y el PDF del mismo partido producen el mismo
    `PlanillaPartidoDTO`.
  - **AC2:** lo que solo trae el PDF (titulares, capitán, entrenador) se ignora.
- **Decisión tomada (2026-10-31):** dorsal, titular, capitán, entrenador, `VAL` y `+/-` no tienen
  lugar en el esquema y no se guardan. `VAL` se puede recalcular (US-202). El resto, si algún día
  hace falta, es una historia nueva con una **migración aditiva** (sección 3). `+/-` no se puede
  recalcular: necesita el minuto a minuto.
- **Testing Mínimo:** _unitaria_ que compara el DTO de los dos fixtures.
- **Archivos:** `src/infraestructura/ingest/planilla_partido_pdf.py`,
  `src/infraestructura/ingest/__init__.py`, `tests/unit/test_planilla_partido_pdf.py`,
  `tests/integration/fixtures/planilla_partido_anonima.pdf`.

#### US-215 — Validación de la Planilla Contra la Fila TOTALES

- **Esfuerzo:** XS (menos de 1 día) · **Prioridad:** Alta · **Depende de:** US-201 · **Toca la
  base:** no
- **Objetivo:** detectar una planilla mal exportada antes de importarla.
- **Entrega:** la función pura `validar_totales(planilla) -> list[Diferencia]`. La usa la US-216.
- **Criterios de Aceptación:**
  - **AC1:** para cada equipo, la suma de las filas de jugadores se compara con la fila `TOTALES`
    en cada columna, y cada diferencia dice equipo, columna, suma y total.
  - **AC2:** los puntos de `TOTALES` son el resultado final del partido.
- **Testing Mínimo:** _unitarias_: planilla que coincide, una con una columna distinta en un
  equipo, y otra con diferencias en los dos.
- **Archivos:** `src/aplicacion/servicios/validar_totales.py`, `tests/unit/test_validar_totales.py`.

#### US-216 — Caso de Uso para Importar una Planilla de Partido

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Urgente (bloquea el análisis con datos reales) ·
  **Depende de:** US-201, US-211, US-215 · **Toca la base:** no (inserta datos con los métodos
  existentes)
- **Objetivo:** convertir un `PlanillaPartidoDTO` en un partido con el boxscore de los dos equipos,
  con vista previa sin efectos y un reporte de lo hecho. De paso crea o completa las listas de buena
  fe de los dos clubes para esa competencia y categoría.
- **Narrativa:** Como analista, quiero importar las planillas de partido de Gesdeportiva (de mi
  club y de los demás) para no transcribir a mano y tener una base con partidos de toda la
  competencia.
- **Entrega:** `ImportarPlanillaPartidoUseCase` con `preview()` y `confirmar()`, e
  `IngestReportDTO` (`creados`, `existentes`, `ambiguos`, `rechazados` con causa, y totales). Los
  usan la US-217 y la US-207. Para guardar reusa `CargarPartidoUseCase` (US-108) y, para los
  jugadores, `IdentificadorJugadores` (US-211). Los dos equipos traen boxscore completo, así que se
  guardan como boxscore (ADR-010).
- **Reglas de Negocio:**
  - El primer club del título (`A vs B`) se toma como local. Es un **supuesto a confirmar** con más
    archivos; `confirmar()` acepta invertirlo.
  - Club que no existe → se crea **sin** vínculo con el usuario (US-108). Se busca por nombre
    normalizado.
  - Competencia y categoría **no** se crean solas: llegan como parámetros (la pantalla las sugiere
    cuando el nombre coincide). Los dos archivos de la CAB nombran distinto la misma categoría
    (`U13MX` e `INFANTILES MIXTO`), así que crearlas automáticamente generaría duplicados.
  - Si la categoría no está habilitada en la competencia, la vista previa lo avisa («se habilita U13
    Mixto en Asociación 2026») y al confirmar se habilita antes de inscribir.
  - Si un club no tiene inscripción en esa competencia y categoría, se crea con su lista
    (`inscribir_con_lista`, con la fecha del partido); los jugadores de la planilla que no están en
    la lista se agregan.
  - La fecha la pone el usuario (la planilla no la trae). Los puntos por cuarto son opcionales, como
    en `CargaPartidoScreen`.
- **Criterios de Aceptación:**
  - **AC1 — Vista previa:** `preview()` muestra qué se crearía (clubes, jugadores, habilitaciones,
    inscripciones) y las diferencias de `validar_totales`, sin persistir nada.
  - **AC2 — Consistencia:** con diferencias contra `TOTALES` el partido se rechaza indicando la
    columna.
  - **AC3 — Transacción:** partido y boxscore se guardan en una sola transacción
    (`save_with_boxscore`). Lo que se crea antes (clubes, jugadores, inscripciones) queda aunque el
    partido falle, y reimportar no lo duplica.
  - **AC4 — Sin duplicados:** importar de nuevo un partido ya cargado (misma competencia, categoría,
    fecha, local y visitante) se rechaza con un aviso.
  - **AC5 — Reporte y log:** `IngestReportDTO` con registros procesados, jugadores
    creados/existentes/ambiguos y errores; el mismo detalle queda en el log (US-110).
- **Decisión tomada (2026-10-31):** lo que se crea antes del partido se guarda con otros métodos,
  cada uno con su propio commit. Se descartó una unidad de trabajo que abarque todo: hoy cada método
  del repositorio hace su propio commit, y cambiarlo es más trabajo del que ahorra.
- **Testing Mínimo:** _unitarias_ con repositorios falsos (club nuevo, jugador ambiguo, lista
  inexistente, totales que no coinciden, local invertido); _integración_: importar el fixture a
  SQLite en memoria, `preview` no cambia nada, reimportar se rechaza.
- **Archivos:** `src/aplicacion/casos_uso/importar_planilla_partido.py`,
  `src/aplicacion/dtos/ingest_dto.py` (+ `IngestReportDTO`), `tests/unit/test_importar_planilla_partido.py`,
  `tests/integration/test_importar_planilla_partido.py`.

#### US-217 — Pantalla de Importación de una Planilla

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-216 · **Toca la base:** no
- **Objetivo:** importar una planilla desde la GUI en una sola pantalla: elegir archivo → completar
  y revisar → confirmar (NFR-4). El aspecto de la vista previa está en el muestrario de la US-111.
- **Entrega:** `ImportScreen` y el componente de vista previa, que recibe un archivo. La US-207 lo
  repite por cada archivo de una tanda.
- **Criterios de Aceptación:**
  - **AC1:** entrada "Importar planilla" en el menú lateral; `FilePicker` con las extensiones que
    conoce `leer_planilla`.
  - **AC2 — Vista previa:** completar la fecha, confirmar competencia y categoría (sugeridas),
    invertir local y visitante, resolver los ambiguos, cargar puntos por cuarto si se tienen, ver el
    boxscore tal como se leyó y las diferencias contra `TOTALES`. Confirmar o descartar.
  - **AC3:** errores de formato, de totales y de duplicado se muestran en pantalla, sin traceback.
- **Testing Mínimo:** _manual guiado:_ importar el Excel (y el PDF, si la US-214 está) del mismo
  partido; el segundo se rechaza como duplicado.
- **Archivos:** `src/infraestructura/ui/flet/screens/import_screen.py`,
  `src/infraestructura/ui/flet/components/vista_previa_planilla.py`, menú lateral y composition root.

#### US-207 — Carga Masiva de Planillas de Partido

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-217 · **Toca la base:** no
- **Objetivo:** elegir de una vez las planillas de una fecha completa (o de varias) y revisar cada
  partido en su vista previa.
- **Por qué cada archivo se sigue confirmando por separado:** la planilla no trae la fecha del
  partido; confirmar todo de un golpe obligaría a cargar las fechas a ciegas.
- **Alcance:** sin casos de uso nuevos: la tanda vive en la pantalla, que llama a `preview()` y
  `confirmar()` de la US-216 por cada archivo. La función pura `misma_planilla(a, b)` compara dos
  `PlanillaPartidoDTO` (mismo título y mismas filas `TOTALES` de los dos equipos) para detectar el
  Excel y el PDF de un mismo partido antes de que ninguno esté guardado.
- **Criterios de Aceptación:**
  - **AC1 — Carga masiva:** `FilePicker` con `allow_multiple=True`. Cada archivo aparece con el
    partido detectado y su estado (listo, con ambiguos, ya cargado, repetido en la tanda,
    rechazado con la causa). Un archivo rechazado no frena a los demás; cada partido se confirma y
    se guarda por separado.
  - **AC2 — Repetidos en la tanda:** si dos archivos describen el mismo partido, el segundo se marca
    como repetido y solo se revisa el primero (el AC4 de la US-216 mira la base, y en ese momento
    ninguno está guardado).
  - **AC3 — Resultado:** al terminar, un resumen con importados, ya cargados, descartados y
    rechazados con su causa; el mismo detalle queda en el log.
- **Testing Mínimo:** _unitarias_ de `misma_planilla` (Excel y PDF del mismo partido → sí; mismo
  título con otros totales → no); _integración_: tanda de cuatro archivos (uno válido, uno ya
  cargado, uno con `TOTALES` que no coincide y el PDF del válido): se importa solo el válido.
- **Archivos:** `src/aplicacion/servicios/misma_planilla.py`,
  `src/infraestructura/ui/flet/screens/import_screen.py`, `tests/unit/test_misma_planilla.py`,
  `tests/integration/test_importar_tanda.py`.

### Épica H2-E2: Motor Estadístico Avanzado (v1.2.0)

Las tres primeras historias son funciones puras sobre `DataFrame` y no dependen de nada: se pueden
tomar en paralelo con la H2-E1. La US-203 tampoco depende de nada y abre la lectura de datos.

#### US-202 — Fórmulas de Tiro y Eficiencia

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — · **Toca la base:** no
- **Objetivo:** tener las métricas avanzadas como funciones puras determinísticas, probadas con
  valores calculados a mano.
- **Narrativa:** Como DT, quiero ver métricas como eFG%, EFF, PPP y PER para evaluar el impacto real
  de mis jugadores y comparar a mi equipo contra el rival.
- **Entrega:** `infraestructura/analytics/formulas.py` y `CalculationError` (datos inconsistentes,
  ej. lanzamientos negativos). Las usan la US-223, la US-224, la US-226, la US-227, la US-229 y la
  US-303.
- **Fórmulas:**
  - **eFG%:** `(T2C + 1.5 × T3C) / (T2L + T3L)`.
  - **EFF:** `PTS + REB + AST + REC + TAP_R − (T2L−T2C) − (T3L−T3C) − (T1L−T1C) − PERD`.
  - **Posesiones (estimación FIBA):** `(T2L + T3L) + 0.44 × T1L + PERD − REB_OF`.
  - **PPP:** `Puntos / Posesiones`.
  - **% de Rebotes:** rebotes capturados sobre el total disponible (recibe los dos equipos).
  - **PER simplificado:** la fórmula exacta se elige y se documenta en esta US (hasta ahora el PRD
    lo nombraba sin definirlo).
- **Criterios de Aceptación:**
  - **AC1:** cada fórmula acepta `pd.DataFrame` y devuelve serie o escalar; división por cero →
    0.0; nunca `NaN` ni `inf`.
  - **AC2:** cada fórmula documenta su fuente.
  - **AC3:** `formulas.py` no accede a la base ni hace I/O.
- **Testing Mínimo:** `tests/unit/test_formulas.py` con cobertura del **100 %**, valores calculados
  a mano y casos límite (ceros).
- **Archivos:** `src/infraestructura/analytics/formulas.py`, `src/dominio/exceptions.py`
  (+ `CalculationError`), `tests/unit/test_formulas.py`.

#### US-218 — Promedio de Puntos por Cuarto

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** — · **Toca la base:** no
- **Objetivo:** promediar los puntos a favor y en contra de un club por período, sin que los
  partidos sin cuartos lo distorsionen (sección 6, "Puntos por cuarto").
- **Entrega:** `promedio_por_cuarto(df)` en `formulas.py`, que devuelve el promedio por período, N
  (partidos con cuartos) y M (partidos del recorte). La usan la US-227 y la US-303.
- **Criterios de Aceptación:**
  - **AC1:** ignora los partidos sin cuartos e informa «sobre N de M partidos»; con N = 0 no
    devuelve valores (no un cero).
  - **AC2:** las prórrogas se promedian solo entre los partidos que las tuvieron.
- **Testing Mínimo:** partidos mezclados (con y sin cuartos, uno con prórroga) y ninguno con
  cuartos.
- **Archivos:** `src/infraestructura/analytics/formulas.py`, `tests/unit/test_formulas.py`.

#### US-219 — Valores Cada 40 Minutos y Aviso de Muestra Chica

- **Esfuerzo:** XS (menos de 1 día) · **Prioridad:** Media · **Depende de:** — · **Toca la base:** no
- **Objetivo:** aplicar la regla de "Muestra chica" de la sección 6 en un solo lugar.
- **Entrega:** `por_40_minutos(df)` y `es_muestra_chica(partidos_jugados)` (mínimo en
  `settings.py`, por defecto 3). Las usan la US-226, la US-227 y la US-229.
- **Criterios de Aceptación:**
  - **AC1:** el valor cada 40 minutos solo se calcula para quien llega al mínimo de partidos.
  - **AC2:** el mínimo sale de `settings.py`, no está repetido en cada caso de uso.
- **Testing Mínimo:** _unitarias_: debajo, en el mínimo y arriba del mínimo; 0 minutos.
- **Archivos:** `src/infraestructura/analytics/formulas.py`, `src/config/settings.py`,
  `tests/unit/test_formulas.py`.

#### US-203 — Interfaz AnalyticsService y Boxscore de un Partido

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — · **Toca la base:** no (lee
  las vistas que ya existen)
- **Objetivo:** abrir la lectura de datos para el motor analítico, con la interfaz completa
  definida de una vez para que las historias que siguen no se pisen.
- **Entrega:** la interfaz `AnalyticsService` (`src/dominio/servicios/analytics_service.py`, junto
  a `PasswordHasher`: es un servicio, no un repositorio) con **todas** sus firmas, y
  `PandasAnalyticsService` con `get_boxscore_partido(partido_id)` implementado y los demás métodos
  lanzando `NotImplementedError` hasta que los complete su historia:

| Método                                                                            | Lo implementa |
| --------------------------------------------------------------------------------- | ------------- |
| `get_boxscore_partido(partido_id)`                                                | US-203        |
| `get_totales_jugador(jugador_id, *, competencia_id, anio, categoria_id, condicion)` | US-220      |
| `get_partidos_club(club_id, *, competencia_id, anio, categoria_id, condicion)`    | US-221        |
| `get_totales_club(club_id, *, competencia_id, anio, categoria_id, condicion)`     | US-221        |
| `get_cuartos_club(club_id, *, competencia_id, anio, categoria_id)`                | US-222        |
| `get_evolucion_jugador(jugador_id, metrica, *, competencia_id, anio, categoria_id, condicion)` | US-223 |

  Los filtros son los de la barra común de la sección 6; `condicion` es local, visitante o `None`.
  Todos son opcionales: sin ninguno, el acumulado es global (toda la carrera o toda la historia del
  club).
- **Criterios de Aceptación:**
  - **AC1:** `PandasAnalyticsService` lee **solo de las vistas SQL** con `pandas.read_sql()`. Los
    recortes se resuelven en pandas sobre lo leído, no con una vista nueva por cada combinación.
  - **AC2:** `get_boxscore_partido` devuelve las filas de `v_boxscore_completo` y los totales de
    equipo de `v_totales_equipo_partido` (que también cubre al rival cargado solo con totales,
    ADR-010), con columnas estandarizadas.
  - **AC3:** partido inexistente → error de dominio, no `KeyError`.
  - **AC4:** queda armado en el composition root.
- **Testing Mínimo:** _integración_ con las vistas reales en `:memory:` y `seed.sql`; _regresión_:
  un test que falla si se renombra una columna consumida.
- **Archivos:** `src/dominio/servicios/analytics_service.py`,
  `src/infraestructura/analytics/pandas_analytics_service.py`, composition root,
  `tests/integration/test_analytics_service.py`.

#### US-220 — Totales de Jugador por Competencia, Categoría y Año

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-203 · **Toca la base:**
  solo una vista (`v_jugador_totales_temporada`; las vistas no guardan datos y se recrean al abrir)
- **Objetivo:** sumar los números de un jugador en cualquier recorte, sin mezclar competencias ni
  categorías distintas.
- **Entrega:** `get_totales_jugador`. La usan la US-226, la US-229 y la US-407.
- **Alcance:** se corrige la vista misma (decidido el 2026-11-08, no se crea otra):
  `GROUP BY j.idJugador, p.idCompetencia, p.idCategoria`, con las columnas `idJugador`,
  `idCompetencia`, `anio_competencia` e `idCategoria`. Se ajustan sus consumidores actuales
  (`tests/integration/test_database.py`, `tests/benchmarks/test_bench_vistas.py`).
- **Criterios de Aceptación:**
  - **AC1:** por partido, competencia, año, categoría o global, sin mezclar dos competencias del
    mismo año ni dos categorías de la misma competencia cuando se pide una sola.
  - **AC2:** los porcentajes se recalculan desde los totales, nunca promediando porcentajes.
  - **AC3:** `condicion` filtra partidos de local o de visitante (`partido.idClubLocal`/
    `idClubVisitante`, sin cambios de esquema).
  - **AC4:** solo cuentan los partidos con boxscore del jugador: un equipo cargado solo con totales
    (ADR-010) no aporta filas individuales.
- **Testing Mínimo:** _integración_: un jugador en dos competencias del mismo año (separadas por
  competencia, sumadas por año y global) y uno que jugó U17 y U19 en la misma competencia
  (separadas por categoría, sumadas sin filtro, porcentajes desde los totales).
- **Archivos:** `src/infraestructura/persistencia/sql/views.sql`,
  `src/infraestructura/analytics/pandas_analytics_service.py`, los dos tests de arriba.

#### US-221 — Partidos y Totales de un Club

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-203 · **Toca la base:** no
- **Objetivo:** responder "¿cómo viene mi equipo en la competencia?" o "¿y este año, sumando todas?"
  (sección 3, agregado por club).
- **Entrega:** `get_partidos_club` (una fila por partido, con lo hecho y lo recibido) y
  `get_totales_club` (la suma de esas filas). Las usan la US-227 y la US-303, que así comparten la
  misma agregación en vez de calcular lo mismo por dos caminos.
- **Alcance:** sale de `v_totales_equipo_partido` unida a `partido`, agrupada en pandas. No hace
  falta una vista nueva, y cubre también a los clubes cargados solo con totales (ADR-010).
- **Criterios de Aceptación:**
  - **AC1:** cada fila de `get_partidos_club` tiene fecha, rival, condición, resultado y los
    totales a favor y en contra.
  - **AC2:** los recortes por competencia, año, categoría y condición se comportan como en el AC1 de
    la US-220; los porcentajes, desde los totales.
- **Testing Mínimo:** _integración_: un club en dos competencias del mismo año; un rival cargado
  solo con totales; condición local/visitante.
- **Archivos:** `src/infraestructura/analytics/pandas_analytics_service.py`,
  `tests/integration/test_analytics_service.py`.

#### US-222 — Puntos por Cuarto de un Club

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-203 · **Toca la base:** no
- **Objetivo:** leer `partidoCuarto` de un club con los filtros comunes.
- **Entrega:** `get_cuartos_club`, que devuelve los puntos a favor y en contra por período y
  partido, listos para `promedio_por_cuarto` (US-218). La usan la US-227 y la US-303.
- **Criterios de Aceptación:** **AC1:** devuelve también los partidos del recorte sin cuartos, para
  poder decir «sobre N de M».
- **Testing Mínimo:** _integración_ con partidos con y sin cuartos y uno con prórroga.
- **Archivos:** `src/infraestructura/analytics/pandas_analytics_service.py`,
  `tests/integration/test_analytics_service.py`.

#### US-223 — Evolución de un Jugador Partido a Partido

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-203, US-202 · **Toca la
  base:** no
- **Objetivo:** ver si un jugador mejora o empeora en una métrica, no solo su total.
- **Entrega:** `get_evolucion_jugador`, una serie ordenada por fecha. La usa la US-305.
- **Criterios de Aceptación:** **AC1:** acepta métricas del boxscore y las de `formulas.py` (ej.
  EFF), ordenadas por fecha, con los filtros comunes y `condicion`.
- **Testing Mínimo:** _integración_: un jugador con cinco partidos en dos competencias; con filtro
  por competencia quedan solo los suyos, en orden.
- **Archivos:** `src/infraestructura/analytics/pandas_analytics_service.py`,
  `tests/integration/test_analytics_service.py`.

#### US-224 — Métricas Avanzadas en el Detalle de Partido

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-202, US-203 · **Toca la
  base:** no
- **Objetivo:** que el DT vea las métricas avanzadas de un partido en la pantalla de detalle que ya
  existe. Es lo visible de la v1.2.0.
- **Entrega:** `CalcularEstadisticasPartidoUseCase` con `MetricasPartidoDTO` y `MetricasJugadorDTO`.
  Los usa la US-309 (informe PDF).
- **Criterios de Aceptación:**
  - **AC1:** `DetallePartidoScreen` suma eFG%, EFF, posesiones, PPP y % de rebotes por equipo, y EFF
    y eFG% por jugador, en `tabla_datos` con alineación numérica.
  - **AC2:** un equipo cargado solo con totales muestra sus métricas de equipo, sin filas por
    jugador.
  - **AC3:** los valores coinciden con `formulas.py`; sin datos → mensaje, no traceback.
- **Testing Mínimo:** _integración_ del caso de uso con `seed.sql`; _manual guiado_ en la pantalla.
- **Archivos:** `src/aplicacion/casos_uso/calcular_estadisticas_partido.py`,
  `src/aplicacion/dtos/metricas_dto.py`, `src/infraestructura/ui/flet/screens/detalle_partido_screen.py`,
  `tests/integration/test_calcular_estadisticas_partido.py`.

### Épica H2-E3: Inteligencia Deportiva (v2.0.0)

> **Por qué hay comparativas (se mantiene de la versión anterior):** surgen de casos reales de un
> DT (¿cómo viene mi jugador contra otro de mi equipo? ¿mi equipo mejoró de una competencia a
> otra?), contrastados con apps de analítica deportiva existentes (Hudl Assist, Hoopsalytics,
> Viziball, Basketball Stats Assistant). Comparar jugadores y equipos con distintos recortes y
> contra un promedio de referencia es estándar en la categoría. Ver también la sección 20.

#### US-225 — Barra Común de Filtros de Estadísticas

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — (usa los casos de uso de
  competencias y categorías del Hito 1) · **Toca la base:** no
- **Objetivo:** que todas las pantallas de estadísticas filtren igual (sección 6, "Filtros de
  estadísticas").
- **Entrega:** `components/filtros_estadisticas.py`. Lo usan la US-205, la US-228, la US-230, la
  US-307, la US-308, la US-311 y la US-408.
- **Criterios de Aceptación:**
  - **AC1:** tres desplegables encadenados, **Año** → **Competencia** → **Categoría**, cada uno con
    «Todos/Todas». Elegir un año achica las competencias; elegir una competencia, las categorías
    habilitadas en ella.
  - **AC2:** el parámetro `categoria_obligatoria` saca «Todas» de la categoría.
  - **AC3:** al cambiar un filtro, avisa a la pantalla con los tres valores (`None` = todos).
- **Testing Mínimo:** _unitarias_ sin ventana: el encadenamiento y `categoria_obligatoria`.
- **Archivos:** `src/infraestructura/ui/flet/components/filtros_estadisticas.py`,
  `tests/unit/test_filtros_estadisticas.py`.

#### US-226 — Caso de Uso de Líderes de una Competencia

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-220, US-202, US-219 · **Toca
  la base:** no
- **Objetivo:** el top-N de jugadores de una competencia y categoría por PTS, REB, AST y EFF.
- **Entrega:** `ObtenerLideresTemporadaUseCase` en versión básica y `LiderDTO`. Los usan la US-205 y
  la US-306, que lo amplía. No reemplaza a `ListarLideresClubUseCase` (Hito 1), que muestra los
  líderes del club propio en Inicio.
- **Criterios de Aceptación:**
  - **AC1:** muestra PJ y deja afuera a quien no llega al mínimo de partidos (US-219).
  - **AC2:** quien jugó en U17 y en U19 en la misma temporada aparece en los dos rankings, cada uno
    con sus partidos.
  - **AC3:** desempate por un criterio secundario fijo (más PJ, después nombre).
- **Testing Mínimo:** _unitario_ de orden y desempate; _integración_ con el caso de las dos
  categorías.
- **Archivos:** `src/aplicacion/casos_uso/obtener_lideres_temporada.py`,
  `src/aplicacion/dtos/metricas_dto.py` (+ `LiderDTO`), `tests/unit/test_leaderboard.py`.

#### US-205 — Pantalla de Líderes

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-225, US-226 · **Toca la
  base:** no
- **Objetivo:** que el DT consulte los líderes de una competencia en la GUI. _(Antes del
  2026-10-31 era el comando de consola `stats leaders`.)_
- **Criterios de Aceptación:**
  - **AC1:** `LideresScreen` con la barra común (categoría obligatoria) y una tabla por rubro en
    `tabla_datos`, con PJ.
  - **AC2:** sin datos → mensaje descriptivo, no traceback.
- **Testing Mínimo:** _manual guiado_ con `seed.sql`.
- **Archivos:** `src/infraestructura/ui/flet/screens/lideres_screen.py`, menú lateral y composition
  root.

#### US-227 — Caso de Uso de Comparativa Entre Dos Clubes

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-221, US-222, US-202,
  US-218, US-219 · **Toca la base:** no
- **Objetivo:** comparar dos clubes en un partido entre ellos o en el acumulado de una competencia y
  categoría.
- **Entrega:** `GenerarTablaComparativaUseCase` y `ComparativaEquipoDTO`. Los usa la US-228.
- **Criterios de Aceptación:**
  - **AC1:** modo **partido** (un `idPartido` entre los dos) y modo **acumulado** (cada club con
    todos sus partidos de esa competencia y categoría, o de un año).
  - **AC2:** cada club trae PJ y el aviso de muestra chica.
  - **AC3:** si hay partidos con cuartos, suma el promedio por cuarto «sobre N de M partidos»; si no
    hay, esa parte viene vacía.
- **Testing Mínimo:** _integración_: dos equipos en un partido (los totales coinciden con el
  resultado) y a lo largo de una competencia (el agregado coincide con la suma).
- **Archivos:** `src/aplicacion/casos_uso/generar_tabla_comparativa.py`,
  `src/aplicacion/dtos/metricas_dto.py`, `tests/integration/test_tabla_comparativa.py`.

#### US-228 — Pantalla de Comparativa de Clubes

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-227, US-225 · **Toca la
  base:** no
- **Objetivo:** mostrar la comparativa en la GUI. _(Antes era el comando `stats compare`.)_
- **Criterios de Aceptación:**
  - **AC1:** filtros **Club** (arranca en el club activo), **Contra** (los otros clubes inscriptos
    en la competencia y categoría elegidas) y la barra común (categoría obligatoria).
  - **AC2:** en modo partido aparece el desplegable **Partido** con los cruces cargados; si no hay,
    se avisa. Si a los casos de uso de partidos del Hito 1 les falta filtrar por rival, se agrega
    en esta US.
  - **AC3:** aviso de muestra chica y sección de cuartos solo si hay datos.
- **Testing Mínimo:** _manual guiado_ en los dos modos.
- **Archivos:** `src/infraestructura/ui/flet/screens/comparativa_screen.py`, menú lateral y
  composition root.

#### US-229 — Caso de Uso de Comparativa de Jugadores

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-220, US-202, US-219 ·
  **Toca la base:** no
- **Objetivo:** comparar dos jugadores en el mismo recorte, o un jugador contra el promedio de su
  categoría y competencia.
- **Entrega:** `GenerarComparativaJugadoresUseCase` y `ComparativaJugadoresDTO`. Los usa la US-230.
- **Criterios de Aceptación:**
  - **AC1:** jugador contra jugador con el mismo recorte (partido, competencia, año o global).
  - **AC2:** jugador contra el promedio de los jugadores de su categoría y competencia, para saber
    si está por encima o por debajo.
  - **AC3:** PJ y aviso de muestra chica en cada lado.
- **Testing Mínimo:** _integración_ con al menos 3 jugadores de `seed.sql`.
- **Archivos:** `src/aplicacion/casos_uso/generar_comparativa_jugadores.py`,
  `src/aplicacion/dtos/metricas_dto.py`, `tests/integration/test_comparativa_jugadores.py`.

#### US-230 — Pantalla de Comparativa de Jugadores

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-229, US-225 · **Toca la
  base:** no
- **Objetivo:** que la comparativa de jugadores tenga dónde verse. Hasta este rearmado, el caso de
  uso existía en el plan pero ninguna pantalla lo mostraba.
- **Criterios de Aceptación:**
  - **AC1:** elegir uno o dos jugadores con búsqueda (`BuscarJugadoresPorNombreUseCase`), o uno solo
    contra el promedio de su categoría; barra común de filtros.
  - **AC2:** la tabla lado a lado se arma extendiendo `tabla_datos.py`, no con un componente nuevo.
- **Testing Mínimo:** _manual guiado_ en los dos modos.
- **Archivos:** `src/infraestructura/ui/flet/screens/comparativa_jugadores_screen.py`, menú lateral
  y composition root.

---

## 11. Hito 3 — Visualización Pro y Reporting (v3.0.0)

**Objetivo del hito:** convertir las estadísticas en tableros, gráficos e informes consumibles
por el DT para tomar decisiones tácticas antes, durante y después del partido.

**Versiones:** H3-E1 → **v2.1.0** · H3-E2 → **v2.2.0** · H3-E3 → **v3.0.0** (cierra el hito).

**Épicas:** 3 · **Historias:** 12 · **Esfuerzo total estimado:** ~24 días·persona

**Decisiones previas requeridas:** ninguna. ADR-005 (`reportlab`) y ADR-007 (`matplotlib`) ya están
aprobados.

> **Rearmado (2026-11-27):** las US-301, US-302 y US-303 se dividieron como las del Hito 2. Dos
> cambios de fondo: la `VerTrayectoriaJugadorUseCase` pasa al Hito 4 (US-407), junto a la única
> pantalla que la usa, y `views_scouting.sql` se descarta: nadie lo cargaba al abrir la app, y el
> scouting sale con pandas de `get_partidos_club` (US-221), como el resto del motor.
>
> **Hallazgo de transcripción (se mantiene):** el `.md` del submódulo solo tenía las US-301 y
> US-302; la épica H3-E3 (Scouting) se completó con el LaTeX. Ver sección 20.

### Mapa de dependencias del Hito 3

| US     | Qué deja hecho                                         | Depende de                     | Tamaño | Sale de |
| ------ | ------------------------------------------------------ | ------------------------------ | ------ | ------- |
| US-301 | `ChartGenerator` (matplotlib → imagen en memoria)      | —                              | S      | US-301  |
| US-304 | `ChartComponent` para mostrar gráficos en pantalla     | US-301                         | XS     | US-301  |
| US-305 | Gráfico de rendimiento de un jugador                   | US-223, US-301                 | S      | US-301  |
| US-306 | Líderes con club, varios años y local/visitante        | US-226                         | S      | US-301  |
| US-307 | `DashboardScreen` del club activo                      | US-225, US-304, US-305, US-306 | M      | US-301  |
| US-308 | Filtros ampliados en `LideresScreen`                   | US-205, US-306                 | S      | US-301  |
| US-302 | Base de informes PDF (`PDFReportGenerator`)            | —                              | M      | US-302  |
| US-309 | Informe PDF de un partido                              | US-302, US-224, US-301         | M      | US-302  |
| US-310 | Botón "Exportar PDF" en el detalle de partido          | US-309                         | XS     | US-302  |
| US-303 | Caso de uso de scouting del rival                      | US-221, US-222, US-218, US-202 | M      | US-303  |
| US-311 | `ScoutingScreen`                                       | US-303, US-225                 | S      | US-303  |
| US-312 | Exportar el scouting a PDF                             | US-303, US-302, US-311         | S      | US-303  |

### Épica H3-E1: Dashboards e Informes (v2.1.0)

#### US-301 — Generador de Gráficos

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — (ADR-007 aprobado) · **Toca
  la base:** no
- **Objetivo:** producir figuras a partir de `DataFrame`s, separado de cualquier pantalla.
- **Entrega:** `ChartGenerator`, que devuelve la imagen PNG en memoria (bytes) con los colores de
  `estilo.py`. Lo usan la US-304, la US-305 y la US-309.
- **Criterios de Aceptación:**
  - **AC1 — Rendimiento:** un gráfico en **menos de 2 segundos** para el dataset de referencia (3
    temporadas, 20 equipos, 1200 filas de boxscore).
  - **AC2:** gráfico de líneas (tendencia) y de barras (comparación); los valores graficados son los
    del `DataFrame` recibido.
- **Testing Mínimo:** _integración_: figura generada con datos semilla, no vacía, bajo el tiempo.
- **Archivos:** `src/infraestructura/analytics/chart_generator.py`, `pyproject.toml`/`uv.lock`
  (+ matplotlib), `tests/integration/test_chart_generator.py`.

#### US-304 — Componente para Mostrar Gráficos

- **Esfuerzo:** XS (menos de 1 día) · **Prioridad:** Alta · **Depende de:** US-301 · **Toca la
  base:** no
- **Objetivo:** mostrar en Flet la imagen de `ChartGenerator`.
- **Entrega:** `components/chart_component.py`. Lo usan la US-307 y la US-408.
- **Criterios de Aceptación:** **AC1:** recibe los bytes y los muestra; sin datos muestra un mensaje
  en lugar del gráfico.
- **Testing Mínimo:** _unitaria_ sin ventana.
- **Archivos:** `src/infraestructura/ui/flet/components/chart_component.py`.

#### US-305 — Gráfico de Rendimiento de un Jugador

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-223, US-301 · **Toca la
  base:** no
- **Objetivo:** graficar la tendencia de un jugador en una métrica, no un promedio fijo.
- **Entrega:** `GenerarGraficoRendimientoUseCase` y `GraficoDTO`. Los usan la US-307 y la US-408.
- **Criterios de Aceptación:** **AC1:** filtros comunes y `condicion` (local/visitante); muestra PJ
  y el aviso de muestra chica.
- **Testing Mínimo:** _unitario_ de la transformación a serie temporal.
- **Archivos:** `src/aplicacion/casos_uso/generar_grafico_rendimiento.py`,
  `src/aplicacion/dtos/reporte_dto.py` (+ `GraficoDTO`).

> **Por qué se agregó (se mantiene):** el "performance trend" (aislar un jugador y una métrica y ver
> su evolución) es un feature estándar en apps de analítica deportiva (Hudl Assist, Hoopsalytics).

#### US-306 — Líderes con Club, Varios Años y Local/Visitante

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-226 · **Toca la base:** no
- **Objetivo:** ampliar el caso de uso de líderes (mismo archivo, sin crear otro) para el tablero y
  para comparar el liderazgo entre temporadas.
- **Entrega:** `ObtenerLideresTemporadaUseCase` con filtro de club opcional, varios años a la vez y
  `condicion`. Lo usan la US-307 y la US-308.
- **Criterios de Aceptación:** **AC1:** con club, solo sus jugadores; con varios años, el ranking
  sobre la suma de esos años; `condicion` como en el AC3 de la US-220. **AC2:** sin parámetros
  nuevos se comporta igual que en la US-226.
- **Testing Mínimo:** _integración_ de cada filtro nuevo.
- **Archivos:** `src/aplicacion/casos_uso/obtener_lideres_temporada.py`, `tests/unit/test_leaderboard.py`.

#### US-307 — Tablero del Club Activo

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-225, US-304, US-305,
  US-306 · **Toca la base:** no
- **Objetivo:** analizar de un vistazo el rendimiento del club activo.
- **Narrativa:** Como DT, quiero ver líderes y gráficos de tendencia en un tablero para analizar el
  rendimiento del equipo de un vistazo.
- **Decisión a tomar al empezar:** Inicio ya muestra los líderes del club (US-113). El tablero o
  reemplaza esa sección o es una pantalla aparte; se decide antes de programar y se anota acá.
- **Criterios de Aceptación:**
  - **AC1:** top-5 por rubro (puntos, rebotes, EFF) de los jugadores del club activo y al menos un
    gráfico de tendencia.
  - **AC2:** barra común con «Todos» en todo: resume toda la historia del club.
  - **AC3:** PJ y el aviso de muestra chica en cada tabla y gráfico.
- **Testing Mínimo:** _manual guiado_ con filtros.
- **Archivos:** `src/infraestructura/ui/flet/screens/dashboard_screen.py`, menú lateral y
  composition root.

#### US-308 — Filtros Ampliados en la Pantalla de Líderes

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-205, US-306 · **Toca la
  base:** no
- **Objetivo:** que `LideresScreen` use los filtros nuevos de la US-306.
- **Criterios de Aceptación:** **AC1:** selector de varios años y de condición (local, visitante o
  todos); cambiar un filtro vuelve a llamar al caso de uso y actualiza `tabla_datos`.
- **Testing Mínimo:** _manual guiado_.
- **Archivos:** `src/infraestructura/ui/flet/screens/lideres_screen.py`.

### Épica H3-E2: Reportería y Exportación (v2.2.0)

#### US-302 — Base de Informes PDF

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** — (ADR-005 aprobado) · **Toca
  la base:** no
- **Objetivo:** un generador de PDF que resuelva el formato una sola vez, para todos los informes.
- **Entrega:** `PDFReportGenerator` (recibe título, bloques de texto, tablas e imágenes y devuelve el
  PDF). Lo usan la US-309 y la US-312.
- **Criterios de Aceptación:**
  - **AC1 — Mismo estilo que la app:** color principal, letra y logo salen de `estilo.py` (US-111).
    Siempre en claro, aunque la app esté en modo oscuro, porque se imprime. El aspecto objetivo está
    en el muestrario de la US-111.
  - **AC2 — Cortes de página:** una tabla que no entra en una hoja sigue en la siguiente
    **repitiendo el encabezado** (`repeatRows` de ReportLab); cada hoja lleva el logo, el tipo de
    informe y «Página N de M».
  - **AC3 — Tablas anchas:** más de ~14 columnas numéricas va en hoja horizontal o partida en
    bloques temáticos (tiro: T2, T3, TL, eFG%, TS%; juego: REB, AST, ROB, PÉR; impacto: EFF, PER,
    +/-). Nunca se achica la letra hasta volverla ilegible.
  - **AC4 — Glosario:** recibe las métricas usadas y agrega al final su nombre y fórmula.
- **Testing Mínimo:** una tabla que ocupa dos páginas repite el encabezado en la segunda (extrayendo
  el texto del PDF); el PDF abre con un lector estándar.
- **Archivos:** `src/infraestructura/reports/pdf_generator.py`, `pyproject.toml`/`uv.lock`
  (+ reportlab), `tests/integration/test_pdf_generator.py`.

#### US-309 — Informe PDF de un Partido

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-302, US-224, US-301 · **Toca
  la base:** no
- **Objetivo:** emitir el informe formal de un partido para el cuerpo técnico.
- **Narrativa:** Como DT, quiero exportar el boxscore a PDF para compartirlo con mi cuerpo técnico
  o imprimirlo.
- **Entrega:** `ExportarReporteUseCase` con `ExportarReporteDTO` y `ReporteResponseDTO`. Lo usa la
  US-310.
- **Criterios de Aceptación:**
  - **AC1 — Resumen primero:** la primera página resume (resultado, 4 o 5 números clave y un
    gráfico); el detalle (boxscore y métricas de la US-224) va en las siguientes.
  - **AC2 — Nombre:** `boxscore_YYYY-MM-DD_Local_vs_Visitante.pdf`, en `~/.statspro/exports/`
    (ruta en `config/rutas.py`, creada si no existe).
  - **AC3 — Robustez:** ruta sin permisos o disco lleno → error controlado con mensaje de qué hacer,
    no un crash. Queda en el log con resultado (regla de la sección 6).
  - **AC4:** el glosario incluye cada métrica que aparece en las tablas.
- **Fuera de alcance:** el informe de temporada (lo nombraba el objetivo viejo, sin criterios). Si
  hace falta, es una historia nueva sobre la US-302.
- **Testing Mínimo:** _integración_: PDF completo desde un `idPartido` de `seed.sql` (válido, nombre
  y ruta esperados); ruta sin permisos → excepción controlada.
- **Archivos:** `src/aplicacion/casos_uso/exportar_reporte.py`, `src/aplicacion/dtos/reporte_dto.py`,
  `src/config/rutas.py`, `tests/integration/test_pdf_export.py`.

#### US-310 — Botón "Exportar PDF" en el Detalle de Partido

- **Esfuerzo:** XS (menos de 1 día) · **Prioridad:** Alta · **Depende de:** US-309 · **Toca la
  base:** no
- **Objetivo:** que el DT exporte el informe desde la pantalla del partido.
- **Criterios de Aceptación:** **AC1:** botón en `DetallePartidoScreen`; al terminar muestra dónde
  quedó el archivo, y los errores de I/O, en pantalla.
- **Testing Mínimo:** _manual guiado_.
- **Archivos:** `src/infraestructura/ui/flet/screens/detalle_partido_screen.py`.

### Épica H3-E3: Inteligencia de Scouting (v3.0.0)

#### US-303 — Caso de Uso de Scouting del Rival

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Depende de:** US-221, US-222, US-218,
  US-202 · **Toca la base:** no
- **Objetivo:** armar un reporte táctico del rival antes del partido, con su historial de la
  temporada.
- **Entrega:** `GenerarScoutingRivalUseCase` y `ScoutingDTO`. Los usan la US-311 y la US-312.
- **Alcance:** sale de `get_partidos_club` (US-221), la misma agregación que usa la comparativa
  (US-227): no se construye un segundo camino para calcular lo mismo.
- **Criterios de Aceptación:**
  - **AC1:** ventana de los últimos _N_ partidos, configurable.
  - **AC2:** patrones: rachas (victorias o derrotas seguidas), tendencia de tiro y pérdidas
    recurrentes, como funciones puras.
  - **AC3:** filtros de competencia y categoría consistentes con la US-221.
  - **AC4:** si el rival tiene partidos con cuartos, en qué cuarto anota y recibe más, «sobre N de
    M partidos» (US-218, US-222).
- **Testing Mínimo:** _unitario_ de rachas y tendencias; _integración_ con al menos 10 partidos del
  rival, filtros y ventana N.
- **Archivos:** `src/aplicacion/casos_uso/generar_scouting_rival.py`,
  `src/aplicacion/dtos/scouting_dto.py`, `tests/integration/test_scouting_rival.py`.

#### US-311 — Pantalla de Scouting

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-303, US-225 · **Toca la
  base:** no
- **Objetivo:** consultar el scouting desde la GUI.
- **Criterios de Aceptación:** **AC1:** elegir **Rival**, la barra común y la ventana de **últimos
  _N_ partidos**; muestra conclusiones destacadas y los datos de los que salen.
- **Testing Mínimo:** _manual guiado_.
- **Archivos:** `src/infraestructura/ui/flet/screens/scouting_screen.py`, menú lateral y composition
  root.

#### US-312 — Exportar el Scouting a PDF

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Baja · **Depende de:** US-303, US-302, US-311 · **Toca
  la base:** no
- **Objetivo:** llevar el scouting impreso al partido.
- **Criterios de Aceptación:** **AC1:** botón en `ScoutingScreen`; usa `PDFReportGenerator` con
  conclusiones y datos fuente citados, en `~/.statspro/exports/`.
- **Testing Mínimo:** _integración_: PDF generado desde un scouting de `seed.sql`.
- **Archivos:** `src/aplicacion/casos_uso/exportar_scouting.py`,
  `src/infraestructura/ui/flet/screens/scouting_screen.py`.

---

## 12. Hito 4 — Interfaz Multiplataforma y Entrega (v4.0.0)

**Objetivo del hito:** completar la GUI Flet (perfil de jugador, tema, adaptación a mobile),
cerrar el hardening de seguridad, garantizar continuidad operativa con backup y restauración, y
distribuir la aplicación también en Android.

**Versiones:** H4-E1 → **v3.1.0** · H4-E2 → **v3.2.0** · H4-E3 → **v3.3.0** · H4-E4 → **v4.0.0**
(cierra el hito).

**Épicas:** 4 · **Historias:** 18 · **Esfuerzo total estimado:** ~38 días·persona

**Decisión previa requerida:** ADR-006 (seguridad) sigue con dos preguntas abiertas: viabilidad de
SQLCipher en Android (bloquea la US-416) y fuente de la lista de contraseñas comprometidas (bloquea
la US-413). ADR-002 (Flet) está aprobado.

> **Rearmado (2026-11-27):** las US-401 a US-404 se dividieron como las del Hito 2. Cambios de fondo:
>
> - Aparece **US-412 (cambio de contraseña)**: la US-403 pedía aplicar la política "en registro y
>   cambio", pero ninguna historia creaba el cambio de contraseña.
> - El arranque en menos de 3 segundos en mobile pasa de la US-401 a la US-404: no se puede medir
>   en mobile antes de tener el APK.
> - El "checklist de estabilización" (AC4 de la vieja US-402) pasa al proceso de cierre de hito
>   (sección 15), porque vale para todos los hitos.
>
> **Hallazgo de transcripción (se mantiene):** el `.md` del submódulo solo tenía la US-401; las
> épicas H4-E2, H4-E3 y H4-E4 se completaron con el LaTeX. Ver sección 20.

### Mapa de dependencias del Hito 4

| US     | Qué deja hecho                                            | Depende de                     | Tamaño | Sale de |
| ------ | --------------------------------------------------------- | ------------------------------ | ------ | ------- |
| US-401 | Modo claro/oscuro según el sistema                        | —                              | S      | US-401  |
| US-405 | Diseño adaptable a pantallas de 1080p y 720p              | US-401                         | M      | US-401  |
| US-406 | Validación visual de formularios en todas las pantallas   | US-405                         | S      | US-401  |
| US-407 | Trayectoria de un jugador por año, competencia y categoría | US-220                        | S      | US-301  |
| US-408 | `PlayerProfileScreen`                                     | US-407, US-305, US-304, US-225 | M      | US-401  |
| US-409 | Versión e ícono visibles en la app                        | —                              | S      | US-404  |
| US-402 | Exportar un backup con metadata                           | US-208                         | S      | US-402  |
| US-410 | Restaurar un backup                                       | US-402, US-204                 | M      | US-402  |
| US-411 | Pantalla de copias de seguridad                           | US-402, US-410                 | S      | US-401  |
| US-403 | Política de contraseñas fuertes                           | —                              | S      | US-403  |
| US-412 | Cambio de contraseña                                      | US-403                         | S      | nueva   |
| US-413 | Lista de contraseñas comprometidas                        | US-403, ADR-006                | M      | US-403  |
| US-414 | Hash con Argon2/bcrypt y migración de hashes viejos       | ADR-006                        | S      | US-403  |
| US-415 | Expiración de la sesión recordada                         | —                              | S      | US-403  |
| US-416 | Cifrado opcional de la base (SQLCipher)                   | US-208, ADR-006                | M      | US-403  |
| US-404 | App de Android en el release                              | US-405                         | M      | US-404  |
| US-417 | macOS en el release                                       | —                              | S      | US-404  |
| US-418 | Guía de instalación por plataforma                        | US-404 (y US-417, si se hace)  | S      | US-404  |

### Épica H4-E1: Interfaz de Usuario Adaptable (v3.1.0)

> **Cambio de alcance (2026-10-31, se mantiene):** las pantallas que la vieja US-401 creaba ya nacen
> en otras historias y acá **no se reimplementan**: `GameEntryScreen` → `CargaPartidoScreen`
> (US-108); `ImportScreen` (US-217 y US-207); `StatsTableComponent` → `tabla_datos.py` (US-107);
> `DashboardScreen` y `ChartComponent` (US-307 y US-304). La UI no tiene lógica de negocio: invoca
> casos de uso por inyección de dependencias.

#### US-401 — Modo Claro y Oscuro Según el Sistema

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** — · **Toca la base:** no
- **Objetivo:** que la app siga la preferencia de tema del sistema.
- **Criterios de Aceptación:**
  - **AC1:** los colores de claro y oscuro viven en `estilo.py`; ninguna pantalla define colores
    propios (DoD 9).
  - **AC2:** los gráficos en pantalla usan la paleta del tema (`ChartGenerator` recibe la paleta);
    los PDF siguen siempre en claro.
- **Testing Mínimo:** _manual guiado_ recorriendo las pantallas en los dos temas.
- **Archivos:** `src/infraestructura/ui/flet/estilo.py`, `src/infraestructura/analytics/chart_generator.py`.

#### US-405 — Diseño Adaptable a 1080p y 720p

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-401 (las dos tocan
  `estilo.py` y `crear_pagina`: van una después de la otra) · **Toca la base:** no
- **Objetivo:** que todas las pantallas se acomoden solas a una PC (1080p) y a un celular (720p).
- **Criterios de Aceptación:** **AC1:** se resuelve en `crear_pagina` y `crear_formulario`, no
  pantalla por pantalla. **AC2:** ninguna pantalla necesita scroll horizontal en 720p salvo las
  tablas anchas, que scrollean dentro de su contenedor.
- **Testing Mínimo:** _manual guiado_ achicando la ventana de escritorio a 720p en cada pantalla (en
  un celular de verdad se prueba en la US-404).
- **Archivos:** `src/infraestructura/ui/flet/components/` (`crear_pagina`, `crear_formulario`).

#### US-406 — Validación Visual de Formularios

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-405 (toca todas las
  pantallas: va al final de la épica para no chocar con nadie) · **Toca la base:** no
- **Objetivo:** que los errores de un formulario aparezcan en el campo, no en un modal genérico.
- **Criterios de Aceptación:** **AC1:** repaso de todos los formularios desde la US-105: cada error
  de validación se muestra en su campo.
- **Testing Mínimo:** _unitarias_ de los validadores y de la navegación entre estados de pantalla.
- **Archivos:** `src/infraestructura/ui/flet/components/formulario.py`, `tests/unit/test_flet_validators.py`.

#### US-407 — Trayectoria de un Jugador

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-220 · **Toca la base:** no
- **Objetivo:** la vista longitudinal de un jugador a través de categorías y temporadas (ej. cómo
  rindió en U15 y cómo le va en U17 este año).
- **Entrega:** `VerTrayectoriaJugadorUseCase` y `TrayectoriaJugadorDTO`. Los usa la US-408.
- **Criterios de Aceptación:** **AC1:** una fila por año, competencia y categoría (un año con dos
  categorías ocupa dos filas), con PJ, usando el historial de `jugadorClub` para el club de cada
  fila.
- **Testing Mínimo:** _integración_ con un jugador de más de una categoría y temporada en `seed.sql`.
- **Archivos:** `src/aplicacion/casos_uso/ver_trayectoria_jugador.py`,
  `tests/integration/test_trayectoria_jugador.py`.

#### US-408 — Perfil de Jugador

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Depende de:** US-407, US-305, US-304,
  US-225 · **Toca la base:** no
- **Objetivo:** ver en una pantalla la carrera y la evolución de un jugador.
- **Narrativa:** Como DT, quiero ver la trayectoria de un jugador y si viene mejorando.
- **Criterios de Aceptación:** **AC1:** se elige el **Jugador** con búsqueda y se le aplica la barra
  común: con todo en «Todos» muestra la carrera completa. **AC2:** trayectoria (US-407) y un
  gráfico de evolución (US-305).
- **Testing Mínimo:** _manual guiado_: Tablero → carga de partido → perfil del jugador.
- **Archivos:** `src/infraestructura/ui/flet/screens/player_profile_screen.py`, menú lateral y
  composition root.

#### US-409 — Versión e Ícono Visibles en la App

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** — · **Toca la base:** no
- **Objetivo:** que el usuario sepa qué versión tiene instalada y la app se reconozca por su ícono.
- **Criterios de Aceptación:**
  - **AC1:** `AcercaDeScreen` muestra la versión, que coincide con el tag del release. Sale de
    `config.version.VERSION` (agregada en el spike de aviso de versión nueva, 2026-11-28): la app
    empaquetada no trae los metadatos del paquete, y el job `version` de `release.yml` frena el
    release si `VERSION` no coincide con el tag.
  - **AC2:** la ventana usa el ícono de la app también en Linux (`page.window.icon`), si no sale
    solo.
- **Testing Mínimo:** _manual guiado_ con el binario de un _pre-release_.
- **Archivos:** `src/infraestructura/ui/flet/screens/acerca_de_screen.py`, menú lateral.

### Épica H4-E2: Resiliencia y Backup (v3.2.0)

#### US-402 — Exportar un Backup con Metadata

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-208 (`crear_copia`) · **Toca
  la base:** no (la lee)
- **Objetivo:** que el usuario saque una copia completa de su base para guardarla donde quiera.
- **Entrega:** `ExportarBackupUseCase`. Lo usan la US-410 (formato) y la US-411.
- **Criterios de Aceptación:**
  - **AC1:** la copia (`VACUUM INTO`, ADR-008) va con su metadata: versión de la app, última
    migración aplicada, fecha y hora y hash SHA-256 del archivo.
  - **AC2:** se registra en el log con resultado.
- **Testing Mínimo:** _integración_: el backup abre, tiene las mismas filas que la base y el hash
  coincide.
- **Archivos:** `src/aplicacion/casos_uso/exportar_backup.py`,
  `src/infraestructura/persistencia/backup_service.py`, `tests/integration/test_backup_restore.py`.

#### US-410 — Restaurar un Backup

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-402, US-204 · **Toca la
  base:** reemplaza el archivo, siempre con una copia de seguridad de la actual
- **Objetivo:** volver a una copia anterior sin arriesgar los datos actuales.
- **Criterios de Aceptación:**
  - **AC1:** se verifica el hash antes de tocar nada; un backup dañado se rechaza.
  - **AC2:** antes de reemplazar, se copia la base actual (`crear_copia`, US-208). Si algo falla
    después, se vuelve a esa copia.
  - **AC3:** un backup de una versión anterior se restaura y se le aplican las migraciones que le
    faltan (US-204); uno de una versión más nueva se rechaza.
  - **AC4:** verificación después de restaurar: conteo de filas de las tablas críticas y un
    checksum de los datos clave contra la metadata.
  - **AC5:** funciona sobre una base vacía y sobre una con datos. Al terminar, la app vuelve a
    abrir la conexión y pide login.
- **Testing Mínimo:** _integración_: exportar → restaurar → mismos datos; restaurar un backup de
  versión anterior (migra); uno más nuevo (rechazado, base intacta); un fallo a mitad de camino
  (vuelve a la copia); después del restore, login, carga de partido y PDF siguen andando.
- **Archivos:** `src/aplicacion/casos_uso/restaurar_backup.py`,
  `src/infraestructura/persistencia/backup_service.py`, `tests/integration/test_backup_restore.py`.

#### US-411 — Pantalla de Copias de Seguridad

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-402, US-410 · **Toca la
  base:** no (usa los casos de uso)
- **Objetivo:** exportar y restaurar desde la GUI.
- **Criterios de Aceptación:** **AC1:** entrada "Copias de seguridad" en el menú; exportar con
  `FilePicker` para elegir dónde guardar; restaurar con confirmación explícita (`pedir_confirmacion`)
  que diga qué se reemplaza. **AC2:** errores en pantalla, sin traceback.
- **Testing Mínimo:** _manual guiado_ del ciclo completo, también en Android (US-404).
- **Archivos:** `src/infraestructura/ui/flet/screens/backup_screen.py`, menú lateral y composition
  root.

### Épica H4-E3: Seguridad de Datos Local (v3.3.0)

**Regla de compatibilidad para esta épica:** los usuarios de versiones anteriores tienen que seguir
entrando con su contraseña y sus datos. Ningún cambio de seguridad puede dejarlos afuera ni tocar el
esquema (sección 3).

#### US-403 — Política de Contraseñas Fuertes

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** — · **Toca la base:** no
- **Objetivo:** que las contraseñas nuevas sean difíciles de adivinar.
- **Entrega:** `credential_policy.validar(contrasena)`. La usan el registro, la US-412 y la US-413.
- **Criterios de Aceptación:**
  - **AC1:** mínimo **12 caracteres**, con mayúscula, número y símbolo; el mensaje dice qué falta.
  - **AC2:** se aplica al registro. Las cuentas existentes con contraseñas más cortas siguen
    entrando.
- **Testing Mínimo:** _unitarias_ de cada regla.
- **Archivos:** `src/infraestructura/security/credential_policy.py`, `tests/unit/test_credential_policy.py`.

#### US-412 — Cambio de Contraseña

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** US-403 · **Toca la base:** no
  (actualiza el hash del usuario)
- **Objetivo:** que un usuario cambie su contraseña desde la app.
- **Criterios de Aceptación:**
  - **AC1:** pide la contraseña actual y la nueva dos veces; la nueva pasa por `credential_policy`.
  - **AC2:** el evento queda en el log sin datos sensibles (los fallos de login ya se registran
    desde la US-110).
- **Testing Mínimo:** _unitarias_ del caso de uso (actual incorrecta, nueva débil, camino feliz);
  _integración_: después del cambio, la contraseña vieja no entra y la nueva sí.
- **Archivos:** `src/aplicacion/casos_uso/cambiar_contrasena.py`,
  `src/infraestructura/ui/flet/screens/cambiar_contrasena_screen.py`, menú y composition root.

#### US-413 — Lista de Contraseñas Comprometidas

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Depende de:** US-403, ADR-006 (fuente de la
  lista; se cierra al empezar) · **Toca la base:** no
- **Objetivo:** bloquear contraseñas que ya circulan en filtraciones.
- **Criterios de Aceptación:**
  - **AC1:** una lista local, empaquetada con la app, bloquea su uso en `credential_policy` (así
    alcanza al registro y al cambio sin tocarlos).
  - **AC2:** procedimiento de actualización mensual en `docs/security/`, con pasos reproducibles.
  - **AC3:** el CI valida la versión vigente y el checksum de la lista en cada PR.
- **Testing Mínimo:** _unitarias_: una contraseña de la lista se rechaza; checksum alterado → CI en
  rojo.
- **Archivos:** `src/infraestructura/security/compromised_password_store.py`,
  `docs/security/password_compromised_update_procedure.md`, `.github/workflows/MainAction.yml`.

#### US-414 — Hash con Argon2 o bcrypt y Migración de Hashes Viejos

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Depende de:** ADR-006 · **Toca la base:** no
  (el algoritmo va como prefijo dentro del mismo texto del hash)
- **Objetivo:** pasar a un hash más robusto sin obligar a nadie a cambiar su contraseña.
- **Criterios de Aceptación:**
  - **AC1:** bcrypt o Argon2 con salt único, sin cambiar la interfaz `PasswordHasher`.
  - **AC2 — Migración perezosa:** al entrar con un hash `pbkdf2` válido, se guarda el hash nuevo. Los
    dos formatos se verifican mientras queden usuarios viejos.
  - **AC3:** la librería elegida compila con `flet build` en Windows, Linux y Android; si no compila
    en Android, se elige la otra antes de mergear.
- **Testing Mínimo:** ciclo hash → verificación; un usuario con hash `pbkdf2` entra y queda migrado.
- **Archivos:** `src/infraestructura/security/` (hasher), `pyproject.toml`/`uv.lock`,
  `docs/adr/ADR-006-seguridad-cifrado.md`.

#### US-415 — Expiración de la Sesión Recordada

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** — · **Toca la base:** no (el
  archivo de sesión es aparte, en `~/.statspro/`)
- **Objetivo:** cerrar el riesgo aceptado en la US-106: hoy "Recordarme" no expira.
- **Criterios de Aceptación:**
  - **AC1:** la sesión recordada expira después de un tiempo configurable en `settings.py`.
  - **AC2:** cerrar sesión la revoca de inmediato; la limpieza es idempotente.
  - **AC3 — Compatibilidad:** un archivo de sesión del formato viejo (sin fecha) se trata como
    vencido: pide login, sin error.
- **Testing Mínimo:** _unitarias_ con reloj falso; archivo del formato viejo.
- **Archivos:** `src/aplicacion/servicios/session_manager.py`, `src/config/settings.py`,
  `tests/unit/test_session_manager.py`.

#### US-416 — Cifrado Opcional de la Base (SQLCipher)

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Baja · **Depende de:** US-208, ADR-006 (viabilidad en
  Android) · **Toca la base:** convierte el archivo, no el esquema
- **Objetivo:** que quien quiera tenga la base cifrada, sin romper la API del `DatabaseManager`.
- **Criterios de Aceptación:**
  - **AC1:** se activa desde la configuración; nunca se cifra una base sin que el usuario lo pida.
  - **AC2:** la conversión arma un archivo nuevo (`sqlcipher_export`), compara el conteo de filas con
    el original y recién entonces lo reemplaza. Antes de empezar se hace una copia (`crear_copia`,
    US-208), que se borra cuando la verificación da bien.
  - **AC3:** si el ADR-006 concluye que no es viable en Android, la opción no aparece en Android.
- **Testing Mínimo:** acceso a la base con y sin cifrado; una conversión que falla deja la base
  original intacta.
- **Archivos:** `src/infraestructura/security/db_encryption_adapter.py`,
  `src/infraestructura/persistencia/database_manager.py`.

### Épica H4-E4: Empaquetado y Distribución (v4.0.0)

> **Contexto (se mantiene):** el release de escritorio para Windows y Linux (`release.yml`, binarios
> por tag) y el `CHANGELOG.md` ya existen desde la US-109, con `flet build`. **iOS está fuera de
> alcance (2026-10-03):** compilar y firmar exige una Mac con Xcode y una cuenta de Apple Developer
> (u$s99/año), un costo que nadie asumió; si se retoma, es un hito aparte. El spike
> `docs/spike/spike_build_cli.md` sigue valiendo para el paquete raíz `statspro`, la base en la
> carpeta de datos del usuario y los `.sql` como datos del paquete.

#### US-404 — App de Android en el Release

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Depende de:** US-405 · **Toca la base:** no
- **Objetivo:** publicar un APK instalable junto a los binarios de escritorio.
- **Criterios de Aceptación:**
  - **AC1:** APK instalable en Android 9+ sin dependencias adicionales, publicado en el GitHub
    Release junto al `.exe`, el `.zip` y el `.deb` (`flet build apk` en `release.yml`).
  - **AC2:** la base y los logs van en la carpeta de datos de la app en Android (`config/rutas.py`), y
    las migraciones (US-204) corren ahí.
  - **AC3 — Arranque:** **menos de 3 segundos** en un celular de referencia (NFR-5).
  - **AC4:** el APK usa el ícono de la app.
- **Testing Mínimo:** instalar en un dispositivo o emulador y recorrer: login → carga de partido →
  importación de un Excel desde `ImportScreen` → backup.
- **Archivos:** `empaquetado/build_android.py`, `.github/workflows/release.yml`, `src/config/rutas.py`.

#### US-417 — macOS en el Release

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Baja · **Depende de:** — · **Toca la base:** no
- **Objetivo:** sumar macOS a la matriz de `release.yml` (NFR-1).
- **Decisión a tomar al empezar:** si se hace. El binario sale sin firmar (macOS lo advierte al
  abrir), porque firmar cuesta la cuenta de Apple Developer.
- **Criterios de Aceptación:** **AC1:** cada tag genera el binario de macOS con los de Windows y
  Linux. **AC2:** abre sin Python instalado.
- **Testing Mínimo:** abrir el binario en una Mac (o un runner `macos-latest`) y crear un club.
- **Archivos:** `.github/workflows/release.yml`.

#### US-418 — Guía de Instalación por Plataforma

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Depende de:** US-404 (y US-417, si se hace) ·
  **Toca la base:** no
- **Objetivo:** que un DT instale la app sin ayuda.
- **Criterios de Aceptación:** **AC1:** pasos para Windows (instalador y portable), Linux (`.deb`) y
  Android (APK), con capturas; dónde quedan los datos y que desinstalar no los borra.
- **Archivos:** `docs/install-guide.md`.

---

## 13. Definición de "Hecho" (DoD)

Una Historia de Usuario se considera **Hecha** cuando cumple TODOS los siguientes puntos:

1. **Código integrado:** PR chica a `main` con _squash_, revisada por el otro integrante y con título `tipo(alcance): descripción`; `main` queda publicable (sección 5).
2. **Tests pasan:** cobertura ≥80% en lógica de negocio general; ≥95% en componentes críticos (autenticación, persistencia transaccional, rollback, fórmulas estadísticas — ver Catálogo de Criticidad). Todos los tests corren sin errores en CI.
3. **Arquitectura respetada:** ninguna clase en `dominio/` importa de `infraestructura/` ni de librerías externas (`sqlite3`, `pandas`). Verificable con grep o una herramienta de análisis de imports.
4. **SQL verificado:** si la US crea o modifica una vista SQL, la vista está en `views.sql` y existe un test de integración que la consulta con datos de `seed.sql`.
5. **Transacciones:** si la US persiste múltiples tablas (ej. partido + estadísticas), existe un test que verifica que un fallo parcial hace rollback completo.
6. **ADR documentado:** si la US requirió una decisión arquitectónica, el ADR correspondiente está aprobado y en el repositorio.
7. **Sin imports cruzados:** verificado con una herramienta de linting de arquitectura.
8. **Docstring mínimo:** todos los métodos públicos tienen docstring de una línea; los métodos complejos documentan sus parámetros.
9. **Si incluye UI:** validada manualmente en desktop (Windows, y Linux si hay entorno gráfico); desde la US-404 (Hito 4), también en Android. Desde la US-111, la pantalla usa `crear_pagina`, sus formularios usan `crear_formulario` y no define colores ni espaciados propios.
10. **Trazabilidad:** eventos de log relevantes implementados con `correlation_id` (desde la US-110; las historias anteriores usan el logger actual).
11. **Pipeline CI en verde:** lint + tests + cobertura.
12. **Base de datos (desde el Hito 2):** si cambia tablas, lo hace con una migración aditiva nueva y no edita ninguna existente (sección 3); si cambia una vista, ajusta a sus consumidores y sus tests.
13. **Dependencias del PRD al día:** todo lo que la historia usa ya estaba en `main`, y lo que deja hecho para otras figura en su campo **Entrega**. Si cambió algo de eso, se actualizó el PRD en la misma PR.

**El repositorio del agregado tiene su propia interfaz en el dominio**, y **la persistencia fue validada mediante una prueba de integración con SQLite** son, además, dos condiciones que ambas fuentes repiten como base mínima innegociable — se mantienen implícitas en los puntos 3 y 4 de arriba.

---

## 15. Proceso de Liberación de Versiones

> **Cambio (2026-11-27):** desaparecen `develop`, `feature/hitoN` y `feature/epicaN`. Se trabaja
> directo contra `main` con PR chicas (sección 5) y la numeración se ata a hitos y épicas.

### Versionado

`vMAJOR.MINOR.PATCH`, con una convención propia del proyecto. **No es SemVer estricto:** acá el
MAJOR marca el cierre de un hito, no un cambio incompatible. Los datos del usuario nunca se rompen
entre versiones (sección 3).

| Qué se publica                                       | Sube  | Ejemplo                  |
| ---------------------------------------------------- | ----- | ------------------------ |
| Cierre del Hito N (su última épica)                  | MAJOR | H1 → v1.0.0, H2 → v2.0.0 |
| Cierre de una épica que no es la última de su hito   | MINOR | H2-E1 → v1.1.0           |
| Actualización de dependencias o corrección de un bug | PATCH | v1.1.0 → v1.1.1          |

| Hito | Épicas y versión                                                                  |
| ---- | --------------------------------------------------------------------------------- |
| H1   | cierre del hito → **v1.0.0** (la primera versión; los tags `v0.1.0-rc.*` fueron pruebas del workflow) |
| H2   | H2-E1 → v1.1.0 · H2-E2 → v1.2.0 · H2-E3 → **v2.0.0**                              |
| H3   | H3-E1 → v2.1.0 · H3-E2 → v2.2.0 · H3-E3 → **v3.0.0**                              |
| H4   | H4-E1 → v3.1.0 · H4-E2 → v3.2.0 · H4-E3 → v3.3.0 · H4-E4 → **v4.0.0**             |

Si una épica se agrega o se divide, la tabla se corre: la última épica de cada hito siempre da el
MAJOR. La app avisa cuando hay una versión nueva (spike en curso), así que publicar seguido no le
complica la vida a nadie.

### Ramas

```text
feature/usNNN-descripcion ──squash──▶ main ──(cierre de épica) tag vX.Y.0──▶ release.yml
hotfix/descripcion (desde el último tag) ──tag vX.Y.Z──▶ release.yml
                                          └──merge commit──▶ main
```

| Rama                        | Propósito                                                                                   | Su PR se mergea con             |
| --------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------- |
| `main`                      | Integración y releases. Siempre publicable: cada PR la deja andando. Nunca se pushea directo. | —                              |
| `feature/usNNN-descripcion` | Una historia, o una parte chica de ella. Sale de `main` actualizado.                         | **_squash_** (hacia `main`)    |
| `release/vX.Y.Z`            | Solo el cambio de versión y el changelog.                                                    | **_squash_** (hacia `main`)    |
| `hotfix/descripcion`        | Bug de una versión publicada, o una actualización que no puede esperar. Sale del **último tag**. | **_merge commit_** (hacia `main`) |

**Por qué el hotfix sale del tag y no de `main`:** `main` ya tiene historias de la épica en curso
que todavía no se publicaron. Un patch armado desde `main` publicaría una épica a medias con un
número de corrección.

**Por qué el hotfix vuelve con _merge commit_:** el tag del patch queda en la rama del hotfix. Con
_squash_, ese commit no llegaría a `main`, y git-cliff (que arma el changelog recorriendo los tags
alcanzables desde `main`) no vería el patch.

**El _squash_ en las PR de trabajo** junta los commits de trabajo ("wip", "fix typo") en uno solo,
con el título del PR como mensaje (por eso el título sigue Conventional Commits, AC11 de la US-109).
Así a `main` llega un commit por PR, y git-cliff arma el changelog con un renglón por cada uno.

### Dependabot

Una PR por semana como máximo por cada ecosistema (`uv`, `github-actions`, `docker`), con **todas**
sus actualizaciones juntas (`.github/dependabot.yml`). Dependabot no puede juntar ecosistemas
distintos en una sola PR. Las alertas de seguridad llegan en PR aparte, porque no esperan al lunes.

- Su PR se revisa y se mergea a `main` como cualquier otra (_squash_). No publica nada por sí sola:
  viaja en la próxima versión.
- Si tiene que llegar a los usuarios antes (seguridad, un bug de una librería que usa la app), se
  publica como **patch** con el procedimiento de hotfix: se hace _cherry-pick_ del commit de
  Dependabot sobre la rama que sale del último tag.

### Release de una épica (o de un hito)

1. **Cuando se mergea la última historia de la épica:** rama `release/vX.Y.Z` desde `main`. Subir
   `version` en `pyproject.toml` y regenerar el changelog con `make changelog VERSION=X.Y.Z`;
   revisar el texto generado (no se edita a mano: un commit que sobra se saca con `.cliffignore`,
   ver la sección 11 del RUNBOOK). PR `chore(release): vX.Y.Z` con el CI entero en verde; _squash_.
2. **(Recomendado) Probar el release:** `git tag vX.Y.Z-rc.1` sobre ese commit de `main` y
   `git push origin vX.Y.Z-rc.1`: `release.yml` arma un _pre-release_. Probar los binarios en una
   máquina sin Python (AC14 de la US-109). Si algo falla, se corrige con una PR y se repite con
   `-rc.2`.
3. **Taggear:** `git checkout main && git pull`, `git tag vX.Y.Z`, `git push origin vX.Y.Z`.
4. **Automático (`release.yml`, US-109):** tests → verifica que el tag coincida con
   `pyproject.toml` → compila con `flet build` → crea el GitHub Release con los binarios y la
   sección del changelog como notas.
5. **Verificar** en GitHub el tag, las notas y los binarios.
6. **Si cierra un hito:** antes del paso 1, el **checklist de estabilización**: rendimiento (los
   tiempos de los NFR), sin errores críticos abiertos, y una regresión manual de los flujos
   principales (login, carga de partido, importación, informe PDF y backup, según lo que ya
   exista). Se cierra el milestone del hito.

### Hotfix (patch)

1. `git checkout -b hotfix/descripcion-breve vX.Y.Z` (el último tag publicado).
2. Aplicar la corrección mínima con un test de regresión que falla sin el fix (o _cherry-pick_ del
   commit de Dependabot).
3. En la misma rama, subir el PATCH en `pyproject.toml` y regenerar el changelog
   (`make changelog VERSION=X.Y.Z+1`).
4. Abrir la PR `hotfix/... → main` para que la revise el otro integrante y corra el CI.
5. Con la PR aprobada: `git tag vX.Y.Z+1` sobre el último commit de la rama y `git push origin
   vX.Y.Z+1`; `release.yml` publica el patch.
6. Mergear la PR con **_merge commit_**. Si choca en `pyproject.toml` o en `CHANGELOG.md`, se queda
   con la versión del hotfix y se regenera el changelog.

### Formato del `CHANGELOG.md`

Estándar **Keep a Changelog** (keepachangelog.com): una sección `[X.Y.Z] - YYYY-MM-DD` por release,
con subsecciones en castellano (Agregado, Cambiado, Corregido, Seguridad). Lo genera git-cliff a
partir de los commits (`feat:` → Agregado, `fix:` → Corregido, etc., configurado en `cliff.toml`):
no se edita a mano, se regenera entero en cada versión y solo se revisa el texto antes del release.

> **Ojo con los patch de dependencias:** hoy `cliff.toml` deja afuera los commits `chore` y `build`,
> que incluyen los de Dependabot (`chore(deps)`). Un patch que solo trae dependencias no tendría
> sección en el changelog, y `release.yml` falla sin publicar si la versión no tiene su sección.
> Antes del primer patch de dependencias hay que sumar a `cliff.toml` una sección "Dependencias" para
> `chore(deps)`.

### Transición al flujo nuevo (fuera de este PRD, pendiente)

Este PRD ya describe el flujo nuevo. Para que el repositorio coincida falta:

- Borrar `develop` (y las `feature/epica*`/`feature/hito*` que queden) después de mergear lo que
  tengan a `main`.
- `.github/workflows/MainAction.yml`: sacar `develop`, `feature/epica*` y `feature/hito*` de
  `branches`.
- Ruleset de GitHub "main y develop" → solo `main`; _squash_ y _merge commit_ habilitados (el
  segundo, para los hotfix).
- `RUNBOOK.md` (ramas, ruleset y release) y el comentario de `Makefile` sobre `develop -> main`.
- `cliff.toml`: la sección "Dependencias" del punto anterior.
- Milestones `M1 - v1.0.0` … `M4 - v4.0.0`, y una issue por cada historia nueva de los Hitos 2 a 4
  (las divididas se cierran apuntando a sus reemplazos).

---

## 16. Roadmap Futuro (Hitos 5–9, visión de producto)

> Los hitos 5–9 son **visión de producto, no compromisos de entrega**. Se refinan y priorizan según feedback real de usuarios al cierre de la v4.0.0. Cada hito cierra con su MAJOR (Hito N → vN.0.0, sección 15). Se transcriben completos porque forman parte del PRD original, aunque no son parte del plan de trabajo actual.

- **Hito 5 · Ecosistema Conectado y Colaborativo (v5.0.0):** romper el aislamiento local. Sincronización cloud híbrida (FastAPI + PostgreSQL, manteniendo la app 100% funcional offline); exportación de "Match Cards" para redes sociales; base de datos compartida de scouting entre DTs (con consentimiento explícito). Investigación previa de la sincronización (local-first con Supabase como alternativa): ver `docs/spike/spike_supabase.md`.
- **Hito 6 · Inteligencia Táctica con IA (v6.0.0):** pasar de análisis descriptivo a prescriptivo. Motor de recomendación de quinteto (scikit-learn/XGBoost); detección automática de patrones (rachas de tiro, degradación defensiva por fatiga, pérdidas en momentos de presión — z-score, ARIMA); explicabilidad con SHAP values; integración de video scouting; marco de experimentación A/B de estrategias.
- **Hito 7 · Live Stats y Cancha Digital (v7.0.0):** captura de datos en tiempo real. Módulo de captura en vivo en tablet (<200ms por acción); dashboard en vivo para el banco (PPP por posesión, eFG% acumulado, +/- por jugador); mapa de tiro interactivo por zonas; control de carga/fatiga con alertas.
- **Hito 8 · Plataforma Federativa y Competición Multi-Liga (v8.0.0):** escalar de club a federación. Integración con APIs federativas (CABB, FIBA); vista multi-club para oficiales de liga; reportería regulatoria automatizada; benchmarking anónimo inter-club; gestión de árbitros y planilleros.
- **Hito 9 · Multi-Deporte y Ecosistema de Formación (v9.0.0):** extender más allá del básquet. Motor estadístico multi-deporte configurable (voleibol, fútbol sala, handball); seguimiento de desarrollo a largo plazo entre categorías; modelado de riesgo de lesión por carga acumulada; módulo de formación para entrenadores; portal de seguimiento para familias (solo lectura, opt-in).

---

## 18. ADRs Pendientes — tabla de bloqueo por hito

(Duplicado intencional de la sección 8, en el formato de tabla de bloqueo que traían ambas
fuentes, por si se prefiere consultar esta vista en vez de la de "Registro de Decisiones":)

| ADR     | Título                   | Bloquea       | Decisión recomendada                                                                                                                  |
| ------- | ------------------------ | ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| ADR-001 | Arquitectura Local-First | Hito 1        | ✅ SQLite + offline-first (ya definido)                                                                                               |
| ADR-002 | Framework UI             | US-105        | ✅ Flet, se descarta Compose Multiplatform; única interfaz desde el 2026-10-31 (ver `docs/adr/ADR-002`)                               |
| ADR-003 | Protocolo de Ingesta     | US-210/US-214 | ⏳ Propuesta con archivos reales: mapeo fijo buscando encabezados por texto; falta elegir la librería de PDF (ver `docs/adr/ADR-003`) |
| ADR-004 | Versionado de DB         | US-204        | ✅ `yoyo-migrations`, solo migraciones aditivas (decidido en el PRD el 2026-11-27; la US-204 actualiza `docs/adr/ADR-004`)            |
| ADR-005 | Reportes PDF             | US-302        | ✅ `reportlab` (ya definido, ver `docs/adr/ADR-005`)                                                                                  |
| ADR-006 | Seguridad y Cifrado      | US-413/414/416 | ✅ v1.0.0: `pbkdf2_hmac` con salt **dinámico**. Hito 4: SQLCipher + bcrypt/argon2, con preguntas abiertas de viabilidad multiplataforma   |
| ADR-007 | Motor de Visualización   | US-301        | ✅ `matplotlib` (ya definido, ver `docs/adr/ADR-007`)                                                                                 |
| ADR-008 | Estrategia de Backup     | Hito 4        | ✅ Export manual con `VACUUM INTO`/backup online de SQLite (ya definido, ver `docs/adr/ADR-008`)                                      |
| ADR-009 | Pipeline CI/CD           | US-109        | ✅ GitHub Actions hosteados por GitHub, ya implementado (ver `docs/adr/ADR-009`)                                                      |

---

## 19. Convenciones rápidas

- **Commits:** `tipo: descripción corta` (`FEAT`, `FIX`, `DOCS`, `STYLE`, `REFACTOR`, `PERF`, `TEST`) — ver `docs/info_modulo/02-reglas.md`.
- **Interfaces de repositorio:** el proyecto usa `ABC`/`@abstractmethod` en la práctica, **no** `typing.Protocol` como sugiere `docs/info_modulo/07-protocolos.md` (que compara ambas). Ambas son válidas — vale un ADR corto para dejarlo asentado.
- **Logging:** `infraestructura/logger.py` (rotación 10MB, 5 backups) con formato JSON, `correlation_id` y redacción de secretos desde la US-110 (`infraestructura/observabilidad.py`, ADR-011) — ver `docs/info_modulo/01-logger.md`. En la aplicación, `logging.getLogger(__name__)`; en infraestructura, `get_logger(__name__)`.
- **Análisis estático:** el proyecto usa `ruff` en la práctica (`pyproject.toml`, `.github/workflows/MainAction.yml`), no `flake8`/`pylint` como sugería el borrador original del Acuerdo de Ingeniería (sección 5) — ya reflejado arriba.
