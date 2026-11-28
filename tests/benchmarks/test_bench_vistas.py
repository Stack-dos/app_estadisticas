"""Benchmarks de las vistas de views.sql que todavía no usa ningún repositorio.

Son la base del motor estadístico (US-203): medirlas ahora deja una referencia para cuando se usen.
Se consultan con SQL directo, como lo haría un repositorio.
"""

import pytest
from ayudantes_bench import medir_lectura

pytestmark = pytest.mark.benchmark


def _consultar(datos, sql, *params):
    def consulta():
        return datos.conexion.execute(sql, params).fetchall()

    return consulta


@pytest.mark.benchmark(group="vistas")
def test_bench_vista_boxscore_de_un_partido(benchmark, datos):
    consulta = _consultar(datos, "SELECT * FROM v_boxscore_completo WHERE id_partido = ?", datos.ids["id_partido"])
    assert len(medir_lectura(benchmark, datos, consulta)) == 24  # 12 jugadores por equipo


@pytest.mark.benchmark(group="vistas")
def test_bench_vista_totales_temporada_completa(benchmark, datos):
    """Toda la vista: es lo que leería el motor de Pandas para calcular las métricas de todos los jugadores."""
    consulta = _consultar(datos, "SELECT * FROM v_jugador_totales_temporada")
    assert medir_lectura(benchmark, datos, consulta)


@pytest.mark.benchmark(group="vistas")
def test_bench_vista_totales_de_un_anio(benchmark, datos):
    consulta = _consultar(
        datos, "SELECT * FROM v_jugador_totales_temporada WHERE anio_competencia = ?", datos.ids["anio"]
    )
    assert medir_lectura(benchmark, datos, consulta)


@pytest.mark.benchmark(group="vistas")
def test_bench_vista_lista_de_una_inscripcion(benchmark, datos):
    consulta = _consultar(datos, "SELECT * FROM v_listas_detalle WHERE id_inscripcion = ?", datos.ids["id_inscripcion"])
    assert len(medir_lectura(benchmark, datos, consulta)) == 12  # EN_CANCHA
