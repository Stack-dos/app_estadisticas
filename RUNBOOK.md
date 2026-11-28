# RUNBOOK — cómo operar StatsPro Basketball

Un *runbook* es la guía práctica de **cómo se usa y se mantiene** algo: qué comandos correr, qué esperar como resultado y qué hacer cuando algo falla. Este documento cubre cómo abrir la
aplicación, la base de datos, los tests y las herramientas de calidad. Para entender **por qué** el código está organizado como está, ver
[docs/info_modulo/04-arquitectura.md](docs/info_modulo/04-arquitectura.md); para la interfaz gráfica, [docs/info_modulo/13-gui-flet-y-eventos.md](docs/info_modulo/13-gui-flet-y-eventos.md).

## Índice

1. [Requisitos e instalación](#1-requisitos-e-instalación)
2. [Cómo abrir la aplicación](#2-cómo-abrir-la-aplicación)
3. [Qué se puede hacer hoy](#3-qué-se-puede-hacer-hoy)
4. [Errores](#4-errores)
5. [La base de datos y los logs](#5-la-base-de-datos-y-los-logs)
6. [Tests, calidad de código y seguridad](#6-tests-calidad-de-código-y-seguridad)
7. [Docker](#7-docker)
8. [Manejo de dependencias](#8-manejo-de-dependencias)
9. [Problemas frecuentes](#9-problemas-frecuentes)
10. [Qué todavía no se puede hacer](#10-qué-todavía-no-se-puede-hacer)
11. [Sacar una versión](#11-sacar-una-versión)

---

## 1. Requisitos e instalación

**Necesitás:**

- **Git**, para clonar el repositorio.
- **[uv](https://docs.astral.sh/uv/)**, la herramienta que instala Python y las dependencias del proyecto. Reemplaza a `pip` y a `python -m venv`: crea el entorno virtual y instala las versiones exactas
  de cada librería (las fijadas en `uv.lock`) con un solo comando. Si no tenés Python ≥ 3.12, uv lo descarga solo.
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

## 2. Cómo abrir la aplicación

Desde la **raíz del repositorio**:

```bash
uv run python src/main.py
```

Se abre la ventana en la pantalla de inicio de sesión. El programa queda corriendo hasta que se cierra la ventana.

- **Primera vez:** Flet descarga su cliente de escritorio (la ventana) y tarda unos segundos más. La base de datos (`~/.statspro/estadisticas.db`, en la carpeta de tu usuario; ver la sección 5) también se crea sola, con
  todas sus tablas. No hay nada que preparar antes.
- **Desde WSL:** hace falta WSLg (el soporte gráfico de WSL en Windows 11). Si la ventana no aparece, abrí la app desde Windows, con su propio entorno (ver la sección 9).

**Como comando instalado (opcional):** para abrirla desde cualquier carpeta, instalala en modo editable desde la raíz del repo:

```bash
uv tool install --editable .     # deja disponible el comando "statspro"
statspro                         # abre la aplicación
uv tool uninstall statspro-basketball   # para quitarlo
```

Al ser editable, usa el código de esta carpeta y la **misma** base que `uv run` (`~/.statspro/estadisticas.db`). Si usás la carpeta desde Windows y WSL, instalalo en uno solo de los dos.

**Sin Python ni el repo:** cada versión publicada trae un instalador de Windows, un `.zip` portable y un `.deb` de Linux (sección 11).

---

## 3. Qué se puede hacer hoy

1. **Crear una cuenta:** en "Crear cuenta", completar nombre, email y contraseña (mínimo 6 caracteres). Al registrarse, la sesión queda iniciada.
2. **Iniciar sesión:** con el email y la contraseña. Enter en el campo de la contraseña equivale a apretar el botón.
   - **"Recordarme":** si la marcás, al cerrar y volver a abrir la app entrás directo, con el mismo club activo. Si no la marcás, al cerrar la ventana la sesión se pierde.
3. **Crear clubes y elegir con cuál trabajar:** el destino "Mis clubes" del menú lateral. Ahí se crea un club **propio** (queda vinculado a tu usuario) y "Usar este club"
   lo deja como **club activo**, que se ve siempre en la barra superior ("StatsPro · Atenas"). Los rivales **no** se crean acá: se escriben al cargar el partido.
   Cada club se ve con un círculo con sus iniciales y un resumen ("2 categorías · 14 jugadores").
   Abajo, **"Clubes rivales"** lista los clubes que se crearon al cargar partidos: se pueden **renombrar** (si escribiste "Pezca") y **eliminar** si todavía no tienen partidos.
4. **Inicio:** con club activo muestra accesos rápidos (Cargar partido, Ver partidos, Jugadores, Listas), el último partido con su resultado y los líderes del club (promedio de puntos, rebotes y asistencias).
5. **Jugadores:** un buscador (filtra mientras escribís) y **"Del club" / "En todos los clubes"**. "Del club" es tu plantel, con íconos para editar, dar de baja (pide la fecha) y eliminar (solo si no tiene partidos ni listas). "En todos los clubes" muestra a todos los jugadores con su club actual, solo para consultar (los que quedaron **sin club** se pueden eliminar). "Nuevo jugador" abre un diálogo; si ya hay alguien con ese nombre avisa en qué club está y, si está **sin club**, ofrece sumarlo en vez de duplicarlo.
6. **Gestionar torneos (con club activo):** el destino "Torneos" del menú lateral da acceso a:
   - **Competencias:** crear competencias eligiendo sus categorías, cambiar las categorías de cada una desde su fila («Categorías»), filtrar por año o categoría y eliminar competencias sin uso.
   - **Categorías:** el catálogo común (U13, U15, Primera...): crear y eliminar las que no se usan.
   - **Inscripciones:** inscribir al club activo en una competencia y categoría habilitada (creando su lista de buena fe), filtrar por año o categoría y dar de baja inscripciones sin partidos cargados. Con **"Agregar todo el plantel a la lista"** (marcada de entrada) los jugadores del club quedan en la lista nueva sin pasar por "Listas".
   - **Listas de buena fe:** marcar varios jugadores del plantel (o «Seleccionar todos») y «Agregar seleccionados»; los que no entran se listan con el motivo. También quitar jugadores, vaciar la lista o dar de baja la inscripción.
7. **Cargar un partido:** "Partidos" → "Cargar partido". Un asistente de **tres pasos** (Datos del partido → Boxscore → Confirmar); "Siguiente" valida el paso y "Atrás" vuelve sin perder lo cargado:
   - **Paso 1, datos:** competencia y categoría (si el club tiene una sola inscripción ya viene elegida), fecha (con calendario), estadio, **rival** (elegirlo o escribirlo; si no existe se crea sin vincularlo a tu usuario) y si jugaste de local o de visitante.
   - **Paso 2, convocados:** sección plegable con las casillas de tu lista de buena fe en varias columnas; se marcan **hasta 12** y solo ellos van a la planilla. Con 12 o menos en la lista vienen todos marcados y la sección viene plegada (el título dice "Convocados: n/12"); con más, viene abierta para elegir.
   - **Tu equipo:** planilla tipo Excel con los convocados. PTS y la fila Equipo se calculan solos. **La fila de quien no jugó se deja vacía.**
   - **Rival:** «Solo totales o resultado» (una fila: si cargás los tiros, los puntos se calculan; si solo sabés el resultado, escribí los puntos) o «Boxscore por jugador» (si el rival ya tiene lista en ese torneo aparecen sus jugadores; si no, se escriben nombre y apellido y se dan de alta solos al guardar).
   - Puntos por cuarto opcionales y el marcador en vivo. Si algo está mal, el error se marca en la planilla (qué jugador y qué columna), abajo dice qué planilla revisar, y no se guarda nada.
   - **Paso 3, confirmar:** resumen con el marcador, los dos equipos y los cuartos. Con **menos de 5** jugadores tuyos o un **partido repetido** (mismo día, torneo y rival) se ve un aviso ahí mismo; "Guardar partido" guarda. **No se guarda un empate** ni más de 12 jugadores por equipo.
   - El rival escrito que no existe se crea **junto con el partido**: si el partido no se guarda, el club tampoco queda.
8. **Ver partidos:** "Partidos" lista los partidos del club con la categoría, el resultado y un cuadradito **G/P**; el filtro de categoría ofrece todas las del catálogo. **"Ver"** abre el partido en su propia pantalla (`/partidos/ver/{id}`): marcador grande, puntos por cuarto (si se cargaron), totales por equipo y un boxscore por equipo, con **"Editar partido"** (abre la carga llena con lo guardado; "Guardar cambios" lo reemplaza) y **"Eliminar partido"** (pide confirmación).
9. **Guía de uso:** el botón **"Guía"** abajo del menú lateral (o "¿Cómo se usa?" en el login) abre un manual corto para el entrenador. El texto está en `src/assets/guia.md`.
10. **Cerrar sesión:** el botón "Cerrar sesión" de la barra superior vuelve al login y borra la sesión recordada.

Qué hace cada caso de uso por dentro: [docs/info_modulo/03-casos-de-uso.md](docs/info_modulo/03-casos-de-uso.md).

---

## 4. Errores

| Qué ves | Qué significa | Qué hacer |
| --- | --- | --- |
| Un mensaje en rojo debajo del formulario (ej. `El email 'x' ya esta registrado`) | Un dato no cumple una regla del negocio | Corregir el dato y volver a intentar |
| `Ya existe un club llamado '...'` | El nombre de club ya está usado en esta base (sin distinguir mayúsculas), aunque sea de otro usuario | Elegir otro nombre (por ejemplo, agregando la ciudad) |
| `Email o contraseña incorrectos` | El email no existe o la contraseña no coincide (el mensaje es el mismo a propósito, para no revelar qué emails tienen cuenta) | Revisar los datos |
| `Ocurrió un error inesperado. El detalle quedó en logs/app.log.` | Un bug del programa, no un error de uso | Reportarlo junto con el archivo `logs/app.log`, que tiene el traceback completo |

La aplicación no se cierra por un error: después de cualquiera de estos mensajes se puede seguir usando.

---

## 5. La base de datos y los logs

| Qué | Dónde |
| --- | --- |
| Base de datos (SQLite) | `~/.statspro/estadisticas.db`, en la carpeta de tu usuario del sistema operativo (en Windows, `C:\Users\<usuario>\.statspro\`) |
| Logs | `~/.statspro/logs/app.log` (rota a los 10 MB, conserva 5 archivos). Una línea JSON por evento (ver abajo) |
| Sesión recordada ("Recordarme") | `~/.statspro/session.json`, en la carpeta de tu usuario del sistema operativo (en Windows, `C:\Users\<usuario>\.statspro\`). Guarda id de usuario, email y club activo; nunca la contraseña |
| Rutas y scripts SQL | `src/config/rutas.py` y `src/infraestructura/persistencia/sql/` |

Todo lo que la app escribe vive en `~/.statspro/`, también cuando se trabaja desde el repo (US-109): instalada, la app no puede escribir en su
propia carpeta, y así una reinstalación no pisa los datos. Windows y WSL tienen carpetas de usuario distintas: cada uno tiene **su propia** base.

### Leer los logs (US-110)

Cada línea de `app.log` es un JSON:

```json
{"ts": "2026-11-27T23:10:04.512+00:00", "nivel": "INFO", "logger": "infraestructura.ui.flet.errores",
 "mensaje": "Fin de clubes.crear: ok", "correlation_id": "b92b...", "accion": "clubes.crear",
 "evento": "accion_fin", "pantalla": "clubes", "resultado": "ok", "duracion_ms": 3.1}
```

- **`correlation_id`**: el mismo en todo lo que pasó por un clic (pantalla, caso de uso, repositorio). Las acciones especiales son
  `arranque` (esquema y sesión recordada) y `navegar` (cada cambio de pantalla).
- **`evento`**: `accion_inicio` / `accion_fin` (con `resultado` `ok`, `error_dominio` o `error`, y `duracion_ms`), `error_dominio`
  (WARNING), `error_inesperado` (ERROR, con `exc`), `login_ok`, `login_fallido`, `logout`, `set_active_club`,
  `partido_transaccion_inicio` / `partido_transaccion_fin`, y altas/ediciones/bajas (`club_creado`, `jugador_actualizado`...).
- Contraseñas, hashes, tokens y **emails** salen como `***`.

| Variable | Valores | Default | Para qué |
| --- | --- | --- | --- |
| `STATSPRO_LOG_SINK` | `archivo`, `consola` | `archivo` | `consola` escribe en la terminal (stderr) en vez del archivo: para mirar en vivo mientras se desarrolla |
| `STATSPRO_LOG_NIVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` | `DEBUG` suma los INSERT de los repositorios |

Un valor desconocido usa el default (no impide abrir la app). Ejemplos:

```bash
STATSPRO_LOG_SINK=consola STATSPRO_LOG_NIVEL=DEBUG uv run python src/main.py   # bash / WSL
jq -c 'select(.nivel=="ERROR")' ~/.statspro/logs/app.log                       # solo errores
jq -c 'select(.correlation_id=="b92b...")' ~/.statspro/logs/app.log            # un clic completo
```

```powershell
$env:STATSPRO_LOG_SINK="consola"; uv run python src/main.py
Get-Content ~/.statspro/logs/app.log | ConvertFrom-Json | Where-Object nivel -eq "ERROR"
Get-Content ~/.statspro/logs/app.log | ConvertFrom-Json | Where-Object accion -eq "carga_partido.guardar" | Format-Table ts, evento, mensaje
```

Para reportar un bug: buscar la línea `error_inesperado`, copiar su `correlation_id` y adjuntar todas las líneas con ese id.

### Aviso de versión nueva

Al abrir, la app pregunta a GitHub (`api.github.com`) si salió una versión estable más nueva y, si hay, muestra un aviso arriba con
**Descargar** (abre la página del release en el navegador), **Omitir esta versión** y **Ahora no**. No descarga ni instala nada sola.

- Consulta **una vez por día** como máximo, en segundo plano y con 3 s de timeout: sin internet la app abre igual y no muestra nada.
- Los _pre-release_ (`-rc`) nunca avisan.
- El estado (último día consultado y versión omitida) está en `~/.statspro/aviso_version.json`. Borrarlo vuelve a consultar al
  próximo arranque.
- **Privacidad:** el pedido no lleva ningún dato del usuario, pero GitHub ve la IP (lo mismo que al abrir la página del repo).
  Para desactivarlo: `STATSPRO_SIN_AVISO_VERSION=1` (PowerShell: `$env:STATSPRO_SIN_AVISO_VERSION="1"`). Cualquier otro valor lo
  deja activo. En el log queda `Aviso de version nueva desactivado`.

- **Si tenías una base de antes (en la raíz del repo, hasta la US-109):** con la app cerrada, movela una sola vez a la carpeta nueva. Si no, la
  app arranca con una base vacía (la vieja sigue ahí, no se borra nada).

  ```bash
  mkdir -p ~/.statspro && mv estadisticas.db ~/.statspro/      # bash (Linux, WSL o Git Bash)
  ```

  ```powershell
  New-Item -ItemType Directory -Force "$HOME\.statspro" | Out-Null; Move-Item estadisticas.db "$HOME\.statspro\"   # PowerShell
  ```

  La carpeta `logs/` de la raíz ya no se usa: se puede borrar.
- **Cada arranque es seguro para los datos:** la app ejecuta el esquema cada vez que se abre, pero `schema.sql` solo crea lo que falta (`CREATE TABLE IF NOT EXISTS`), nunca borra.
- **Hacer un backup:** copiar el archivo `estadisticas.db` con la aplicación cerrada.
- **Empezar de cero:** borrar `estadisticas.db`. Se vuelve a crear vacía la próxima vez que se abre la app. **Se pierden todos los datos.**
- **Olvidar la sesión recordada a mano:** borrar `~/.statspro/session.json` (o "Cerrar sesión" desde la app). Si el archivo se rompe o queda con un usuario que ya no
  existe en la base, la app lo ignora y pide login.
- **Mirar el contenido:** abrir `estadisticas.db` con cualquier visor de SQLite (por ejemplo [DB Browser for SQLite](https://sqlitebrowser.org/)).

**Datos de ejemplo:** si querés datos ya cargados para probar (2 clubes, 10 jugadores, 1 competencia, 2 partidos, 1 categoría), se puede cargar el *seed*. Los clubes del seed **no están vinculados a ningún usuario**: no aparecen en "Mis clubes" y no se puede crear otro con el mismo nombre.
Hacelo **solo sobre una base vacía**
(sin `estadisticas.db` o después de borrarla, ver arriba):

```bash
uv run python -c "import config.rutas as r; from infraestructura.persistencia.database_manager import SQLiteManager; m = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL, r.SEED_SQL); m.connect(); m.inicializar_schema(); m.cargar_seed()"
```

---

## 6. Tests, calidad de código y seguridad

Todo se ejecuta con `uv run` (o con el atajo `make` que se indica). Detalle de cómo escribir tests en [docs/info_modulo/09-testing.md](docs/info_modulo/09-testing.md).

```bash
uv run pytest                                   # toda la suite
uv run pytest tests/unit                        # solo los unitarios (no usan base de datos, son muy rápidos)
uv run pytest -k "vincular"                     # solo los tests cuyo nombre contiene "vincular"
uv run pytest -v --cov=src --cov-report=html    # con cobertura; abrir reportes_cobertura/html/index.html   (make run_test)

uv run ruff check .                             # estilo, imports y errores comunes (reglas: pyproject.toml) (make run_linter_ruf)
uv run ruff format --check .                    # avisa si algún archivo no está formateado, sin tocarlo     (make run_linter_ruf)
uv run ruff format .                            # formatea el código                                         (make corregir_linter)
uv run actionlint                               # revisa los workflows de .github/workflows/                 (make run_linter_ruf)
uv run mypy src/ --strict --explicit-package-bases   # revisión de tipos                                     (make static_check)

# Benchmarks de consultas (tests/benchmarks/): la suite normal los saltea; se corren aparte (guía: docs/info_modulo/14-benchmarks.md)
uv run pytest tests/benchmarks -m benchmark --benchmark-only
uv run pytest tests/benchmarks -m benchmark --benchmark-only -k partido   # solo los de un repositorio

# Vulnerabilidades conocidas en las dependencias: ver el comando de la sección 8
```

Estos mismos chequeos se ejecutan automáticamente en GitHub (`.github/workflows/MainAction.yml`) en cada Pull Request y en cada `push` a `main` o `develop`: lint, tipos, tests en Linux, Windows y Docker,
auditoría de dependencias (`pip-audit`) y revisión de los propios workflows (`actionlint`). Los tests de Linux se repiten con **Python 3.12, 3.13 y 3.14**; Windows y Docker corren una sola vez (3.13) y mypy una sola vez (contra la 3.12). El lint incluye `ruff format --check`, y los jobs de tests prueban antes que la app importe sin errores (`python -c "import main"`, sin abrir ninguna ventana).
Un job final, `ci-ok`, queda en rojo si cualquiera de los anteriores falló: es el que se marca como obligatorio en GitHub para que un PR con el CI en rojo no se pueda mergear.
Aparte, `.github/workflows/titulo-pr.yml` exige que el **título del PR** siga Conventional Commits (`feat: ...`, `fix(gui): ...`,
`docs: ...`): al hacer _squash_, ese título es el commit que llega a la rama y de ahí sale el changelog. Si falla, se corrige el
título del PR (el chequeo se vuelve a correr solo); no hace falta otro push.
En Linux la cobertura mínima es **85 %** y el reporte HTML queda para descargar (pestaña _Actions_ → la corrida → sección _Artifacts_). Además, [Dependabot](.github/dependabot.yml) abre PR cuando hay versiones nuevas de las dependencias.

### Qué deja el CI en cada PR

- **Un comentario de resumen** (job `resumen-pr`, armado por `.github/scripts/resumen_pr.py`), que se **edita** en cada push en
  vez de sumar comentarios: semáforo de cada job, cobertura total con el **delta contra la rama base**, cobertura de las **líneas
  cambiadas** (diff-cover), tests fallidos y los más lentos, errores de ruff y mypy, la **HU vinculada** y un aviso si cambió
  `src/` sin cambiar `docs/`. En las PRs de Dependabot queda solo en la página de la corrida (su token no puede comentar).
- **Un segundo comentario con los benchmarks de consultas**, que también se edita en cada push: tiempos en dos escalas de
  datos, crecimiento, comparación con la rama base y plan de ejecución de cada consulta. Cómo leerlo y primeros resultados:
  [docs/info_modulo/14-benchmarks.md](docs/info_modulo/14-benchmarks.md).
- **Anotaciones en _Files changed_:** cada error de ruff y de mypy aparece sobre la línea del diff.
- **Dependency review:** falla si la PR agrega una dependencia con una vulnerabilidad conocida (moderada o peor).
- **Labels automáticos** (`.github/workflows/pr-meta.yml`): por capa según las carpetas que toca (`.github/labeler.yml`), y la
  épica, la US y el hito (milestone) de la HU. La HU se busca por `Closes #N` en el cuerpo o, si no está, por el número de la
  rama (`feature/us107-...` → la issue `[US-107] ...`).

El delta se calcula contra la última corrida de un push a la rama base: por eso `MainAction` también corre en los push a las
ramas de integración (`feature/epica*`, `feature/hito*`). Si la base nunca corrió (o sus artifacts vencieron, a los 90 días), el
resumen lo dice y muestra la cobertura sin delta.

### Reglas del repositorio en GitHub

Configuradas a mano en GitHub (Settings), no en un archivo del repo (US-109):

- **Ruleset `main y develop`:** no se puede hacer push directo ni force push, ni borrar las ramas; todo entra por PR. Para mergear,
  `ci-ok` y `titulo-pr` tienen que estar en verde. Métodos de merge: _squash_ (PR de trabajo, el mensaje es el título del PR) y
  _merge commit_ (PR de promoción `develop → main`); _rebase_ está desactivado.
- **CodeQL** (_default setup_, Python y GitHub Actions): analiza cada PR, cada push a `main` y una vez por semana. Los hallazgos están
  en _Security → Code scanning_.

### Hooks de pre-commit (opcional)

Con [pre-commit](https://pre-commit.com/), ruff revisa y formatea los archivos **al hacer `git commit`**. Los hooks de ruff y de actionlint (este último revisa los workflows de GitHub Actions) se ejecutan con `uv run`, o sea que usan la **misma versión que fija `pyproject.toml`** (y que usa el CI): hace falta tener `uv` instalado (sección 1).

```bash
uv tool install pre-commit     # una sola vez
pre-commit install             # activa los hooks en este repositorio
make pre_commit                # (opcional) corre los hooks sobre todo el proyecto: puede modificar archivos, revisá el git diff
```

---

## 7. Docker

Corre los tests en un contenedor limpio, igual que en el CI (no depende de nada de tu máquina). Explicación completa en [docs/info_modulo/10-docker-para-tests.md](docs/info_modulo/10-docker-para-tests.md).

```bash
make docker_test
# equivale a:
docker build -f Dockerfile.test -t app-estadisticas-tests .
docker run --rm app-estadisticas-tests
```

La imagen usa Python 3.12 por defecto. Para probar con otra versión (el CI usa la 3.13):

```bash
make docker_test PYTHON_VERSION=3.13
# equivale a:
docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.13 -t app-estadisticas-tests .
```

---

## 8. Manejo de dependencias

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

## 9. Problemas frecuentes

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `uv: command not found` | uv no está instalado o la terminal no se reinició | Instalar uv (sección 1) y abrir una terminal nueva |
| `ModuleNotFoundError: flet` (o `pandas`, `pytest`…) | Se está usando otro Python, no el entorno del proyecto | Ejecutar siempre con `uv run ...`, y `uv sync` si falta instalar |
| `AttributeError: module 'config.rutas' has no attribute 'LOG_DIR'` | Hay un paquete `config` de terceros instalado en tu Python global que tapa al del proyecto | Usar `uv run ...` (el entorno del proyecto no lo tiene) |
| `error: failed to remove file ... .venv\lib64` (o el entorno deja de andar al alternar entre Windows y WSL) | La carpeta del proyecto la usan Windows **y** WSL, y cada sistema necesita su **propio** entorno virtual: uno intenta recrear el `.venv` del otro y lo deja a medias | Que uno de los dos use un entorno fuera del proyecto: en WSL, `export UV_PROJECT_ENVIRONMENT=~/.venvs/app_estadisticas` (por ejemplo en `~/.bashrc`) y después `uv sync`. Para reparar un `.venv` roto, borrarlo **desde el mismo sistema que lo creó** y correr `uv sync` |
| La primera vez la ventana tarda en aparecer | Flet está descargando su cliente de escritorio | Esperar: pasa una sola vez |
| La ventana no aparece desde WSL | WSL sin soporte gráfico (WSLg) | Abrir la app desde Windows |
| `Installing flet-desktop ...` al abrir la app | El entorno no tiene `flet-desktop` (por ejemplo, un `.venv` viejo) | `uv sync`: la dependencia es `flet[desktop]` y queda fijada en `uv.lock` |
| `Ocurrió un error inesperado` en un formulario | Un bug: el detalle está en `logs/app.log` | Reportarlo con el log |
| Los acentos o la `ñ` se ven raros en los logs de la consola de Windows | Codificación de la consola | Ejecutar con `PYTHONUTF8=1` (o `chcp 65001` en cmd) |
| Al abrir la app entra directo con otro usuario o sin pedir login | Quedó una sesión recordada ("Recordarme") | "Cerrar sesión", o borrar `~/.statspro/session.json` |
| Al abrir la app pide login aunque marqué "Recordarme" | El archivo de sesión se borró, se dañó o su usuario ya no está en la base (por ejemplo, se borró `estadisticas.db`) | Volver a iniciar sesión; el detalle queda como warning en `~/.statspro/logs/app.log` |
| `database is locked` | Otro programa (ej. un visor de SQLite) tiene la base abierta para escribir | Cerrar el otro programa y reintentar |

---

## 10. Qué todavía no se puede hacer

El estado del proyecto por historia de usuario está en el [PRD](docs/plan_desarrollo_detallado.md). Hoy, desde la aplicación:

- **La sesión recordada no vence** (v0.1): con "Recordarme", cualquiera que use tu cuenta del sistema operativo abre la app sin contraseña. La expiración llega con la US-403.
- **No se pueden cargar partidos entre dos clubes ajenos** (decidido en la US-114): van a entrar por la importación de planillas (US-201) y la carga masiva (US-207).
- **No se puede renombrar ni borrar un club propio** desde la app (los rivales sí, en "Mis clubes → Clubes rivales").

---

## 11. Sacar una versión

Una versión se publica **con un tag** `vX.Y.Z` sobre `main`: el workflow [`release.yml`](.github/workflows/release.yml) hace el resto solo
(US-109). Por qué el proceso es así (ramas, versionado, hotfix) está en la sección 15 del [PRD](docs/plan_desarrollo_detallado.md).

### Qué publica cada versión

En la pestaña _Releases_ de GitHub, tres archivos (más el código fuente, que agrega GitHub):

| Archivo | Para qué |
| --- | --- |
| `StatsPro-X.Y.Z-windows-x64-instalador.exe` | Instalador de Windows (Inno Setup): menú Inicio, acceso directo opcional, desinstalador |
| `StatsPro-X.Y.Z-windows-x64-portable.zip` | La misma app sin instalar: se descomprime y se abre `StatsPro\StatsPro.exe` |
| `statspro_X.Y.Z_amd64.deb` | Paquete de Linux (Ubuntu/Debian): se instala en `/opt/statspro` y queda el comando `statspro` |

Ninguno necesita Python. Los tres guardan los datos en `~/.statspro/` (sección 5), y desinstalar **no** los borra.

- **Windows:** el instalador no está firmado (la firma es de la US-404), así que la primera vez Windows muestra "Windows protegió su PC":
  _Más información → Ejecutar de todas formas_. Una versión nueva se instala encima de la anterior. Se desinstala desde
  _Configuración → Aplicaciones_.
- **Linux:** `sudo apt install ./statspro_X.Y.Z_amd64.deb` (con `./`, para que `apt` resuelva las dependencias). Se abre con `statspro` o
  desde el menú. Se desinstala con `sudo apt remove statspro`.

### Qué estrategia de merge va en cada PR

| PR | Cómo se mergea | Por qué |
| --- | --- | --- |
| `feature/usXXX` → su épica o `develop` | **Squash** | Junta los commits de trabajo en uno; el título del PR es el mensaje, y de ahí sale una línea del changelog |
| Promoción (épica → hito → `develop` → `main`) | **Merge commit** | Conserva un commit por historia: con squash, a `main` llegaría un solo commit por hito |
| `hotfix/...` → `main` | **Squash** | Una corrección, un commit |

El título del PR tiene que seguir Conventional Commits (lo controla `titulo-pr`, sección 6). _Rebase_ está desactivado.

### Paso a paso

1. **PR `develop → main`** con dos cambios más:
   - `version = "X.Y.Z"` en `pyproject.toml` y `VERSION = "X.Y.Z"` en `src/config/version.py` (la que usa la app para saber
     si hay una versión nueva; la app empaquetada no puede leer `pyproject.toml`);
   - el changelog regenerado: `make changelog VERSION=X.Y.Z` (sin `make`: `uvx git-cliff@2.14.2 --tag vX.Y.Z -o CHANGELOG.md`).

   Leé la sección nueva del `CHANGELOG.md`. El archivo **no se edita a mano**: se regenera entero en cada versión y se perdería el
   cambio. Si una línea sobra (por ejemplo, un commit con el tipo equivocado), se saca agregando el hash del commit a un archivo
   `.cliffignore` en la raíz y se vuelve a generar. El CI tiene que pasar entero; se mergea con **merge commit**.
2. **Probar con un pre-release:** sobre `main` actualizado, `git tag vX.Y.Z-rc.1 && git push origin vX.Y.Z-rc.1`. En unos 30 minutos
   aparece en _Releases_ un _pre-release_ con los tres archivos. Probarlos en una máquina sin Python (por ejemplo Windows Sandbox): la
   app abre, se registra un usuario y se crea un club. Si algo falla, se corrige con un PR y se prueba con `-rc.2`.
3. **Publicar:** `git checkout main && git pull`, `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. **Verificar** en _Releases_: la versión, sus notas (la sección del changelog) y los tres archivos.
5. **Limpiar los pre-release:** borrarlos en _Releases_ (ícono de basura) y borrar sus tags:
   `git push --delete origin vX.Y.Z-rc.1 && git tag -d vX.Y.Z-rc.1`.

### Si el workflow falla

`release.yml` corre en orden y **no publica nada** hasta el último job (`publicar`): si falla antes, no hay nada que deshacer.

| Falla en | Causa típica | Qué hacer |
| --- | --- | --- |
| `version` | El tag no coincide con `version` de `pyproject.toml` o con `VERSION` de `src/config/version.py` | Borrar el tag (`git push --delete origin vX.Y.Z && git tag -d vX.Y.Z`), corregir con un PR y volver a taggear |
| `tests-linux` / `tests-windows` | Un test que falla con Python 3.14 (el que va adentro del paquete) | Corregir con un PR; nuevo `-rc` |
| `build-windows` / `build-linux` | `flet build`, Inno Setup o el `.deb` | Leer el log del paso que falló; corregir con un PR; nuevo `-rc` |
| `publicar` | Falta la sección `## [X.Y.Z]` en `CHANGELOG.md` | No se corrió `make changelog`: PR con el changelog, borrar el tag y volver a taggear |

Un tag que **ya publicó** una versión no se reusa: si hay que corregirla, sale la siguiente (`vX.Y.Z+1`, ver "Hotfix" en el PRD).
