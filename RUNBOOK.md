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

Al ser editable, usa el código de esta carpeta y la **misma** base que `uv run` (`~/.statspro/estadisticas.db`). Si usás la carpeta desde Windows y WSL, instalalo en uno solo de los dos. El empaquetado
real (un instalable para otra máquina) es la US-404.

---

## 3. Qué se puede hacer hoy

1. **Crear una cuenta:** en "Crear cuenta", completar nombre, email y contraseña (mínimo 6 caracteres). Al registrarse, la sesión queda iniciada.
2. **Iniciar sesión:** con el email y la contraseña. Enter en el campo de la contraseña equivale a apretar el botón.
   - **"Recordarme":** si la marcás, al cerrar y volver a abrir la app entrás directo, con el mismo club activo. Si no la marcás, al cerrar la ventana la sesión se pierde.
3. **Crear clubes y elegir con cuál trabajar:** el botón "Clubes" de la barra superior abre "Mis clubes". Ahí se crea un club (queda vinculado a tu usuario) y "Usar este club"
   lo deja como **club activo**, que se ve siempre en la barra superior ("StatsPro · Atenas").
4. **Cerrar sesión:** el botón "Cerrar sesión" de la barra superior vuelve al login y borra la sesión recordada.

Las pantallas para cargar jugadores, competencias, listas de buena fe y partidos llegan con las US-107 y US-108; los casos de uso ya existen (ver
[docs/info_modulo/03-casos-de-uso.md](docs/info_modulo/03-casos-de-uso.md)).

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
| Logs | `~/.statspro/logs/app.log` (rota a los 10 MB, conserva 5 archivos) |
| Sesión recordada ("Recordarme") | `~/.statspro/session.json`, en la carpeta de tu usuario del sistema operativo (en Windows, `C:\Users\<usuario>\.statspro\`). Guarda id de usuario, email y club activo; nunca la contraseña |
| Rutas y scripts SQL | `src/config/rutas.py` y `src/infraestructura/persistencia/sql/` |

Todo lo que la app escribe vive en `~/.statspro/`, también cuando se trabaja desde el repo (US-109): instalada, la app no puede escribir en su
propia carpeta, y así una reinstalación no pisa los datos. Windows y WSL tienen carpetas de usuario distintas: cada uno tiene **su propia** base.

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

# Vulnerabilidades conocidas en las dependencias: ver el comando de la sección 8
```

Estos mismos chequeos se ejecutan automáticamente en GitHub (`.github/workflows/MainAction.yml`) en cada Pull Request y en cada `push` a `main` o `develop`: lint, tipos, tests en Linux, Windows y Docker,
auditoría de dependencias (`pip-audit`) y revisión de los propios workflows (`actionlint`). Los tests de Linux se repiten con **Python 3.12, 3.13 y 3.14**; Windows y Docker corren una sola vez (3.13) y mypy una sola vez (contra la 3.12). El lint incluye `ruff format --check`, y los jobs de tests prueban antes que la app importe sin errores (`python -c "import main"`, sin abrir ninguna ventana).
Un job final, `ci-ok`, queda en rojo si cualquiera de los anteriores falló: es el que se marca como obligatorio en GitHub para que un PR con el CI en rojo no se pueda mergear.
Aparte, `.github/workflows/titulo-pr.yml` exige que el **título del PR** siga Conventional Commits (`feat: ...`, `fix(gui): ...`,
`docs: ...`): al hacer _squash_, ese título es el commit que llega a la rama y de ahí sale el changelog. Si falla, se corrige el
título del PR (el chequeo se vuelve a correr solo); no hace falta otro push.
En Linux la cobertura mínima es **85 %** y el reporte HTML queda para descargar (pestaña _Actions_ → la corrida → sección _Artifacts_). Además, [Dependabot](.github/dependabot.yml) abre PR cuando hay versiones nuevas de las dependencias.

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

- **No hay pantallas de gestión** (US-107): jugadores, competencias, categorías e inscripciones existen en los casos de uso, pero todavía no en la interfaz. Clubes sí.
- **La sesión recordada no vence** (v0.1): con "Recordarme", cualquiera que use tu cuenta del sistema operativo abre la app sin contraseña. La expiración llega con la US-403.
- **No se pueden cargar partidos ni estadísticas** (US-108).
- **No se puede editar ni borrar** clubes, competencias ni jugadores (el PRD solo pide crear, listar y vincular): un dato mal cargado hoy solo se corrige en la base.
