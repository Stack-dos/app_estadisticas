# RUNBOOK — cómo operar StatsPro Basketball

Un *runbook* es la guía práctica de **cómo se usa y se mantiene** algo: qué comandos correr, qué esperar como resultado y qué hacer cuando algo falla. Este documento cubre la CLI
(`stats`), la base de datos, los tests y las herramientas de calidad. Para entender **por qué** el código está organizado como está, ver [docs/info_modulo/04-arquitectura.md](docs/info_modulo/04-arquitectura.md).

## Índice

1. [Requisitos e instalación](#1-requisitos-e-instalación)
2. [Cómo ejecutar la CLI](#2-cómo-ejecutar-la-cli)
3. [Referencia de comandos](#3-referencia-de-comandos)
4. [Ejemplo completo, paso a paso](#4-ejemplo-completo-paso-a-paso)
5. [Errores y códigos de salida](#5-errores-y-códigos-de-salida)
6. [La base de datos y los logs](#6-la-base-de-datos-y-los-logs)
7. [Tests, calidad de código y seguridad](#7-tests-calidad-de-código-y-seguridad)
8. [Docker](#8-docker)
9. [Manejo de dependencias](#9-manejo-de-dependencias)
10. [Problemas frecuentes](#10-problemas-frecuentes)
11. [Qué todavía no se puede hacer](#11-qué-todavía-no-se-puede-hacer)

---

## 1. Requisitos e instalación

**Necesitás:**

- **Git**, para clonar el repositorio.
- **[uv](https://docs.astral.sh/uv/)**, la herramienta que instala Python y las dependencias del proyecto. Reemplaza a `pip` y a `python -m venv`: crea el entorno virtual y instala las versiones exactas
  de cada librería (las fijadas en `uv.lock`) con un solo comando. Si no tenés Python ≥ 3.11, uv lo descarga solo.
- *(Opcional)* **Docker**, solo si querés correr los tests en un contenedor.

**Instalar uv** (una sola vez):

```bash
# Windows
winget install --id=astral-sh.uv -e

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Instalar el proyecto:**

```bash
git clone https://github.com/nicopinera/app_estadisticas.git
cd app_estadisticas
uv sync
```

`uv sync` lee `pyproject.toml` y `uv.lock`, crea la carpeta `.venv/` con Python y deja instaladas **todas** las dependencias (las de la app y las de desarrollo: pytest, ruff, mypy).
No hace falta activar el entorno: cada comando se antepone con `uv run`, que usa ese entorno automáticamente.

Para verificar que quedó bien:

```bash
uv run pytest -q
```

---

## 2. Cómo ejecutar la CLI

Todos los comandos se ejecutan **desde la raíz del repositorio**:

```bash
uv run python src/main.py <grupo> <acción> [--opciones]
```

En la ayuda el programa se llama `stats` (`stats club add ...`); en la práctica se lo invoca con la línea de arriba. Los grupos disponibles son `club`, `jugador`, `competencia`, `categoria`, `inscripcion`, `lista` y `partido`.

```bash
uv run python src/main.py --help                  # lista los grupos
uv run python src/main.py jugador --help          # lista las acciones de un grupo
uv run python src/main.py jugador link --help     # lista las opciones de una acción
```

**Cómo leer los ejemplos de esta guía:** para abreviar, escriben `stats jugador add ...`; el comando real es `uv run python src/main.py jugador add ...`.

**Primera ejecución:** la base de datos (`estadisticas.db`, en la raíz del repositorio) se crea sola, con todas sus tablas, la primera vez que corrés cualquier comando. No hay nada que preparar antes.

---

## 3. Referencia de comandos

Todas las opciones son obligatorias salvo que se indique lo contrario. Los ids (`--id-club`, `--id-jugador`…) son los números que muestran los propios comandos al crear las cosas.

| Comando | Qué hace |
| --- | --- |
| [`club add`](#club-add) | Crea un club |
| [`club list`](#club-list) | Lista los clubes de un usuario |
| [`jugador add`](#jugador-add) | Registra un jugador |
| [`jugador link`](#jugador-link) | Vincula un jugador a un club |
| [`jugador unlink`](#jugador-unlink) | Da de baja a un jugador de su club actual (para poder cambiarlo de club) |
| [`jugador list`](#jugador-list) | Lista los jugadores actuales de un club |
| [`competencia add`](#competencia-add) | Crea una competencia |
| [`competencia inscribir`](#competencia-inscribir) | Inscribe un club en una competencia y categoría |
| [`competencia list`](#competencia-list) | Lista todas las competencias (para conocer sus ids) |
| [`categoria add`](#categoria-add) | Crea una categoría (ej. U21) |
| [`categoria list`](#categoria-list) | Lista todas las categorías (para conocer sus ids) |
| [`inscripcion list`](#inscripcion-list) | Lista las inscripciones de un club y el id de su lista de buena fe |
| [`lista add`](#lista-add) | Habilita a un jugador en la lista de buena fe de una inscripción |
| [`lista remove`](#lista-remove) | Quita a un jugador de la lista de buena fe de una inscripción |
| [`lista list`](#lista-list) | Lista los jugadores habilitados en una lista de buena fe |
| [`partido list`](#partido-list) | Lista los partidos de un club, con los nombres de los clubes |

### `club add`

Crea un club nuevo. El nombre no puede repetirse.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--nombre` | texto | Nombre del club |

```text
$ stats club add --nombre "Atenas"
Club creado: Atenas (id=1)
```

Si el nombre ya existe: `Error: no se pudo guardar el club`. Si está vacío: `Error: El nombre del club no puede estar vacio` (código de salida 1 en ambos casos).

### `club list`

Muestra en una tabla los clubes a los que pertenece un usuario.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-usuario` | número | Id del usuario |

```text
$ stats club list --id-usuario 1
El usuario 1 no pertenece a ningun club.
```

> **Limitación actual:** los clubes todavía no se vinculan a un usuario (eso llega con el login, US-104), así que el resultado normal por ahora es ese aviso. La opción `--id-usuario` es provisoria: cuando exista la sesión, el comando va a leer el usuario de ahí.

### `jugador add`

Registra un jugador nuevo. El DNI es único.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--nombre` | texto | Nombre |
| `--apellido` | texto | Apellido |
| `--dni` | número | DNI (positivo, no puede repetirse) |
| `--anio` | número | Año de nacimiento (entre 1901 y el año actual) |

```text
$ stats jugador add --nombre Manu --apellido Ginobili --dni 20111222 --anio 1977
Jugador creado: Manu Ginobili (id=1)

$ stats jugador add --nombre Otro --apellido Jugador --dni 20111222 --anio 1990
Error: Ya existe un jugador con DNI 20111222

$ stats jugador add --nombre Otro --apellido Jugador --dni -5 --anio 1990
Error: El DNI debe ser un numero positivo - Valor actual: -5

$ stats jugador add --nombre Otro --apellido Jugador --dni 5 --anio 3000
Error: El año de nacimiento debe estar entre 1901 y 2026 - Valor actual: 3000
```

El nombre y el apellido tampoco pueden estar vacíos.

### `jugador link`

Vincula un jugador a un club a partir de una fecha. Un jugador solo puede tener **un** club activo a la vez (ni el mismo club dos veces).
Para **cambiarlo de club** primero hay que darle de baja del actual con [`jugador unlink`](#jugador-unlink): el vínculo nuevo no puede empezar antes de la fecha de baja del anterior.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-jugador` | número | Id del jugador |
| `--id-club` | número | Id del club |
| `--fecha-desde` | fecha `AAAA-MM-DD` | Desde cuándo juega en el club (`2026-1-5` se normaliza a `2026-01-05`) |

```text
$ stats jugador link --id-jugador 1 --id-club 1 --fecha-desde 2026-01-05
Jugador 1 vinculado al club 1 desde 2026-01-05

$ stats jugador link --id-jugador 1 --id-club 2 --fecha-desde 2026-02-01
Error: El jugador (idJugador=1), tiene un club activo (idClub=1)

$ stats jugador link --id-jugador 99 --id-club 1 --fecha-desde 2026-02-01
Error: No existe un jugador con idJugador=99
```

### `jugador unlink`

Da de baja a un jugador de su club **actual**: cierra el vínculo poniéndole una fecha de fin. El jugador y el club no se borran y el historial queda guardado. Es el paso previo a vincularlo a otro club.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-jugador` | número | Id del jugador |
| `--fecha-hasta` | fecha `AAAA-MM-DD` | Último día en el club (no puede ser anterior al día en que se vinculó) |

```text
$ stats jugador unlink --id-jugador 1 --fecha-hasta 2026-06-30
Jugador 1 desvinculado del club 1 (desde 2026-01-05 hasta 2026-06-30)

$ stats jugador link --id-jugador 1 --id-club 2 --fecha-desde 2026-06-01
Error: El vinculo nuevo empieza el 2026-06-01, antes de que termine el anterior del jugador (idClub=1, hasta 2026-06-30)

$ stats jugador link --id-jugador 1 --id-club 2 --fecha-desde 2026-07-01
Jugador 1 vinculado al club 2 desde 2026-07-01

$ stats jugador unlink --id-jugador 1 --fecha-hasta 2026-06-01
Error: La fecha de baja (2026-06-01) no puede ser anterior al inicio del vinculo (2026-07-01)
```

Si el jugador no tiene un club actual: `Error: El jugador (idJugador=1) no tiene un club activo`. Después de la baja, el jugador deja de aparecer en `jugador list` del club viejo.

### `jugador list`

Muestra en una tabla los jugadores **actuales** de un club (los que ya se fueron no aparecen).

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-club` | número | Id del club |

```text
$ stats jugador list --id-club 1
+------+---------------+---------------------+
|   ID | Jugador       |   Año de nacimiento |
+======+===============+=====================+
|    1 | Manu Ginobili |                1977 |
+------+---------------+---------------------+
```

Si el club no tiene jugadores: `El club 2 no tiene jugadores.`

### `competencia add`

Crea una competencia (una liga o torneo).

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--nombre` | texto | Nombre de la competencia |
| `--anio` | número | Año (tiene que ser **mayor a 1900**) |
| `--tipo` | texto, *opcional* | Tipo (ej. `PROVINCIAL`) |

```text
$ stats competencia add --nombre "Liga Provincial" --anio 2026 --tipo PROVINCIAL
Competencia creada: Liga Provincial 2026 (id=1)

$ stats competencia add --nombre "Vieja" --anio 1900
Error: Año debe ser mayor que 1900 - Valor actual: 1900
```

### `competencia inscribir`

Inscribe un club en una competencia y una categoría, y **crea automáticamente su lista de buena fe vacía**. Las dos cosas se guardan juntas: o quedan las dos o no queda ninguna.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-club` | número | Id del club |
| `--id-categoria` | número | Id de la categoría (ver [`categoria add`](#categoria-add) y [`categoria list`](#categoria-list)) |
| `--id-competencia` | número | Id de la competencia (ver [`competencia list`](#competencia-list)) |
| `--fecha-presentacion` | fecha `AAAA-MM-DD` | Fecha de presentación de la lista de buena fe |

```text
$ stats competencia inscribir --id-club 1 --id-categoria 1 --id-competencia 1 --fecha-presentacion 2026-03-01
Club 1 inscripto en la competencia 1 (categoria 1). Inscripcion id=1, lista de buena fe id=1
```

Errores posibles: el club, la competencia o la categoría no existen (`Error: No existe un club con idClub=9`, etc.), o el club ya está inscripto en esa competencia y categoría
(`Error: El club (idClub=1) ya esta inscripto en la competencia (idCompetencia=1) y categoria (idCategoria=1)`).

### `competencia list`

Muestra en una tabla todas las competencias, con su id (el que pide `competencia inscribir`). No tiene opciones.

```text
$ stats competencia list
+------+-----------------+-------+------------+
|   ID | Competencia     |   Año | Tipo       |
+======+=================+=======+============+
|    1 | Liga Provincial |  2026 | PROVINCIAL |
+------+-----------------+-------+------------+
```

Si todavía no hay ninguna: `No hay competencias cargadas.`

### `categoria add`

Crea una categoría (ej. `U21`, `Primera`). Sin categorías no se puede inscribir a ningún club. El nombre no puede repetirse: se compara **sin distinguir mayúsculas ni espacios** de los extremos.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--nombre` | texto | Nombre de la categoría |

```text
$ stats categoria add --nombre U21
Categoria creada: U21 (id=1)

$ stats categoria add --nombre " u21"
Error: Ya existe una categoria con el nombre 'u21'
```

### `categoria list`

Muestra en una tabla todas las categorías, con su id (el que pide `competencia inscribir`). No tiene opciones.

```text
$ stats categoria list
+------+-------------+
|   ID | Categoria   |
+======+=============+
|    1 | U21         |
+------+-------------+
```

Si todavía no hay ninguna: `No hay categorias cargadas.`

### `inscripcion list`

Muestra en una tabla las inscripciones de un club. Es la forma de volver a conocer el **id de la inscripción** y el **id de su lista de buena fe** después de haber inscripto al club.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-club` | número | Id del club |

```text
$ stats inscripcion list --id-club 1
+------------------+---------------+-------------+---------------------+
|   ID inscripcion |   Competencia |   Categoria |   Lista de buena fe |
+==================+===============+=============+=====================+
|                1 |             1 |           1 |                   1 |
+------------------+---------------+-------------+---------------------+
```

Si el club no tiene inscripciones: `El club 1 no tiene inscripciones.`

### `lista add`

Habilita a un jugador en la **lista de buena fe** de una inscripción. Solo los jugadores habilitados en la lista pueden figurar en la carga oficial de un partido.
Para habilitarlo, el jugador tiene que **existir**, **jugar hoy en el club de la inscripción** (tener un vínculo vigente, ver [`jugador link`](#jugador-link)) y **no estar ya en la lista**.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-inscripcion` | número | Id de la inscripción (ver [`inscripcion list`](#inscripcion-list)) |
| `--id-jugador` | número | Id del jugador a habilitar |

```text
$ stats lista add --id-inscripcion 1 --id-jugador 1
Jugador 1 habilitado en la lista de buena fe 1 (inscripcion 1)

$ stats lista add --id-inscripcion 1 --id-jugador 1
Error: El jugador (idJugador=1) ya esta en la lista de buena fe (idListaBuenaFe=1)

$ stats lista add --id-inscripcion 1 --id-jugador 2
Error: El jugador (idJugador=2) no tiene un vinculo vigente con el club de la inscripcion (idClub=1)

$ stats lista add --id-inscripcion 9 --id-jugador 1
Error: No existe una inscripcion con idInscripcion=9
```

Si se habilitó a alguien por error, se deshace con [`lista remove`](#lista-remove).

### `lista remove`

Quita a un jugador de la lista de buena fe de una inscripción. Solo deshace la habilitación: el jugador sigue existiendo y sigue en su club.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-inscripcion` | número | Id de la inscripción |
| `--id-jugador` | número | Id del jugador a quitar |

```text
$ stats lista remove --id-inscripcion 1 --id-jugador 1
Jugador 1 quitado de la lista de buena fe 1 (inscripcion 1)

$ stats lista remove --id-inscripcion 1 --id-jugador 1
Error: El jugador (idJugador=1) no esta en la lista de buena fe (idListaBuenaFe=1)
```

### `lista list`

Muestra en una tabla los jugadores habilitados en la lista de buena fe de una inscripción.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-inscripcion` | número | Id de la inscripción |

```text
$ stats lista list --id-inscripcion 1
+------+---------------+---------------------+
|   ID | Jugador       |   Año de nacimiento |
+======+===============+=====================+
|    1 | Manu Ginobili |                1977 |
+------+---------------+---------------------+
```

Si todavía no hay nadie: `La lista de buena fe de la inscripcion 1 no tiene jugadores.` Si la inscripción no existe: `Error: No existe una inscripcion con idInscripcion=9`.

### `partido list`

Muestra en una tabla los partidos en los que jugó un club, como local o como visitante, del más antiguo al más reciente. Los datos salen de la vista `v_partidos_resumen`, por eso aparecen los **nombres**.

| Opción | Tipo | Descripción |
| --- | --- | --- |
| `--id-club` | número | Id del club |

```text
$ stats partido list --id-club 1
+------+------------+----------------------+---------------------+---------------+------------------+
|   ID | Fecha      | Estadio              | Competencia         | Club local    | Club visitante   |
+======+============+======================+=====================+===============+==================+
|    1 | 2026-05-21 | Cancha Atenas        | PROVINCIAL U21 2026 | Atenas        | Universitario    |
+------+------------+----------------------+---------------------+---------------+------------------+
|    2 | 2026-06-20 | Cancha Universitario | PROVINCIAL U21 2026 | Universitario | Atenas           |
+------+------------+----------------------+---------------------+---------------+------------------+
```

(Ejemplo con los datos del seed, ver la sección 4.) Si el club no tiene partidos: `El club 1 no tiene partidos.`

---

## 4. Ejemplo completo, paso a paso

Recorrido típico sobre una base vacía (los ids `1` salen porque es la primera vez que se crea cada cosa):

```bash
# 1. Crear los clubes
uv run python src/main.py club add --nombre "Atenas"
uv run python src/main.py club add --nombre "Universitario"

# 2. Registrar un jugador y vincularlo a Atenas
uv run python src/main.py jugador add --nombre Manu --apellido Ginobili --dni 20111222 --anio 1977
uv run python src/main.py jugador link --id-jugador 1 --id-club 1 --fecha-desde 2026-01-05
uv run python src/main.py jugador list --id-club 1

# 3. Crear una competencia
uv run python src/main.py competencia add --nombre "Liga Provincial" --anio 2026 --tipo PROVINCIAL

# 4. Crear una categoría y ver los ids que hacen falta para inscribir
uv run python src/main.py categoria add --nombre U21
uv run python src/main.py categoria list
uv run python src/main.py competencia list

# 5. Inscribir a Atenas en la competencia (categoría 1, competencia 1) y ver el id de su lista de buena fe
uv run python src/main.py competencia inscribir --id-club 1 --id-categoria 1 --id-competencia 1 --fecha-presentacion 2026-03-01
uv run python src/main.py inscripcion list --id-club 1

# 6. Habilitar al jugador en la lista de buena fe (tiene que jugar en el club de la inscripción: paso 2)
uv run python src/main.py lista add --id-inscripcion 1 --id-jugador 1
uv run python src/main.py lista list --id-inscripcion 1

# 7. Si se equivocó: quitarlo de la lista. Y para cambiarlo de club: darle de baja y vincularlo al nuevo
uv run python src/main.py lista remove --id-inscripcion 1 --id-jugador 1
uv run python src/main.py jugador unlink --id-jugador 1 --fecha-hasta 2026-06-30
uv run python src/main.py jugador link --id-jugador 1 --id-club 2 --fecha-desde 2026-07-01
```

**Datos de ejemplo:** si querés probar los listados con datos ya cargados (2 clubes, 10 jugadores, 1 competencia, 2 partidos, 1 categoría), se puede cargar el *seed*. Hacelo **solo sobre una base vacía**
(sin `estadisticas.db` o después de borrarla, ver sección 6):

```bash
uv run python -c "import config.rutas as r; from infraestructura.persistencia.database_manager import SQLiteManager; m = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL, r.SEED_SQL); m.connect(); m.inicializar_schema(); m.cargar_seed()"
uv run python src/main.py partido list --id-club 1
```

---

## 5. Errores y códigos de salida

Los errores se muestran como una línea `Error: ...` en la salida de **errores** (stderr), sin ningún traceback, y el programa termina con un código de salida que sirve para automatizar:

| Código | Significa | Ejemplo |
| --- | --- | --- |
| `0` | Todo bien | `Club creado: Atenas (id=1)` |
| `1` | Error de negocio: la operación no está permitida o no se pudo guardar | `Error: Ya existe un jugador con DNI 20111222` |
| `2` | Uso incorrecto de la CLI (lo devuelve `argparse`): falta una opción, un número mal escrito, una fecha inválida | `error: argument --fecha-desde: '31-12-2026' no es una fecha valida, use el formato AAAA-MM-DD` |

Si ves un **traceback** (un mensaje largo con `Traceback (most recent call last)`), es un bug del programa y no un error de uso: reportalo junto con el comando que ejecutaste y el archivo `logs/app.log`.

---

## 6. La base de datos y los logs

| Qué | Dónde |
| --- | --- |
| Base de datos (SQLite) | `estadisticas.db`, en la raíz del repositorio (no se sube a git) |
| Logs | `logs/app.log` (rota a los 10 MB, conserva 5 archivos) |
| Rutas y scripts SQL | `src/config/rutas.py` y `src/infraestructura/persistencia/sql/` |

- **Cada arranque es seguro para los datos:** la CLI ejecuta el esquema en cada comando, pero `schema.sql` solo crea lo que falta (`CREATE TABLE IF NOT EXISTS`), nunca borra.
- **Hacer un backup:** copiar el archivo `estadisticas.db` mientras no se esté ejecutando ningún comando.
- **Empezar de cero:** borrar `estadisticas.db`. Se vuelve a crear vacía en el próximo comando. **Se pierden todos los datos.**
- **Mirar el contenido:** abrir `estadisticas.db` con cualquier visor de SQLite (por ejemplo [DB Browser for SQLite](https://sqlitebrowser.org/)).

---

## 7. Tests, calidad de código y seguridad

Todo se ejecuta con `uv run` (o con el atajo `make` que se indica). Detalle de cómo escribir tests en [docs/info_modulo/09-testing.md](docs/info_modulo/09-testing.md).

```bash
uv run pytest                                   # toda la suite
uv run pytest tests/unit                        # solo los unitarios (no usan base de datos, son muy rápidos)
uv run pytest -k "vincular"                     # solo los tests cuyo nombre contiene "vincular"
uv run pytest -v --cov=src --cov-report=html    # con cobertura; abrir reportes_cobertura/html/index.html   (make run_test)

uv run ruff check .                             # estilo, imports y errores comunes (reglas: pyproject.toml) (make run_linter_ruf)
uv run ruff format --check .                    # avisa si algún archivo no está formateado, sin tocarlo     (make run_linter_ruf)
uv run ruff format .                            # formatea el código                                         (make corregir_linter)
uv run mypy src/ --strict --explicit-package-bases   # revisión de tipos                                     (make static_check)

# Vulnerabilidades conocidas en las dependencias: ver el comando de la sección 9
```

Estos mismos chequeos se ejecutan automáticamente en GitHub (`.github/workflows/MainAction.yml`) en cada Pull Request y en cada `push` a `main` o `develop`: lint, tipos, tests en Linux, Windows y Docker,
auditoría de dependencias (`pip-audit`) y detección de secretos (`gitleaks`). Los tests de Linux se repiten con **Python 3.12, 3.13 y 3.14**; Windows y Docker corren una sola vez (3.13) y mypy una sola vez (contra la 3.12). El lint incluye `ruff format --check`, y los jobs de tests prueban antes que la CLI arranque (`python src/main.py --help`).
Un job final, `ci-ok`, queda en rojo si cualquiera de los anteriores falló: es el que se marca como obligatorio en GitHub para que un PR con el CI en rojo no se pueda mergear.
En Linux la cobertura mínima es **85 %** y el reporte HTML queda para descargar (pestaña _Actions_ → la corrida → sección _Artifacts_). Además, [Dependabot](.github/dependabot.yml) abre PR cuando hay versiones nuevas de las dependencias.

### Hooks de pre-commit (opcional)

Con [pre-commit](https://pre-commit.com/), ruff revisa y formatea los archivos **al hacer `git commit`**. Los hooks de ruff se ejecutan con `uv run`, o sea que usan la **misma versión que fija `pyproject.toml`** (y que usa el CI): hace falta tener `uv` instalado (sección 1).

```bash
uv tool install pre-commit     # una sola vez
pre-commit install             # activa los hooks en este repositorio
make pre_commit                # (opcional) corre los hooks sobre todo el proyecto: puede modificar archivos, revisá el git diff
```

---

## 8. Docker

Corre los tests en un contenedor limpio, igual que en el CI (no depende de nada de tu máquina). Explicación completa en [docs/info_modulo/10-docker-para-tests.md](docs/info_modulo/10-docker-para-tests.md).

```bash
make docker_test
# equivale a:
docker build -f Dockerfile.test -t app-estadisticas-tests .
docker run --rm app-estadisticas-tests
```

La imagen usa Python 3.11 por defecto. Para probar con otra versión (el CI usa la 3.13):

```bash
make docker_test PYTHON_VERSION=3.13
# equivale a:
docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.13 -t app-estadisticas-tests .
```

---

## 9. Manejo de dependencias

Todas las dependencias están declaradas en **`pyproject.toml`** con **versión exacta** (`==`), y `uv.lock` fija además las versiones de todo lo que ellas instalan. Así cualquier persona (y el CI) instala exactamente lo mismo.

| Quiero… | Comando |
| --- | --- |
| Instalar todo lo del proyecto | `uv sync` |
| Agregar una librería de la app | `uv add nombre==1.2.3` |
| Agregar una herramienta de desarrollo | `uv add --dev nombre==1.2.3` |
| Actualizar una librería | cambiar la versión en `pyproject.toml` y correr `uv lock` y `uv sync` |
| Verificar que no haya vulnerabilidades conocidas | ver abajo |

```bash
uv export --frozen --no-emit-project --no-hashes -o requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --no-deps --disable-pip
```

El resultado esperado es `No known vulnerabilities found`. Después de agregar o actualizar dependencias, hay que **commitear también `uv.lock`**.

---

## 10. Problemas frecuentes

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `uv: command not found` | uv no está instalado o la terminal no se reinició | Instalar uv (sección 1) y abrir una terminal nueva |
| `ModuleNotFoundError: tabulate` (o `pandas`, `pytest`…) | Se está usando otro Python, no el entorno del proyecto | Ejecutar siempre con `uv run ...`, y `uv sync` si falta instalar |
| `AttributeError: module 'config.rutas' has no attribute 'LOG_DIR'` | Hay un paquete `config` de terceros instalado en tu Python global que tapa al del proyecto | Usar `uv run ...` (el entorno del proyecto no lo tiene) |
| `error: failed to remove file ... .venv\lib64` (o el entorno deja de andar al alternar entre Windows y WSL) | La carpeta del proyecto la usan Windows **y** WSL, y cada sistema necesita su **propio** entorno virtual: uno intenta recrear el `.venv` del otro y lo deja a medias | Que uno de los dos use un entorno fuera del proyecto: en WSL, `export UV_PROJECT_ENVIRONMENT=~/.venvs/app_estadisticas` (por ejemplo en `~/.bashrc`) y después `uv sync`. Para reparar un `.venv` roto, borrarlo **desde el mismo sistema que lo creó** y correr `uv sync` |
| `Error: no se pudo guardar el club` | El nombre del club ya existe | Elegir otro nombre |
| `Error: No existe una categoria con idCategoria=1` | La base no tiene categorías todavía | Crear una con `categoria add` (ver sección 4) o cargar el seed |
| `Error: ... no tiene un vinculo vigente con el club de la inscripcion` | Al habilitar en la lista a un jugador que no juega en ese club | Vincularlo antes con `jugador link` (o revisar que sea el club correcto con `inscripcion list`) |
| `Error: El jugador (idJugador=N), tiene un club activo` | Al vincular a un jugador que todavía está en otro club | Darle de baja primero con `jugador unlink` |
| `Error: El vinculo nuevo empieza el ..., antes de que termine el anterior` | La fecha de `--fecha-desde` es anterior a la baja del club anterior | Usar una fecha igual o posterior a la de la baja |
| `Error: El nombre del club no puede estar vacio` (o DNI/año inválidos) | Un dato no cumple las reglas de la entidad | Corregir el dato y repetir el comando |
| `El usuario 1 no pertenece a ningun club` | Los clubes aún no se vinculan a usuarios (llega con el login) | Es lo esperado por ahora |
| Los acentos o la `ñ` se ven raros en la consola de Windows | Codificación de la consola | Ejecutar con `PYTHONUTF8=1` (o `chcp 65001` en cmd) |
| `database is locked` | Otro programa (ej. un visor de SQLite) tiene la base abierta para escribir | Cerrar el otro programa y reintentar |

---

## 11. Qué todavía no se puede hacer

El estado del proyecto por historia de usuario está en el [README](README.md). Hoy, desde la CLI:

- **No hay login ni sesión** (US-104): por eso `club list` pide `--id-usuario` y no existe `club select`. Los clubes creados no quedan vinculados a ningún usuario.
- **No se puede editar ni borrar** clubes, competencias ni jugadores (el PRD solo pide crear, listar y vincular): un dato mal cargado hoy solo se corrige en la base.
- **No hay un comando para ver el historial de clubes de un jugador** (`jugador list` muestra solo los actuales de un club); el dato está guardado y el repositorio ya lo expone.
- **No se pueden cargar partidos ni estadísticas** (US-105): `partido list` solo muestra los que ya estén en la base (por ejemplo, los del seed).
- **Errores de nombre repetido de club** muestran un mensaje genérico (`no se pudo guardar el club`).
