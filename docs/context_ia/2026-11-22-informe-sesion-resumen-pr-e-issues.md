# Informe de sesión — Resumen de la PR en el CI, issues y Project (2026-11-22)

Rama: `feature/mejora-ci`. Amplía la US-109 (AC16 a AC19 del PRD).

## Issues y Project (GitHub, ya aplicado)

- Las issues usaban la numeración vieja (antes de las renumeraciones del 31/10 y del 08/11). Se regeneraron **desde el PRD**:
  24 reusadas (título, cuerpo, labels, milestone y estado corregidos) y 18 nuevas (US-105, 106, 111, 107, 112, 204, 205, 206,
  207, 303, 402, 403, 404, la tarea del DNI y las épicas H1-E3, H3-E2, H3-E3, H4-E2, H4-E3, H4-E4).
- Reasignaciones: #29 (CargarPartido) → US-108, reabierta; #41 → US-110; #42 → US-109; #31 → H2-E3 (pasó al milestone M2);
  #27 → US-301 Dashboards. La #30 (CLI con Command) se cerró como _not planned_. M0 se cerró (todas sus issues estaban cerradas).
- Las US-105, 106, 111 y 109 se marcaron **Hechas** en el PRD con sus PR (#48, #49, #50, #51); la US-107 queda en review (PR #52).
- Labels viejos borrados (`hito1`, `Hito 2..4`, `Epic`, `Task`, `Sub-Task`, `documentation`); los nuevos están en la sección 5 del PRD.
- Project de la organización **StatsPro – Roadmap** con Status, Prioridad y Esfuerzo cargados para las 42 issues.
- Los templates de `.github/ISSUE_TEMPLATE/` tenían conflictos de merge sin resolver commiteados: se resolvieron quedándose con
  la versión más completa, con los labels y títulos nuevos.

## CI

- `resumen-pr` (MainAction) + `.github/scripts/resumen_pr.py`: un comentario editable con semáforo, cobertura y delta,
  diff-cover, tests, ruff, mypy, benchmarks, HU y aviso de docs. Probado de punta a punta en local con los resultados reales.
- `dependency-review` (en `ci-ok`), anotaciones de ruff y mypy, `benchmark` (informativo).
- `pr-meta.yml` + `.github/labeler.yml` + `.github/scripts/vincular_hu.py`: labels por capa y de la HU.
- `pyproject.toml`: `diff-cover` y `pytest-benchmark` en el grupo dev; `-m "not benchmark"` en `addopts`.

## Pendiente

- Probarlo en una PR real (la de esta rama sirve): que aparezca el comentario, los labels y las anotaciones.
- Decidir qué índices agregar (o no) a partir del informe de benchmarks (§7.6 de la guía 14).
- Las vistas del Project (tablero, tabla por hito, roadmap) se crean desde la web: la API no permite crearlas.

## Ampliación: benchmarks de consultas

- El benchmark de ejemplo medía sobre `seed.sql` (11 inserts): no decía nada. Se reemplazó por 19 consultas (lecturas de los
  cinco repositorios, vistas y dos escrituras) sobre datos de volumen en dos escalas (`temporada` y `x10`), con el
  `EXPLAIN QUERY PLAN` de cada una capturado con `set_trace_callback`.
- El reporte va en un **segundo comentario** de la PR (pedido de Nico), con su propia marca; el principal muestra una línea.
- Hallazgos (detalle en `docs/info_modulo/14-benchmarks.md` §7): `SCAN partido` en los partidos de un club y `SCAN` de
  `jugadorPartido` en el boxscore de un partido (las dos crecen lineal con cada temporada). Índices candidatos listados en
  §7.6; **no** se agregaron: es una decisión de diseño del schema.
