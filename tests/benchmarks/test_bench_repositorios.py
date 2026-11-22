"""Benchmarks de ejemplo: cuanto tarda una consulta de repositorio sobre SQLite en memoria (con seed.sql).

No corren con la suite normal (pyproject.toml: addopts = -m "not benchmark"). Para correrlos:
    uv run pytest tests/benchmarks -m benchmark --benchmark-only

El CI los corre en cada PR y compara la media contra la rama base (solo informativo: no hace fallar el CI).
"""

import pytest

from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio

pytestmark = pytest.mark.benchmark

# TODO(nico): elegir que medir. Candidatos: las consultas que crecen con los datos (listados por club,
# vistas de estadisticas) y, desde la US-203, el motor de Pandas. Este es solo un ejemplo de la forma.


def test_bench_buscar_jugadores_por_club(benchmark, db_conexion):
    repo = SqliteJugadorRepositorio(db_conexion)

    jugadores = benchmark(repo.buscar_por_club, 1)

    assert jugadores is not None
