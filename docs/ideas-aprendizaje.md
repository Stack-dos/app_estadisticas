# Ideas de servicios/funcionalidades chicas para aprender

> Propuestas puntuales, no demasiado complejas, pensadas como ejercicios de aprendizaje sobre la
> marcha del proyecto — no reemplazan al roadmap del PRD, son "side quests" chicas que enseñan un
> concepto concreto de Python y encajan naturalmente en algún punto de la arquitectura ya
> definida. Ninguna tiene código acá a propósito — son propuestas para que las implementen
> ustedes.

## 1. Decorador de reintento con backoff

**Qué es:** una función que envuelve a otra y, si falla, la reintenta automáticamente con espera
creciente (1s, 2s, 4s...) en vez de fallar directo. Útil para operaciones de I/O que pueden fallar
transitoriamente (leer un Excel bloqueado por otro proceso, escribir a disco cuando el antivirus
está escaneando, etc.).

**Por qué es un buen ejercicio:** enseña **decoradores** de Python (`@mi_decorador` arriba de una
función), que es una herramienta que se usa todo el tiempo en frameworks reales (Flask, pytest,
FastAPI la usan constantemente) y que cuesta entender la primera vez. También es la misma idea de
backoff exponencial que aparece en sistemas distribuidos reales (la vimos en detalle en otro
proyecto con MQTT/reconexión de red).

**Dónde encajaría:** en `infraestructura/ingest/` (Hito 2, US-201), envolviendo la lectura del
Excel de Gesdeportiva — si el archivo está momentáneamente bloqueado (por ejemplo, todavía
abierto en Excel), reintenta un par de veces antes de fallar.

## 2. Cache simple en memoria para consultas de solo lectura

**Qué es:** guardar en memoria (un diccionario, o usando `functools.lru_cache`) el resultado de
una consulta a una vista SQL que no cambia seguido dentro de la misma ejecución del programa —
por ejemplo, la lista de competencias o categorías, que rara vez cambia mientras el usuario está
cargando un partido.

**Por qué es un buen ejercicio:** enseña **memoización** y, más importante, cuándo _no_ usarla —
el desafío real de cualquier cache no es guardar el dato, es saber cuándo invalidarlo (¿qué pasa
si el usuario crea una competencia nueva mientras el cache todavía tiene la lista vieja?). Es una
introducción liviana a un problema que en sistemas más grandes se vuelve mucho más difícil.

**Dónde encajaría:** en la capa de infraestructura, como un wrapper opcional alrededor de
`obtener_categorias()`/`obtener_todas_competencias()` del futuro
`SqliteCompetenciaRepositorio` — nunca en el dominio, porque el dominio no debería saber que
existe un cache.

## 3. Exportador a CSV de cualquier vista SQL

**Qué es:** una función chica que toma el nombre de una vista (`v_jugador_totales_temporada`, por
ejemplo) y la vuelca a un archivo `.csv`, reutilizando `pandas.read_sql()` +
`DataFrame.to_csv()`.

**Por qué es un buen ejercicio:** es la introducción más suave posible a Pandas — antes de meterse
con las fórmulas estadísticas más elaboradas de la US-202 (eFG%, EFF, PPP), esto ya te obliga a
practicar el patrón básico "SQL → DataFrame → algo útil" que vas a repetir todo el Hito 2.

**Dónde encajaría:** `infraestructura/analytics/`, como una utilidad chica separada de
`formulas.py` (que según el PRD debe quedar 100% libre de I/O — el exportador si necesita tocar
disco, así que va aparte).

## 4. Loader de configuración por variables de entorno

Este es el que más se amplió a pedido: cómo funciona, qué configuraciones incluiría, y cómo se
conecta con el empaquetado final del Hito 4.

### Cómo funciona

Hoy, `config/rutas.py` calcula rutas relativas al proyecto (dónde está `schema.sql`, dónde va el
`.db`, dónde van los logs) — todo eso está bien porque son ubicaciones que **no dependen del
entorno**, siempre son "relativas a donde vive el código". Un **loader de configuración** es otra
cosa: resuelve valores que **sí** cambian según el entorno (desarrollo vs. testing vs. la
computadora del usuario final) — por ejemplo, el nivel de logging, o si se debe usar una DB en
memoria en vez del archivo real.

El patrón típico en Python:

1. Un archivo `.env` en la raíz del proyecto (con formato `CLAVE=valor` por línea) — **nunca se
   versiona** (va en `.gitignore`), porque puede tener secretos o valores específicos de la
   máquina de cada desarrollador.
2. Un `.env.example` **sí versionado**, con las mismas claves pero valores de ejemplo/vacíos —
   sirve de plantilla para que cualquiera que clone el repo sepa qué variables tiene que definir.
3. La librería `python-dotenv` lee el `.env` al arrancar el programa y carga esas claves a
   `os.environ` (las variables de entorno del proceso).
4. Un módulo (podría llamarse `config/settings.py`) es el **único** lugar del código que llama
   `os.getenv("CLAVE", valor_por_defecto)` — expone esos valores como constantes o atributos de
   una clase `Settings`. El resto de la aplicación nunca llama `os.getenv` directamente; le pide
   el valor a `Settings`. Esto es importante: si mañana cambia _de dónde_ viene la configuración
   (ver el punto de empaquetado más abajo), solo se toca `Settings`, nada más en el proyecto se
   entera del cambio.

### Qué configuraciones incluiría

Uniendo lo que hoy ya existe (derivado, no como variable de entorno todavía) con lo que falta:

| Variable                                         | Hoy                                        | Con el loader                                                                                                  |
| ------------------------------------------------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Ruta de la DB (`estadisticas.db`)                | Calculada en `rutas.py`, fija              | Podría permitir override (`STATSPRO_DB_PATH`) para testing o para que el usuario elija dónde guardar sus datos |
| Rutas de los `.sql` (schema/views/seed/limpieza) | Calculadas en `rutas.py`                   | Se quedan como están — son parte del código, no del entorno                                                    |
| Carpeta de logs                                  | Calculada en `rutas.py`                    | Igual — parte del código                                                                                       |
| Nivel de logging                                 | Fijo en `logger.py` (INFO al archivo)      | `STATSPRO_LOG_LEVEL` — `DEBUG` en desarrollo, `INFO` o `WARNING` en producción, sin tocar código               |
| Modo de base de datos                            | Implícito en cada test (`:memory:` a mano) | `STATSPRO_ENV=test` podría hacer que `Settings` fuerce `:memory:` automáticamente                              |
| Configuración de Gesdeportiva (Hito 2+)         | No existe todavía                          | Si el formato de columnas cambia entre clubes, podría parametrizarse acá en vez de hardcodear en el parser     |

La regla general: **si dos personas del equipo, o dos entornos (tu máquina / CI / la compu del
usuario final), necesitarían un valor distinto para lo mismo, es candidato a variable de
entorno.** Si el valor es siempre el mismo sin importar dónde corra (como las rutas relativas al
código), se queda en `rutas.py` tal cual está.

### Por qué separar esto de `rutas.py`

`rutas.py` responde "¿dónde, dentro de la carpeta del proyecto, está tal archivo?" — es
determinístico, no cambia según quién lo ejecute. Un loader de configuración responde "¿qué
comportamiento quiero en este entorno particular?" — sí cambia según quién y dónde lo ejecute. Son
preguntas distintas, aunque hoy convivan mezcladas en el mismo módulo por simplicidad (razonable
para el tamaño actual del proyecto).

### Cómo se conecta con el empaquetado final (Hito 4, US-404)

Esta es la parte más interesante a largo plazo. Cuando el proyecto pase de "lo corro con
`python src/main.py` desde mi entorno de desarrollo" a "lo distribuyo como un ejecutable que
alguien más instala en su computadora" (PyInstaller o `flet build`), **ya no existe un `.env` de
desarrollador** — el usuario final ni sabe qué es eso, y no tiene sentido pedirle que edite un
archivo de texto con sintaxis de variables de entorno.

En ese escenario, la configuración pasa a vivir en un archivo tipo
`~/.statspro/config.json` (o `%APPDATA%\StatsPro\config.json` en Windows) — un archivo que:

1. **Se genera automáticamente la primera vez que corre la app**, con valores por defecto
   sensatos (nivel de log INFO, ruta de DB en una carpeta estándar del usuario).
2. El usuario puede editarlo a mano si quiere cambiar algo (o, más adelante, la propia GUI en
   Flet podría tener una pantalla de "Configuración" que lo edite por él).

La pieza clave del diseño: **el mismo módulo `Settings` que en desarrollo lee del `.env` puede,
en el build empaquetado, leer de ese `config.json` en su lugar** — el resto de la aplicación
(los casos de uso, los repositorios, la UI) le siguen pidiendo valores a `Settings` exactamente
igual, sin enterarse de si la fuente real es un `.env`, variables de entorno del sistema, o un
JSON en el home del usuario. Es el mismo principio de **"Configuración Externalizada"** que
mencionamos charlando de otro proyecto (ahí aplicado a Kubernetes con ConfigMaps) — acá el
"entorno de despliegue" no es un clúster, es la computadora del entrenador que instaló la app,
pero el problema que resuelve es idéntico: que el comportamiento de la app dependa de dónde
corre, sin tener que tocar código para cada instalación.

## 5. Validadores de reglas de negocio como funciones puras

**Qué es:** en vez de meter toda la validación dentro de `__post_init__` de cada entidad, separar
funciones chicas y testeables (`validar_dni(dni: int) -> bool`,
`validar_fechas_afiliacion(desde: str, hasta: str | None) -> bool`) que las entidades usan
internamente.

**Por qué es un buen ejercicio:** funciones puras (mismo input → mismo output, sin efectos
secundarios) son lo más fácil de testear que existe en programación — ideal para practicar
`pytest` con casos borde antes de meterse con la lógica más compleja de la US-103.

**Dónde encajaría:** un módulo nuevo, por ejemplo `dominio/validaciones.py`, usado desde
`__post_init__` de las entidades que lo necesiten.

## 6. Un comando CLI mínimo, antes de construir toda la US-106

> **Obsoleta (2026-10-31):** la CLI ya se construyó en la US-103 y se retira en la US-105. Queda como registro de la idea.

**Qué es:** antes de armar toda la infraestructura de Command Pattern que pide la US-106, un
experimento chico: un único archivo con `argparse` que soporte `stats club list` y lea
directamente de `v_partidos_resumen` (sin pasar por casos de uso todavía).

**Por qué es un buen ejercicio:** `argparse` tiene una curva de aprendizaje propia (subparsers,
argumentos posicionales vs. opcionales) — vale la pena practicarlo aislado, en un script chico
descartable, antes de comprometerse con la arquitectura completa de comandos que pide el PRD.

## 7. Completar el pipeline de CI (hoy solo lintea y testea)

> **Nota (2026-09-20):** esta sección se escribió cuando el CI tenía solo `linter.yml` y `test.yml`. Hoy existe `MainAction.yml` y varias de estas ideas ya están hechas (mypy, pip-audit, Docker). El estado actual y lo que falta está en la **[sección 8](#8-revisión-del-cicd-actual-mainaction--qué-le-falta-y-cómo-completarlo)**.

Hoy `.github/workflows/` tiene dos jobs reales: `linter.yml` (ruff, solo reglas `E`/`I`) y
`test.yml` (pytest + cobertura, en Linux y Windows, sube el log como artifact si falla). Es una
base sólida, pero para que sea "un CI completo" en el sentido de lo que hace un equipo profesional
faltan piezas — cada una es chica de agregar (son pasos de YAML, no lógica nueva) y enseña un
concepto de CI/DevOps distinto:

### 7.1 Que la cobertura realmente bloquee el PR

`test.yml` genera el reporte de cobertura (`--cov-report=html`), pero **nada falla si la
cobertura es baja** — el PRD (US-108, AC1) pide explícitamente que el pipeline "falle si
cobertura < 80% en módulos no críticos", y hoy eso no está pasando. La forma más simple: agregar
`--cov-fail-under=80` al comando de `pytest` (o configurarlo directamente en `pytest.ini`, que ya
existe, con `[coverage:report] fail_under = 80`). Es literalmente un flag — el ejercicio de
aprendizaje acá es entender la diferencia entre "medir" algo y "hacer que ese número tenga
consecuencias".

### 7.2 Chequeo de formato, no solo de lint

`ruff check --select E --select I` valida estilo (E) e imports ordenados (I), pero **no valida
que el código esté formateado** de manera consistente — eso es un chequeo distinto
(`ruff format --check .`, que falla si algún archivo no está formateado como lo formatearía
`ruff format`, sin modificarlo). Ya tienen `black` en `.pre-commit-config.yaml` para el hook
local; vale la pena decidir (con un ADR chico, si quieren) si el formateador oficial del proyecto
es `black` o `ruff format`, y que el CI valide exactamente eso — hoy el CI no valida ningún
formateador, solo estilo/imports.

### 7.3 Revisión de tipos con `mypy`

El código ya usa type hints en todos lados (`int | None`, `list[Club]`, etc.), pero nada verifica
que esos tipos sean consistentes — `mypy` (o `pyright`) los analiza estáticamente y detecta, por
ejemplo, que una función declarada `-> Club` en realidad puede devolver `None` (que es
justo lo que pasa hoy en `sqlite_club_repositorio.py::buscar_por_id`, que devuelve `None` pero
está tipado como `-> Club`, no `-> Club | None`). Es un buen ejercicio para aprender qué tan en
serio se puede tomar Python con tipado gradual, y probablemente va a encontrar un par de
inconsistencias reales como esa en el código actual.

### 7.4 Escaneo de dependencias con vulnerabilidades conocidas

Un paso con `pip-audit` (herramienta oficial del packaging de Python) que revisa
las dependencias (`pyproject.toml` / `uv.lock`) contra una base de datos de vulnerabilidades conocidas (CVEs) y falla el
build si alguna dependencia instalada tiene una vulnerabilidad reportada. Es un paso de una sola
línea (hoy: `uvx pip-audit -r requirements-audit.txt`, ver 8.10) y es exactamente el tipo de
chequeo que un proyecto "profesional" tiene y uno de aprendizaje normalmente no — buena
introducción al concepto de _supply chain security_ sin ninguna complejidad de implementación.

### 7.5 Detección de secretos accidentales

Un paso (ej. con la acción `gitleaks`) que escanea el diff del PR buscando patrones de
contraseñas, tokens o claves que se hayan subido por error. Particularmente relevante acá porque
el proyecto maneja hashes de contraseñas y, más adelante, quizás credenciales de la base de datos
o de algún servicio externo (Gesdeportiva). Es un solo paso de YAML, sin configuración adicional
para el caso base.

### 7.6 Validar que el schema/vistas SQL siguen siendo válidos, aislado de pytest

Ya está cubierto indirectamente por `test.yml` (que corre toda la suite, incluidos
`test_schema_sql_ejecuta_sin_errores` y `test_views_sql_ejecuta_sin_errores`), así que esto no es
un job nuevo — es más una nota: si el proyecto crece y separar "tests rápidos" de "tests de
integración con DB" empieza a tener sentido (con markers de pytest, `@pytest.mark.integration`),
ahí sí valdría la pena un job de CI aparte que corra primero los rápidos y falle temprano antes
de gastar tiempo en los de integración. Por ahora, con una suite que corre en pocos
segundos, no hace falta — mencionarlo para cuando la suite crezca.

### 7.7 Actualización automática de dependencias

Un archivo `.github/dependabot.yml` (nada de workflow, es configuración declarativa que lee
GitHub directamente) que abre un PR automático cada vez que una dependencia de
`pyproject.toml` tiene una versión nueva. Cero mantenimiento una vez configurado, y es la
forma más simple de no terminar con dependencias congeladas en versiones de hace un año.

### 7.8 Build de la imagen Docker, si llegan a armarla

Si terminan armando el `Dockerfile` de `docs/info_modulo/10-docker-para-tests.md`, un paso lindo para
sumar después es que el propio CI construya la imagen en cada PR (`docker build .`) — así un
`Dockerfile` roto se detecta en el PR, no cuando alguien lo necesita usar. Directamente conecta
esta idea con la guía de Docker que ya armamos.

**Para no perderse en la lista:** si tuvieran que elegir con qué arrancar, el orden de
"impacto vs. esfuerzo" sería 7.1 (cobertura real) → 7.3 (mypy, porque ya encontró un bug real de
tipado arriba) → 7.4/7.5 (seguridad, un paso cada uno) → el resto según les vaya interesando.

---

## 8. Revisión del CI/CD actual (MainAction) — qué le falta y cómo completarlo

> **Estado al 2026-09-20.** Esta sección reemplaza en la práctica a la 7, que se escribió cuando el CI tenía solo dos workflows sueltos (`linter.yml` y `test.yml`).
> Hoy hay un único workflow, `MainAction.yml`, bastante más completo. Acá está descrito **qué hace hoy**, **qué le falta** y, para cada faltante, **qué es, por qué importa y cómo agregarlo paso a paso**,
> pensado para alguien que nunca tocó un CI. Las mejoras marcadas como _"ya hecho"_ ya están aplicadas (el 2026-09-20); el resto son recomendaciones.

### 8.0 Vocabulario básico (leer primero si es la primera vez)

| Palabra                                | Qué significa                                                                                                                                                               |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CI** (_Integración Continua_)        | Un robot que, cada vez que alguien propone un cambio, **baja el código, lo prueba y avisa** si algo se rompió. Así los errores se descubren en minutos y no semanas después |
| **CD** (_Entrega/Despliegue Continuo_) | El paso siguiente: si todo está bien, el robot además **publica** el programa (lo empaqueta, lo sube a un servidor, genera un instalador…). Ver 8.15                        |
| **GitHub Actions**                     | El servicio de GitHub que corre esos robots. Se configura con archivos `.yml` dentro de la carpeta `.github/`                                                               |
| **Workflow**                           | Un archivo `.yml` en `.github/workflows/` que describe **una receta completa** (acá: `MainAction.yml`)                                                                      |
| **Trigger** (_disparador_)             | **Cuándo** se ejecuta el workflow. Se declara en la clave `on:` (ej. "cuando se abre un Pull Request")                                                                      |
| **Job**                                | Un bloque de trabajo dentro del workflow. Cada job corre en **su propia máquina limpia**, y por defecto los jobs corren **en paralelo** salvo que se declare `needs:`       |
| **Runner**                             | La máquina virtual donde corre un job (`ubuntu-latest`, `windows-latest`…). Arranca **vacía** en cada ejecución                                                             |
| **Step** (_paso_)                      | Una instrucción dentro de un job: o un comando (`run:`) o una acción reutilizable (`uses:`)                                                                                 |
| **Action**                             | Un paso empaquetado y reutilizable que alguien publicó (ej. `actions/checkout@v4` baja el código). El `@v4` es la versión                                                   |
| **Composite action**                   | Una action propia hecha de varios pasos. En este repo están en `.github/actions/` y se usan con `uses: ./.github/actions/...`                                               |
| **Artifact**                           | Un archivo que el job guarda para poder descargarlo después desde la página de la ejecución (ej. un reporte)                                                                |
| **Pull Request (PR)**                  | La propuesta de incorporar una rama a otra (ej. `feature/us103` a `main`). El CI corre sobre el PR **antes** de que alguien lo apruebe                                      |
| **Required status check**              | Una regla de GitHub que **impide mergear** un PR si un job determinado no terminó en verde. Sin esta regla, el CI avisa pero no bloquea (ver 8.9)                           |

### 8.1 Qué hace hoy el CI

Se dispara al abrir/actualizar un Pull Request, con cada `push` a `main` o `develop`, y manualmente (botón _Run workflow_). Ver 8.5. Tiene 7 jobs; los marcados con "matriz" se repiten una vez por cada versión de Python (3.11, 3.12, 3.13 y 3.14); Windows corre solo con la 3.13. Una corrida completa son **16 ejecuciones**:

| Job             | Corre en | Qué hace                                                                                                                      | Espera a |
| --------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------- | -------- |
| `check_dep`     | Linux    | Exporta las versiones fijadas de `uv.lock` y las revisa con **pip-audit** buscando vulnerabilidades conocidas                 | —        |
| `gitleaks`      | Linux    | Escanea **todo el historial** de git buscando secretos (contraseñas, tokens). Ver 8.12                                        | —        |
| `lint`          | Linux    | `ruff check --select E --select I .` con la versión de ruff de `uv.lock`                                                      | —        |
| `static`        | Linux    | `mypy src/ --strict` con la versión de mypy de `uv.lock`, chequeando contra cada versión de Python (matriz)                   | —        |
| `tests-linux`   | Linux    | `pytest` con cobertura **mínima de 85 %**; guarda el reporte HTML como _artifact_ (matriz)                                    | `lint`   |
| `tests-windows` | Windows  | `pytest` con cobertura, solo con Python 3.13 (sin matriz)                                                                     | `lint`   |
| `tests-docker`  | Linux    | Construye la imagen de `Dockerfile.test` con esa versión de Python y corre los tests adentro (matriz)                         | `lint`   |

**Qué de la sección 7 ya está resuelto:** el chequeo de tipos (7.3, job `static`), el escaneo de dependencias (7.4, `check_dep`), el build de Docker (7.8, `tests-docker`) y, desde el 2026-09-20,
la cobertura mínima que bloquea de verdad (7.1, 85 % en Linux), la detección de secretos (7.5, `gitleaks`) y la actualización automática de dependencias (7.7, Dependabot).
**Sigue pendiente:** el chequeo de formato (7.2), ver 8.2.

**Cambios hechos el 2026-09-20 (migración a uv):** se eliminó `requerimientos.txt` (todo está en `pyproject.toml` + `uv.lock`), por lo que se actualizaron los pasos de instalación de las actions de tests y del job `check_dep`
(ahora usan `astral-sh/setup-uv` y `uv sync --locked`). Eso trajo de regalo **caché de dependencias** (`enable-cache: true`, ver 8.8) y dependencias **exactamente reproducibles** (ver 8.10).

**Cambios hechos el 2026-09-20 (segunda tanda):** una sola versión de ruff y mypy en pre-commit y CI (8.4); la versión de Python como parámetro de las actions y matriz 3.11 a 3.14 en Linux, mypy y Docker, con Windows solo en 3.13 (8.3); disparo también con `push` (8.5);
`concurrency`, `permissions` y `timeout-minutes` (8.6); reporte de cobertura guardado y umbral de 85 % en Linux (8.7); Dependabot (8.11) y gitleaks (8.12).
Al revisar el workflow se corrigieron además **tres referencias que no funcionaban** (se detallan en el informe de sesión, Bloque H):

- `astral-sh/setup-uv@v10` **no existe**: esa action ya no publica etiquetas móviles de versión mayor, hay que indicar la versión exacta (`@v10.1.0`).
- `pypa/pip-audit-action@v1.6.0` **no existe**: la action real se llama `pypa/gh-action-pip-audit` (`@v1.1.0`).
- `actions/checkout@v4` corre sobre Node 20, que GitHub retiró de sus máquinas el 2026-09-16: se pasó a `@v7` (Node 24).

**Ojo:** todo esto se probó **en la máquina local** (ver el informe), no en GitHub: la primera corrida real es la prueba definitiva.

---

### 8.2 Chequeo de formato: `ruff format --check`

**Qué es.** El _lint_ (`ruff check`) revisa **reglas** (líneas largas, imports desordenados). El _formato_ (`ruff format`) es otra cosa: reescribe el código con un estilo uniforme (comillas, espacios, saltos de línea)
para que todo el equipo escriba "igual" y los cambios del PR muestren solo diferencias reales y no discusiones de estilo. `ruff format --check` **no modifica nada**: solo falla si algún archivo no está formateado.

**Por qué importa.** Sin este chequeo, cada persona formatea distinto y los PR se llenan de cambios de espacios que tapan lo importante.

**Qué hay hoy.** El archivo `.pre-commit-config.yaml` corre el formateador de ruff **en la máquina de cada persona, al hacer commit** (si instaló _pre-commit_), pero el CI no lo verifica: si alguien commitea sin pre-commit, nadie se entera. (Desde el 2026-09-20 esos hooks usan la misma versión de ruff que el CI: ver 8.4.)
Hoy hay archivos sin formatear en el repo (por ejemplo `src/infraestructura/repositorios/sqlite_club_repositorio.py`, por espacios sobrantes al final de líneas de docstring).

**Qué hacer, paso a paso.**

1. Formatear todo el proyecto una vez (para partir de cero): `uv run ruff format .` y commitear el resultado en un commit aparte (ej. `STYLE: formatea el proyecto con ruff format`).
2. Sumar el chequeo a la action de lint (`.github/actions/style/ruff/action.yml`), debajo de `ruff check`:

```yaml
- name: Verificar formato
  shell: bash
  run: uv run --no-sync ruff format --check .
```

1. **Unificar versiones de ruff:** _ya hecho_ (ver 8.4). Pre-commit, el CI y tu máquina usan la versión de `pyproject.toml`/`uv.lock`, así que ya no pueden formatear distinto.

**Cómo comprobar que funcionó.** Deformá a propósito un archivo (agregá espacios de más), hacé un PR de prueba y confirmá que el job `lint` falla con "would reformat".

---

### 8.3 Versiones de Python: probar con más de una (_ya hecho_)

**Qué es.** Un programa puede funcionar en Python 3.13 y romperse en 3.11 (o al revés), porque el lenguaje cambia entre versiones. Una **matriz** (_matrix strategy_) hace que GitHub repita el mismo job con distintos valores.

**Por qué importa.** `pyproject.toml` promete `requires-python = ">=3.11"`: es decir, que anda en 3.11, 3.12, 3.13… pero antes solo se probaba en **algunas** versiones (tests en 3.11; lint, mypy y Docker en 3.13; `mypy` configurado para 3.11).

**Qué se hizo.**

1. Todas las actions (`style/ruff`, `style/mypy`, `coverage/linux`, `coverage/windows` y `coverage/docker`) reciben la versión como **parámetro** `python-version`. Si no se les pasa nada, usan `"3.11"` (la mínima que promete el proyecto):

```yaml
inputs:
  python-version:
    description: "Versión de Python con la que se corren los tests (ej. 3.12)"
    required: false
    default: "3.11"

runs:
  using: "composite"
  steps:
    - uses: astral-sh/setup-uv@v10.1.0
      with:
        python-version: ${{ inputs.python-version }}
        enable-cache: true
```

1. En `MainAction.yml`, los jobs `static`, `tests-linux` y `tests-docker` se repiten con una **matriz** (3.11 a 3.14) y le pasan a la action la versión de cada vuelta (`tests-windows` no usa matriz: le pasa fijo `python-version: "3.13"`):

```yaml
tests-linux:
  strategy:
    fail-fast: false # si falla la 3.11, igual sigue probando las demás (así ves todo junto)
    matrix:
      python-version: ["3.11", "3.12", "3.13", "3.14"]
  steps:
    - uses: actions/checkout@v7
    - uses: ./.github/actions/coverage/linux
      with:
        python-version: ${{ matrix.python-version }}
```

1. Detalles por herramienta:
   - **mypy:** además de instalar esa versión de Python, se le pasa `--python-version`, que pisa el `python_version = "3.11"` de `pyproject.toml`: los tipos se chequean contra la versión de cada vuelta.
   - **Docker:** `Dockerfile.test` tiene `ARG PYTHON_VERSION=3.11` y la action hace `docker build --build-arg PYTHON_VERSION=...`. A mano: `make docker_test PYTHON_VERSION=3.13`.
   - **ruff (`lint`):** no usa matriz, porque su resultado no depende de la versión de Python que lo ejecuta. Corre una sola vez.
   - **Windows:** una sola versión (3.13), sin matriz. Sirve para detectar problemas propios del sistema operativo (rutas, saltos de línea, SQLite); lo que depende de la versión de Python ya se prueba en Linux. Además, en un repositorio privado los minutos de Windows cuestan el doble.

**Para agregar una versión nueva** (por ejemplo 3.15): sumarla a la lista `python-version` de los **3 jobs con matriz** (`static`, `tests-linux` y `tests-docker`; la lista está repetida en cada uno).

**Cómo comprobar.** En la pestaña _Actions_ de un PR aparecen las ejecuciones `static (3.11)` … `tests-docker (3.14)`. Localmente: `make docker_test PYTHON_VERSION=3.14`.

> **Ojo:** al usar una matriz, los nombres de los jobs cambian (llevan la versión entre paréntesis). Por eso conviene el job agregador de 8.9, para no tener que registrar cada nombre en las reglas de GitHub.

---

### 8.4 Una sola versión de ruff y mypy (_ya hecho_; queda un detalle)

**Qué es.** Antes había **tres** versiones de ruff en juego: la de `pyproject.toml` (`0.16.8`), la de `.pre-commit-config.yaml` (`v0.6.9`) y la del CI, que hacía `pip install ruff` **sin versión** (la última que existiera ese día). Con mypy pasaba lo mismo entre `pyproject.toml` y el CI.

**Por qué importa.** Un día publican una versión nueva de ruff con reglas o formato distintos y el CI empieza a fallar **sin que nadie haya cambiado el código** (o peor: pasa en el CI y falla en tu máquina, que tiene otra versión).
Además, el job de `mypy` instalaba solo mypy, no las librerías del proyecto: funcionaba porque el código no importa `pandas` todavía, pero **iba a fallar** cuando entre la importación de Excel (US-201).

**Qué se hizo.** La **única fuente de verdad** es `pyproject.toml` (que `uv.lock` traduce a versiones exactas), y todos la leen:

| Quién                      | Cómo obtiene la versión                                                                                   |
| -------------------------- | --------------------------------------------------------------------------------------------------------- |
| Tu máquina                 | `uv sync` (instala lo del lockfile) y `uv run ruff ...` / `uv run mypy ...`                               |
| CI: action de ruff         | `uv sync --locked --only-group dev` (solo las herramientas de desarrollo) y `uv run --no-sync ruff ...`   |
| CI: action de mypy         | `uv sync --locked` (todo el proyecto, mypy necesita las librerías) y `uv run --no-sync mypy ...`          |
| pre-commit                 | Hooks **locales** que ejecutan `uv run --locked ruff check --fix` y `uv run --locked ruff format`         |

Los hooks de pre-commit dejaron de usar el repositorio `ruff-pre-commit` (que pide un `rev:` escrito a mano y hay que acordarse de subir): ahora son `repo: local` con `language: system`, es decir, ejecutan **el ruff de tu entorno de uv**.

```yaml
- repo: local
  hooks:
    - id: ruff-check
      name: ruff check
      entry: uv run --locked ruff check --fix
      language: system
      types_or: [python, pyi]
      require_serial: true
```

**Consecuencia práctica:** para subir la versión de ruff o mypy se cambia **un solo lugar** (`pyproject.toml`), se corre `uv lock` y se commitean `pyproject.toml` y `uv.lock`. CI, pre-commit y tu máquina se actualizan juntos
(y Dependabot, ver 8.11, propone ese cambio solo). **Costo:** para usar pre-commit hace falta tener `uv` instalado (el RUNBOOK explica cómo).

También se corrigieron los pasos de la action de mypy, que se llamaban "Instalar Ruff" y "Ejecutar Ruff" (copiados de la de ruff).

**Qué queda pendiente.** Los jobs `check_dep`, `lint` y `static` siguen haciendo `checkout` con `submodules: recursive`, o sea que **clonan el repositorio de documentación** (el submódulo) en cada corrida sin necesitarlo.
Se puede sacar esa línea de cada uno (es un cambio de 2 líneas por job; no se hizo porque no fue parte del pedido).

**Cómo comprobar.** En el log del paso de instalación de cada job aparecen las líneas `+ ruff==0.16.8` y `+ mypy==2.3.1`, que tienen que coincidir con `pyproject.toml`. En tu máquina: `uv run ruff --version`.

---

### 8.5 Cuándo se dispara el CI (`on:`) (_ya hecho_)

**Qué es.** La clave `on:` del workflow define **qué eventos lo disparan**. Los dos más comunes:

- `pull_request`: cuando se abre, se actualiza o se reabre un PR. Prueba el cambio **propuesto**, antes de aprobarlo.
- `push`: cuando se sube código a una rama. Con `branches: [main]`, prueba lo que **ya quedó** en esa rama.

**Por qué importa.** Antes solo corría en `pull_request` y a mano. Si alguien sube directo a `main`/`develop` (o si el merge combina dos PR que por separado estaban bien pero juntos se rompen), **nadie corría el CI**.

**Qué se hizo.**

```yaml
on:
  workflow_dispatch:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: [main, develop]
```

No hay corridas duplicadas: un push a una rama con PR abierto dispara `pull_request`, y el `push` solo se dispara para `main` y `develop` (por ejemplo, al mergear un PR).

**Cómo comprobar.** Hacer un merge a `develop` y ver que aparece una ejecución nueva con el evento `push`.

---

### 8.6 `concurrency`, `permissions` y `timeout-minutes` (_ya hecho_)

Tres líneas de configuración que **no cambian qué se prueba** pero hacen al CI más barato, más seguro y menos frágil.

**a) `concurrency` — cancelar corridas viejas.**

- **Qué es:** agrupa las ejecuciones del workflow y, con `cancel-in-progress`, cancela la anterior cuando llega una nueva del mismo grupo.
- **Por qué importa:** si hacés 3 `push` seguidos a un PR, sin esto se ejecutan las 3 completas (gastando los minutos gratuitos y haciendo esperar). Solo importa la última.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

El grupo es "este workflow + este PR" (o, si no es un PR, la rama). Se cancela **solo en Pull Requests**: en `main` y `develop` se deja terminar cada corrida, para tener el resultado de cada commit mergeado.

**b) `permissions` — mínimo privilegio.**

- **Qué es:** cada ejecución recibe un "carnet" temporal (`GITHUB_TOKEN`) para hablar con GitHub. Por defecto puede tener **permisos de escritura** (crear releases, tocar ramas…).
- **Por qué importa:** si una action de terceros se compromete (pasó con varias), un token con permisos amplios puede hacer daño. Nuestro CI **solo necesita leer** el código.

```yaml
permissions:
  contents: read
```

Está al nivel del workflow, así que aplica a todos los jobs. El job `gitleaks` declara además el suyo (`contents: read` + `pull-requests: read`), porque necesita leer el PR para saber qué commits escanear; lo que un job declara **reemplaza** al general.

**c) `timeout-minutes` — que un job colgado no se quede para siempre.**

- **Qué es:** el tiempo máximo que puede correr un job antes de que GitHub lo mate.
- **Por qué importa:** por defecto es **6 horas**. Un test que se cuelga (una espera infinita) consumiría los minutos del mes.

| Job                                    | `timeout-minutes` |
| -------------------------------------- | ----------------- |
| `check_dep`, `gitleaks`, `lint`, `static` | 10             |
| `tests-linux`                          | 15                |
| `tests-windows`, `tests-docker`        | 20                |

Los tests tardan segundos; los topes son holgados a propósito (Windows y Docker tardan más en arrancar).

**Cómo comprobar:** hacer dos `push` seguidos a un PR y ver que la primera ejecución aparece como "Cancelled".

---

### 8.7 Guardar el reporte de cobertura y subir el umbral (_ya hecho_, solo en Linux)

**Qué es.** La _cobertura_ mide qué porcentaje de las líneas del código ejecutaron los tests. `pytest --cov-report=html` genera un sitio web con el detalle (qué líneas quedaron sin probar).

**Por qué importaba (dos problemas).**

1. **El reporte se generaba y se tiraba.** Cada job crea el HTML en la máquina del CI y, al terminar el job, la máquina se destruye: nadie podía verlo. Un _artifact_ lo guarda para descargarlo.
2. **El umbral era muy bajo.** `.coveragerc` exige `fail_under = 60`, pero el PRD (US-108) pide **80 %** y la cobertura real ronda el **91 %**: la cobertura podía caer 30 puntos sin que el CI protestara.

**Qué se hizo** (en `.github/actions/coverage/linux/action.yml`; **Windows y Docker quedan como estaban**):

1. **Umbral de 85 %**, exigido con `--cov-fail-under` (el flag pisa el `fail_under = 60` de `.coveragerc`, que queda como piso base para tu máquina, Windows y Docker). El valor es un parámetro de la action (`cobertura-minima`, por defecto `85`):

```yaml
inputs:
  cobertura-minima:
    description: "Porcentaje minimo de cobertura: si baja de este valor el job falla"
    default: "85"
# ...
run: uv run --locked pytest -v --cov=src --cov-report=term --cov-report=html --cov-fail-under="$COBERTURA_MINIMA"
```

1. **Guardar el reporte HTML** como _artifact_, incluso si un test o la cobertura fallaron (que es cuando más sirve verlo):

```yaml
- name: Guardar reporte de cobertura (HTML)
  if: ${{ !cancelled() }}
  uses: actions/upload-artifact@v7
  with:
    name: reporte-cobertura-linux-py${{ inputs.python-version }}
    path: reportes_cobertura/html/ # la ruta que define .coveragerc
    if-no-files-found: error
    retention-days: 14
```

Como `tests-linux` corre con 4 versiones de Python, se guardan **4 reportes** (`reporte-cobertura-linux-py3.11` … `py3.14`); el nombre incluye la versión porque dos artifacts no pueden llamarse igual dentro de una misma corrida.
También se agregó `--cov-report=term` para que el porcentaje aparezca en el log del job.

**Por qué 85 y no 80 o 90.** Medido localmente: 91,2 % (Windows, Python 3.13) y 90,8 % (Linux, Python 3.14). El PRD pide 80 %; 85 % deja ~6 puntos de margen para que una diferencia entre versiones de Python no rompa el CI sin motivo.

**Cómo comprobar.** En la página de la ejecución (pestaña _Actions_ → la corrida → sección _Artifacts_ al final) aparecen los reportes para descargar; se abre `index.html`. Para probar el umbral, subir `cobertura-minima` a `99` en un PR de prueba: el job tiene que fallar con "Required test coverage of 99% not reached".

---

### 8.8 Caché de dependencias (_ya hecho_)

**Qué es.** Cada job arranca en una máquina vacía y tiene que descargar e instalar todas las librerías. Un **caché** guarda esa descarga entre ejecuciones para no repetirla.

**Qué hay hoy.** Las actions de tests ya usan `astral-sh/setup-uv` con `enable-cache: true`: uv guarda su caché de paquetes y la reutiliza mientras no cambie `uv.lock`. **No hay nada que hacer**: se agregó al migrar de `pip` a `uv`.
Antes, las actions usaban `cache: "pip"`, que por defecto busca archivos con nombres estándar como `requirements.txt`; el del proyecto se llamaba `requerimientos.txt`, o sea que el caché no estaba atado al archivo correcto.

Desde la segunda tanda (8.4) también lo usan las actions de `lint` y `static`.

---

### 8.9 Job agregador y _required status checks_ (que un PR en rojo no se pueda mergear)

**Qué es.** Un CI que solo **avisa** es un semáforo que nadie está obligado a respetar. GitHub permite volverlo **obligatorio**: en la configuración de la rama se declara qué jobs tienen que estar en verde
para habilitar el botón _Merge_. Eso se llama _required status checks_ (dentro de _branch protection rules_ o _rulesets_).

**Por qué importa.** Sin esta regla, cualquiera puede mergear un PR con los tests rotos.

**Por qué un job agregador.** La regla necesita los **nombres exactos** de cada job, y esos nombres cambian (y ya cambiaron: con la matriz de 8.3 los jobs se llaman `tests-linux (3.11)`, `tests-linux (3.12)`…; son 16 nombres distintos).
Un job final que **espera a todos** y falla si alguno falló permite registrar **un solo nombre** en la regla, que no cambia nunca.

**Qué hacer, paso a paso.**

1. Agregar el job al final de `MainAction.yml`:

```yaml
ci-ok:
  name: CI OK
  if: always() # corre siempre, aunque otro job haya fallado
  needs: [check_dep, gitleaks, lint, static, tests-linux, tests-windows, tests-docker]
  runs-on: ubuntu-latest
  steps:
    - name: Fallar si algún job falló o se canceló
      run: |
        if [[ "${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}" == "true" ]]; then
          echo "Algún job falló"; exit 1
        fi
```

1. En GitHub: **Settings → Branches → Add branch protection rule** (o _Rules → Rulesets_).
2. En _Branch name pattern_ poner `main` (repetir para `develop` si querés).
3. Tildar **Require a pull request before merging** y **Require status checks to pass before merging**.
4. En el buscador de checks escribir `CI OK` y seleccionarlo (solo aparece después de que el job corrió al menos una vez).
5. Tildar **Require branches to be up to date before merging** (obliga a actualizar el PR con `main` antes de mergear).
6. Guardar.

**Cómo comprobar.** Abrir un PR con un test roto a propósito: el botón _Merge_ aparece bloqueado con el cartel "Required statuses must pass".

---

### 8.10 Dependencias reproducibles y auditadas (_ya hecho_)

**Qué es.**

- **Fijar versiones:** en `pyproject.toml` cada librería tiene versión exacta (`pandas==3.0.6`). Sin eso, "pandas" podría instalar una versión distinta cada día y el mismo código funcionar hoy y romperse mañana.
- **Lockfile (`uv.lock`):** además de las librerías que elegimos, cada una instala **otras** (sus dependencias, y las de esas). El lockfile fija **también esas**: 23 paquetes en total, versión y hash exactos. Cualquier persona y el CI instalan **exactamente lo mismo**.
- **pip-audit:** una herramienta que compara cada paquete instalado contra una base pública de vulnerabilidades conocidas (CVE) y avisa si alguno tiene un problema de seguridad publicado.

**Qué se hizo el 2026-09-20.** Se fijaron todas las versiones, se generó `uv.lock` y se auditó todo: resultado `No known vulnerabilities found`. Además se comprobó que la auditoría **funciona de verdad**:
al pasarle a propósito un paquete viejo con fallas conocidas (`requests==2.19.0`) reportó 10 vulnerabilidades. El job `check_dep` repite esa auditoría en cada PR.

**Cómo repetirlo a mano** (por ejemplo, después de agregar una librería):

```bash
uv export --frozen --no-emit-project --no-hashes -o requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --no-deps --disable-pip
```

**Qué hacer si aparece una vulnerabilidad.** El reporte indica la versión que la corrige (columna _Fix Versions_). Se cambia la versión en `pyproject.toml`, se corre `uv lock`, se vuelven a correr los tests y se commitean `pyproject.toml` y `uv.lock`.

---

### 8.11 Actualización automática de dependencias: Dependabot (_ya hecho_)

**Qué es.** Con versiones fijas las librerías **no se actualizan solas**, lo cual es bueno para la estabilidad pero significa que uno se olvida y queda con versiones viejas (y con vulnerabilidades nuevas sin parchear).
**Dependabot** es un robot de GitHub que revisa periódicamente y **abre un PR** por cada actualización disponible. El CI corre sobre ese PR y, si todo pasa, alcanza con aprobarlo.

**Qué se hizo.** Se creó `.github/dependabot.yml` (no es un workflow: es configuración que GitHub lee directamente). Vigila **tres** cosas, una vez por semana (los lunes):

| Ecosistema       | Qué vigila                                                                               | Cómo agrupa los PR                                              |
| ---------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `uv`             | Las dependencias de `pyproject.toml` y `uv.lock`                                         | `pytest`, `pytest-cov`, `ruff` y `mypy` juntos en un solo PR    |
| `github-actions` | Las actions de los workflows y de las actions propias (`/.github/actions/*/*`)           | Todas juntas en un solo PR                                      |
| `docker`         | La imagen base y la versión de `uv` de `Dockerfile.test`                                 | Un PR por cada una                                              |

Todos los PR llevan un prefijo en el título (`chore(deps)`, `chore(ci)`, `chore(docker)`) y hay un máximo de 5 PR abiertos por ecosistema.

**Por qué esto cierra el círculo con 8.4:** como `pyproject.toml` fija versiones exactas, un PR de Dependabot cambia esa versión y regenera `uv.lock`. Al mergearlo, **ruff y mypy suben a la vez** en el CI, en pre-commit y en tu máquina.

**Qué falta hacer a mano** (son ajustes de la cuenta, no se pueden hacer desde el repositorio): en GitHub, **Settings → Code security** y activar _Dependabot alerts_ y _Dependabot security updates_.

**Limitaciones.** El `rev: v4.6.0` de `pre-commit-hooks` en `.pre-commit-config.yaml` no está vigilado (hay que subirlo a mano de vez en cuando). Los PR van a la rama principal del repositorio (`main`); si el equipo prefiere que vayan a `develop`, se agrega `target-branch: "develop"` a cada bloque.

**Cómo comprobar.** En la pestaña _Insights → Dependency graph → Dependabot_ aparece el estado de cada ecosistema (si el archivo tuviera un error, se muestra ahí); en unos días llegan los primeros PR con título "chore(deps): Bump ...".

---

### 8.12 Detección de secretos: gitleaks (_ya hecho_)

**Qué es.** Un "secreto" es una contraseña, un token o una clave que **nunca** debería estar en el repositorio. Se suben por accidente (un `.env`, una clave pegada en un archivo de prueba) y, una vez en el historial de git, **quedan ahí** aunque se borren después.
**gitleaks** escanea los commits buscando patrones típicos de secretos.

**Por qué importa acá.** El proyecto va a manejar credenciales (hashes de contraseñas, la sesión local, quizás claves de un servicio externo).

**Qué se hizo.** Se agregó el job `gitleaks` a `MainAction.yml`:

```yaml
gitleaks:
  runs-on: ubuntu-latest
  timeout-minutes: 10
  permissions:
    contents: read
    pull-requests: read
  steps:
    - uses: actions/checkout@v7
      with:
        fetch-depth: 0 # baja TODO el historial: gitleaks necesita ver los commits del PR
    - uses: gitleaks/gitleaks-action@v3
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        GITLEAKS_ENABLE_COMMENTS: false
```

- **Sin licencia:** el repositorio es de una cuenta personal (`nicopinera`). Si algún día pasa a una **organización**, la action pide además una licencia gratuita (`GITLEAKS_LICENSE`, se saca en el sitio de gitleaks).
- **`GITLEAKS_ENABLE_COMMENTS: false`:** la action puede comentar en el PR, pero para eso necesitaría permiso de **escritura**. Se prefirió no dárselo: el resultado queda en el resumen del job y en un archivo (SARIF) adjunto.
- Corre en paralelo con los demás jobs: no bloquea ni espera a nadie.

**Resultado del escaneo de hoy.** Se corrió gitleaks sobre todo el historial en la máquina local (por Docker): `218 commits scanned … no leaks found`. Para repetirlo:

```bash
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest git /repo --redact
```

**Qué hacer si encuentra algo.** No alcanza con borrar el archivo: hay que **revocar/cambiar el secreto** (ya se considera filtrado) y recién después limpiarlo del repositorio.

**Pendiente:** sumar `gitleaks` a la lista `needs:` del job agregador de 8.9 cuando se cree.

---

### 8.13 Fijar las actions por hash (_supply chain_)

**Qué es.** `uses: actions/checkout@v4` apunta a una **etiqueta** (`v4`), y una etiqueta **se puede mover**: si alguien toma el control de esa action, puede cambiar lo que hay detrás de `v4` y tu CI ejecutaría código ajeno con acceso a tu repositorio.
Fijar por **hash de commit** (`@<40 caracteres>`) apunta a una versión concreta e inmutable.

**Por qué importa.** Es una de las formas más comunes de ataque a proyectos de software (ataques a la _cadena de suministro_). Las actions oficiales de GitHub y de Astral son de bajo riesgo, pero `pypa/gh-action-pip-audit` y `gitleaks/gitleaks-action` son de terceros.

**Qué hacer.**

```yaml
- uses: actions/checkout@<hash-de-40-caracteres> # v4.2.2
```

El hash se obtiene de la página de _releases_ de cada action. Es engorroso a mano, por eso conviene **hacerlo junto con Dependabot (8.11)**, que actualiza el hash y el comentario de versión automáticamente.
Prioridad baja: hacerlo solo para las actions de terceros es un buen punto medio.

---

### 8.14 Probar que la CLI "prende" (_smoke test_)

> **Aplicada el 2026-10-11; cambia en la US-105:** con la CLI retirada, el paso deja de ser `main.py --help` y pasa a importar el composition root de la GUI (`app.py`) sin abrir ninguna ventana. La idea (probar que el programa arranca fuera de pytest) es la misma.

**Qué es.** Un _smoke test_ ("prueba de humo") verifica solo lo mínimo: que el programa arranca. Viene de la electrónica: enchufás el aparato y mirás si sale humo.

**Por qué importa.** Los tests de `pytest` ya cubren la CLI (incluido un recorrido completo de punta a punta), pero corren dentro de pytest. Este paso ejecuta el programa **como lo ejecutaría una persona**, tal cual, y detecta problemas de instalación
(un import que falla, un archivo que no se empaquetó).

**Qué hacer.** Agregar un paso al final de la action de tests de Linux:

```yaml
- name: Smoke test de la CLI
  shell: bash
  run: uv run python src/main.py --help
```

**Cómo comprobar.** Romper a propósito un `import` en `src/main.py`: el paso tiene que fallar.

---

### 8.15 CD: entrega continua (_todavía no aplica_)

**Qué es.** El CI **prueba**; el CD **publica**. Ejemplos: armar un instalador, subirlo a la sección _Releases_ de GitHub cuando se etiqueta una versión (`v1.0.0`), generar un ejecutable para Windows.

**Por qué todavía no.** La aplicación se ejecuta desde el código fuente (`uv run python src/main.py ...`); no hay nada que empaquetar todavía. El empaquetado y la distribución son una historia propia del plan de desarrollo:
**US-404** (Hito 4, "Empaquetado"). Cuando llegue ese momento, el CD se agrega como un workflow **aparte** (`release.yml`) que se dispara cuando se crea una etiqueta de versión (`on: push: tags: ["v*"]`).

**Qué conviene ir preparando desde ya** (no cuesta nada y ordena el camino): definir el número de versión en un solo lugar (`pyproject.toml` ya tiene `version = "0.1.0"`) y registrar en un ADR corto cómo se va a versionar (SemVer).

---

### 8.16 Resumen y orden sugerido

**Pendiente:**

| #    | Mejora                                                                     | Impacto                                       | Esfuerzo                   | Sugerido                   |
| ---- | -------------------------------------------------------------------------- | --------------------------------------------- | -------------------------- | -------------------------- |
| 8.9  | Job agregador + _required status checks_ (incluye sumar `gitleaks`)        | **Alto**: el CI pasa de "avisar" a "proteger" | Bajo (un job y unos clics) | **1º**                     |
| 8.2  | `ruff format --check`                                                      | Medio                                         | Bajo                       | **2º**                     |
| 8.4  | Sacar `submodules: recursive` de `check_dep`, `lint` y `static`            | Bajo (velocidad)                              | Muy bajo                   | 3º                         |
| 8.14 | Smoke test de la CLI                                                       | Bajo                                          | Muy bajo                   | 4º                         |
| 8.13 | Fijar actions por hash (Dependabot ya está y lo facilita)                  | Bajo–medio                                    | Medio                      | 5º                         |
| 8.15 | CD / empaquetado                                                           | —                                             | Alto                       | Con la US-404              |

**Ya hecho:** 8.3 (parámetro y matriz de Python), 8.4 (una sola versión de ruff y mypy), 8.5 (disparo en `push`), 8.6 (`concurrency`, `permissions`, `timeout-minutes`), 8.7 (reporte y umbral de cobertura en Linux),
8.8 (caché con uv), 8.10 (versiones fijas, lockfile y auditoría), 8.11 (Dependabot) y 8.12 (gitleaks).

**Cómo aplicarlas sin romper nada:** de a una por vez, cada una en su propio PR. Es normal que el CI falle la primera vez que se agrega un chequeo nuevo (por ejemplo, `ruff format --check` va a marcar los archivos que hoy no están formateados):
conviene arreglar eso en el mismo PR y no desactivar el chequeo.
