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
9. [Hito 1 — Núcleo de Datos e Interfaz CLI (v0.1)](#9-hito-1--núcleo-de-datos-e-interfaz-cli-v01)
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
| 5   | Rigidez de plataformas   | El DT no puede integrar datos de Ges Deportivo fácilmente       | Ingesta manual             |

Desglose adicional (basado en encuestas reales a DTs):

- **Interferencia en el juego:** la carga manual en tiempo real distrae al entrenador o requiere una persona dedicada exclusivamente a esa tarea.
- **Ritmo frenético:** la velocidad del básquet genera demoras entre la carga de una estadística y la siguiente.
- **Cálculo manual y falta de tendencias:** los DTs pierden tiempo pasando el boxscore a mano y calculando estadísticas avanzadas por su cuenta; no logran identificar numéricamente hacia dónde van las tendencias del juego.
- **Falta de centralización:** no hay un espacio virtual cómodo para el registro histórico, lo que dificulta comparar rivales o evaluar la evolución de los propios jugadores.
- **Herramientas inflexibles:** las apps existentes no se adaptan a los sistemas de competencia locales, y los datos de plataformas externas (Ges Deportivo) no se integran sin trabajo manual.

**Línea base cuantificada:** carga manual >20-40 min; 0% de automatización de importación Excel; 65% de los usuarios encuestados requieren uso offline; datos aislados por partido sin acumulación histórica.

### 1.2 Visión del producto

Desarrollar una aplicación multiplataforma (PC y Mobile) de ejecución local que centralice el conocimiento deportivo en un motor estadístico profesional, permitiendo una gestión integral **sin necesidad de internet**, con un flujo optimizado mediante la carga de planillas de "Ges Deportivo".

Pilares del producto:

1. **Accesibilidad y flexibilidad:** acceso desde cualquier dispositivo — cancha (celular/tablet) o casa (PC/notebook) para análisis más profundo.
2. **Gestión organizativa completa:** perfil de usuario, club, categorías, competencias y listas de buena fe.
3. **Ingesta de datos automatizada y manual:** además de la carga manual partido a partido, el software interpreta automáticamente planillas Excel de Ges Deportivo.
4. **Generación de estadísticas avanzadas:** motor de análisis que entrega resúmenes y estadísticas acumuladas, tradicionales y avanzadas, individuales y de equipo.
5. **Visualización y toma de decisiones:** comparación de equipos/jugadores, filtros, gráficos claros para identificar tendencias a corto, mediano y largo plazo.

### 1.3 Metas y no metas

**En el alcance (v1.0):**

- **Ingesta multimodal:**
  - _Automática:_ carga de planillas Excel de Ges Deportivo.
  - _Manual:_ formulario para carga post-partido (jugador por jugador).
- **Persistencia local:** base de datos SQLite única por instalación de usuario.
- **Motor estadístico:** análisis de tendencias, PPP, estadistica avanzada y eficiencia con Pandas.
- **Multiplataforma:** ejecución en Windows, Linux, macOS y dispositivos móviles.

**Fuera de alcance (v1.0):**

- **Carga en vivo:** toma de datos en tiempo real durante el partido — se posterga a versiones post-estables (ver Hito 7 en el roadmap futuro).
- **Sincronización cloud:** no se contempla almacenamiento en la nube inicialmente.
- **Importación automática/API:** no hay conexión directa con servidores de Ges Deportivo (solo archivos Excel exportados manualmente por el usuario).
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
| **Analista / Asistente** | Responsable de carga y procesamiento de datos                | Proveer informes rápidos y precisos al DT      | Carga redundante de datos ya existentes en Ges Deportivo |

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

- Relación **1:1** entre `inscripcion` y `listaBuenaFe`.
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
- **Infraestructura** (`src/infraestructura/`): repositorios SQLite, parser Excel (Pandas), UI CLI/GUI y generación de reportes.

### Regla de dependencias

```text
dominio  ←  aplicación  ←  infraestructura
```

`dominio` no puede importar `aplicación` ni `infraestructura`. `aplicación` puede importar `dominio`, pero no `infraestructura`.

### Patrones de diseño

- **Repository Pattern:** abstracción de persistencia por agregado (`UsuarioRepositorio`, `JugadorRepositorio`, etc.).
- **Dependency Injection:** los casos de uso reciben puertos (interfaces), no implementaciones concretas, por constructor.
- **Command Pattern:** CLI extensible por subcomandos sin bloques monolíticos `if/else`.

### Estructura de directorios de referencia

```mermaid
---
config:
  treeView:
    showIcons: true
---
treeView-beta
  src/
    main.py :::highlight icon(logos:python) ## punto de entrada y composition root de la CLI (parser + manejo de errores)
    utils.py ## helpers puros compartidos (id_persistido, abortar, fecha_iso)
    config/
      rutas.py ## rutas de la base, scripts SQL y logs
    dominio/
      entidades/ ## @dataclass puras, sin imports externos
      repositorios/ ## interfaces (ABC) de repositorios
      exceptions.py ## excepciones de negocio
      services/ ## lógica de dominio compleja (opcional)
    aplicacion/
      dtos/ ## dataclasses de entrada/salida entre capas
      services/ ## servicios de aplicación (ej. SessionManager) — pendiente, US-105
      casos_usos/ ## orquestadores (reciben repos por DI), un archivo por acción
    infraestructura/
      logger.py ## ✅ configuración central del logging
      repositorios/ ## implementaciones SQLite de las interfaces de dominio
      persistencia/
        databases_manager.py ## SQLiteManager y abrir_conexion()
        sql/
          schema.sql
          views.sql
          seed.sql
          limpieza.sql
      analytics/ ## motor Pandas
      ingest/ ## parser Excel
      reports/ ## generador PDF
      security/ ## PasswordHasher
      ui/
        cli/ ## interfaz de línea de comandos
          commands/ ## un archivo por acción (club_add.py, jugador_link.py, ...)
          formatters/ ## table_formatter.py (wrapper de tabulate)
        flet/ ## GUI
tests/
  unit/ ## sin DB, con mocks (entidades, casos de uso, comandos CLI, helpers)
  integration/ ## con SQLite real en memoria (repositorios, esquema) y CLI de punta a punta
  conftest.py ## fixtures compartidas y fábricas de datos (**overrides)
```

> **Convención de la CLI: un archivo por acción.** Cada comando vive en su propio archivo de `commands/` (`club_add.py`, `jugador_link.py`, …) y `main.py` lo registra en
> `construir_parser()` con `set_defaults(func=...)`.

### ¿Qué va en cada capa? Guía práctica

**Capa de Dominio (`src/dominio/`)** — el núcleo del sistema. No depende de ninguna tecnología concreta.

- **`entidades/`** — clases Python puras (`@dataclass`) que modelan los conceptos del básquet. Pueden tener métodos con lógica de negocio simple (validaciones, cálculos derivados). **No importan** `sqlite3`, `pandas` ni ningún framework. Ejemplo objetivo: `Jugador` con `calcular_edad()`; `EstadisticaJugador` con `validar_consistencia_puntos()`.
- **`repositorios/`** — interfaces abstractas (`ABC` + `@abstractmethod` en este proyecto — ver nota sobre `Protocol` en sección 19) que definen _qué_ operaciones existen sobre los datos, sin decir _cómo_. Ejemplo real: `JugadorRepositorio` declara `buscar_por_id`, `buscar_por_dni`,
  `guardar`, sin una sola línea de SQL.
- **`exceptions.py`** — errores propios del negocio deportivo: `DNIDuplicadoError`, `JugadorNoHabilitadoError`, `PartidoInvalidoError("El club local no puede ser el visitante")`.

**Capa de Aplicación (`src/aplicacion/`)** — orquesta el dominio para los casos de uso del usuario. No contiene lógica de negocio pura (eso va en dominio) ni detalles técnicos (eso va en infraestructura).

- **`casos_uso/`** — un archivo = una acción del usuario. Cada caso de uso recibe sus dependencias (repositorios, servicios) por constructor y expone un único método `ejecutar(dto)`. Ejemplo: `RegistrarJugadorUseCase.ejecutar(dto)` crea la entidad `Jugador` (que valida sus tipos), la persiste con `repo.guardar` (el repositorio rechaza un DNI duplicado con `DNIDuplicadoError`) y retorna un `JugadorDTO`. Detalle de los 9 casos de uso en `docs/info_modulo/03-casos-de-uso.md`.
- **`dtos/`** — dataclasses simples, sin lógica, que viajan entre la CLI y los casos de uso (`CrearJugadorDTO` entra, `JugadorDTO` sale). Un archivo por entidad, con los DTOs de entrada y de salida juntos.
- **`services/`** — servicios transversales que no pertenecen a un caso de uso específico, como `SessionManager` (sesión persistente) y `ExecutionContext` (propagación de `correlation_id` para logs).

**Capa de Infraestructura (`src/infraestructura/`)** — implementa los contratos del dominio con tecnologías concretas. Es la única capa que puede importar `sqlite3`, `pandas`, `flet`, `bcrypt`, etc.

- **`repositorios/`** — implementaciones SQLite de las interfaces de dominio. Cada clase hereda de su interfaz correspondiente (`SqliteJugadorRepositorio(JugadorRepositorio)`).
- **`persistencia/`** — infraestructura técnica de la base: `database_manager.py` (conexión, inicialización), archivos `.sql` (schema, vistas, seed), migraciones futuras. Sin lógica de negocio.
- **`analytics/`** — `formulas.py` (funciones puras sobre DataFrames), `pandas_analytics_service.py`, `chart_generator.py`.
- **`ingest/`** parser Excel de Ges Deportivo y servicio de ingesta.
- **`reports/`** generadores de PDF y reportería de CLI (leaderboards).
- **`ui/`** — subárbol separado por interfaz: `ui/cli/` y `ui/flet/`. Llaman a casos de uso; nunca acceden a la base de datos directamente.
- **`security/`** — hashing de contraseñas, política de credenciales, adaptador de cifrado de DB.

### Data Transfer Objects (DTOs)

Un **DTO** es una clase simple cuya única responsabilidad es transportar datos entre capas — **no contiene lógica de negocio**.

**¿Por qué se usan?**

- **Desacoplamiento:** la UI no necesita conocer las entidades de dominio, y el dominio no se expone directamente al exterior.
- **Control de la frontera:** el DTO de entrada valida el formato antes de que el caso de uso lo procese; el DTO de salida define exactamente qué información se devuelve.
- **Evolución independiente:** se puede cambiar la entidad de dominio sin romper la UI, y viceversa.

**Patrón de uso:** cada caso de uso recibe un DTO de entrada (datos crudos del usuario) y retorna un DTO de salida (datos procesados para mostrar). Las entidades de dominio **nunca salen** de la capa de aplicación hacia la UI.

**Ejemplo — registrar un jugador:**

- `RegistrarJugadorInputDTO`: `nombre`, `apellido`, `dni`, `fecha_nacimiento`, `club_id`. Solo datos planos, sin métodos.
- El caso de uso recibe este DTO, crea la entidad `Jugador` con las reglas de dominio, y persiste.
- Retorna `JugadorOutputDTO`: `id`, `nombre_completo`, `dni`, `club_nombre`. Solo lo que la CLI/GUI necesita mostrar.

Ubicación: `src/aplicacion/dtos/`. Convención de nombres: `jugador_dto.py` puede contener tanto el DTO de entrada como el de salida para esa entidad.

### Gestión de sesión y club activo

La sesión local persistirá en un archivo JSON en `~/.statspro/session.json` (o `./data/session.json` en desarrollo). El `SessionManager` es el único responsable de leer y escribir este archivo.

**Estructura del archivo de sesión:**

- `usuario_id`: identificador del usuario autenticado.
- `email`: email del usuario (para mostrar en la UI).
- `club_activo_id`: ID del club seleccionado actualmente (`null` si no se seleccionó ninguno).
- `session_token_hash`: hash del token de sesión (nunca el token en texto plano).
- `expires_at`: timestamp ISO 8601 de expiración.

**¿Cómo se establece el `club_activo_id`?**

1. Al hacer login, el `SessionManager` crea la sesión con `club_activo_id = null`.
2. El usuario ejecuta `stats club select <id>`.
3. El comando llama a `CambiarClubActivoUseCase`, que verifica que el club pertenezca al usuario.
4. Si la verificación pasa, el `SessionManager` actualiza `club_activo_id` en el archivo.
5. Los comandos operativos (cargar partido, listar jugadores) leen `club_activo_id` al inicio; si es `null`, abortan con un mensaje claro.

> **¿Por qué club activo y no pasarlo como argumento?** Un DT trabaja siempre en el contexto de un club. Tener el club activo en la sesión evita escribir `--club-id 3` en cada comando — el mismo patrón que usan los IDEs con el "proyecto activo" o las shells con el "directorio actual".

### Composition Root: cómo se ensambla la aplicación

El **Composition Root** es el único lugar del sistema donde se instancian todas las dependencias y se conectan entre sí. En esta arquitectura, ese lugar es `src/main.py` (CLI) y será `src/infraestructura/ui/flet/app.py` (GUI, Hito 4).

> **Cómo quedó en la CLI:** como cada ejecución de la CLI es un proceso nuevo que corre **un único comando**, `main.py` solo inicializa la base, arma el parser y despacha el comando elegido (`args.func(args)`); **cada comando arma las dependencias que necesita** (`ejecutar(args, repo=None)`: si no se le inyecta un repositorio, arma el real con `abrir_conexion()`). Así no se construyen repositorios que no se van a usar, y los tests inyectan repositorios falsos. Los errores de negocio (`ErrorDeDominio`) se atrapan en un único `except` de `main()`.

**¿Por qué es importante?** Porque en todos los demás archivos, las clases reciben sus dependencias como argumentos (nunca las crean con instanciación directa). Esto hace el sistema
testeable: en los tests se pueden pasar repositorios falsos (mocks) sin modificar el código de producción.

**Flujo de ensamblaje esperado en `main.py`** (crece con cada US):

1. **US-101/102:** se instancia `SQLiteManager`, se ejecutan las migraciones/inicialización, se crean los repositorios SQLite pasando la conexión.
2. **US-103/104/105:** se crean los servicios de aplicación (`SessionManager`) y los casos de uso administrativos, pasando los repositorios.
3. **US-106/107:** se crean los casos de uso operativos y se registran todos los subcomandos CLI.
4. **US-108:** se inicializa el `ExecutionContext` antes de despachar cualquier comando y se conecta el logging.
5. **US-401 (GUI):** mismo patrón en `app.py`, pero las pantallas Flet reciben los casos de uso como dependencias.

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
- Sesión requiere usuario autenticado y, para comandos operativos, club activo.

**Jugadores, Clubes y Afiliaciones**:

- DNI de jugador único cuando está informado.
- Un jugador no puede tener dos vínculos activos superpuestos con el mismo club.
- Historial de afiliación coherente en fechas: `fecha_hasta >= fecha_desde`.

**Competencias, Inscripciones y Listas**:

- Una inscripción es única por club + competencia + categoría + temporada.
- Cada inscripción tiene una única lista de buena fe asociada (1:1).
- Solo jugadores habilitados en lista pueden figurar en carga oficial de partido.

**Partidos y Estadísticas**:

- Un partido no puede tener el mismo club como local y visitante.
- Toda carga de partido y boxscore es atómica (todo o nada).
- Estadísticas de tiro: convertidos ≤ lanzados; todos los valores no negativos.
- Puntos de jugador = T1C + T2C×2 + T3C×3 (coherencia verificada).
- Minutos por jugador no pueden exceder el máximo reglamentario definido por competencia.

**Analítica y Reporting**:

- Fórmulas avanzadas deben manejar división por cero y no devolver `NaN`/`inf`.
- Reportes y dashboards se construyen sobre vistas SQL normalizadas y versionadas.
- Toda exportación (PDF/backup) debe ser trazable en logs con timestamp y resultado.

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
| ADR-002 | Framework UI               | Aprobado (`docs/adr/ADR-002-framework-ui.md`)                                             | Flet (Python puro); se descarta Compose Multiplatform                                                                                              | Hito 4          |
| ADR-003 | Protocolo de Ingesta Excel | Pendiente — borrador con pregunta abierta (`docs/adr/ADR-003-protocolo-ingesta-excel.md`) | Falta un archivo real de Ges Deportivo para fijar el mapeo de columnas                                                                             | US-201          |
| ADR-004 | Versionado de DB           | Pendiente — pregunta abierta (`docs/adr/ADR-004-versionado-db.md`)                        | Migraciones manuales vs. Alembic — falta decidir si vale agregar SQLAlchemy solo por el runner                                                     | Hito 2          |
| ADR-005 | Reportes PDF               | Aprobado (`docs/adr/ADR-005-reportes-pdf.md`)                                             | `reportlab`; se descarta `weasyprint`                                                                                                              | US-302          |
| ADR-006 | Seguridad y Cifrado        | Aprobado v0.1 / Pendiente v1.0 (`docs/adr/ADR-006-seguridad-cifrado.md`)                  | Hash de passwords con `pbkdf2_hmac` y salt dinámico; cifrado DB (SQLCipher) y migración a bcrypt/argon2 quedan para Hito 4, con preguntas abiertas | US-104 / Hito 4 |
| ADR-007 | Motor de Visualización     | Aprobado (`docs/adr/ADR-007-motor-visualizacion.md`)                                      | `matplotlib`; se descarta `plotly` para este motor                                                                                                 | US-301          |
| ADR-008 | Estrategia de Backup       | Aprobado (`docs/adr/ADR-008-estrategia-backup.md`)                                        | Exportación/restauración manual con `VACUUM INTO`/backup online de SQLite                                                                          | Hito 4          |
| ADR-009 | Pipeline CI/CD             | Aprobado, ya implementado (`docs/adr/ADR-009-pipeline-cicd.md`)                           | GitHub Actions (hosted) para lint, tests y cobertura automáticos                                                                                   | US-109          |

Estructura canónica de un ADR (ver `docs/documentacion_app_estadistica/ADR/template_adr.md`): Contexto → Alternativas Consideradas → Decisión Tomada → Ventajas y Desventajas. Los ADR escritos viven en `docs/adr/` (no en el submódulo de documentación, que es de otro repositorio). **Estado (2026-10-03): los 9 ADR ya están redactados en `docs/adr/`.** Aprobados sin preguntas
pendientes: ADR-001, ADR-002, ADR-005, ADR-007, ADR-008, ADR-009. Con preguntas abiertas a
resolver antes de cerrarlos del todo: ADR-003 (falta un archivo real de Ges Deportivo),
ADR-004 (manuales vs. Alembic) y ADR-006 (viabilidad de SQLCipher en Android y fuente de la lista
de contraseñas comprometidas, ambas para la parte de v1.0).

---

## 9. Hito 1 — Núcleo de Datos e Interfaz CLI (v0.1)

**Objetivo del hito:** construir una base técnica funcional por CLI con persistencia robusta, autenticación local, casos de uso operativos, validaciones de integridad y un entorno de calidad que garantice reproducibilidad desde el primer commit. Sistema funcional por línea de comandos con persistencia robusta.

**Épicas:** 3 · **Historias:** 9 (US-101 a US-109; la US-104 original se dividió en Autenticación
y Sesión el 2026-10-03, ver nota al inicio de la Épica H1-E2) · **Esfuerzo total estimado:** ~50
días·persona

### Épica H1-E1: Infraestructura y Persistencia

#### US-101 — Esquema SQLite, Vistas y Datos Semilla

**Esfuerzo:** L (6-10 días) · **Prioridad:** Urgente (bloqueante)

**Objetivo Funcional:** habilitar un esquema relacional local verificable y un conjunto de vistas operativas que sirvan de contrato estable para todo el ciclo del producto, garantizando que Pandas y la capa de aplicación consuman datos sin transformaciones ambiguas.

**Narrativa:** Como desarrollador, quiero el esquema relacional completo en SQLite, con sus vistas de análisis y datos de prueba, para tener una base verificable sobre la que construir el sistema.

**Capa de Infraestructura:**

- **Clase `SQLiteManager`** (`src/infraestructura/persistencia/database_manager.py`):
  - `connect()`: retorna una conexión activa con `PRAGMA foreign_keys = ON` y `row_factory = sqlite3.Row`.
  - `inicializar_schema()`: ejecuta de forma atómica los scripts `schema.sql`, `views.sql` (y opcionalmente `seed.sql`) usando `executescript()`.
- **Scripts SQL** (`src/infraestructura/persistencia/sql/`):
  - `schema.sql`: DDL completo, tablas con tipos estrictos, PK, FK, `CHECK` constraints, `CREATE TABLE IF NOT EXISTS` y `DROP TABLE IF EXISTS` en orden inverso de dependencias.
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
- **AC4.** El campo `dni` en `jugador` es `UNIQUE` pero permite `NULL`.
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

**Esfuerzo:** M (3-5 días). **Prioridad:** Urgente (bloqueante). **Dependencias:** US-101

**Objetivo Funcional:** implementar el orquestador de conexión y las interfaces de persistencia bajo Clean Architecture, asegurando que el acceso a datos sea independiente del motor de base de datos y garantizando la integridad referencial.

**Narrativa:** Como desarrollador, quiero una capa de infraestructura que gestione el ciclo de vida de la conexión SQLite y exponga repositorios tipados para cada agregado del dominio.

**Capa de Dominio — Interfaces (`src/dominio/repositorios/`):** las firmas reales ya migraron de "parámetros sueltos" a **recibir la dataclass completa**

- `UsuarioRepositorio`: `encontrar_por_mail(email)`, `encontrar_por_id(id)`, `guardar(usuario: Usuario)`.
- `ClubRepositorio`: `buscar_por_id_usuario`, `buscar_por_id`, `buscar_por_nombre`, `guardar(club: Club)`, `link_user_to_club(us_club: UsuarioClub)`.
- `JugadorRepositorio`: `buscar_por_id`, `buscar_por_dni`, `buscar_por_club`, `guardar(jugador: Jugador)`, `link_to_club(jc: JugadorClub)`, `club_activo`.
- `CompetenciaRepositorio`: `guardar_competencia(compe:Competencia)`, `buscar_competencia_por_id`, `obtener_todas_competencias`, `guardar_categoria(cat:Categoria)`, `obtener_categorias`, `guardar_inscripcion(inscripcion: Inscripcion)`, `buscar_inscripcion_por_id`, `obtener_inscripciones_por_club`, `guardar_lista_buena_fe(listaBF: ListaBuenaFe)`, `obtener_lista_por_inscripcion` _(tipada `-> ListaBuenaFe` singular, coherente con la relación 1:1)_, `agregar_jugador_lista(idJugador, idListaBuenaFe)` y `obtener_jugadores_lista`.
- `JuegoRepositorio`: `buscar_por_club`, `buscar_por_id`, `guardar_partido(partido: Partido)`, `guardar_boxscore(boxscore:JugadorPartido)`.

**Capa de Infraestructura:**

- **Clase `SQLiteManager`:** administra la conexión; `connect()` activa `PRAGMA foreign_keys` y `row_factory = sqlite3.Row`, retornando la conexión activa si ya existe; `inicializar_schema()` ejecuta `schema.sql` + `views.sql` en una sola llamada atómica.
- **Implementaciones concretas** (`src/infraestructura/repositorios/`): `SqliteUsuarioRepositorio`, `SqliteClubRepositorio`, `SqliteJugadorRepositorio`, `SqliteCompetenciaRepositorio`, `SqliteJuegoRepositorio`. `SqliteCompetenciaRepositorio` maneja competencia, categoria, inscripcion, listaBuenaFe y jugadorListaBuenaFe como un único agregado competitivo. Cada repositorio mapea manualmente `sqlite3.Row` a las dataclasses de dominio mediante un método privado `_row_to_entity()`.

**Criterios de Aceptación:**

- **AC1 — Gestión de Conexión:** `connect()` garantiza integridad referencial y acceso por nombre de columna.
- **AC2 — Abstracción Total:** la capa `dominio/` no importa `sqlite3`, `pandas` ni ninguna librería de infraestructura.
- **AC3 — Mapeo de Datos:** los repositorios retornan objetos `@dataclass` puros, nunca tuplas de SQLite.
- **AC4 — Transaccionalidad:** `SqliteJuegoRepositorio.guardar_boxscore()` (y, a futuro, un método combinado tipo `save_with_boxscore`) debe permitir transacciones multi-tabla para asegurar la integridad de la carga de partidos.

**Reglas de Negocio:**

- Validación de DNI duplicado al guardar un jugador (lanza excepción de dominio).
- Uso de `cursor.lastrowid` para retornar la entidad con el ID asignado por la base de datos.

**Entidades/Modelos implicados:** `Usuario`, `Club`, `Jugador`, `JugadorClub`, `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`, `Partido`, `EstadisticaJugadorPartido`.

**Vistas SQL necesarias:** `v_partidos_resumen` y `v_boxscore_completo` para optimizar las consultas de lectura en los repositorios.

**Testing Mínimo:**

- _Integración (`tests/integration/test_repositories.py`):_ CRUD completo por repositorio usando DB `:memory:`; `buscar_por_dni` retorna `None` si no existe, sin lanzar excepción; el `save()` de un partido y sus estadísticas es atómico; los repositorios de lectura usan las vistas SQL correctamente.

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
      juego_repositorio.py
  infraestructura/
    repositorios/
      sqlite_usuario_repositorio.py
      sqlite_club_repositorio.py
      sqlite_jugador_repositorio.py
      sqlite_competencia_repositorio.py
      sqlite_juego_repositorio.py
```

### Épica H1-E2: Lógica de Aplicación y CLI

> **Nota de numeración (2026-10-03):** esta épica tenía 5 historias (US-103 a US-107). La
> "US-104 — Autenticación y Sesión Local" original se dividió en **US-104 (Autenticación de
> Usuarios)** y **US-105 (Sesión Persistente y Club Activo)** — ver el motivo en el recuadro al
> inicio de la nueva US-104 — y el resto se corrió un número (vieja US-105→106, vieja US-106→107).
> Por eso esta épica pasó de 5 a 6 historias.

#### US-103 — Gestión de Entidades (Casos de Uso Administrativos)

**Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-101, US-102

**Objetivo Funcional:** implementar la lógica de negocio pura y la interfaz de usuario por comandos para la gestión integral de las entidades del sistema (jugadores, clubes, competencias, inscripciones), asegurando la validación de reglas deportivas y la integridad de los datos.

**Narrativa:** Como administrador, quiero disponer de casos de uso con lógica de negocio validada para gestionar el ciclo de vida de los jugadores y sus afiliaciones, así como la estructura de competencias y clubes.

**Capa de Dominio:**

- **Entidades:** `Usuario`, `Club`, `Jugador`, `JugadorClub` (historial N:M jugador-club), `Competencia`, `Categoria`, `Inscripcion`, `ListaBuenaFe`, `JugadorListaBuenaFe`, `Partido`, `JugadorPartido`. `@dataclass` puras, serializables, sin dependencias externas.
- **Lógica de validación** (`__post_init__` de entidades): tipos de todos los campos (`TypeError`: bug del programa); y **reglas de valor** (`DatoInvalidoError`: error del usuario, llega a la CLI como mensaje): nombres de `Club`, `Jugador` (nombre y apellido), `Competencia` y `Categoria` no vacíos (ni solo espacios); `Jugador.dni` mayor a 0; `Jugador.anioNacimiento` mayor a 1900 y no posterior al año actual; `Competencia.anio` mayor a 1900 ; en `JugadorPartido`, tiros convertidos ≤ lanzados, minutos entre 0 y 48, valores no negativos y `puntos = T2C·2 + T3C·3 + T1C`.
- **Modelo de lectura:** `PartidoResumen` (dataclass sin validación, es lo que devuelve la vista `v_partidos_resumen`: fecha, estadio, competencia, año y nombres de los dos clubes).
- **Propiedades calculadas:** `Jugador.nombre_completo` y `JugadorPartido.rebotes_totales` (defensivos + ofensivos); no se guardan en la base.
- **Excepciones** (`src/dominio/exceptions.py`), todas hijas de `ErrorDeDominio`: `DNIDuplicadoError`, `ClubNoEncontradoError`, `JugadorNoEncontradoError`, `CompetenciaNoEncontradaError`, `CategoriaNoEncontradaError`, `InscripcionDuplicadaError`, `VinculoActivoExistenteError`, `CategoriaDuplicadaError`, `InscripcionNoEncontradaError`, `ListaBuenaFeNoEncontradaError`, `JugadorYaEnListaError`, `JugadorNoPerteneceAlClubError`, `JugadorNoEstaEnListaError`, `JugadorSinVinculoActivoError`, `VinculoSuperpuestoError`, `DatoInvalidoError` (además hereda de `ValueError`, para que el código que ya atrapaba `ValueError` siga funcionando), `UsuarioNoEncontradoError` y `CredencialesInvalidasError`.

**Capa de Aplicación** ✅ (`src/aplicacion/`):

- **Casos de uso** (`casos_uso/`, método `ejecutar()`):
  - `RegistrarJugadorUseCase` (crea la entidad y el repositorio rechaza el DNI duplicado),
  - `CrearClubUseCase`,
  - `VincularJugadorAClubUseCase` (verifica que existan jugador y club, evita vínculos activos duplicados y que el vínculo nuevo se superponga con uno anterior),
  - `CrearCompetenciaUseCase`,
  - `InscribirClubEnCompetenciaUseCase` (valida club, competencia y categoría, evita la inscripción duplicada y genera la `listaBuenaFe` vacía asociada, 1:1, **de forma atómica** con `CompetenciaRepositorio.inscribir_con_lista`),
  - `ListarClubesUsuarioUseCase`
  - `ListarJugadoresClubUseCase` (solo vínculos vigentes),
  - `ListarPartidosPorClubUseCase` (devuelve `PartidoResumenDTO` con nombres, desde la vista)
  - `CambiarClubActivoUseCase` (valida que el club exista y pertenezca al usuario; guardar el club en la sesión es de la US-105).
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

- DNI de jugadores numérico, positivo y único. Nombre y apellido no vacíos. Año de nacimiento mayor a 1900 y no posterior al año actual.
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

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103

> **Alcance de esta US y por qué se separó de la sesión:** hasta el 2026-10-03 esto era una sola
> historia ("US-104 — Autenticación y Sesión Local") que mezclaba dos preocupaciones distintas:
> demostrar quién es el usuario (acá) y recordar el contexto entre ejecuciones de la CLI (club
> activo, ahora US-105). Se separaron para no repetir el problema de la US-103 (una historia que
> terminó siendo una PR enorme): esta US termina en un usuario que puede registrarse y loguearse;
> **todavía no persiste nada entre ejecuciones de la CLI** (eso es la US-105). No toca `club_list`
> ni ningún comando existente.

**Objetivo Funcional:** permitir el registro y el acceso seguro de entrenadores al sistema, con
contraseñas hasheadas y nunca almacenadas en texto plano.

**Narrativa:** Como usuario, quiero poder registrarme y loguearme de forma local, con mis
credenciales protegidas.

**Estado real verificado (2026-10-03):** nada de esta US existe todavía en el código (no hay
`src/infraestructura/security/`, no hay `password_hasher.py`, no hay subparser `auth` en
`src/main.py`). Sí existen y se reusan tal cual: la entidad `Usuario`
(`src/dominio/entidades/usuario.py`, hoy con un único campo de contraseña, `pw` — ver más abajo),
`UsuarioRepositorio`/`SqliteUsuarioRepositorio` (`encontrar_por_mail`, `encontrar_por_id`,
`guardar` — **en español**, no `get_by_email`/`get_by_id`/`save` como decía el texto viejo de esta
US) y las excepciones `UsuarioNoEncontradoError`/`CredencialesInvalidasError` (en
`src/dominio/exceptions.py`, ya están, reusables sin cambios).

**Capa de Dominio:**

- **Entidad `Usuario`:** se renombra el campo `pw` a `password_hash` (claridad, sin agregar un
  campo `salt` separado: el salt va embebido en el propio string que devuelve `PasswordHasher.hash()`,
  formato estándar de `pbkdf2`/`bcrypt` — no hace falta tocar la columna `contrasenia` de la tabla
  `usuario`, es un cambio de nombre de atributo Python, no de esquema). Se agregan las
  validaciones de valor que al resto de las entidades (`Club`, `Jugador`, etc.) ya les llegaron en
  la US-103 y a `Usuario` no: `nombre`/`email` no vacíos (`DatoInvalidoError`), con el mismo
  `__post_init__` que ya usan las demás entidades.
- **Excepción nueva:** `EmailYaRegistradoError` (hija de `ErrorDeDominio`, junto a las que ya
  existen).

**Capa de Aplicación:**

- **Casos de uso:** `RegistrarEntrenadorUseCase` (rechaza email duplicado con
  `EmailYaRegistradoError`, usando `UsuarioRepositorio.encontrar_por_mail`), `LoginLocalUseCase`
  (`CredencialesInvalidasError` si el email no existe o la contraseña no verifica — sin distinguir
  cuál de los dos pasó, para no filtrar si un email está registrado).
- **DTOs:** `RegistrarDTO`, `LoginDTO`.

**Capa de Infraestructura:**

- **Seguridad:** `PasswordHasher` en `src/infraestructura/security/password_hasher.py`, con solo
  dos métodos públicos: `hash(password) -> str` y `verify(password, hash) -> bool`. **Decisión
  tomada (resuelve la contradicción que tenía el ADR-006 — ver sección 8 de ADRs):** v0.1 usa
  `hashlib.pbkdf2_hmac` con **salt dinámico** (uno distinto por usuario, generado con `os.urandom`
  al registrarse y guardado junto al hash en el mismo string) — no salt fijo. Migrar a
  `bcrypt`/`argon2-cffi` queda para v1.0, sin cambiar la interfaz pública de `PasswordHasher`.
- **Persistencia:** `SqliteUsuarioRepositorio` — ya existe, sin cambios (sigue guardando lo que
  reciba en la columna `contrasenia`; ahora va a recibir el resultado de `PasswordHasher.hash()`
  en vez de texto plano).
- **CLI:** `stats auth register`, `stats auth login`, `stats auth logout`. Se registran como
  subparsers nuevos en `construir_parser()` de `src/main.py` (no se recrea el parser). Siguiendo la
  convención **un archivo por acción**, se crean `auth_register.py`, `auth_login.py`,
  `auth_logout.py` en `ui/cli/commands/`. `auth_logout` en esta US solo informa "no hay sesión que
  cerrar" (todavía no hay nada que persista entre comandos) — borrar la sesión real es de la US-105.

**Base de Datos:** tabla `usuario` (`idUsuario`, `nombre`, `email`, `contrasenia`) — ya existe, sin
cambios de esquema.

**Criterios de Aceptación:**

- **AC1 — Seguridad de Credenciales:** las contraseñas NUNCA se almacenan ni se loguean en texto
  plano. Hashing con salt dinámico por usuario.
- **AC2 — Validaciones:** email único (`EmailYaRegistradoError`); contraseña con requisitos
  mínimos (≥6 caracteres en v0.1; ≥12 con complejidad en v1.0, ver US-403).

**Testing Mínimo:**

- _Unitarias:_ `hash`/`verify` de `PasswordHasher` (incluye que dos hashes de la misma contraseña
  sean distintos, por el salt dinámico); `RegistrarEntrenadorUseCase`/`LoginLocalUseCase` con
  `UsuarioRepositorio` mock (camino feliz + `EmailYaRegistradoError` + `CredencialesInvalidasError`).
- _Integración:_ flujo completo registro → login con DB `:memory:`.

**Archivos a crear:**

```text
src/infraestructura/security/
└── password_hasher.py

src/aplicacion/casos_uso/
├── registrar_entrenador.py
└── login_local.py

src/aplicacion/dtos/
└── auth_dto.py

src/infraestructura/ui/cli/commands/
├── auth_register.py
├── auth_login.py
└── auth_logout.py

tests/unit/
└── test_password_hasher.py
tests/integration/
└── test_auth_flujo.py
```

#### US-105 — Sesión Persistente y Club Activo

**Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-104

**Objetivo Funcional:** mantener un estado de sesión persistente entre ejecuciones de la CLI, para
no pedir credenciales ni el club activo en cada comando.

**Narrativa:** Como usuario, quiero que la CLI recuerde que ya inicié sesión y con qué club estoy
trabajando, entre una ejecución y la siguiente.

**Por qué hace falta una CLI arranca-y-termina:** cada comando (`stats club list`, `stats jugador
add`, etc.) es un proceso nuevo — nada en memoria sobrevive de un comando al siguiente. Por eso
"estar logueado" y "tener un club activo" tienen que persistirse en disco y releerse al arrancar
cada comando. Esa es la razón de ser del `SessionManager`.

**Decisiones tomadas (antes eran preguntas abiertas, documentadas en el historial de esta US —
ver `docs/explicacion_us/us104-explicacion.md` hasta el 2026-10-03, ya absorbido acá):**

1. **Dónde se persiste:** archivo **JSON**, no la misma base SQLite — es el mecanismo estándar
   para este tipo de estado de CLI (`~/.aws/credentials`, `~/.netrc`), no compite por locks con la
   base, y permite borrar la sesión a mano sin tocar datos de negocio.
2. **Ruta única:** `~/.statspro/session.json`, resuelta con `pathlib.Path.home()` (funciona igual
   en Windows, que es donde corre el entorno de desarrollo de este proyecto). Se elimina la ruta
   alternativa `~/.statspro_session.json` y la de `./data/session.json` que aparecían en dos
   lugares distintos del plan viejo — quedaba sin resolver cuál era la real.
3. **Sin token ni expiración:** `SessionDTO` queda tal como ya lo define esta historia —
   `usuario_id`, `email`, `club_activo_id` — sin `session_token_hash` ni `expires_at`. Ese esquema
   es el de una sesión **web** (cliente y servidor en procesos/máquinas distintas); acá el mismo
   proceso local lee y escribe su propio archivo, no hay token que viajar ni nadie de quien
   protegerse salvo los permisos del propio archivo.
4. **Configurable, no hardcodeado:** se agrega un loader de configuración mínimo —
   `src/config/settings.py` + `.env.example` (idea tomada de `docs/ideas-aprendizaje.md`, sección
   4: "Loader de configuración por variables de entorno", encaja justo acá porque los tests de
   integración necesitan apuntar la sesión a un archivo temporal sin parchear código) — con al
   menos `STATSPRO_SESSION_PATH` (default `~/.statspro/session.json`) y `STATSPRO_DB_PATH`
   (default: lo que ya calcula `config/rutas.py`, sin romper nada existente).

**Gap real encontrado y su corrección (no es alcance nuevo, es un bug de una pieza ya cerrada de
US-103):** `CrearClubUseCase` (`src/aplicacion/casos_uso/crear_club.py`, ya implementado en
US-103) crea el club pero **nunca inserta en `usuarioClub`** — la tabla N:M que vincula usuario y
club con `rolEntrenador`. Sin ese vínculo, `club list` (que hace `JOIN usuarioClub`) y
`club select` (de esta misma US) no encuentran ningún club para ningún usuario real. Se corrige
acá, **documentado explícitamente como fix**, extendiendo `CrearClubUseCase` para que reciba el
`idUsuario` de la sesión y lo vincule como entrenador al crear el club.

**Capa de Aplicación:**

- **Servicio:** `SessionManager` (`load_session`/`get_current`, `save_session`,
  `is_authenticated`, `clear_session`/`destroy`, `set_active_club`/`set_club_activo`). `clear_session()`
  es idempotente (no falla sin sesión previa); `set_active_club()` falla si no hay sesión previa.
- **Caso de uso extendido:** `CrearClubUseCase` (US-103) pasa a recibir `idUsuario` y vincular en
  `usuarioClub` — no se crea un caso de uso nuevo para esto.

**Capa de Infraestructura:**

- **CLI:** `stats club select <id>` (usa `CambiarClubActivoUseCase`, de US-103, que solo valida
  pertenencia; acá se le suma guardar el club elegido en `SessionManager`); módulo de guards
  compartido `require_auth()`/`require_active_club()` (cada comando arma su propio `SessionManager`,
  igual que ya arma su propio repositorio si no se le inyecta uno — mismo patrón que ya usan). Se
  le saca el `--id-usuario` provisorio a `club_list.py`, que pasa a leer el usuario autenticado de
  la sesión.

**Criterios de Aceptación:**

- **AC1 — Persistencia de Sesión:** la sesión sobrevive al cierre de la CLI; al reiniciar,
  `is_authenticated()` retorna `True` si había sesión activa.
- **AC2 — Manejo de Contexto:** el archivo de sesión recuerda el club activo actual.
- **AC3 — Club realmente vinculado:** después de `club add` seguido de `club select`, el club
  aparece en `club list` del mismo usuario (cierra el gap de `usuarioClub`).

**Reglas de Negocio:**

- `clear_session()` es idempotente.
- `set_active_club()` falla si no hay sesión previa.
- Los comandos protegidos ejecutan `require_auth()` y `require_active_club()` según corresponda.

**Testing Mínimo:**

- _Unitarias:_ `SessionManager` con archivo temporal (no con DB `:memory:` — es estado de archivo,
  no de base); guards `require_auth()`/`require_active_club()` con sesión mock.
- _Integración:_ flujo completo registro → login → `club add` → `club select` → `club list` (ya
  muestra el club) usando DB `:memory:` y un archivo de sesión temporal.

**Archivos a crear:**

```text
src/config/
└── settings.py            ← nuevo: lee .env (python-dotenv) y expone STATSPRO_SESSION_PATH/STATSPRO_DB_PATH

src/aplicacion/
├── services/session_manager.py
└── dtos/session_dto.py    ← SessionDTO (usuario_id, email, club_activo_id)

src/infraestructura/ui/cli/
├── auth_guards.py          ← require_auth() / require_active_club()
└── commands/club_select.py

.env.example

tests/unit/
└── test_session_manager.py
tests/integration/
└── test_sesion_club_activo_flujo.py
```

#### US-106 — Carga Atómica de Partido (CargarPartido)

- **Esfuerzo:** S (1-3 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-104, US-105
- **Objetivo Funcional:** registrar un evento de partido y sus estadísticas individuales
  asociadas garantizando la integridad de los datos mediante una transacción atómica (todo o
  nada).
- **Narrativa:** Como DT, quiero registrar un partido completo con todas las estadísticas de los
  jugadores en una única operación; si falla una sola estadística, nada se persiste.

> **Estado real verificado (2026-10-03) — esta US quedó mucho más chica de lo que decía el texto
> viejo.** El texto anterior describía un bloqueo real inexistente ("`SqliteJuegoRepositorio` no
> funcional, tabla `Juego` inexistente"). El repositorio real se llama `SqlitePartidoRepositorio`
> (`src/infraestructura/repositorios/sqlite_partido_repositorio.py`), la tabla es `partido` (con
> sus `CHECK`/FK correctos en `schema.sql`), y **ya existe y ya funciona** `guardar_partido` y
> `guardar_boxscore`. Más importante: **el método atómico que esta US pide ya está implementado**
> — `save_with_boxscore(partido, boxscore)`, con `with self.conexion:` (COMMIT/ROLLBACK automático
> de `sqlite3`), validando competencia/clubes/jugadores existentes antes de insertar — y **ya está
> probado** (`tests/integration/test_repositorios_partido.py::test_save_with_boxscore_rollback_no_deja_partido_huerfano`).
> La entidad `JugadorPartido` (`src/dominio/entidades/partido.py`) ya valida con `DatoInvalidoError`
> todo lo que pide la sección de Reglas de Negocio de más abajo (fórmula de puntos, convertidos ≤
> lanzados, minutos 0-48, no negativos). Este trabajo se hizo durante la US-103 ("Auditoría de
> cierre de la US-103", sección 18) sin que el texto de esta US se actualizara — es el mismo
> problema de historias pisándose entre sí que motivó esta revisión completa, en sentido inverso
> (acá ya se hizo de más, no de menos). **Lo único que falta de verdad es la capa de aplicación y
> el comando CLI**, descritos abajo.

- **Capa de Dominio:** nada nuevo — `Partido`/`JugadorPartido` y sus validaciones ya existen
  (ver arriba).
- **Capa de Aplicación (lo que realmente falta):**
  - **Caso de uso:** `CargarPartidoUseCase` — orquesta: valida que el boxscore solo tenga
    jugadores habilitados (`CompetenciaRepositorio.obtener_jugadores_lista`, ya existe de
    US-103) y llama a `PartidoRepositorio.save_with_boxscore`.
  - **DTOs:** `PartidoDTO` (de carga — el de solo lectura que ya existe se llama
    `PartidoResumenDTO`, no se toca), `BoxscoreDTO`, `EstadisticaInputDTO`.
- **Capa de Infraestructura:**
  - **CLI:** `stats partido add` con flujo interactivo multi-paso. **Decisión tomada (resuelve una
    pregunta que quedaba abierta entre esta US y la US-105):** el club **local** es siempre el
    club activo de la sesión (`SessionManager`, US-105) — no se vuelve a pedir; el club
    **visitante** se pide como argumento/paso del formulario.
- **Criterios de Aceptación:**
  - **AC1 — Atomicidad Garantizada (ya cumplido a nivel repositorio, falta ejercitarlo desde el
    caso de uso):** si falla la inserción del boxscore en cualquier punto, no se guarda el partido
    huérfano. `save_with_boxscore` ya lo garantiza; falta el test desde `CargarPartidoUseCase`.
  - **AC2 — Validaciones Pre-persistencia:** la validación de boxscore contra la lista de buena fe
    ocurre ANTES de llamar al repositorio; el mensaje de error especifica qué jugador causó el
    error.
  - **AC3 — Independencia:** el caso de uso no contiene SQL embebido — se delega totalmente al
    repositorio.
- **Reglas de Negocio (ya implementadas en `JugadorPartido.__post_init__`, se listan para
  trazabilidad):**
  - `(T1C×1) + (T2C×2) + (T3C×3)` = puntos totales.
  - `convertidos ≤ lanzados` para T1, T2, T3.
  - Todos los campos numéricos `≥ 0`.
  - `minutosJugados` entre 0 y 48.
  - No se puede cargar un partido si los clubes involucrados no existen en la DB (ya lo valida
    `save_with_boxscore`).
  - **Solo pueden figurar en el boxscore jugadores habilitados en la lista de buena fe** del club
    (regla de la sección 3). Los datos ya se pueden cargar desde la US-103 (`stats lista add`);
    esta US los usa para validar (`CompetenciaRepositorio.obtener_jugadores_lista`) y lanza una
    excepción de dominio si un jugador no está habilitado. **Esta es la única decisión que sigue
    de verdad pendiente:** el partido guarda competencia y clubes, pero **no la categoría**; si un
    club tiene inscripciones en más de una categoría de la misma competencia, hay que definir
    contra qué lista se valida (por ejemplo, agregar la categoría al partido o validar contra la
    unión de las listas del club en esa competencia) — a resolver antes de escribir
    `CargarPartidoUseCase`.
  - **Nota (campo propuesto, no implementado todavía):** si se agrega a `Partido` un resultado
    final (`puntosLocalFinal`/`puntosVisitanteFinal`, ver sección 20 y el DER en
    `docs/diagramas/diagramas.md`), esta US sería el lugar natural para completarlo — junto con
    una regla que valide que la suma de puntos del boxscore por club coincide con ese resultado
    final antes de persistir.
- **Testing Mínimo:**
  - _Unitarias:_ `CargarPartidoUseCase` rechaza un jugador no habilitado en la lista de buena fe
    (mock de `CompetenciaRepositorio`), camino feliz llama a `save_with_boxscore` con los DTOs
    traducidos.
  - _Integración:_ flujo completo (partido + boxscore) en DB `:memory:` con repositorios reales —
    puede reusar el fixture ya existente de `tests/integration/test_repositorios_partido.py`.

**Archivos a crear:**

```text
src/aplicacion/
├── dtos/partido_dto.py     ← se extiende: PartidoDTO (carga), BoxscoreDTO, EstadisticaInputDTO
└── casos_uso/cargar_partido.py

src/infraestructura/ui/cli/commands/
└── game_add.py              ← stats partido add

tests/unit/
└── test_uc_cargar_partido.py
tests/integration/
└── test_cargar_partido_flujo.py
```

#### US-107 — CLI con Command Pattern

- **Esfuerzo:** S (1-3 días) · **Prioridad:** Alta · **Dependencias:** US-103, US-104, US-105, US-106
- **Narrativa:** Como administrador, quiero una CLI estructurada con subcomandos claros para
  gestionar todas las entidades, que muestre los datos en tablas formateadas.
- **Objetivo Funcional:** **no crea la CLI desde cero** — `main.py` (el composition root) y la
  mayoría de `commands/` ya existen desde la US-103 (club, jugador, competencia y partido list),
  la US-104 (auth) y la US-105 (club select). Esta US cierra lo que falta (`partido boxscore`, ya
  que `partido add` lo agrega la US-106) y hace el pulido final: aplica `require_auth()`/
  `require_active_club()` (US-105) a todos los comandos que corresponda, muestra DNI y club
  activo en `jugador list` (pendiente desde la US-103), y confirma que el patrón de subcomandos
  desacoplados se sostuvo sin bloques `if/else` a lo largo de todas las historias anteriores.
  **Convención adoptada:** un archivo por acción en `commands/`.
- **Comandos (usar `argparse`):**

```text
stats auth register / login / logout          ✅ US-104

stats club add --nombre                       ✅ US-103 (US-105 le agrega el vínculo a usuarioClub)
stats club list                               ✅ US-103 (ya lee el usuario de la sesión desde US-105)
stats club select <id>                        ✅ US-105 → actualiza sesión

stats jugador add --nombre --apellido --dni --anio     ✅ US-103
stats jugador list --id-club                           ✅ US-103 → esta US agrega DNI y club activo en la tabla
stats jugador link --id-jugador --id-club --fecha-desde  ✅ US-103
stats jugador unlink --id-jugador --fecha-hasta        ✅ US-103 (cierra el vínculo vigente; permite el cambio de club)

stats competencia add --nombre --anio [--tipo]                                        ✅ US-103
stats competencia inscribir --id-club --id-categoria --id-competencia --fecha-presentacion  ✅ US-103
stats competencia list                                                                ✅ US-103

stats categoria add --nombre                  ✅ US-103
stats categoria list                          ✅ US-103

stats inscripcion list --id-club              ✅ US-103
stats lista add --id-inscripcion --id-jugador ✅ US-103 (lista de buena fe)
stats lista remove --id-inscripcion --id-jugador  ✅ US-103 (deshace una habilitación)
stats lista list --id-inscripcion             ✅ US-103

stats partido list --id-club        ✅ US-103 (con nombres de clubes y competencia, desde v_partidos_resumen)
stats partido add                   ✅ US-106 → formulario multi-paso
stats partido boxscore <id_partido> ⬜ US-107 → tabla con v_boxscore_completo
```

- **Archivos (la mayoría ya existe de US-103 a US-106 — acá solo se extiende):**

```text
src/main.py                         ✅ existe desde US-103 — composition root: se le agregan subparsers, no se recrea
src/infraestructura/ui/cli/
├── commands/                       # un archivo por acción
│   ├── jugador_add.py, jugador_link.py, jugador_unlink.py, jugador_list.py  ✅ US-103 (list se extiende acá)
│   ├── club_add.py, club_list.py                                 ✅ US-103
│   ├── competencia_add.py, competencia_inscribir.py, competencia_list.py  ✅ US-103
│   ├── categoria_add.py, categoria_list.py, inscripcion_list.py  ✅ US-103
│   ├── lista_add.py, lista_remove.py, lista_list.py              ✅ US-103
│   ├── game_list.py                                              ✅ US-103 (stats partido list)
│   ├── auth_register.py, auth_login.py, auth_logout.py           ✅ US-104
│   ├── club_select.py, auth_guards.py                            ✅ US-105
│   ├── game_add.py (interactivo)                                 ✅ US-106
│   └── game_boxscore.py                                          ⬜ US-107
└── formatters/
    └── table_formatter.py          ✅ existe desde US-103 (wrapper de tabulate)
```

- **Criterios de Aceptación:**
  - **AC1 — Command Pattern:** agregar un nuevo comando (ej. `stats categoria add`)
    solo requiere crear su archivo en `commands/` y registrarlo en `construir_parser()` de
    `main.py` — sin modificar ningún otro comando. Las excepciones de dominio nunca muestran tracebacks al
    usuario final.
  - **AC2 — Visualización con vistas SQL:** `stats partido list` usa `v_partidos_resumen` (nombres
    de clubes, no IDs); `stats partido boxscore <id>` usa `v_boxscore_completo`; `stats jugador list`
    muestra el club activo del jugador (del historial `jugadorClub`).
  - **AC3 — Flujo de sesión:** los comandos `club`, `jugador` y `partido` ejecutan `require_auth()`
    al inicio (de `auth_guards.py`, US-105); `partido` y `jugador list` ejecutan
    `require_active_club()`.
- **Testing Mínimo:**
  - _Unitario:_ `jugador list` muestra DNI y club activo; `partido boxscore` formatea
    `v_boxscore_completo`.
  - _Integración:_ ejecución de cada subcomando con DB en memoria, verificando salida esperada;
    comando sin sesión → mensaje de error controlado (usa los guards de US-105).

#### US-108 — Monitoreo y Trazabilidad Operativa

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Media · **Dependencias:** US-107
- **Objetivo Funcional:** proveer observabilidad transversal estructurada para depuración y
  soporte, con correlación de eventos extremo-a-extremo por ejecución de comando.
- **Archivos a crear:**

```text
src/infraestructura/logging/
├── logger_config.py       ← configuración de sinks (local-file / Seq)
└── seq_handler.py         ← handler HTTP para Seq (opcional)

src/aplicacion/services/
└── execution_context.py   ← genera correlation_id UUIDv4 y propaga contexto

docker-compose.yml          ← perfil "observabilidad" con Seq (opcional)

test/
├── test_execution_context.py
└── test_logging_redaction.py
```

- **Eventos de log obligatorios:** inicio/fin de comando CLI (resultado + duración);
  `LoginLocalUseCase`/`auth_logout`, `SessionManager.set_active_club` (US-104/105), fallos de
  autenticación; inicio/fin de transacciones críticas (`CargarPartidoUseCase` de US-106,
  importación Excel, backup/restore); creación/actualización de entidades principales;
  excepciones de dominio y errores de infraestructura, clasificados por severidad.
- **Criterios de Aceptación:**
  - **AC1.** Niveles DEBUG/INFO/WARNING/ERROR en formato JSON estructurado.
  - **AC2.** `correlation_id` UUIDv4 generado al inicio de cada comando y propagado hasta
    repositorios.
  - **AC3.** Secretos (passwords, tokens, hashes sensibles) redactados en todos los niveles de
    log.
  - **AC4.** Selección de sink (local-file o Seq) por configuración, sin cambiar código de
    negocio.
  - **AC5.** En modo Seq, eventos filtrables por `correlation_id`, `command_name` y nivel.
- **Testing Mínimo:**
  - _Unitario:_ creación y propagación de `execution_context`; redacción de secretos en campos
    conocidos.
  - _Integración:_ flujo CLI completo → verificar que cada evento tiene el mismo
    `correlation_id`.

> **Estado real:** el proyecto ya tiene un logger funcional (`src/infraestructura/logger.py`,
> rotación 10MB/5 backups, formato `asctime - name - levelname - message`) — es más simple que lo
> que pide esta US (sin JSON estructurado, sin `correlation_id`, sin redacción de secretos, sin
> Seq). Es un buen punto de partida, no un reemplazo completo de la US-108. Ver
> `docs/info_modulo/01-logger.md`.

### Épica H1-E3: Entorno de Calidad y Pipeline CI/CD

> **Regla de alcance para US-104 a US-109 (agregada el 2026-10-03):** si al implementar cualquiera
> de estas historias hace falta tocar algo que no está declarado en su propia sección — en
> particular, cualquier cambio de CI/CD o de Docker, que es responsabilidad de la US-109 — se
> anota explícitamente en la sección de esa US como **"trabajo adelantado de US-109"**, en vez de
> mezclarse en el mismo PR sin dejar rastro. Es la corrección directa a lo que ya pasó una vez: ver
> la nota de "Estado real" de la US-109 más abajo.

#### US-109 — Entorno de Desarrollo y Pipeline CI/CD

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Alta · **Dependencias:** —
- **Objetivo Funcional:** garantizar que todo nuevo commit sea verificado automáticamente con
  linting, tests y cobertura, haciendo del pipeline la única fuente de verdad sobre el estado de
  calidad del proyecto.
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
pytest.ini                      ✅ existe (pythonpath=src, testpaths=tests)
.pre-commit-config.yaml         ✅ existe (check-yaml, end-of-file-fixer, trailing-whitespace y ruff check/format
                                     ejecutados con `uv run`: misma versión de ruff que el CI)
pyproject.toml                  ✅ existe (dependencias con versión fija + config de ruff/mypy; uv.lock; sin requerimientos.txt)
Makefile                        ✅ existe (instalar_dependencias [uv sync], run_test, run_linter_ruf, corregir_linter, pre_commit, docker_test, static_check)
docs/catalogo-criticidad.md     ❌ no existe — ver sección 14
docs/info_modulo/11-flujo-de-trabajo-git.md  ❌ no existe
```

- **Criterios de Aceptación:**
  - **AC1.** `make run_test` ejecuta la suite completa y falla si la cobertura baja del piso de
    `.coveragerc` (`fail_under = 60`). El job de Linux del CI exige además **85 %** (parámetro
    `cobertura-minima`; cumple el ≥ 80 % pedido) y guarda el reporte HTML como _artifact_.
  - **AC2.** `make lint`/`run_linter_ruf` falla ante cualquier infracción de estilo.
  - **AC3.** El pipeline CI falla el PR ante test fallido, cobertura insuficiente (Linux), error
    de linting o de tipos, dependencias con vulnerabilidades conocidas o secretos en el historial.
  - **AC4.** `pre-commit install` configura hooks locales en un único comando (los hooks de ruff
    se ejecutan con `uv run`: usan la versión fijada en `pyproject.toml`, la misma del CI).
  - **AC5.** `docs/catalogo-criticidad.md` inicializado con al menos los módulos de autenticación
    y persistencia.
  - **AC6 — Job agregador y required status checks (nuevo, antes solo vivía en
    `ideas-aprendizaje.md` §8.9):** un job final `ci-ok` que depende de todos los demás y falla si
    alguno falló; registrado como _required status check_ de la rama, para que un PR con el CI en
    rojo no se pueda mergear.
  - **AC7 — `ruff format --check` (nuevo, antes §8.2):** el job `lint` también falla si algún
    archivo no está formateado con `ruff format`, no solo si viola reglas de estilo.
  - **AC8 — Smoke test de la CLI (nuevo, antes §8.14):** un paso que corre
    `uv run python src/main.py --help` y falla si el import se rompe.
- **Testing Mínimo:** manual — push a rama feature dispara el workflow; error de lint
  intencional hace fallar CI; cobertura por debajo del umbral hace fallar CI con mensaje
  explicativo; un PR con un job en rojo no puede mergearse (AC6).

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
> US-104 a US-109" agregada al principio de esta épica.
>
> **Aplicado el 2026-10-11 (trabajo adelantado de US-109, hecho en la rama de la US-104 antes de
> abrir su PR — ver la "Regla de alcance" de arriba):**
>
> - **AC6:** job agregador `ci-ok` (falla si algún job falló, se canceló o se salteó). **Falta un
>   paso manual en GitHub:** marcarlo como _required status check_ en Settings → Branches.
> - **AC7:** el job `lint` corre también `ruff format --check .`.
> - **AC8:** smoke test `python src/main.py --help` en los jobs de tests de Linux y Windows.
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

**Objetivo del hito:** automatizar la carga desde Ges Deportivo, producir métricas avanzadas
confiables, exponer estadísticas por CLI y asegurar la evolución controlada del esquema de base
de datos.

**Épicas:** 3 · **Historias:** 5 · **Esfuerzo total estimado:** ~30 días·persona

**Decisión previa requerida:** ninguna sobre ADR-002. _Nota (2026-10-03): el LaTeX decía que
ADR-002 bloqueaba este hito, pero la tabla de ADRs lo listaba bloqueando el Hito 4 — contradicción
ya resuelta en `docs/adr/ADR-002-framework-ui.md`: el Hito 2 es 100 % CLI y no usa GUI en ningún
momento (su propio texto lo aclara más abajo), así que no lo bloqueaba de verdad. **Sí hay dos
decisiones previas reales todavía sin cerrar para este hito:** ADR-003 (protocolo de ingesta
Excel, bloquea la US-201 — falta un archivo real de Ges Deportivo) y ADR-004 (versionado de DB,
bloquea la US-204 — falta decidir si vale agregar SQLAlchemy solo por el runner de Alembic). Ver
`docs/adr/`._

### Épica H2-E1: Integración "Ges Deportivo" y Gobernanza de Esquema

> **Nota de reordenamiento (2026-10-03):** la US-204 (Versionado de Esquema y Migraciones) vivía
> antes en la Épica H2-E3, mezclada sin ninguna relación temática con el motor analítico
> (US-203/US-205) — además aparecía físicamente _después_ de la US-205 en el documento, pese a
> tener un número menor. Se la mueve acá, antes de la US-201, porque esta última la necesita de
> verdad: el AC3 de la US-201 (verificar que la suma de puntos del boxscore coincida con el
> resultado final del partido) requiere agregar un campo nuevo a `Partido` que hoy no existe en
> el schema, y agregar una columna a una tabla existente sin perder datos es exactamente el
> problema que resuelve la US-204. La Épica H2-E3 quedó renombrada a solo "Inteligencia Deportiva
> (Pandas Engine)" — ver más abajo.

#### US-204 — Versionado de Esquema y Migraciones

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-101, ADR-004
- **Objetivo Funcional:** asegurar la evolución controlada del esquema de base de datos entre
  versiones sin pérdida de datos, con un runner que aplique migraciones en orden y registre cada
  resultado. **Se implementa antes que la US-201 porque esta la necesita:** agregar el campo de
  resultado final del partido que pide el AC3 de la US-201 es la primera migración real que corre
  sobre una base con datos (la de `001_init.sql` ya existente desde v0.1).
- **Archivos a crear:**

```text
src/infraestructura/persistencia/sql/migrations/
├── 001_init.sql          ← schema completo de v0.1; desde acá el schema no se toca directo
└── 002_*.sql              ← migraciones incrementales, NNN_descripcion_corta.sql, idempotentes

src/infraestructura/persistencia/migration_runner.py

test/test_migrations.py (upgrade multi-versión y rollback)
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

#### US-201 — Parseo de Planillas Excel con Pandas

- **Esfuerzo:** L (6-10 días) · **Prioridad:** Urgente (bloqueante) · **Dependencias:** US-106,
  US-204, ADR-003
- **Objetivo Funcional:** convertir planillas Excel externas de Ges Deportivo en datos
  persistibles sin transcripción manual, incluyendo modo _preview_ sin efecto secundario y
  reporte de calidad de la importación.
- **Narrativa:** Como analista, quiero procesar los archivos de Ges Deportivo para eliminar el
  error humano en la transcripción y agilizar el análisis.
- **Capa de Dominio:** **Excepciones:** `InvalidExcelFormatError`.
- **Capa de Aplicación:**
  - **Caso de uso:** `ImportarExcelUseCase`.
  - **DTOs:** `IngestRowDTO`, `IngestResultDTO`, `ResultadoImportacionDTO`,
    `IngestReportDTO` (contiene `creados`, `actualizados`, `rechazados` con causa, y totales).
- **Capa de Infraestructura:**
  - **Servicios:** `GesDeportivoExcelParser` (`src/infraestructura/ingest/excel_parser.py`) — lee
    con `pd.read_excel()`, mapea columnas al formato interno, convierte tipos, detecta filas
    malformadas; `IngestService` (`src/infraestructura/ingest/ingest_service.py`) — lógica de
    merge y validación cruzada.
  - **CLI:** `stats import excel --file <ruta>`.
- **Base de Datos:** afecta `club`, `jugador`, `competencia`, `partido`, `jugadorPartido`.
- **Criterios de Aceptación:**
  - **AC1 — Mapeo y Validación de Formato:** el parser lanza `InvalidExcelFormatError` si faltan
    columnas requeridas, antes de procesar.
  - **AC2 — Lógica de Merge:** si el jugador no existe (por DNI), se crea automáticamente; si ya
    existe, se vincula.
  - **AC3 — Verificación de Consistencia:** la suma de puntos individuales debe coincidir con el
    resultado final del partido cargado. **Este AC no es implementable tal cual está redactado
    con el schema actual:** no existe ningún campo que guarde el "resultado final" oficial del
    partido para comparar contra la suma de `jugadorPartido.puntos` — hoy solo se puede sumar el
    boxscore contra sí mismo, no contra un total independiente informado por la planilla de Ges
    Deportivo. Se necesita primero agregar a `Partido`/`partido` un campo de resultado final (ej.
    `puntosLocalFinal`/`puntosVisitanteFinal` — propuesta ya volcada en el DER de
    `docs/diagramas/diagramas.md` y en la sección 20) antes de poder escribir este AC como un
    test verificable.
  - **AC4 — Transaccionalidad:** el proceso es atómico por partido; si falla una estadística, no
    se guarda el partido ni sus jugadores asociados.
  - **AC5 — Vista Previa:** método `preview()` que valida el archivo sin persistir cambios.
  - **AC6 — Logs:** reporte con registros procesados, jugadores creados/vinculados y errores.
- **Reglas de Negocio:**
  - Fila sin DNI en el Excel → se rechaza (log y continuar).
  - Club o competencia inexistentes → se crean automáticamente con los nombres provistos.
  - El formato de fechas se valida según el estándar del proyecto.
- **Testing Mínimo:**
  - _Unitarias:_ mapeo de columnas, tipado correcto, detección de errores de formato; estrategias
    de merge y rechazo de filas inválidas.
  - _Integración:_ importación de fixture a DB `:memory:`, verificando persistencia y rollback
    ante error; modo `preview` no produce cambios.

**Archivos a crear:**

```text
src/infraestructura/ingest/
├── excel_parser.py
└── ingest_service.py

src/aplicacion/
├── casos_uso/importar_excel.py
└── dtos/ingest_dto.py

test/
├── test_excel_import.py (integración)
└── fixtures/ges_deportivo_sample.xlsx (con casos borde: fila sin DNI, puntos inconsistentes, jugador ya existente)
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
- **Testing Mínimo:**
  - _Unitarias (`test_formulas.py`):_ cobertura del **100%** de las funciones matemáticas, con
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

**Archivos a crear:**

```text
src/infraestructura/analytics/formulas.py

src/aplicacion/
├── casos_uso/calcular_estadisticas_avanzadas.py
├── casos_uso/generar_tabla_comparativa.py
├── casos_uso/generar_comparativa_jugadores.py    ← nuevo
└── dtos/metricas_dto.py

test/test_formulas.py
```

### Épica H2-E3: Inteligencia Deportiva (Pandas Engine)

#### US-203 — Integración de Motor Estadístico (Pandas Engine)

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-202
- **Objetivo Funcional:** conectar las Vistas SQL con DataFrames de Pandas para calcular métricas
  avanzadas automáticamente a partir de los datos cargados, sin acoplar fórmulas y persistencia.
- **Capa de Dominio:** **Interfaz:** `AnalyticsService` (`src/dominio/repositorios/analytics_service.py`)
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

#### US-205 — Consulta Estadística por CLI

- **Esfuerzo:** S (1-2 días) · **Prioridad:** Media · **Dependencias:** US-203, US-107
- **Objetivo Funcional:** exponer las métricas del motor analítico directamente desde la CLI,
  permitiendo al DT consultar líderes, estadísticas de un partido y comparativas de equipo sin
  necesidad de la interfaz gráfica.
- **Comandos CLI:**
  - `stats show partido <id>` — boxscore + métricas avanzadas del partido.
  - `stats leaders <temporada> [--top N]` — top-N por PTS, REB, AST, EFF. **Versión básica: la
    US-301 (Hito 3) extiende/reemplaza el caso de uso detrás de este mismo comando con filtros de
    competencia y multi-año — no es un comando nuevo que compita con este, es el mismo que gana
    funcionalidad más adelante (mismo patrón que `club_list`/`CrearClubUseCase` en el Hito 1).**
  - `stats compare <partido_id>` — comparativa equipo vs. rival.
- **Criterios de Aceptación:**
  - **AC1.** Cada comando produce salida tabular legible con alineación numérica correcta.
  - **AC2.** Filtros `--temporada` y `--competencia` funcionan en `stats leaders`.
  - **AC3.** Partido inexistente → mensaje descriptivo, no traceback.
  - **AC4.** Todos los valores consistentes con los calculados por `formulas.py`.
- **Testing Mínimo:** integración — cada subcomando con datos semilla verificando columnas y
  valores; partido/temporada inexistente → mensaje de error controlado.

**Archivos a crear (US-203 + US-205):**

```text
src/dominio/repositorios/analytics_service.py
src/infraestructura/analytics/pandas_analytics_service.py
src/aplicacion/casos_uso/calcular_estadisticas_partido.py

src/infraestructura/ui/cli/commands/     # un archivo por acción, misma convención del Hito 1 (AC1 de la US-107)
├── stats_show.py                         ← stats show partido
├── stats_leaders.py                      ← stats leaders
└── stats_compare.py                      ← stats compare

test/
├── test_analytics_service.py (integración)
└── test_stats_commands.py (integración)
```

> **Nota sobre el formatter:** se reutiliza `table_formatter.py` (ya existente desde la US-103)
> para la salida tabular — no se crea un `stats_formatter.py` aparte salvo que, al implementar
> esta US, aparezca una necesidad real que `table_formatter.py` no cubra (ej. un formato de
> comparativa lado a lado que `tabulate` no resuelva directo); si eso pasa, se extiende
> `table_formatter.py` en vez de duplicar un wrapper de formato nuevo.

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

### Épica H3-E1: Dashboards e Informes (CLI & Engine)

#### US-301 — Dashboards e Informes Interactivos

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-203, US-205
- **Objetivo Funcional:** proveer una visualización avanzada de datos en la terminal y preparar
  el motor de generación de gráficos para la futura GUI.
- **Narrativa:** Como DT, quiero ver tablas de líderes y gráficos de tendencia en mi terminal para
  analizar el rendimiento del equipo sin salir de la CLI.
- **Nota de reuso (no se pisa con la US-205):** `ObtenerLideresTemporadaUseCase` reemplaza al caso
  de uso simple que la US-205 arma detrás de `stats leaders` — es el mismo comando CLI
  (`stats_leaders.py`, ya creado en la US-205), con la lógica de ese comando ampliada acá, no un
  comando nuevo ni un archivo duplicado.
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
  - **Reportería CLI:** `TablaLideresReporter` (usa `rich`), `GraficoTendenciaReporter` (usa
    `textual` o `rich.panel`).
  - **Motor de Gráficos:** `ChartGenerator` (`src/infraestructura/analytics/chart_generator.py`)
    — genera figuras a partir de DataFrames, según la librería que defina ADR-007.
- **Vistas SQL requeridas:** `v_jugador_totales_temporada`, `v_partidos_resumen`.
- **Criterios de Aceptación:**
  - **AC1 — Dashboards en Consola:** uso de `rich` para mostrar top-5 de líderes por rubro
    (puntos, rebotes, EFF).
  - **AC2 — Generación de Figuras:** `ChartGenerator` produce gráficos (PNG o interactivos) en
    **menos de 2 segundos** para un dataset de referencia (3 temporadas, 20 equipos, 1200 filas
    de boxscore).
  - **AC3 — Interactividad:** filtro por temporada (`--season 2025`) **y por competencia**
    (`--competencia <id>`) en los comandos de reportes.
  - **AC4.** Valores graficados coinciden con los calculados por las vistas SQL.
  - **AC5 (nuevo) — Split local/visitante:** los reportes de líderes y de rendimiento aceptan un
    filtro opcional `--condicion local|visitante` para ver si un jugador/equipo rinde distinto
    según de local o de visitante (dato ya disponible en `partido.idClubLocal`/`idClubVisitante`,
    no requiere cambios de schema).
- **Implementación requerida:** `stats leaders --season 2025` invoca al caso de uso
  correspondiente y muestra resultados formateados.
- **Testing Mínimo:**
  - _Unitario:_ ordenamiento de líderes y desempate por criterio secundario; transformación de
    DataFrame a serie temporal para gráficos.
  - _Integración:_ reporter CLI + chart generator con datos semilla, verificando salida completa.
  - _Integración:_ `VerTrayectoriaJugadorUseCase` con un jugador que participó en más de una
    categoría/temporada en el dataset semilla.

> **Por qué se agregó esto:** la investigación de mercado (sección 20) confirma que el
> "performance trend" — aislar un jugador/métrica y ver su evolución con el tiempo, no solo un
> promedio fijo — es un feature estándar en apps de analítica deportiva (Hudl Assist,
> Hoopsalytics), y ya encaja con `GenerarGraficoRendimientoUseCase` que esta US ya tenía planeado;
> solo faltaba conectarlo explícitamente con un método de evolución en `AnalyticsService`.

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
  (`src/infraestructura/reports/pdf_generator.py`), librería según ADR-005.
- **Criterios de Aceptación:**
  - **AC1 — Formato Profesional:** encabezado con nombres de clubes, fecha, metadata; tablas de
    boxscore y métricas avanzadas con alineación numérica y cabeceras claras.
  - **AC2 — Convención de Nombres:** `boxscore_YYYY-MM-DD_Local_vs_Visitante.pdf`.
  - **AC3 — Robustez:** creación automática del directorio `exports/` si no existe; errores de
    I/O (ruta sin permisos, disco lleno) producen mensaje de recuperación, no crash.
- **Testing Mínimo:** generación exitosa de un PDF completo desde un `idPartido` con datos
  semilla (válido, no corrupto, abre con lector estándar); nombre de archivo y ruta esperados;
  ruta sin permisos → excepción controlada.

**Archivos a crear (US-301 + US-302):**

```text
src/aplicacion/casos_uso/
├── obtener_lideres_temporada.py
├── generar_grafico_rendimiento.py
└── exportar_reporte.py

src/aplicacion/dtos/reporte_dto.py

src/infraestructura/analytics/chart_generator.py
src/infraestructura/reports/
├── cli_leaderboard_reporter.py
└── pdf_generator.py

test/
├── test_leaderboard.py
├── test_chart_generator.py (integración)
└── test_pdf_export.py (integración)
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

**Archivos a crear:**

```text
src/infraestructura/persistencia/sql/views_scouting.sql
src/aplicacion/casos_uso/generar_scouting_rival.py
src/aplicacion/dtos/scouting_dto.py
test/test_scouting_rival.py (integración)
```

---

## 12. Hito 4 — Interfaz Multiplataforma y Entrega (v1.0)

**Objetivo del hito:** migrar a experiencia visual completa con Flet, cerrar el hardening de
seguridad, garantizar continuidad operativa mediante backup/restore y distribuir la aplicación
como binario autónomo para las plataformas objetivo.

**Épicas:** 4 · **Historias:** 4 · **Esfuerzo total estimado:** ~35 días·persona

**Decisión previa requerida:** ninguna — ✅ **ADR-002 ya aprobado** (Flet confirmado como
framework de UI, ver `docs/adr/ADR-002-framework-ui.md`).

> **Hallazgo de transcripción:** el `.md` del submódulo solo tenía **US-401** para este hito —
> **le faltaban por completo las épicas H4-E2 (Resiliencia/Backup, US-402), H4-E3
> (Seguridad, US-403) y H4-E4 (Empaquetado, US-404)**, que sí están en el LaTeX. Se completa con
> esa fuente. Ver sección 20.

### Épica H4-E1: Interfaz de Usuario Adaptable (GUI)

#### US-401 — Implementación de Interfaz Flet (Desktop/Mobile)

- **Esfuerzo:** L (6-10 días) · **Prioridad:** Alta · **Dependencias:** US-106, US-201, US-301,
  US-302, US-402, ADR-002
- **Objetivo Funcional:** ofrecer una interfaz visual completa reutilizando los casos de uso
  consolidados en hitos previos, operativa en desktop y mobile sin modificar la lógica de
  negocio.
- **Narrativa:** Como DT, quiero una experiencia fluida y visual que no requiera comandos para
  gestionar mis estadísticas desde mi PC o celular.
- **Nota de reuso (no se pisa con otras US):** las pantallas de esta US **no agregan lógica de
  negocio nueva**, solo envuelven casos de uso ya construidos — `GameEntryScreen` envuelve
  `CargarPartidoUseCase` (US-106); `ImportScreen` envuelve `ImportarExcelUseCase` (US-201); el
  botón de backup del AC4 envuelve `ExportarBackupUseCase`/`RestaurarBackupUseCase` (US-402, por
  eso se agrega como dependencia). Ninguna de estas tres piezas se reimplementa acá.
- **Capa de Infraestructura (UI):**
  - **Tecnología:** Flet (Python-based).
  - **Componentes:** `ChartComponent` (wrapper de los gráficos de US-301),
    `StatsTableComponent`.
  - **Navegación/Pantallas:** `DashboardScreen`, `GameEntryScreen`, `PlayerProfileScreen`,
    `ImportScreen`.
- **Criterios de Aceptación:**
  - **AC1 — Performance:** tiempo de arranque **< 3 segundos** (desktop, 4GB RAM, SSD, Python
    3.11+).
  - **AC2 — UX:** soporte de Modo Oscuro/Claro basado en preferencias del sistema.
  - **AC3 — Responsividad:** adaptación automática a resoluciones de PC (1080p) y Mobile (720p).
  - **AC4 — Gestión de Datos:** botón de "Sincronización/Backup" que invoca
    `ExportarBackupUseCase`/`RestaurarBackupUseCase` (**ya creados en la US-402** — esta US solo
    le agrega la pantalla/botón, no reimplementa el backup).
  - **AC5.** Formularios con validación visual (mensajes de error en campo, sin modal genérico).
  - **AC6.** La UI no contiene lógica de negocio; invoca casos de uso vía inyección de
    dependencias.
- **Testing Mínimo:**
  - _Unitario:_ validadores de formularios, reglas de navegación de estado de pantalla.
  - _Manual guiado:_ flujo Dashboard → GameEntry → PlayerProfile en desktop y mobile;
    importación de Excel desde la pantalla de importación.

**Archivos a crear:**

```text
src/infraestructura/ui/flet/
├── app.py
├── screens/
│   ├── dashboard_screen.py
│   ├── game_entry_screen.py
│   ├── player_profile_screen.py
│   └── import_screen.py
└── components/
    ├── chart_component.py
    └── stats_table_component.py

test/test_flet_validators.py
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

**Archivos a crear:**

```text
src/aplicacion/casos_uso/
├── exportar_backup.py
└── restaurar_backup.py

src/infraestructura/persistencia/backup_service.py
test/test_backup_restore.py (integración)
```

### Épica H4-E3: Seguridad de Datos Local

#### US-403 — Hardening de Seguridad Local

- **Esfuerzo:** M (3-5 días) · **Prioridad:** Alta · **Dependencias:** US-104, US-105, ADR-006
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
  - **AC7.** Política de sesión: expiración configurable, revocación inmediata en logout, limpieza
    idempotente.
  - **AC8.** Eventos de seguridad (fallos de login, cambios de contraseña) trazados en log sin
    exponer datos sensibles.
- **Testing Mínimo:** política de contraseñas (longitud, complejidad, lista comprometidas); ciclo
  hash → verificación, migración de hash legado; expiración y revocación de sesión; acceso a DB
  con y sin cifrado según configuración.

**Archivos a crear:**

```text
src/infraestructura/security/
├── credential_policy.py
├── compromised_password_store.py
└── db_encryption_adapter.py (adaptador SQLCipher, opcional)

docs/security/password_compromised_update_procedure.md
test/test_credential_policy.py
```

### Épica H4-E4: Empaquetado y Distribución

#### US-404 — Empaquetado y Distribución Multiplataforma

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
  - **AC4.** Versión embebida en la aplicación (About screen / CLI `--version`) coincide con el
    tag de release.
  - **AC5.** `CHANGELOG.md` actualizado siguiendo formato _Keep a Changelog_ en cada release.
- **Testing Mínimo:** instalar binario desktop en máquina limpia (sin Python) y ejecutar flujo
  completo; instalar APK en dispositivo/emulador Android y verificar arranque; el pipeline de
  release ejecuta tests completos antes de generar artefactos.

**Archivos a crear:**

```text
build/
├── build_desktop.py   ← script PyInstaller (Windows/Linux/macOS)
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
9. **Si incluye UI:** validada manualmente en al menos dos plataformas (desktop + mobile).
10. **Trazabilidad:** eventos de log relevantes implementados con `correlation_id` (ver US-108).
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
  scouting entre DTs (con consentimiento explícito).
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
| **Clubes**         | `SqliteClubRepositorio`        | `v_listas_detalle`                          | ✅ funcional, sin tests dedicados                                        |
| **Jugadores**      | `SqliteJugadorRepositorio`     | `v_jugador_totales_temporada`               | ⚠️ bug en `link_to_club` (ver sección 20)                                |
| **Competencia**    | `SqliteCompetenciaRepositorio` | `v_listas_detalle`                          | ⚠️ implementado, con 3 bugs y 2 métodos sin implementar (ver sección 20) |
| **Partidos/Stats** | `SqliteJuegoRepositorio`       | `v_partidos_resumen`, `v_boxscore_completo` | ❌ no funcional (ver sección 20)                                         |

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
| ADR-002 | Framework UI               | Hito 4        | ✅ Flet, se descarta Compose Multiplatform (ya definido, ver `docs/adr/ADR-002-framework-ui.md`)                                                                                  |
| ADR-003 | Protocolo de Ingesta Excel | US-201/US-202 | ⏳ Pendiente de archivo real de Ges Deportivo (ver `docs/adr/ADR-003-protocolo-ingesta-excel.md`)                                                                                 |
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
  la US-108 (JSON estructurado + `correlation_id`), no un reemplazo.
- **Análisis estático:** el proyecto usa `ruff` en la práctica (`pyproject.toml`,
  `.github/workflows/linter.yml`), no `flake8`/`pylint` como sugería el borrador original del
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
  pide la US-106 (que por eso quedó reescrita: este trabajo ya está hecho, ver su "Estado real").
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
  `docs/diagramas/diagramas.md` y anotada en US-106 y US-201.
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
  con la CLI correspondiente. Ver `docs/info_modulo/03-casos-de-uso.md` y
  `docs/context_ia/2026-08-17-us103-explicada-en-profundidad.md` para el detalle.
- ✅ **Huecos de alcance detectados y cerrados (2026-09-20):** el PRD prometía "categorías y listas de buena fe" en el pilar 2, pero ninguna US planificaba crear/listar categorías, listar competencias
  ni administrar la lista de buena fe, aunque las tablas y los métodos del repositorio existían. Se incorporaron a la US-103 (ver el recuadro "Alcance ampliado" de esa US).
  ✅ **Auditoría de cierre de la US-103 (2026-09-20):** se cerró también el ciclo de vida del vínculo jugador-club (`jugador unlink`, regla de no superposición), **quitar un jugador de la lista** (`lista remove`),
  las validaciones de valor de las entidades (`DatoInvalidoError`) y `partido list` con nombres (vista `v_partidos_resumen`).
  **Decisiones que siguen abiertas:** (1) **cómo valida la US-106 la lista cuando el partido no guarda la categoría** (ver la regla agregada en la US-106); (2) si la regla "el jugador debe tener vínculo vigente
  con el club" para habilitarlo admite excepciones (préstamos); (3) **editar o borrar** clubes, competencias y jugadores no está en ninguna US (el PRD solo pide crear, listar y vincular), por lo que un dato
  mal cargado hoy solo se corrige en la base; (4) **`jugador historial`** (ver todos los clubes por los que pasó un jugador): el repositorio ya expone `historial_vinculos`, falta el caso de uso y el comando si se los necesita.

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

### Lo que ya está sólido

- ✅ `SQLiteManager` (`database_manager.py`): conexión, `PRAGMA foreign_keys`, `row_factory`,
  inicialización de schema/vistas/seed/limpieza, con manejo de errores y logging.
- ✅ Las 4 vistas SQL (`views.sql`) funcionan y están probadas, incluyendo protección contra
  división por cero (salvo el bug de agrupación de `v_jugador_totales_temporada` ya anotado).
- ✅ Los 5 repositorios SQLite funcionales y testeados, con manejo de errores logueado
  consistentemente.
- ✅ `mypy --strict` en verde (0 errores) y suite completa en verde (53 tests).
- ✅ Pipeline CI real: `pip-audit`, `gitleaks`, `ruff` (lint), `mypy --strict` y tests en
  Linux/Windows/Docker con matriz de Python 3.11–3.14 (Windows solo con 3.13; cobertura ≥ 85 % en Linux). Falta el job
  agregador con _required status checks_ (ver `docs/ideas-aprendizaje.md`, 8.9).
- ✅ Suite de tests dividida por repositorio (`test_repositorios_*.py`), más fácil de mantener que el archivo único anterior — aunque dos de esos archivos todavía están vacíos (ver arriba).
