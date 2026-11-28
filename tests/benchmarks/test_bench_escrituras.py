"""Benchmarks de las escrituras transaccionales: guardan varias tablas a la vez, todo o nada.

Cada ronda escribe sobre una copia nueva de la base de la escala (`copiar_base`, en el setup, que no se mide):
así se mide siempre la misma escritura, no una que encuentra la base cada vez más llena.
"""

import pytest
from ayudantes_bench import EN_CANCHA, copiar_base, plan_de_ejecucion

from dominio.entidades.competencia import Competencia
from dominio.entidades.partido import JugadorPartido, Partido
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
from infraestructura.repositorios.sqlite_partido_repositorio import SqlitePartidoRepositorio

pytestmark = pytest.mark.benchmark
RONDAS = 20


def _registrar(benchmark, datos, repo_de_prueba, funcion_de_prueba, *args):
    benchmark.extra_info.update(
        escala=datos.escala,
        datos=datos.conteos,
        filas=1,
        plan=plan_de_ejecucion(repo_de_prueba, funcion_de_prueba, *args),
    )


@pytest.mark.benchmark(group="escrituras")
def test_bench_guardar_partido_con_boxscore(benchmark, datos):
    """La carga de un partido (US-108): cabecera + 24 filas de boxscore en una transacción."""
    plantel = {
        club: [
            fila[0]
            for fila in datos.conexion.execute(
                "SELECT idJugador FROM jugadorClub WHERE idClub = ? AND fechaHasta IS NULL LIMIT ?", (club, EN_CANCHA)
            )
        ]
        for club in (1, 2)
    }
    partido = Partido(
        fecha="2026-12-01",
        estadio="Estadio 01",
        idCompetencia=datos.ids["id_competencia"],
        idCategoria=datos.ids["id_categoria"],
        idClubLocal=1,
        idClubVisitante=2,
    )
    boxscore = [
        JugadorPartido(
            idJugador=j,
            idPartido=0,
            idClub=club,
            minutosJugados=20.0,
            puntos=9,
            t2c=2,
            t2l=5,
            t3c=1,
            t3l=5,
            t1c=2,
            t1l=5,
        )
        for club, jugadores in plantel.items()
        for j in jugadores
    ]

    def preparar():
        return (SqlitePartidoRepositorio(copiar_base(datos)),), {}

    def guardar(repo):
        return repo.save_with_boxscore(partido, boxscore)

    resultado = benchmark.pedantic(guardar, setup=preparar, rounds=RONDAS)
    assert resultado is not None
    copia = copiar_base(datos)
    _registrar(benchmark, datos, copia, SqlitePartidoRepositorio(copia).save_with_boxscore, partido, boxscore)


@pytest.mark.benchmark(group="escrituras")
def test_bench_guardar_competencia_con_categorias(benchmark, datos):
    competencia = Competencia(nombre="Copa de Invierno", anio=2026, tipo="copa")

    def preparar():
        return (SqliteCompetenciaRepositorio(copiar_base(datos)),), {}

    def guardar(repo):
        return repo.guardar_competencia_con_categorias(competencia, [1, 2, 3, 4])

    assert benchmark.pedantic(guardar, setup=preparar, rounds=RONDAS) is not None
    copia = copiar_base(datos)
    _registrar(
        benchmark,
        datos,
        copia,
        SqliteCompetenciaRepositorio(copia).guardar_competencia_con_categorias,
        competencia,
        [1, 2, 3, 4],
    )
