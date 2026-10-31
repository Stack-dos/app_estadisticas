# StatsPro Basketball — estadísticas de básquet

Aplicación **local (offline-first)** para que entrenadores de básquet carguen las estadísticas de sus partidos y obtengan estadísticas avanzadas de jugadores y equipos.
Está pensada para el básquet de Córdoba: clubes, competencias, categorías, listas de buena fe y boxscores.

## Estado actual

Hoy la aplicación se usa desde la **línea de comandos (CLI)**. **La CLI se retira en la US-105**, que la reemplaza por una aplicación de escritorio con ventanas (Flet); hasta entonces, los comandos de abajo siguen funcionando. El plan completo está en el [PRD](docs/plan_desarrollo_detallado.md).

## Qué se puede hacer hoy

```text
stats club add --nombre "Atenas"
stats jugador add --nombre Manu --apellido Ginobili --dni 20111222 --anio 1977
stats jugador link --id-jugador 1 --id-club 1 --fecha-desde 2026-01-05
stats jugador unlink --id-jugador 1 --fecha-hasta 2026-06-30   # da de baja del club (para poder cambiarlo)
stats jugador list --id-club 1
stats competencia add --nombre "Liga Provincial" --anio 2026 --tipo PROVINCIAL
stats competencia list
stats categoria add --nombre U21
stats categoria list
stats competencia inscribir --id-club 1 --id-categoria 1 --id-competencia 1 --fecha-presentacion 2026-03-01
stats inscripcion list --id-club 1
stats lista add --id-inscripcion 1 --id-jugador 1        # habilita al jugador en la lista de buena fe
stats lista remove --id-inscripcion 1 --id-jugador 1     # deshace la habilitación
stats lista list --id-inscripcion 1
stats partido list --id-club 1
```

La guía completa de cada comando, con ejemplos y errores posibles, está en el **[RUNBOOK](RUNBOOK.md)**.

## Inicio rápido

Necesitás [uv](https://docs.astral.sh/uv/) (instala Python y las dependencias; no hace falta `pip`).

```bash
git clone https://github.com/nicopinera/app_estadisticas.git
cd app_estadisticas
uv sync                                                       # instala todo
uv run python src/main.py club add --nombre "Atenas"          # primer comando (crea la base de datos sola)
uv run pytest                                                 # corre los tests
```

## Tecnologías

- **Python ≥ 3.11**, con dependencias y entorno manejados por **uv** (`pyproject.toml` + `uv.lock`, versiones fijas).
- **SQLite** para la persistencia local.
- **argparse** (CLI) y **tabulate** (tablas en consola).
- Calidad: **pytest** (+ cobertura), **ruff** (estilo), **mypy** (tipos), **pip-audit** (seguridad de dependencias), **Docker** y **GitHub Actions** (CI).

## Cómo está organizado el código

Sigue una **Arquitectura Limpia / Hexagonal**: la lógica de negocio no depende de la base de datos ni de la interfaz.

```text
src/
├── main.py             Punto de entrada de la CLI
├── utils.py            Helpers puros compartidos
├── dominio/            Entidades, contratos de repositorios y excepciones de negocio
├── aplicacion/         Casos de uso y DTOs
└── infraestructura/    SQLite, logger y CLI (comandos y tablas)
tests/
├── unit/               Tests sin base de datos (rápidos)
└── integration/        Tests con SQLite real y la CLI de punta a punta
docs/                   Documentación técnica, plan de desarrollo (PRD) e informes de trabajo
```

## Documentación

| Qué buscás                                            | Dónde                                                                      |
| ----------------------------------------------------- | -------------------------------------------------------------------------- |
| Cómo usar la CLI y operar el proyecto                 | [RUNBOOK.md](RUNBOOK.md)                                                   |
| Plan de desarrollo, historias de usuario y decisiones | [docs/plan_desarrollo_detallado.md](docs/plan_desarrollo_detallado.md)     |
| Qué hace cada caso de uso, paso a paso                | [docs/info_modulo/03-casos-de-uso.md](docs/info_modulo/03-casos-de-uso.md) |
| Arquitectura, patrones, testing, Docker               | [docs/info_modulo/](docs/info_modulo/) (guías numeradas)                   |
| Informes de trabajo y decisiones tomadas              | [docs/context_ia/](docs/context_ia/)                                       |
| Ideas de mejora y revisión del CI                     | [docs/ideas-aprendizaje.md](docs/ideas-aprendizaje.md)                     |

## Contribuir

- Los commits siguen el formato `TIPO: descripción corta` (ver [docs/info_modulo/02-reglas.md](docs/info_modulo/02-reglas.md)).
- Antes de abrir un Pull Request: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy src/ --strict --explicit-package-bases` deben pasar. El CI los corre por vos en cada PR.
