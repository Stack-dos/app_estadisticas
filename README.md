# StatsPro Basketball — estadísticas de básquet

Aplicación **local (offline-first)** para que entrenadores de básquet carguen las estadísticas de sus partidos y obtengan estadísticas avanzadas de jugadores y equipos.
Está pensada para el básquet de Córdoba: clubes, competencias, categorías, listas de buena fe y boxscores.

## Estado actual

La aplicación es de **escritorio, con ventanas** (Flet). Desde la US-105 se puede registrar un entrenador, iniciar sesión y cerrarla. La carga de clubes, jugadores, competencias, listas de buena fe y partidos ya está implementada en los casos de uso y llega a la interfaz con las pantallas de gestión (US-106 a US-108). La línea de comandos (CLI) que tenía el proyecto hasta la US-104 se retiró. El plan completo está en el [PRD](docs/plan_desarrollo_detallado.md).

## Descargar

Cada versión publicada está en [Releases](https://github.com/nicopinera/app_estadisticas/releases): instalador `.exe` y `.zip`
portable para Windows, y `.deb` para Linux. No hace falta Python. Cómo instalarlos: sección 11 del [RUNBOOK](RUNBOOK.md).

## Inicio rápido

Necesitás [uv](https://docs.astral.sh/uv/) (instala Python y las dependencias; no hace falta `pip`).

```bash
git clone https://github.com/nicopinera/app_estadisticas.git
cd app_estadisticas
uv sync                          # instala todo
uv run python src/main.py        # abre la aplicación (crea la base de datos sola)
uv run pytest                    # corre los tests
```

La primera vez que se abre, Flet descarga su cliente de escritorio y tarda un poco más. Cómo operar el proyecto (base de datos, logs, tests, Docker, dependencias) está en el **[RUNBOOK](RUNBOOK.md)**.

## Tecnologías

- **Python ≥ 3.12**, con dependencias y entorno manejados por **uv** (`pyproject.toml` + `uv.lock`, versiones fijas).
- **Flet** para la interfaz gráfica de escritorio.
- **SQLite** para la persistencia local.
- Calidad: **pytest** (+ cobertura), **ruff** (estilo), **mypy** (tipos), **pip-audit** (seguridad de dependencias), **Docker** y **GitHub Actions** (CI).

## Cómo está organizado el código

Sigue una **Arquitectura Limpia / Hexagonal**: la lógica de negocio no depende de la base de datos ni de la interfaz.

```text
src/
├── main.py             Punto de entrada: abre la GUI
├── utils.py            Helpers puros compartidos
├── dominio/            Entidades, contratos de repositorios y excepciones de negocio
├── aplicacion/         Casos de uso, DTOs y la sesión en memoria
└── infraestructura/    SQLite, logger, seguridad y la GUI (ui/flet: composition root y pantallas)
tests/
├── unit/               Tests sin base de datos (rápidos), incluidas las pantallas sin ventana
└── integration/        Tests con SQLite real y los casos de uso de punta a punta
docs/                   Documentación técnica, plan de desarrollo (PRD) e informes de trabajo
```

## Documentación

| Qué buscás                                            | Dónde                                                                      |
| ----------------------------------------------------- | -------------------------------------------------------------------------- |
| Cómo operar el proyecto (base, logs, tests, Docker)   | [RUNBOOK.md](RUNBOOK.md)                                                   |
| Plan de desarrollo, historias de usuario y decisiones | [docs/plan_desarrollo_detallado.md](docs/plan_desarrollo_detallado.md)     |
| Qué hace cada caso de uso, paso a paso                | [docs/info_modulo/03-casos-de-uso.md](docs/info_modulo/03-casos-de-uso.md) |
| Arquitectura, patrones, testing, Docker               | [docs/info_modulo/](docs/info_modulo/) (guías numeradas)                   |
| La GUI: Flet, eventos, rutas y pantallas              | [13-gui-flet-y-eventos.md](docs/info_modulo/13-gui-flet-y-eventos.md)      |
| Informes de trabajo y decisiones tomadas              | [docs/context_ia/](docs/context_ia/)                                       |
| Ideas de mejora y revisión del CI                     | [docs/ideas-aprendizaje.md](docs/ideas-aprendizaje.md)                     |

## Contribuir

- Los commits siguen el formato `TIPO: descripción corta` (ver [docs/info_modulo/02-reglas.md](docs/info_modulo/02-reglas.md)). El **título
  del PR** también: al mergear con _squash_ es el commit que queda, y de ahí sale el [CHANGELOG](CHANGELOG.md).
- Antes de abrir un Pull Request: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy src/ --strict --explicit-package-bases` deben pasar. El CI los corre por vos en cada PR.
