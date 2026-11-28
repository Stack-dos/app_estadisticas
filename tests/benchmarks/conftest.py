"""Fixture `datos`: la base de volumen de cada escala (ver ayudantes_bench.py)."""

import pytest
from ayudantes_bench import ESCALAS, Datos, construir_base


@pytest.fixture(scope="session", params=list(ESCALAS), ids=list(ESCALAS))
def datos(request: pytest.FixtureRequest) -> Datos:
    """La base de cada escala se arma una sola vez por corrida y la comparten todos los benchmarks de lectura."""
    base = construir_base(request.param)
    yield base
    base.conexion.close()
