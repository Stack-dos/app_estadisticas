# Informe de sesión (2026-09-19 y 2026-09-20): cierre de la US-103

> **Para quién es este documento:** para cualquier integrante del equipo que no estuvo en la sesión y necesite entender **qué se agregó, por qué y para qué**. Está pensado para leerse de arriba hacia abajo,
> pero cada bloque se entiende solo. No hace falta haber leído nada antes; los términos técnicos se explican la primera vez que aparecen y hay un glosario al final.
>
> **Rama:** `feature/us103`. **Autor de la sesión:** Nico, trabajando con un asistente de IA (Claude). Los cambios de la **parte 1** (2026-09-19/20 de madrugada) ya están commiteados
> (`63da850`, `114d011`, `d3e532a`, `e7fb0f3`, `7ab7bb6`, `9264d1d`). Los de la **parte 2** (2026-09-20, Bloques B a H) están en el árbol de trabajo **sin commitear** al momento de escribir esto.

## Índice

0. [Resumen ejecutivo y qué tenés que hacer al bajar estos cambios](#0-resumen-ejecutivo-y-qué-tenés-que-hacer-al-bajar-estos-cambios)
1. [Mapa de la sesión](#1-mapa-de-la-sesión)
2. [Bloque A — Casos de uso de la US-103](#2-bloque-a--casos-de-uso-de-la-us-103-parte-1)
3. [Bloque B — Dependencias con `uv` (adiós `requerimientos.txt`)](#3-bloque-b--dependencias-con-uv-adiós-requerimientostxt)
4. [Bloque C — Los comandos de la CLI](#4-bloque-c--los-comandos-de-la-cli)
5. [Bloque D — Revisión y ampliación de los tests](#5-bloque-d--revisión-y-ampliación-de-los-tests)
6. [Bloque E — Documentación](#6-bloque-e--documentación)
6 bis. [Bloque F — Ampliación de la US-103: categorías, consultas y lista de buena fe](#bloque-f--ampliación-de-la-us-103-categorías-consultas-y-lista-de-buena-fe)
6 ter. [Bloque G — Auditoría de cierre de la US-103](#bloque-g--auditoría-de-cierre-de-la-us-103)
6 quater. [Bloque H — CI/CD: versiones unificadas, matriz de Python y seguridad](#bloque-h--cicd-versiones-unificadas-matriz-de-python-y-seguridad)
7. [Bugs encontrados y corregidos](#7-bugs-encontrados-y-corregidos)
8. [Decisiones de diseño y por qué se tomaron](#8-decisiones-de-diseño-y-por-qué-se-tomaron)
9. [Incidentes de la sesión (transparencia)](#9-incidentes-de-la-sesión-transparencia)
10. [Lo que NO se hizo y límites conocidos](#10-lo-que-no-se-hizo-y-límites-conocidos)
11. [Cómo verificar todo](#11-cómo-verificar-todo)
12. [Próximos pasos sugeridos](#12-próximos-pasos-sugeridos)
13. [Inventario de archivos](#13-inventario-de-archivos)
14. [Glosario](#14-glosario)

---

## 0. Resumen ejecutivo y qué tenés que hacer al bajar estos cambios

**En una frase:** la US-103 (gestión de clubes, jugadores, competencias e inscripciones) quedó **terminada de punta a punta**: la lógica de negocio (casos de uso), la línea de comandos (CLI) que la usa,
una suite de tests ordenada y sin repetición, dependencias reproducibles con `uv`, y documentación actualizada. En el camino aparecieron y se corrigieron **varios bugs reales**, uno de ellos grave
(la app borraba todos los datos cada vez que se abría, ver [7](#7-bugs-encontrados-y-corregidos)).

**Qué se logró:**

- **17 casos de uso** con sus reglas de negocio y excepciones: los 9 de la planificación original (4 nuevos y 5 corregidos), 6 agregados después para cerrar huecos del PRD (categorías, consultas y lista de buena fe: Bloque F)
  y 2 más de la auditoría de cierre (desvincular un jugador de su club y quitarlo de una lista: Bloque G).
- **16 comandos de CLI** (`club`, `jugador`, `competencia`, `categoria`, `inscripcion`, `lista` y `partido`) con tablas y errores sin traceback.
- **Dependencias fijadas** con `uv`: `pyproject.toml` + `uv.lock`, auditadas contra vulnerabilidades. Se eliminó `requerimientos.txt`.
- **Tests:** de un puñado de tests de repositorios a una suite de casi **400 tests** (unitarios, de integración y de punta a punta), con cobertura ≈ 91 %.
- **Documentación:** 7 guías movidas a `docs/info_modulo/` y completadas, PRD actualizado, `RUNBOOK.md` y `README.md` nuevos, informe de revisión del CI.
- **CI/CD:** una sola versión de ruff y mypy (CI, pre-commit y local), tests (Linux y Docker) y tipos en Python 3.11 a 3.14 (Windows con 3.13), cobertura mínima de 85 % con reporte descargable, `concurrency`/`permissions`/`timeout-minutes`, Dependabot y gitleaks; se corrigieron además 3 referencias del workflow que no existían ([Bloque H](#bloque-h--cicd-versiones-unificadas-matriz-de-python-y-seguridad)).

**Qué tenés que hacer vos al traer estos cambios (una sola vez):**

```bash
git pull                 # o el flujo que usen
uv sync                  # instala EXACTAMENTE las versiones de uv.lock (si no tenés uv: ver RUNBOOK.md, sección 1)
uv run pytest            # tiene que dar todo en verde
```

**Si tenías un entorno virtual armado con `pip install -r requerimientos.txt`:** ese archivo **ya no existe**. Borrá tu `.venv` y corré `uv sync`. Desde ahora **todo se ejecuta con `uv run ...`**
(por ejemplo `uv run python src/main.py club add --nombre Atenas`). Guía completa de uso: [RUNBOOK.md](../../RUNBOOK.md).

---

## 1. Mapa de la sesión

| Bloque | Qué es | Cuándo | Estado |
| --- | --- | --- | --- |
| **A** | Casos de uso de la US-103: los 4 faltantes, correcciones a los 5 existentes, excepciones nuevas, método atómico de inscripción | 09-19/20 | ✅ Commiteado |
| **A'** | Ajustes posteriores: mypy limpio, filtro de jugadores vigentes, regla del año de `Competencia` | 09-20 | ✅ Commiteado |
| **B** | Migración a `pyproject.toml` + `uv`, versiones fijas, `uv.lock`, auditoría, Docker y CI adaptados | 09-20 | ⏳ Sin commitear |
| **C** | Comandos de la CLI, `main.py`, `utils.py`, formatter de tablas, manejo de errores | 09-20 | ⏳ Sin commitear |
| **D** | Revisión de tests: reclasificación, `parametrize`, `**overrides`, `unittest.mock`, tests de excepciones, E2E | 09-20 | ⏳ Sin commitear |
| **E** | Guías movidas y completadas, PRD, RUNBOOK, README, revisión de CI | 09-20 | ⏳ Sin commitear |
| **F** | Ampliación de la US-103: categorías, `competencia list`, `inscripcion list` y lista de buena fe (casos de uso, DTOs, comandos, tests y docs) | 09-20 | ⏳ Sin commitear |
| **G** | Auditoría de cierre de la US-103: quitar de la lista de buena fe, ciclo de vida del vínculo jugador-club, validaciones de valor, `partido list` con nombres | 09-20 | ⏳ Sin commitear |

---

## 2. Bloque A — Casos de uso de la US-103 (parte 1)

### Qué es un caso de uso (repaso de 30 segundos)

Es **una acción que el usuario puede pedir** ("registrar un jugador", "inscribir un club en una competencia") escrita como una clase con un método `ejecutar()`.
Ahí viven las reglas de negocio. La CLI no las conoce (solo pide la acción) y el repositorio tampoco (solo guarda y lee). El detalle de cada uno, paso a paso, está en
[`docs/info_modulo/03-casos-de-uso.md`](../info_modulo/03-casos-de-uso.md).

### A.1 Los 4 casos de uso que faltaban

| Caso de uso | Qué hace | Por qué existe |
| --- | --- | --- |
| `CrearCompetenciaUseCase` | Crea una competencia (liga o torneo) | Sin competencias no se puede inscribir a nadie ni cargar partidos |
| `InscribirClubEnCompetenciaUseCase` | Verifica que existan club, competencia y categoría, que el club no esté ya inscripto, y guarda la inscripción **junto con su lista de buena fe vacía** | Es el corazón del "mundo competitivo". Tiene 4 reglas de negocio y una restricción de atomicidad (ver A.3) |
| `ListarPartidosPorClubUseCase` | Lista los partidos de un club (como local o visitante) | Necesario para el comando `partido list` |
| `CambiarClubActivoUseCase` | Valida que un club exista y que el usuario pertenezca a él | Es la parte "de negocio" de `club select`. Guardar la elección en la sesión **no** se hace acá: es de la US-104 |

### A.2 Correcciones a los 5 casos de uso que ya existían

| Caso de uso | Problema | Corrección | Por qué |
| --- | --- | --- | --- |
| `VincularJugadorAClubUseCase` | No verificaba que el jugador ni el club existieran (dependía de que la base fallara en silencio); `ClubNoEncontradoError` estaba definida y nadie la usaba | Ahora recibe también el repo de clubes y lanza `JugadorNoEncontradoError` / `ClubNoEncontradoError` | Un error claro ("no existe el club 9") en vez de "no se pudo guardar" |
| `ListarJugadoresClubUseCase` | Si el repositorio devolvía `None`, el `for` explotaba | `or []` | Un listado sin resultados es una lista vacía, no un error |
| `RegistrarJugadorUseCase` | Devolvía la entidad `Jugador` (el dominio se "escapaba" hacia la CLI) | Devuelve `JugadorDTO` y maneja el caso `None` | Que la CLI dependa de un DTO estable y no de la forma interna del dominio |
| `ListarClubesUsuarioUseCase` | Devolvía `None` cuando no había clubes | Devuelve `[]` | Consistencia entre todos los listados: la CLI itera sin chequear `None` |
| `CrearClubUseCase` | Docstring con un placeholder (`_description_`) y sin tipo de retorno | Docstring completo y `-> ClubDTO \| None` | Que mypy y quien lea el código sepan qué devuelve |

### A.3 Piezas de infraestructura y dominio que se agregaron para sostener los casos de uso

- **4 excepciones de dominio nuevas** (`dominio/exceptions.py`): `JugadorNoEncontradoError`, `CompetenciaNoEncontradaError`, `CategoriaNoEncontradaError`, `InscripcionDuplicadaError`.
  *Por qué:* cada regla de negocio necesita "su" excepción para que la CLI pueda explicarle al usuario exactamente qué pasó. Todas heredan de `ErrorDeDominio`, así se capturan juntas.
- **`CompetenciaRepositorio.inscribir_con_lista()`** (interfaz + implementación SQLite). Guarda la inscripción y su lista de buena fe **en una sola transacción**.
  *Por qué:* una inscripción **siempre** debe tener su lista (relación 1 a 1). Si se guardaran por separado y la segunda falla, queda una inscripción huérfana e inconsistente. Con una transacción:
  o se guardan las dos o no se guarda ninguna (esto se llama **atomicidad**, criterio AC5 de la US-103). Hay tests que fuerzan el fallo de la segunda para comprobar que la primera se deshace.
- **Filtro de vínculo vigente en `buscar_por_club`** (`AND fechaHasta IS NULL`). *Por qué:* "jugadores del club" devolvía también a los que ya se fueron (tienen `fechaHasta` cargada) y a los que
  salieron y volvieron los mostraba duplicados.
- **Año de `Competencia` mayor a 1900.** *Por qué:* la entidad rechazaba años `<= 2000` (con un mensaje que decía "menor que 2000") pero el `CHECK` de la base dice `anio > 1900`. Ahora los dos coinciden.
- **`id_persistido()`** (hoy en `src/utils.py`). *Por qué:* las entidades declaran su ID como `int | None` (antes de guardarse no lo tienen) pero los DTOs de salida piden `int`. Esta función deja explícita
  la garantía "un repositorio siempre devuelve entidades con ID" en **un solo lugar** y deja a `mypy --strict` en cero errores (había 9).

---

## 3. Bloque B — Dependencias con `uv` (adiós `requerimientos.txt`)

### Qué es `uv` y por qué se adoptó

`uv` es una herramienta moderna (escrita en Rust) que **reemplaza a `pip` y a `python -m venv`**: instala Python si falta, crea el entorno virtual e instala las dependencias, todo mucho más rápido y con un
**archivo de bloqueo** (`uv.lock`) que fija la versión exacta de *todo*. El problema que resuelve: con `requerimientos.txt` sin versiones, `pip install` podía instalar cosas distintas en cada máquina
y en cada día ("en mi máquina funciona"), y el proyecto ni siquiera declaraba todas sus dependencias.

### Qué se hizo

| Cambio | Archivo | Para qué |
| --- | --- | --- |
| Todas las dependencias declaradas con **versión exacta** (`==`) | `pyproject.toml` | Que todos instalen lo mismo. Antes solo `pandas` figuraba, sin versión |
| `tabulate` agregada como dependencia | `pyproject.toml` | La CLI la usa para las tablas y **no estaba declarada**: en el CI o en Docker habría fallado con `ModuleNotFoundError` |
| Herramientas de desarrollo en un *dependency group* `dev` | `pyproject.toml` | `uv sync` las instala por defecto (pytest, pytest-cov, ruff, mypy) |
| `uv.lock` generado | `uv.lock` (nuevo) | Fija versión y hash de **los 23 paquetes** del árbol completo (eran 45 antes de sacar `sphinx`). **Se commitea** |
| `requerimientos.txt` **eliminado** | — | Ya no hace falta: `pyproject.toml` + `uv.lock` lo reemplazan |
| Auditoría de vulnerabilidades (`pip-audit`) | — | Resultado: **"No known vulnerabilities found"**. Se comprobó que la auditoría funciona pasándole a propósito un paquete viejo con fallas conocidas (reportó 10) |
| Override de mypy para `tabulate` | `pyproject.toml` | `tabulate` no publica tipos y `mypy --strict` se quejaba al importarla |
| Corrección de un **bug previo** del `pyproject.toml` | `pyproject.toml` | La tabla `[tool.setuptools.packages.find-namespace]` **no existe** en setuptools: el proyecto **nunca pudo instalarse**. Ahora es `[tool.setuptools.packages.find]` con `namespaces = true` |

**Versiones fijadas:** `pandas==3.0.6`, `tabulate==0.10.0`, `pytest==9.1.1`, `pytest-cov==7.1.0`, `ruff==0.16.8`, `mypy==2.3.1`.
(*Sphinx* y `sphinx-rtd-theme` estuvieron unas horas en la lista y **se sacaron**: no había `conf.py` ni uso en el repo, y arrastraban unos 20 paquetes más al lockfile.)

### Efectos en el resto del proyecto (consecuencias necesarias de borrar `requerimientos.txt`)

Todo lo que instalaba con `pip install -r requerimientos.txt` se adaptó para que **nada se rompa**:

| Archivo | Cambio |
| --- | --- |
| `Dockerfile.test` | Instala con `uv sync --locked --no-install-project` (versiones del lockfile); se probó de verdad: la imagen se construye y los tests pasan adentro |
| `.dockerignore` | Se agregaron `.venv/`, `.git/` y `.mypy_cache/`: sin eso, `COPY . .` metía el entorno virtual local (de Windows) dentro de la imagen de Linux |
| `Makefile` | Los targets usan `uv run ...`; `instalar_dependencias_w/l` se unificaron en `instalar_dependencias` |
| `.github/actions/coverage/linux/action.yml` y `.../windows/action.yml` | Instalan con `astral-sh/setup-uv` + `uv sync --locked` (y de regalo, caché de dependencias) |
| `.github/workflows/MainAction.yml` | El job `check_dep` exporta `uv.lock` a un archivo de requisitos y se lo pasa a `pip-audit` |

> **Importante:** en esta primera tanda estos fueron los **únicos** cambios hechos en `.github/`. Las mejoras de CI que se detectaron quedaron como informe en [`docs/ideas-aprendizaje.md`](../ideas-aprendizaje.md), sección 8;
> varias se aplicaron después (ver el [Bloque H](#bloque-h--cicd-versiones-unificadas-matriz-de-python-y-seguridad)).

---

## 4. Bloque C — Los comandos de la CLI

### Cómo está construida (decisiones heredadas del doc del 29/08)

- **Un archivo por acción** en `src/infraestructura/ui/cli/commands/` (`club_add.py`, `jugador_link.py`…). *Por qué:* es el **patrón Command**: agregar un comando nuevo es crear su archivo y registrarlo
  en el parser, sin tocar los demás (criterio AC1 de la US-106). Explicación en [`06-patron-command.md`](../info_modulo/06-patron-command.md).
- **Flags de `argparse`** (`--nombre`, `--id-club`…), no preguntas interactivas.
- **Inyección de dependencias en cada comando:** `ejecutar(args, repo=None)`. En producción el comando arma el repositorio real; en los tests se le pasa uno falso. *Por qué:* es lo que hace testeable
  cada comando sin tocar la base de datos.

### Los comandos

| Comando | Archivo | Caso de uso | Opciones |
| --- | --- | --- | --- |
| `club add` | `club_add.py` | `CrearClub` | `--nombre` |
| `club list` | `club_list.py` | `ListarClubesUsuario` | `--id-usuario` *(provisorio hasta la US-104)* |
| `jugador add` | `jugador_add.py` *(ya existía; se refactorizó)* | `RegistrarJugador` | `--nombre --apellido --dni --anio` |
| `jugador link` | `jugador_link.py` | `VincularJugadorAClub` | `--id-jugador --id-club --fecha-desde` |
| `jugador list` | `jugador_list.py` | `ListarJugadoresClub` | `--id-club` |
| `competencia add` | `competencia_add.py` | `CrearCompetencia` | `--nombre --anio [--tipo]` |
| `competencia inscribir` | `competencia_inscribir.py` | `InscribirClubEnCompetencia` | `--id-club --id-categoria --id-competencia --fecha-presentacion` |
| `partido list` | `game_list.py` | `ListarPartidosPorClub` | `--id-club` |

`club select` **no se hizo a propósito**: necesita la sesión de la US-104 (login). Cómo se usa cada comando, con ejemplos y errores: [`RUNBOOK.md`](../../RUNBOOK.md).

### Las piezas de soporte y por qué existen

| Pieza | Dónde | Qué hace | Por qué |
| --- | --- | --- | --- |
| **Manejo central de errores** | `main.py` | Un único `except ErrorDeDominio` alrededor de `args.func(args)`: muestra `Error: ...` en stderr, sale con código 1, **sin traceback** | Criterio AC3. Antes cada comando tenía su propio `try/except`; ahora es un solo lugar y los comandos quedan más cortos |
| **`src/utils.py`** *(archivo único en la raíz de `src/`)* | `src/utils.py` | `id_persistido` (movida desde `aplicacion/utils.py`), `abortar(mensaje)` y `fecha_iso` | Un solo módulo de utilidades que llama quien lo necesite. Solo tiene **funciones puras** (no importa `infraestructura`): si las importara, `aplicacion` dependería indirectamente de una capa externa |
| **`abortar(mensaje)`** | `utils.py` | Imprime el error en stderr y termina con código 1 | Los comandos que no pudieron guardar terminan igual que un error de negocio |
| **`fecha_iso`** | `utils.py` | Valida y **normaliza** fechas `AAAA-MM-DD` (`2026-1-5` → `2026-01-05`) | Las fechas se guardan como texto y el schema las compara como texto (`fechaHasta >= fechaDesde`): un formato inconsistente rompería esas comparaciones sin avisar |
| **`abrir_conexion()`** | `database_manager.py` | Abre la base real (`estadisticas.db`) | Evita repetir en 8 comandos la construcción de `SQLiteManager` con las rutas. Está junto a esa clase porque es lo que envuelve |
| **`table_formatter.py`** | `ui/cli/formatters/` | Wrapper de `tabulate` para todos los listados | Criterio AC4 (salida en tablas) y un solo lugar donde cambiar el estilo |

### Detalles de comportamiento que conviene conocer

- **Códigos de salida:** `0` éxito, `1` error de negocio, `2` uso incorrecto de la CLI (lo devuelve `argparse`).
- **Un año de competencia inválido** (`ValueError` de la entidad) también se muestra como mensaje (`competencia_add` lo captura con `abortar`), no como traceback.
- Los comandos de listado muestran un aviso ("El club 2 no tiene jugadores.") en vez de una tabla vacía.

---

## 5. Bloque D — Revisión y ampliación de los tests

### D.1 Qué se encontró al revisar los tests existentes

| Hallazgo | Por qué era un problema | Qué se hizo |
| --- | --- | --- |
| Dos tests "de integración" en realidad probaban **solo entidades** (`Club(nombre=None)`, `Usuario(...)` con tipos incorrectos), sin tocar la base | Un test de integración es más lento y su fallo apunta al lugar equivocado | Se movieron a `tests/unit/test_entidades.py` |
| Las validaciones de **casi todas las entidades** (Club, Jugador, Partido, Inscripcion…) y las reglas del boxscore **no tenían ningún test unitario** | Solo existían los `CHECK` de SQL: si alguien tocaba una regla de Python, nada avisaba | Se agregaron (ver D.2) |
| `test_repositorios_partido.py` armaba un `JugadorPartido` de **20 campos cinco veces** copiando todo | Ruido: lo único que cambiaba era una línea | Fábrica con `**overrides` + `@parametrize` |
| `test_database.py` tenía `test_schema_sql_ejecuta_sin_errores` **definida dos veces** | En Python la segunda definición **tapa a la primera**: uno de los dos tests nunca corría | Quedó una sola (y se unificó otro par casi idéntico) |
| `test_check_constraints` y `test_business_constraints` repetían bloques `pytest.raises(IntegrityError)` | Repetición, y un caso nuevo obligaba a copiar y pegar | `@parametrize` con una fixture de datos base |
| No había tests de casos de uso, de excepciones de dominio ni de comandos de la CLI | Toda la lógica de negocio nueva quedaba sin proteger | Se agregaron (ver D.2) |

### D.2 Tests nuevos, por archivo

| Archivo | Qué prueba | Técnica principal |
| --- | --- | --- |
| `unit/test_entidades.py` | El `TypeError` de **cada campo de cada entidad** (11 entidades) | `@parametrize` con una tabla de entidades |
| `unit/test_entidad_jugador_partido.py` | Cada regla del boxscore: minutos 0–48, puntos = T2C·2+T3C·3+T1C, convertidos ≤ lanzados, no negativos, y los **límites** exactos | Fábrica `crear_boxscore(**overrides)` + `@parametrize` |
| `unit/test_exceptions.py` | Que **toda** excepción de `dominio/exceptions.py` herede de `ErrorDeDominio` (descubre las clases sola: si mañana alguien agrega una y olvida la herencia, falla) | `inspect` + `@parametrize` |
| `unit/test_uc_jugadores.py`, `test_uc_clubes.py`, `test_uc_competencias.py`, `test_uc_partidos.py` | Los **9 casos de uso**: camino feliz, **una prueba por cada excepción de dominio**, el caso "el repositorio no pudo guardar" y listas vacías | `MagicMock(spec=Repositorio)` |
| `unit/test_cli_comandos.py` | Cada comando: mensaje de éxito, tablas, y "no se pudo guardar" (código 1, mensaje en stderr) | Repos falsos + `capsys` |
| `unit/test_cli_main.py` | Que el parser asocia cada comando con su función y tipos; que rechaza argumentos incorrectos (código 2); que `main()` traduce `ErrorDeDominio` y **no esconde** errores que no son de negocio | `monkeypatch` de `sys.argv` |
| `unit/test_utils.py`, `unit/test_table_formatter.py` | `id_persistido`, `abortar`, `fecha_iso` (fechas válidas, inválidas, bisiestos) y el formato de tablas | `@parametrize` |
| `integration/test_cli_e2e.py` | La CLI **completa** (`main()` real) contra una base SQLite temporal: crear club → jugador → vínculo → competencia → inscripción → listados, y los errores de negocio | `tmp_path` + `monkeypatch` |

### D.3 Las técnicas que se introdujeron (y por qué)

Están explicadas a fondo, con ejemplos del proyecto, en [`docs/info_modulo/09-testing.md`](../info_modulo/09-testing.md). En una línea cada una:

- **`@pytest.mark.parametrize`:** ejecuta el mismo test con muchos datos distintos, y cada combinación aparece como un test separado en el reporte. *Para qué:* no copiar y pegar y ver exactamente cuál combinación falló.
- **Patrón `**overrides` (fábricas):** una función que arma una entidad **válida** por defecto y deja pisar solo el campo que le importa al test (`crear_boxscore(idJugador=999999)`). *Para qué:* que cada test
  diga en una línea qué está rompiendo, en vez de repetir 20 campos.
- **`unittest.mock` (`MagicMock(spec=...)`):** un repositorio falso que solo acepta los métodos que tiene el real y recuerda cómo lo llamaron. *Para qué:* probar los casos de uso en microsegundos, sin base de datos, simulando
  cualquier respuesta (incluso errores difíciles de provocar) y verificando qué **no** se llamó (`assert_not_called`: prueba que ante un error el caso de uso cortó antes de guardar).
- **Tests de excepciones de dominio (`pytest.raises`):** por cada regla de negocio, un test que la rompe y verifica el tipo de excepción, su mensaje (`match=`) y que **no se guardó nada**.
- **Test de regresión:** cuando se corrige un bug, se agrega el test que lo habría detectado (ver el del `DROP TABLE` en el punto 7).

### D.4 Cómo se comprobó que los tests sirven (mutación a mano)

Un test que nunca falla no protege nada. Se **rompió a propósito** el código en 4 lugares y se verificó que los tests nuevos lo detectan, restaurando el archivo después de cada prueba:
reponer el `DROP TABLE` en `schema.sql`, romper la regla `T2C <= T2L` de la entidad, sacar el chequeo de club activo de `VincularJugadorAClub`, y hacer que `main()` deje de traducir errores de dominio. Los cuatro fallaron como debían.

### D.5 Resultado

333 tests en verde (al 2026-09-20, ya incluido el Bloque F), cobertura ≈ **89 %** (el mínimo configurado en `.coveragerc` es 60 %), `mypy --strict` sin errores (57 archivos) y `ruff` limpio.
Los tests unitarios corren en menos de un segundo porque no usan base de datos.

---

## 6. Bloque E — Documentación

| Qué | Dónde | Para qué |
| --- | --- | --- |
| **Guía de casos de uso** (qué entra, qué sale, paso a paso, excepciones de cada uno) | `docs/info_modulo/03-casos-de-uso.md` | Entender la lógica de negocio sin leer el código |
| **7 guías movidas** de `docs/guias/` a `docs/info_modulo/` con numeración (`04` a `10`) | ver tabla abajo | Un solo lugar para las guías técnicas, ordenadas |
| **Guía de testing ampliada** (tipos de test, `parametrize`, `**overrides`, `unittest.mock`, excepciones de dominio, fixtures, CLI) | `09-testing.md` | Que el equipo sepa escribir tests siguiendo las mismas técnicas |
| **PRD actualizado** | `docs/plan_desarrollo_detallado.md` | Que el plan refleje lo realmente construido (US-103 ✅, estructura de la CLI por acción, composition root en `main.py`) |
| **`RUNBOOK.md`** | raíz | Cómo usar cada comando, la base de datos, tests, Docker y dependencias; problemas frecuentes |
| **`README.md`** (provisorio) | raíz | Qué es el proyecto, su estado por US, cómo arrancar y dónde está cada cosa |
| **Revisión del CI/CD** | `docs/ideas-aprendizaje.md`, sección 8 | Lista priorizada de qué le falta al CI, explicada desde cero para quien nunca tocó uno |

### Guías movidas

| Antes (`docs/guias/`) | Ahora (`docs/info_modulo/`) | Qué se completó |
| --- | --- | --- |
| `arquitectura.md` | `04-arquitectura.md` | Reescrita con los nombres y el flujo **reales** (`dominio`, `casos_uso`, `ABC`, `SQLiteManager`, `main()`); antes describía el diseño previo en inglés |
| `Guia_Arquitectura_AppEstadistica.md` | `05-guia-arquitectura-app.md` | Sección nueva "Cómo quedó aplicado en este proyecto": mapa entre cada concepto y el código real |
| `Guia_del_Patron_Command.md` | `06-patron-command.md` | Sección nueva con los roles del patrón mapeados a `argparse` y a los archivos de `commands/` |
| `info_protocolos.md` | `07-protocolos.md` | Reescrita: `Protocol` vs `ABC`, y cuál usa el proyecto (**`ABC`**) y por qué |
| `vistas_sql.md` | `08-vistas-sql.md` | Sección nueva: ciclo de vida de las vistas y limitaciones (por ejemplo, `v_jugador_totales_temporada` agrupa por año y no por competencia) |
| `testing.md` | `09-testing.md` | Reestructurada y ampliada (ver arriba) |
| `docker-para-tests.md` | `10-docker-para-tests.md` | Dejó de ser "ejercicio": explica el `Dockerfile.test` real línea por línea |

Se usó `git mv`, así que **el historial de cada archivo se conserva**. Los links internos entre documentos se corrigieron. En las guías **no** se escribió la cantidad de tests, para no tener que actualizarla cada vez.

---

## Bloque F — Ampliación de la US-103: categorías, consultas y lista de buena fe

### Por qué se hizo

Al probar la CLI de punta a punta apareció un problema: `competencia inscribir` pide el id de una **categoría**, pero **no había forma de crearla** (solo por seed o tocando la base a mano). Revisando el PRD se confirmó que
**el propio PRD lo saltea**: el pilar 2 del producto promete "gestión organizativa completa: perfil de usuario, club, **categorías**, competencias y **listas de buena fe**", pero ninguna historia de usuario planificaba
crear ni listar categorías, listar competencias ni administrar la lista de buena fe. Las tablas y los métodos del repositorio (`guardar_categoria`, `agregar_jugador_lista`, `obtener_jugadores_lista`…) ya existían desde
la US-101/102, pero **ningún caso de uso los usaba**. Además, la regla de negocio "solo jugadores habilitados en lista pueden figurar en carga oficial de partido" no tenía de dónde salir.
Para no arrastrar esos huecos hacia la US-104 y siguientes, se decidió cerrarlos **dentro de la US-103**.

### Qué se agregó

| Caso de uso | Comando | Para qué sirve |
| --- | --- | --- |
| `CrearCategoriaUseCase` | `categoria add --nombre` | Crear categorías (ej. U21). Sin ellas no se puede inscribir a ningún club |
| `ListarCategoriasUseCase` | `categoria list` | Conocer el `--id-categoria` que pide `competencia inscribir` |
| `ListarCompetenciasUseCase` | `competencia list` | Conocer el `--id-competencia`: antes solo se veía al crear la competencia |
| `ListarInscripcionesClubUseCase` | `inscripcion list --id-club` | Volver a conocer el id de una inscripción y el de su lista de buena fe (antes solo se veían al inscribir) |
| `AgregarJugadorAListaBuenaFeUseCase` | `lista add --id-inscripcion --id-jugador` | Habilitar a un jugador en la lista de buena fe |
| `ListarListaBuenaFeUseCase` | `lista list --id-inscripcion` | Ver quiénes están habilitados en una lista |

- **DTOs nuevos:** `CrearCategoriaDTO` y `CategoriaDTO` (`categoria_dto.py`); `AgregarJugadorListaDTO` y `JugadorEnListaDTO` (`lista_buena_fe_dto.py`). Los listados reutilizan `CompetenciaDTO`, `InscripcionDTO` y `JugadorDTO`.
- **5 excepciones de dominio nuevas:** `CategoriaDuplicadaError`, `InscripcionNoEncontradaError`, `ListaBuenaFeNoEncontradaError`, `JugadorYaEnListaError` y `JugadorNoPerteneceAlClubError`.
- **6 comandos nuevos**, uno por archivo en `ui/cli/commands/` (`categoria_add.py`, `categoria_list.py`, `competencia_list.py`, `inscripcion_list.py`, `lista_add.py`, `lista_list.py`) y registrados en `main.py`.
- No hizo falta tocar ningún repositorio: todo se apoya en métodos que ya existían.

### Reglas de negocio nuevas (y las decisiones detrás)

| Regla | Por qué |
| --- | --- |
| **Una categoría no puede repetirse**, sin distinguir mayúsculas ni espacios de los extremos (`" u21"` es `U21`) | La tabla `categoria` no tiene `UNIQUE` sobre el nombre; sin la regla, "U21", "u21" y "U21 " serían tres categorías distintas y confundirían las inscripciones |
| **Para habilitar a un jugador en una lista debe existir, no estar ya en la lista y tener un vínculo vigente con el club de la inscripción** | Las dos primeras son integridad básica. La tercera (**el vínculo vigente**) **no estaba en el PRD**: se propuso para evitar listas con jugadores de otros clubes. Si el negocio admite préstamos u otras excepciones, se relaja en `AgregarJugadorAListaBuenaFeUseCase` (es una sola condición). **Conviene confirmarla con quien conozca el reglamento** |

### Tests

- 3 archivos unitarios nuevos para los casos de uso (`test_uc_categorias.py`, `test_uc_consultas_competencias.py`, `test_uc_listas_buena_fe.py`), con una prueba por cada excepción, y uno para los comandos (`test_cli_comandos_listas.py`).
- El parser (`test_cli_main.py`) y el recorrido de punta a punta (`test_cli_e2e.py`) se ampliaron: el E2E **ya no carga la categoría con SQL a mano**, usa `categoria add`, y recorre inscribir → `inscripcion list` → `lista add` → `lista list`, más los errores nuevos.
- Se repitió la **mutación a mano** sobre las reglas nuevas (sacar la regla del club, sacar el chequeo de "ya está en la lista", sacar la normalización del nombre): los tres cambios fueron detectados.

### Documentación actualizada

- **PRD:** US-103 (casos de uso, DTOs, excepciones, comandos, reglas y un recuadro "Alcance ampliado" que explica el hueco), **US-105** (nueva regla: validar el boxscore contra la lista de buena fe, con una decisión pendiente), **US-106** (lista de comandos) y la sección 20 (hueco detectado y decisiones abiertas).
- **Guía de casos de uso (`03-casos-de-uso.md`):** los 6 casos de uso nuevos con su paso a paso, DTOs y excepciones. De paso se corrigió su tabla "Estado en la CLI", que había quedado **desactualizada** (decía "Pendiente" en casi todos los comandos).
- **RUNBOOK, README y `04-arquitectura.md`:** comandos nuevos, y el ejemplo completo ya no usa el atajo de SQL para cargar la categoría.

### Decisiones que siguen abiertas

1. ✅ **Quitar a un jugador de una lista de buena fe:** _resuelto después, en el [Bloque G](#bloque-g--auditoría-de-cierre-de-la-us-103)_ (`lista remove`).
2. **US-105 y la categoría:** el partido guarda competencia y clubes, pero **no la categoría**. Si un club está inscripto en dos categorías de la misma competencia, hay que definir contra qué lista se valida el boxscore.
3. **La regla del vínculo vigente** para habilitar jugadores (ver arriba): confirmarla con el negocio.

---

## Bloque G — Auditoría de cierre de la US-103

### Por qué se hizo

Cuando se preguntó "¿qué falta para cerrar la US-103?" no alcanzaba con decir "nada": se **auditó la US contra sus propias reglas y contra el PRD**, punto por punto, para no arrastrar huecos a la US-104 y siguientes.
Salieron cuatro huecos reales (más una decisión que ya estaba pendiente: poder quitar a un jugador de una lista). Todos se cerraron dentro de la US-103.

### G.1 Quitar a un jugador de la lista de buena fe

- **Problema:** `lista add` habilitaba a un jugador pero **no había forma de deshacerlo**: una habilitación por error quedaba para siempre (solo tocando la base a mano).
- **Qué se agregó:** `QuitarJugadorDeListaBuenaFeUseCase` + `stats lista remove --id-inscripcion --id-jugador`. Pide la inscripción, su lista, verifica que el jugador **esté** en ella (`JugadorNoEstaEnListaError` si no) y lo quita.
  Para eso se sumó `quitar_jugador_lista` al contrato `CompetenciaRepositorio` y a su versión SQLite (un `DELETE` que devuelve `True` solo si borró una fila).
- **Para qué sirve:** corregir errores de carga y dar de baja a alguien de la lista sin borrarlo del sistema ni del club.

### G.2 El ciclo de vida del vínculo jugador-club (cambio de club)

- **Problema:** `jugador link` creaba el vínculo, pero **nada lo cerraba**. Como un jugador solo puede tener un club activo, **quien se vinculaba a un club nunca podía pasar a otro**. La columna `fechaHasta` existía en la base, pero ningún código la escribía.
- **Qué se agregó:**
  - `DesvincularJugadorDeClubUseCase` + `stats jugador unlink --id-jugador --fecha-hasta`: cierra el vínculo vigente. Errores: el jugador no existe, no tiene club activo (`JugadorSinVinculoActivoError`) o la fecha de baja es anterior al inicio (`DatoInvalidoError`).
  - Repositorio: `historial_vinculos` (todos los vínculos del jugador, ordenados) y `cerrar_vinculo` (pone `fechaHasta` al vigente).
  - **Regla nueva:** al vincular, el vínculo nuevo **no puede empezar antes de que termine el anterior** (`VinculoSuperpuestoError`). Sin esta regla se podía "viajar en el tiempo" y dejar dos períodos superpuestos en el historial; el `CHECK` del schema solo compara las dos fechas *de una misma fila*.
  - `VincularJugadorAClubUseCase` ahora devuelve un `VinculoDTO` (antes devolvía la entidad `JugadorClub`, la única excepción a la regla "la CLI no ve entidades"). Se agregaron `DesvincularJugadorDTO` y `VinculoDTO`.
- **Efecto visible:** después de `jugador unlink`, el jugador deja de aparecer en `jugador list` del club viejo (que solo muestra vínculos vigentes) y puede vincularse a otro club; el historial completo queda en la tabla `jugadorClub`.

### G.3 Validaciones de valor en las entidades

- **Problema:** las entidades solo validaban **tipos** (`TypeError`). Un nombre de club vacío (`""`), un DNI negativo o un año de nacimiento `3000` se guardaban sin queja.
- **Qué se agregó** (en el `__post_init__`): nombres no vacíos (`Club`, `Jugador`, `Competencia`, `Categoria`), `dni > 0`, y `1900 < anioNacimiento <= año actual`.
- **Decisión de diseño — `DatoInvalidoError`:** una excepción nueva que **hereda de `ErrorDeDominio` y también de `ValueError`**. Antes las entidades lanzaban `ValueError` pelado y la CLI mostraba un traceback (o cada comando tenía que atraparlo a mano, como hacía `competencia add`).
  Ahora `main()` la atrapa con su único `except ErrorDeDominio` y muestra `Error: ...`; y como sigue siendo un `ValueError`, el código y los tests que ya lo esperaban **no se rompen**. `competencia add` dejó de necesitar su `try/except` propio.
  El `TypeError` **sigue sin atraparse**: un tipo incorrecto es un bug del programa, no un error del usuario.

### G.4 `partido list` con nombres (vista SQL)

- **Problema:** el PRD (US-106, AC2) pide que `partido list` muestre **nombres** de clubes usando `v_partidos_resumen`, pero mostraba ids. Además la vista no traía los ids de los clubes, así que no se podía filtrar por club.
- **Qué se hizo:** la vista ahora expone también `id_club_local` e `id_club_visitante`; `PartidoRepositorio.resumen_por_club` la consulta (`WHERE id_club_local = ? OR id_club_visitante = ?`, ordenada por fecha); el caso de uso devuelve un `PartidoResumenDTO`
  (que **reemplaza** a `PartidoDTO`) y la tabla muestra `ID | Fecha | Estadio | Competencia (nombre y año) | Club local | Club visitante`.
- **Por qué una vista y no un `JOIN` en el código:** la vista ya existía justamente para eso (evitar `JOIN`s en la capa de aplicación) y resuelve todo en una sola consulta. La vista se recrea en cada arranque, así que no hizo falta ninguna migración.
- Se agregó `PartidoResumen`, una entidad **de lectura** sin validación (es lo que devuelve la vista, no algo que el usuario cree).

### G.5 Propiedades calculadas

`Jugador.nombre_completo` y `JugadorPartido.rebotes_totales` (defensivos + ofensivos): el PRD las pedía como "campos calculados". Son `@property`, no se guardan en la base; `nombre_completo` reemplaza al `f"{nombre} {apellido}"` que se repetía en tres casos de uso.

### Tests

- **Unitarios:** `test_entidades_valores.py` (nuevo: cada regla de valor con sus **bordes** —DNI 0 y 1, año 1900 y 1901, año actual y siguiente—, la jerarquía de `DatoInvalidoError` y las dos propiedades calculadas); y los casos de uso, comandos y parser ampliados (`unlink`, `remove`, superposición, `partido list` con nombres).
- **Integración:** repositorios (`historial_vinculos`, `cerrar_vinculo` incluido el rechazo del `CHECK`, `quitar_jugador_lista`, `resumen_por_club`) y el recorrido de punta a punta (`test_cli_e2e.py`): cambio de club sin pisar el período anterior, `lista remove`, nombres en `partido list`, y los errores nuevos por la CLI real.
- **Mutación a mano (10 cambios a propósito):** sacar la regla de superposición (y volverla no estricta), sacar el chequeo de la fecha de baja, sacar el chequeo de "está en la lista", sacar la validación de nombre vacío, aceptar DNI 0, aceptar año futuro, aceptar 1900, que `DatoInvalidoError` deje de ser de dominio e invertir el orden del listado. **Los 10 fueron detectados** por al menos un test, y el código se restauró y se volvió a correr la suite completa.
- **Prueba real de la CLI** sobre una copia del proyecto: cambio de club completo, los errores nuevos (código de salida 1, sin traceback) y los `--help` de los comandos nuevos.

### Decisiones que conviene confirmar con el equipo

1. **La regla de no superposición** de vínculos no estaba en el PRD; se agregó al implementar el cierre del vínculo. Si el negocio necesita permitir períodos que se solapan (por ejemplo, un préstamo), se relaja en `VincularJugadorAClubUseCase`.
2. **El rango del año de nacimiento** (`1901` hasta el año actual, calculado con `date.today()`) se eligió por consistencia con el `CHECK` de `competencia.anio`. Si se quiere una edad mínima o máxima, es una condición en `Jugador.__post_init__`.
3. **Quitar de la lista no borra nada más:** el jugador sigue en su club y en las demás listas.

### Lo que se dejó afuera a propósito

- **Editar o borrar** clubes, competencias y jugadores: el PRD solo pide crear, listar y vincular; no se inventó alcance.
- **`jugador historial`** (ver todos los clubes por los que pasó un jugador): el repositorio ya lo expone (`historial_vinculos`); falta un caso de uso y un comando si se lo necesita.
- **AC4 al pie de la letra** ("los resultados exitosos se muestran en tablas"): hoy los comandos que **crean** algo imprimen una línea de confirmación y los **listados** usan tablas. Se consideró un criterio razonable; si el equipo lo quiere literal, es un cambio chico en los comandos `*_add`.

---

## Bloque H — CI/CD: versiones unificadas, matriz de Python y seguridad

### Por qué se hizo

El informe de CI de [`docs/ideas-aprendizaje.md`](../ideas-aprendizaje.md) (sección 8) describía mejoras que habían quedado **solo como recomendación**. Nico pidió aplicar una parte:
unificar la versión de ruff y mypy, pasar la versión de Python como parámetro a las actions para probar en más de una, corregir los disparadores (`on:`), agregar `concurrency`, `permissions` y `timeout-minutes`,
guardar el reporte de cobertura y subir el umbral (solo en Linux), Dependabot y gitleaks. La explicación didáctica de cada concepto está en esa sección 8; acá va **qué se cambió y por qué**.

### H.1 Una sola versión de ruff y mypy

**El problema:** había tres versiones de ruff dando vueltas — `0.16.8` en `pyproject.toml`, `v0.6.9` en `.pre-commit-config.yaml` y "la última" en el CI (que hacía `pip install ruff` sin versión). Distintas versiones pueden formatear o avisar distinto:
el código podía pasar el CI y fallar en la máquina de alguien, o al revés. Con mypy pasaba lo mismo entre `pyproject.toml` y el CI.

**La solución:** la única fuente de verdad es `pyproject.toml` (traducido a versiones exactas por `uv.lock`) y todos la leen a través de `uv`:

| Quién | Cómo obtiene la versión |
| --- | --- |
| Action de ruff (`style/ruff`) | `uv sync --locked --only-group dev` (solo las herramientas de desarrollo) y `uv run --no-sync ruff ...` |
| Action de mypy (`style/mypy`) | `uv sync --locked` (todo el proyecto: mypy necesita las librerías para resolver imports) y `uv run --no-sync mypy ...` |
| pre-commit | Hooks `repo: local` con `language: system` que ejecutan `uv run --locked ruff check --fix` y `uv run --locked ruff format` |

**Consecuencia:** subir la versión de ruff o mypy es cambiar **un solo lugar** (`pyproject.toml` + `uv lock`). **Costo:** para usar pre-commit hace falta `uv` instalado. Las reglas de ruff no se tocaron.
También se corrigieron los nombres de los pasos de la action de mypy ("Instalar Ruff" / "Ejecutar Ruff", copiados de la de ruff).

### H.2 La versión de Python como parámetro, y matriz 3.11 a 3.14

- Las 5 actions propias (`style/ruff`, `style/mypy`, `coverage/linux`, `coverage/windows`, `coverage/docker`) tienen el parámetro `python-version` (por defecto `"3.11"`, la mínima que promete `requires-python`).
- En `MainAction.yml`, los jobs `static` (mypy), `tests-linux` y `tests-docker` usan una **matriz** con `["3.11", "3.12", "3.13", "3.14"]` y `fail-fast: false` (si una versión falla, las demás igual terminan y se ven todos los resultados).
  `lint` (ruff) no usa matriz: su resultado no depende de la versión de Python. `tests-windows` tampoco: corre **solo con Python 3.13** (alcanza para detectar problemas propios del sistema operativo —rutas, saltos de línea, SQLite—; las diferencias entre versiones de Python ya se cubren en Linux, y en un repositorio privado los minutos de Windows cuestan el doble). Una corrida completa son **16 ejecuciones** (7 jobs; 3 de ellos × 4 versiones).
- **mypy:** se le pasa `--python-version`, que pisa el `python_version = "3.11"` de `pyproject.toml`, para chequear los tipos contra la versión de cada vuelta.
- **Docker:** `Dockerfile.test` pasó de `FROM python:3.13-slim` a `ARG PYTHON_VERSION=3.11` + `FROM python:${PYTHON_VERSION}-slim`; la action hace `docker build --build-arg PYTHON_VERSION=...`.
  El `Makefile` tiene `PYTHON_VERSION ?= 3.11`, así que a mano se usa `make docker_test PYTHON_VERSION=3.13`.

### H.3 Disparadores, `concurrency`, `permissions` y `timeout-minutes`

- **`on:`** ahora es `workflow_dispatch` + `pull_request` (`opened`, `synchronize`, `reopened`, `ready_for_review`) + **`push` a `main` y `develop`** (antes no corría al mergear).
- **`concurrency`:** una sola corrida por PR o por rama; si llega un push nuevo se **cancela la anterior, pero solo en Pull Requests** (en `main`/`develop` cada corrida termina, para conservar el resultado de cada commit).
- **`permissions: contents: read`** para todo el workflow (mínimo privilegio del `GITHUB_TOKEN`). El job `gitleaks` declara el suyo, con `pull-requests: read` además.
- **`timeout-minutes`** en cada job: 10 (`check_dep`, `gitleaks`, `lint`, `static`), 15 (`tests-linux`), 20 (`tests-windows`, `tests-docker`).

### H.4 Cobertura: reporte guardado y umbral de 85 % (solo Linux)

- La action de Linux exige **85 %** con `--cov-fail-under` (parámetro `cobertura-minima`). El flag pisa el `fail_under = 60` de `.coveragerc`, que se dejó **como piso base** para tu máquina, Windows y Docker (por eso el pedido "solo Linux").
- Guarda el reporte HTML (`reportes_cobertura/html/`) con `actions/upload-artifact`, incluso si algo falla (`if: ${{ !cancelled() }}`), durante 14 días. Hay un reporte por versión de Python (`reporte-cobertura-linux-py3.11` …), porque dos artifacts no pueden tener el mismo nombre.
- Se agregó `--cov-report=term` para que el porcentaje también se vea en el log.
- **Por qué 85 %:** medido 91,2 % (Windows, Python 3.13) y 90,8 % (Linux, Python 3.14). El PRD pide 80 %; 85 % deja margen para que una diferencia entre versiones no rompa el CI sin motivo.

### H.5 Dependabot

Nuevo `.github/dependabot.yml`: cada lunes revisa **`uv`** (`pyproject.toml` + `uv.lock`; `pytest`, `pytest-cov`, `ruff` y `mypy` en un solo PR), **`github-actions`** (workflows y actions propias, todas en un PR) y **`docker`** (`Dockerfile.test`).
Como las versiones están fijadas con `==`, cada PR cambia la versión y regenera el lockfile: ruff y mypy suben a la vez en CI, pre-commit y local. Los PR van a `main` (sin `target-branch`).

### H.6 gitleaks

Nuevo job `gitleaks` (`gitleaks/gitleaks-action@v3`, con `fetch-depth: 0` para ver todo el historial). El repositorio es de una cuenta personal, así que **no necesita licencia** (sí la necesitaría si pasara a una organización).
Se desactivaron los comentarios automáticos en el PR (`GITLEAKS_ENABLE_COMMENTS: false`) para no darle permiso de escritura; el resultado queda en el resumen del job.
Se corrió gitleaks sobre todo el historial en local: **218 commits escaneados, 0 filtraciones**.

### H.7 Tres referencias del CI que no funcionaban (corregidas)

Al verificar cada action contra GitHub (`git ls-remote`, `action.yml`) aparecieron tres problemas que habrían roto el CI en la primera corrida:

1. **`astral-sh/setup-uv@v10` no existe.** Esa action dejó de publicar etiquetas móviles de versión mayor; solo existen las exactas (`v10.1.0`). Lo había escrito la sesión anterior (Bloque B) sin verificarlo. Ahora es `@v10.1.0` en el workflow y en las 5 actions (Dependabot la mantiene al día).
2. **`pypa/pip-audit-action@v1.6.0` no existe.** El repositorio real es `pypa/gh-action-pip-audit` (última versión `v1.1.0`). Venía así **desde antes de esta sesión**: el job `check_dep` nunca pudo arrancar.
3. **`actions/checkout@v4` corre sobre Node 20**, que según el aviso de GitHub se retiró de sus máquinas el 2026-09-16. Se pasó a `@v7` (Node 24), igual que `upload-artifact@v7` y `gitleaks-action@v3`.

### H.8 Cómo se verificó — y qué NO se pudo verificar

**Verificado en la máquina local (nada se subió a GitHub):**

- **`actionlint`** sobre todos los workflows y actions locales: sin errores. Se comprobó además que **sí detecta** problemas (se rompió a propósito el nombre de un parámetro y lo marcó).
- Los pasos de las actions se emularon a mano, con un entorno aislado por versión y sobre una **copia** del proyecto: ruff limpio y, para Python 3.11, 3.12 y 3.13, mypy sin errores + `pytest` con **399 tests en verde, 91,23 % de cobertura** (≥ 85) y reporte HTML generado.
- **Python 3.14:** el instalador de `uv` falló en esta máquina (error local, no del proyecto), así que se verificó de otra forma: mypy con `--python-version 3.14` sin errores y la **imagen Docker con Python 3.14.7 real**: 399 tests en verde, 90,79 % de cobertura.
- **Docker:** se comprobó que sin `--build-arg` la imagen usa Python 3.11.16 y con `--build-arg PYTHON_VERSION=3.14` usa 3.14.7.
- **pre-commit:** `validate-config` correcto; sobre una copia, los hooks `ruff check` y `ruff format` pasan y ejecutan `ruff 0.16.8` (la de `pyproject.toml`).
- **gitleaks** sobre todo el historial (Docker): 218 commits, sin filtraciones.

**No se pudo verificar (hay que mirarlo en la primera corrida real):** la ejecución en los runners de GitHub (nada se subió), el job de **Windows** (Python 3.13), el comportamiento de `gitleaks-action@v3` y de `gh-action-pip-audit@v1.1.0` (solo se comprobó que existen y sus parámetros),
y que GitHub acepte el `dependabot.yml` (si tuviera un error, aparece en _Insights → Dependency graph → Dependabot_).

### Qué tenés que hacer al bajar estos cambios

1. Tener **`uv`** instalado y, si querés los hooks, `uv tool install pre-commit` + `pre-commit install` (RUNBOOK, sección 7).
2. Al abrir el primer PR, mirar que corran las **16 ejecuciones** y, si alguna falla, leer el log: es la primera vez que este workflow corre de verdad.
3. En GitHub, activar **Dependabot alerts** y **security updates** (_Settings → Code security_): es un ajuste de la cuenta, no se puede hacer desde el repositorio.
4. Cuando se decida, crear el **job agregador y las _required status checks_** (sección 8.9 del informe de CI): con la matriz, los nombres de los jobs cambiaron.

### Decisiones que conviene confirmar

1. **Incluir Python 3.14** en la matriz (si no se quiere, se saca de la lista de los 3 jobs con matriz).
2. **El umbral de 85 %** (medido ≈ 91 %; el PRD pide 80 %).
3. **Costo de minutos:** los tests de Linux y de Docker se repiten 4 veces; Windows corre una sola (3.13). En un repositorio **público** es gratis; en uno privado los minutos de Windows cuentan doble (por eso Windows va con una sola versión).
4. **Dependabot sin `target-branch`:** los PR de actualización van a `main`. Si el flujo del equipo integra en `develop`, hay que agregarlo.
5. **Reglas de ruff que no coinciden:** el CI y el `Makefile` corren `ruff check --select E --select I` (todas las reglas `E`), mientras que `pyproject.toml` selecciona solo `E501` e `I` y pre-commit usa esa configuración. El CI es un poco más estricto que pre-commit. No se tocó (fuera del pedido); conviene unificarlo.

### Lo que se dejó afuera a propósito

Job agregador y _required status checks_ (8.9), `ruff format --check` (8.2), smoke test de la CLI (8.14), fijar actions por hash (8.13), sacar `submodules: recursive` de `check_dep`/`lint`/`static` (8.4) y agregar mypy o gitleaks a pre-commit: no se pidieron y quedaron documentados en la sección 8.

---

## 7. Bugs encontrados y corregidos

| # | Bug | Gravedad | Cómo apareció | Corrección | Test que lo protege |
| --- | --- | --- | --- | --- | --- |
| 1 | **`schema.sql` empezaba con 12 `DROP TABLE` y `main()` lo ejecuta en cada arranque → la app borraba todos los datos cada vez que se abría** | 🔴 Crítica | Al probar la CLI de verdad: el segundo club creado también salía con `id=1` y `jugador link` no encontraba al jugador recién creado. Antes nadie lo notaba porque solo existía `jugador add` | Se quitaron los `DROP TABLE` (todas las tablas ya eran `CREATE TABLE IF NOT EXISTS`: el diseño buscaba que fuera idempotente). Las vistas sí se recrean en cada arranque (es seguro: no guardan datos) | `test_los_datos_persisten_entre_ejecuciones` (E2E) |
| 2 | `pyproject.toml` con una tabla de setuptools inexistente → el proyecto **no podía instalarse** | 🟠 Alta | Al correr `uv sync` | `[tool.setuptools.packages.find]` con `namespaces = true` | — (lo cubre el CI al instalar) |
| 3 | `ListarJugadoresClubUseCase` se rompía si el repositorio devolvía `None` | 🟠 Alta | Análisis de tipos (mypy) | `or []` | `test_listar_jugadores_sin_resultados_devuelve_lista_vacia` |
| 4 | `buscar_por_club` incluía jugadores que ya se habían ido del club (y duplicaba a los que volvieron) | 🟠 Alta | Revisión del repositorio | Filtro `fechaHasta IS NULL` | `test_buscar_por_club_excluye_vinculos_cerrados` |
| 5 | La entidad `Competencia` rechazaba años `<= 2000` (el 2000 mismo y todos los anteriores), pero el `CHECK` de la base permite `> 1900`; además el mensaje decía "menor que 2000" | 🟡 Media | Revisión de reglas | Ahora `<= 1900` y con el valor recibido en el mensaje | `test_entidad_competencia.py`, `test_business_constraints` |
| 6 | `VincularJugadorAClub` no verificaba que el jugador ni el club existieran | 🟡 Media | Revisión del caso de uso | Excepciones `JugadorNoEncontradoError` / `ClubNoEncontradoError` | `test_vincular_jugador_que_rompe_una_regla_...` |
| 7 | `mypy --strict` reportaba 9 errores (ID `int \| None` vs `int`) y el CI corre mypy | 🟡 Media | Análisis de tipos | `id_persistido()` | `test_utils.py` |
| 8 | Un test de `test_database.py` **nunca corría** (nombre de función duplicado) | 🟡 Media | Revisión de tests | Queda una sola definición | — |
| 9 | `tabulate` no estaba declarada como dependencia → el CI y Docker habrían fallado | 🟠 Alta (prevenido) | Al agregar la CLI | Declarada en `pyproject.toml` | El CI |
| 10 | `.dockerignore` no excluía `.venv/` → `COPY . .` copiaba el entorno local de Windows a la imagen | 🟡 Media (prevenido) | Revisión de Docker | Se agregó | Build de la imagen |
| 12 | **Un jugador que se vinculaba a un club nunca podía pasar a otro**: nada cerraba el vínculo (`fechaHasta` no se escribía en ningún lado) | 🟠 Alta | Auditoría de la US-103 | `jugador unlink` + regla de no superposición (Bloque G.2) | `test_desvincular_*`, `test_un_jugador_puede_cambiar_de_club_...` |
| 13 | Se aceptaban nombres vacíos, DNI negativos y años de nacimiento imposibles | 🟡 Media | Auditoría de la US-103 | `DatoInvalidoError` en las entidades (Bloque G.3) | `test_entidades_valores.py`, casos de error del E2E |
| 14 | `partido list` mostraba ids en lugar de nombres, aunque el PRD pedía usar la vista | 🟡 Media | Auditoría de la US-103 | `resumen_por_club` sobre `v_partidos_resumen` (Bloque G.4) | `test_resumen_por_club_*`, `test_partido_list_muestra_los_nombres_...` |
| 15 | **`astral-sh/setup-uv@v10` no existe** (esa action ya no publica etiquetas móviles): todo job que instalaba uv habría fallado al arrancar | 🔴 Crítica | Al verificar las versiones de las actions contra GitHub (Bloque H.7) | Versión exacta `@v10.1.0` en el workflow y en las 5 actions | Primera corrida real en GitHub; `actionlint`; Dependabot la mantiene al día |
| 16 | **`pypa/pip-audit-action@v1.6.0` no existe** (el repositorio real es `pypa/gh-action-pip-audit`): el job `check_dep` nunca pudo correr. Venía de antes de la sesión | 🟠 Alta | Idem | `pypa/gh-action-pip-audit@v1.1.0` | Idem |
| 17 | **`actions/checkout@v4` usa Node 20**, retirado de los runners de GitHub el 2026-09-16 | 🟠 Alta | Al revisar el `using:` de cada action | `actions/checkout@v7` (Node 24) | Idem |
| 11 | Un paquete `config` de terceros, instalado en el Python global, **tapaba** al `src/config` del proyecto (`AttributeError: ... 'LOG_DIR'`) | 🟡 Media (entorno) | Al correr pytest con el Python global | No hay cambio de código: usando el entorno de `uv` no ocurre. Está documentado en el RUNBOOK | — |

---

## 8. Decisiones de diseño y por qué se tomaron

| Decisión | Alternativas consideradas | Por qué se eligió esta |
| --- | --- | --- |
| **Un archivo por acción** en `commands/` | Un archivo por entidad (`club_commands.py`), como decía el PRD | Es lo que ya estaba construido (`jugador_add.py`) y lo que documentó el 29/08; es el patrón Command más literal. **El PRD se actualizó** para reflejarlo |
| **`main.py` como composition root** (sin `main_cli.py`) | Un `main_cli.py` separado | Cada ejecución de la CLI corre **un único comando**; `main.py` ya cumplía ese rol y no tiene sentido duplicarlo |
| **Cada comando arma sus dependencias** (`ejecutar(args, repo=None)`) | Que `main.py` arme todos los repositorios al arrancar | Armar 6 repositorios para usar 1 es trabajo desperdiciado; y la inyección opcional hace testeable a cada comando |
| **Un solo `except ErrorDeDominio` en `main()`** | `try/except` en cada comando | Un solo lugar; agregar comandos no obliga a repetirlo; los tests verifican la regla una vez |
| **Errores en stderr con código de salida ≠ 0** | Imprimir el error en stdout | Estándar de las herramientas de línea de comandos: permite automatizar y separar la salida normal de los errores |
| **`src/utils.py` en la raíz de `src/` con solo funciones puras** | Dos `utils.py` (uno en `aplicacion/` y otro en la CLI) | Un solo módulo; y al ser puro no rompe la regla de dependencias entre capas. `abrir_conexion` **no** va ahí (importa infraestructura): quedó junto a `SQLiteManager` |
| **Los casos de uso devuelven DTOs** | Devolver entidades | La CLI no depende de la forma interna del dominio |
| **`id_persistido()`** para el tipo `int \| None` | `assert` en cada lugar; o tipar los DTOs como `int \| None` | Sirve dentro de listas por comprensión (donde un `assert` no cabe), no se apaga con `python -O` y deja el DTO honesto (siempre tiene ID) |
| **`MagicMock(spec=...)`** en lugar de repositorios "fake" escritos a mano | Clases fake | Cada test necesita pocas respuestas puntuales; el fake obliga a implementar todos los métodos abstractos. La guía de testing muestra ambos |
| **Sin `__init__.py`** | Agregarlos en `src/` y `tests/` | Desde Python 3.3 no hacen falta (paquetes *namespace*); el proyecto ya funcionaba así. La única consecuencia: los archivos de test deben tener **nombres únicos** |
| **`uv` + `pyproject.toml` + `uv.lock`** | Seguir con `requerimientos.txt` + `pip` | Reproducibilidad exacta, instalación más rápida y una sola fuente de verdad para las dependencias |
| **Versiones fijas (`==`)** | Rangos (`>=`) | Es una aplicación (no una librería): interesa reproducir exactamente lo probado. Las actualizaciones se hacen a propósito (y se pueden automatizar con Dependabot, ver el informe de CI) |

---

## 9. Incidentes de la sesión (transparencia)

Cosas que salieron mal durante el trabajo y cómo se resolvieron, para que nadie se sorprenda:

1. **`tests/unit/` desapareció y se recreó.** Al comparar `mypy` contra el estado anterior se usó `git stash -u`, y git **borró la carpeta `tests/unit/`**, que estaba vacía y sin trackear. Se recreó con los tests nuevos.
   No se perdió ningún archivo con contenido.
2. **El seed de ejemplo se cargó por error en tu `estadisticas.db` real** (2026-09-20, 11:28). Durante una prueba de comandos de una línea se ejecutó `import config.rutas` desde una carpeta temporal, pero Python resolvió el
   paquete **instalado** del proyecto (el real) y no el de la copia de prueba. Se detectó al ver que el hash del archivo había cambiado, y se confirmó con el log. La base tenía las tablas vacías antes (los conteos
   coincidían exactamente con el seed), así que se **guardó una copia del estado con seed y se vaciaron las tablas** para dejarla como estaba. Si querés datos de ejemplo, el RUNBOOK (sección 4) explica cómo cargar el seed.
   *Lección aplicada:* las pruebas de la CLI se hacen sobre una **copia** del proyecto y se verifica el hash de la base real antes y después.
3. **`git add -N .`** (usado para listar archivos nuevos) dejó marcados los archivos nuevos en el índice y **stageó el borrado del PDF del PRD**; se revirtió: el índice quedó como antes (los `git mv`/`git rm` de las guías y de
   `requerimientos.txt` sí quedan preparados a propósito).
4. **Una prueba de "mutación"** modificó temporalmente archivos de `src/`; todos se restauraron y la suite se volvió a correr completa en verde.
5. **Cambió el hash de `estadisticas.db`** entre dos momentos de la sesión (las tablas siguen **vacías**, sin ningún dato). La explicación probable: al modificar la vista `v_partidos_resumen`, cualquier arranque de la app que abre
   la base real la recrea con la definición nueva (las vistas se recrean en cada arranque, por diseño), y eso reescribe el archivo. Se comprobó que la suite de tests **no** la toca (el hash queda igual antes y después de correrla)
   y que las pruebas de la CLI se hicieron sobre copias. Si querés estar seguro, abrila con un visor de SQLite: no tiene filas.
6. **El `.venv` del proyecto quedó roto (y era de Linux).** Al correr `uv run pytest` desde Windows para medir la cobertura, `uv` encontró un `.venv` creado por otra máquina (uv 0.12.17, Python 3.12.3, `home = /usr/bin`: casi seguro
   desde **WSL**), decidió recrearlo, borró casi todo su contenido y se detuvo con `Acceso denegado` al llegar al enlace `lib64`. Quedó solo `pyvenv.cfg` y `lib64`. **No se perdió ningún dato** (es un entorno regenerable e ignorado por git),
   pero **hay que volver a correr `uv sync` desde el sistema donde se usaba (WSL)**. *Lección aplicada:* no se vuelve a ejecutar `uv` dentro de la carpeta real; el resto de las pruebas de CI se hicieron sobre una **copia** del proyecto con
   entornos propios. El RUNBOOK (sección 10) explica cómo evitarlo (un entorno por sistema con `UV_PROJECT_ENVIRONMENT`).
7. **Se creó la carpeta `C:\c\...` por error** con los entornos temporales de esas pruebas: `uv` no traduce las rutas estilo Git Bash (`/c/Users/...`) y las tomó como `C:\c\Users\...`. Se comprobó que solo contenía esos entornos y se borró.

---

## 10. Lo que NO se hizo y límites conocidos

**No se hizo (a propósito):**

- **Mejoras de CI:** se aplicaron las del Bloque H. Quedan como recomendación (`docs/ideas-aprendizaje.md`, sección 8): job agregador + _required status checks_, `ruff format --check`, smoke test, fijar actions por hash y CD.
- **No se tocó el submódulo** `docs/documentacion_app_estadistica/` (está desactualizado; el PRD vigente es `docs/plan_desarrollo_detallado.md`).
- **`sphinx` y `sphinx-rtd-theme` se sacaron** de las dependencias de desarrollo (decisión de Nico) porque no había `conf.py` ni uso en el repo.
- **No se hicieron commits** de la parte 2.

**Límites conocidos de lo que hoy funciona:**

| Límite | Por qué | Cuándo se resuelve |
| --- | --- | --- |
| No hay login ni sesión: `club list` pide `--id-usuario` y no existe `club select` | Depende del `SessionManager` | US-104 |
| Los clubes creados **no se vinculan a ningún usuario** (no aparecen en `club list`) | Necesita saber quién está logueado | US-104 |
| No se puede **editar ni borrar** un club, una competencia ni un jugador | El PRD solo pide crear, listar y vincular | Si se lo necesita, es una US nueva |
| No se pueden cargar partidos ni estadísticas | Es la US-105 | US-105 |
| Un club con nombre repetido da un mensaje genérico (`no se pudo guardar el club`) | El repositorio devuelve `None` ante cualquier error de SQLite | Un `ClubDuplicadoError` sería una mejora chica |
| No hay un comando para ver **todos los clubes por los que pasó** un jugador | `jugador list` muestra solo los vínculos vigentes de un club | Falta un caso de uso `jugador historial` (el repositorio ya expone el dato) |
| El CI nuevo (matriz de Python, gitleaks, Dependabot, cobertura 85 %) **solo se probó en local**, no en GitHub | No se subió nada | La primera corrida real (ver Bloque H.8) |

---

## 11. Cómo verificar todo

```bash
uv sync                                                         # instalar exactamente lo del lockfile
uv run pytest                                                   # toda la suite (todo en verde)
uv run pytest tests/unit                                        # solo unitarios (rápidos)
uv run ruff check --select E --select I .                       # estilo: "All checks passed"
uv run mypy src/ --strict --explicit-package-bases              # tipos: "Success: no issues found"
docker build -f Dockerfile.test -t app-estadisticas-tests . && docker run --rm app-estadisticas-tests   # tests en un contenedor limpio
uv export --frozen --no-emit-project --no-hashes -o requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --no-deps --disable-pip   # "No known vulnerabilities found"
```

**Resultados obtenidos el 2026-09-20:** suite completa en verde (399 tests), cobertura ≈ 91 %, mypy y ruff sin errores, imagen Docker construida y con los tests pasando adentro, auditoría sin vulnerabilidades,
y el YAML de los workflows de CI válido. Además se probó la CLI **de verdad** (los 16 comandos, en camino feliz y de error) sobre una copia del proyecto.

**Verificación del Bloque H (CI):** `actionlint` sin errores en workflows y actions; para Python 3.11, 3.12 y 3.13, mypy limpio y 399 tests en verde con 91,23 % de cobertura (mínimo 85 %); Python 3.14 con mypy (`--python-version 3.14`) y con una imagen
Docker real (399 tests, 90,79 %); gitleaks sobre 218 commits sin filtraciones; hooks de pre-commit válidos y con `ruff 0.16.8`. La ejecución en GitHub **no** se pudo probar (ver Bloque H.8).

---

## 12. Próximos pasos sugeridos

1. **Revisar y commitear la parte 2** (sugerencia de commits separados: dependencias/uv, CLI, tests, documentación).
2. **Subir el CI y mirar la primera corrida** (Bloque H.8); después, lo que falta del informe de CI: job agregador + *required checks* (8.9) y `ruff format --check` (8.2): `docs/ideas-aprendizaje.md`, sección 8.16.
3. **US-104** (login y sesión): desbloquea `club select`, vincular clubes con usuarios y dejar de usar `--id-usuario`.
4. Al arrancar la **US-105**, definir contra qué lista se valida el boxscore cuando el partido no guarda la categoría (ver Bloque F). Confirmar además las decisiones del Bloque G (superposición de vínculos y rango del año de nacimiento).
5. **US-105/106:** carga de partidos, formularios interactivos y `partido boxscore` (los nombres en `partido list` ya están).
6. Activar Dependabot alerts/security updates en GitHub y confirmar las decisiones del Bloque H (Python 3.14 en la matriz, umbral de 85 %, `target-branch` de Dependabot, reglas de ruff del CI vs. `pyproject.toml`).

---

## 13. Inventario de archivos

**Código (`src/`)**

| Estado | Archivos |
| --- | --- |
| Nuevos | `utils.py`; `infraestructura/ui/cli/commands/{club_add,club_list,jugador_link,jugador_list,competencia_add,competencia_inscribir,game_list}.py`; `infraestructura/ui/cli/formatters/table_formatter.py`; **Bloque F:** `aplicacion/casos_uso/{crear_categoria,listar_categorias,listar_competencias,listar_inscripciones_club,agregar_jugador_lista,listar_lista_buena_fe}.py`, `aplicacion/dtos/{categoria_dto,lista_buena_fe_dto}.py`, `infraestructura/ui/cli/commands/{categoria_add,categoria_list,competencia_list,inscripcion_list,lista_add,lista_list}.py`; **Bloque G:** `aplicacion/casos_uso/{desvincular_jugador_club,quitar_jugador_lista}.py`, `infraestructura/ui/cli/commands/{jugador_unlink,lista_remove}.py` |
| Modificados | **Bloque G:** `dominio/exceptions.py`, `dominio/entidades/{club,jugador,competencia,partido}.py`, los contratos `{jugador,competencia,partido}_repositorio.py` y sus versiones SQLite, `persistencia/sql/views.sql`, `dtos/{club,partido,lista_buena_fe}_dto.py`, `casos_uso/{vincular_jugador_club,partidos_por_club}.py`, `commands/{game_list,competencia_add}.py`; además: `main.py`; `infraestructura/persistencia/database_manager.py` (`abrir_conexion`); `infraestructura/persistencia/sql/schema.sql` (sin `DROP TABLE`); `infraestructura/ui/cli/commands/jugador_add.py`; `aplicacion/casos_uso/*` (imports de `utils`) |
| Eliminados | `aplicacion/utils.py` (se movió a `utils.py`) |
| Parte 1 (commiteada) | 4 casos de uso nuevos y 5 corregidos; `dominio/exceptions.py`; `CompetenciaRepositorio.inscribir_con_lista` (interfaz y SQLite); `Competencia` (año); `buscar_por_club` (filtro) |

**Tests (`tests/`)**

| Estado | Archivos |
| --- | --- |
| Nuevos | `unit/{test_entidades,test_entidad_jugador_partido,test_exceptions,test_uc_jugadores,test_uc_clubes,test_uc_competencias,test_uc_partidos,test_cli_comandos,test_cli_main,test_utils,test_table_formatter}.py`; `integration/test_cli_e2e.py`; **Bloque F:** `unit/{test_uc_categorias,test_uc_consultas_competencias,test_uc_listas_buena_fe,test_cli_comandos_listas}.py`; **Bloque G:** `unit/test_entidades_valores.py` |
| Modificados | `conftest.py` (fábricas `crear_jugador`/`crear_partido`/`crear_boxscore`); `integration/{test_database,test_repositorios_club,test_repositorios_partido,test_repositorios_usuario}.py` |
| Eliminados | `unit/test_utils_aplicacion.py` (reemplazado por `test_utils.py`) |

**Dependencias e infraestructura de proyecto**

`pyproject.toml` (modificado), `uv.lock` (nuevo), `requerimientos.txt` (**eliminado**), `Dockerfile.test` (`ARG PYTHON_VERSION`), `.dockerignore`, `Makefile` (`PYTHON_VERSION`), `.coveragerc` (comentario),
`.pre-commit-config.yaml` (ruff con `uv run`), `.github/workflows/MainAction.yml` (Bloque B: instalación; Bloque H: reescrito), `.github/actions/{coverage/{linux,windows,docker},style/{ruff,mypy}}/action.yml` y **`.github/dependabot.yml`** (nuevo).

**Documentación**

`RUNBOOK.md` (nuevo), `README.md` (reescrito), `docs/plan_desarrollo_detallado.md` (PRD), `docs/ideas-aprendizaje.md` (sección 8 nueva), `docs/info_modulo/04…10-*.md` (movidas y completadas),
`docs/info_modulo/03-casos-de-uso.md` (los 17 casos de uso), `docs/info_modulo/{04-arquitectura,08-vistas-sql}.md` (Bloque G), `docs/context_ia/2026-07-31…`, `2026-08-08…` y `2026-08-29…` (solo se corrigieron rutas y enlaces), y este informe.

---

## 14. Glosario

| Término | Significado |
| --- | --- |
| **Caso de uso** | Una acción del usuario escrita como clase con `ejecutar()`; contiene las reglas de negocio |
| **DTO** | *Data Transfer Object*: un objeto plano que solo transporta datos entre capas (entra a un caso de uso o sale de él) |
| **Entidad** | Una clase del dominio (`Jugador`, `Club`…) que valida sus propios datos al crearse |
| **Repositorio** | La clase que sabe guardar y leer entidades de la base de datos. El dominio define su *contrato* (`ABC`) y la infraestructura lo implementa con SQLite |
| **Excepción de dominio** | Un error de negocio esperable (`DNIDuplicadoError`); todas heredan de `ErrorDeDominio` |
| **Composition root** | El único lugar donde se arman y conectan las dependencias (acá: `main.py` y cada comando) |
| **Atomicidad** | "Todo o nada": varias escrituras que se guardan juntas o no se guarda ninguna |
| **Idempotente** | Que se puede ejecutar varias veces con el mismo resultado (el schema debe serlo, porque corre en cada arranque) |
| **Mock / `MagicMock`** | Un objeto falso para tests que devuelve lo que se le indique y recuerda cómo lo llamaron |
| **Fixture** | Una función de pytest que prepara algo que el test necesita (una base en memoria, una entidad) |
| **`uv` / lockfile** | La herramienta que instala Python y las dependencias / el archivo (`uv.lock`) que fija la versión exacta de cada una |
| **CI** | Integración continua: el robot que prueba cada Pull Request (ver `docs/ideas-aprendizaje.md`, sección 8.0) |
| **Regresión (test de)** | Un test que asegura que un bug ya corregido no vuelva a aparecer |
