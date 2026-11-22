"""Benchmarks de las consultas de lectura de los repositorios SQLite, en las dos escalas de `datos`.

Cada benchmark mide una consulta con los ids representativos de `datos.ids` y guarda su plan de ejecución.
El grupo (`group`) es el repositorio: así se agrupan en la tabla de pytest-benchmark y en el reporte de la PR.
"""

import pytest
from ayudantes_bench import medir_lectura

from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio
from infraestructura.repositorios.sqlite_partido_repositorio import SqlitePartidoRepositorio
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio

pytestmark = pytest.mark.benchmark


# ------------------------------------------------------------------ usuario


@pytest.mark.benchmark(group="usuario")
def test_bench_usuario_encontrar_por_mail(benchmark, datos):
    repo = SqliteUsuarioRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.encontrar_por_mail, datos.ids["email"]) is not None


# ------------------------------------------------------------------ club


@pytest.mark.benchmark(group="club")
def test_bench_club_buscar_por_id_usuario(benchmark, datos):
    repo = SqliteClubRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.buscar_por_id_usuario, datos.ids["id_usuario"])


@pytest.mark.benchmark(group="club")
def test_bench_club_buscar_por_nombre(benchmark, datos):
    repo = SqliteClubRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.buscar_por_nombre, datos.ids["nombre_club"])


# ------------------------------------------------------------------ jugador


@pytest.mark.benchmark(group="jugador")
def test_bench_jugador_buscar_por_club(benchmark, datos):
    repo = SqliteJugadorRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.buscar_por_club, datos.ids["id_club"])


@pytest.mark.benchmark(group="jugador")
def test_bench_jugador_club_activo(benchmark, datos):
    repo = SqliteJugadorRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.club_activo, datos.ids["id_jugador"]) is not None


@pytest.mark.benchmark(group="jugador")
def test_bench_jugador_historial_vinculos(benchmark, datos):
    repo = SqliteJugadorRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.historial_vinculos, datos.ids["id_jugador_con_historial"])


# ------------------------------------------------------------------ competencia


@pytest.mark.benchmark(group="competencia")
def test_bench_competencia_obtener_todas(benchmark, datos):
    repo = SqliteCompetenciaRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.obtener_todas_competencias)


@pytest.mark.benchmark(group="competencia")
def test_bench_competencia_categorias_de_competencia(benchmark, datos):
    repo = SqliteCompetenciaRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.obtener_categorias_de_competencia, datos.ids["id_competencia"])


@pytest.mark.benchmark(group="competencia")
def test_bench_competencia_inscripciones_por_club(benchmark, datos):
    repo = SqliteCompetenciaRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.obtener_inscripciones_por_club, datos.ids["id_club"])


@pytest.mark.benchmark(group="competencia")
def test_bench_competencia_jugadores_lista(benchmark, datos):
    repo = SqliteCompetenciaRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.obtener_jugadores_lista, datos.ids["id_lista"])


# ------------------------------------------------------------------ partido


@pytest.mark.benchmark(group="partido")
def test_bench_partido_buscar_por_id(benchmark, datos):
    repo = SqlitePartidoRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.buscar_por_id, datos.ids["id_partido"]) is not None


@pytest.mark.benchmark(group="partido")
def test_bench_partido_buscar_por_club(benchmark, datos):
    repo = SqlitePartidoRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.buscar_por_club, datos.ids["id_club"])


@pytest.mark.benchmark(group="partido")
def test_bench_partido_resumen_por_club(benchmark, datos):
    repo = SqlitePartidoRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.resumen_por_club, datos.ids["id_club"])
