"""Tests unitarios del caso de uso de partidos, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.partido_dto import BoxscoreFilaDTO, PartidoResumenDTO
from dominio.entidades.partido import BoxscoreFila, PartidoResumen
from dominio.repositorios.partido_repositorio import PartidoRepositorio


@pytest.fixture
def repo_partido():
    return MagicMock(spec=PartidoRepositorio)


def test_listar_partidos_muestra_los_nombres_de_la_competencia_y_de_los_clubes(repo_partido):
    repo_partido.resumen_por_club.return_value = [
        PartidoResumen(1, "2026-05-21", "Cancha Atenas", "PROVINCIAL U21", 2026, "Atenas", "Universitario", "U21"),
        PartidoResumen(2, "2026-06-20", None, "PROVINCIAL U21", 2026, "Universitario", "Atenas"),
    ]

    resultado = ListarPartidosPorClubUseCase(repo_partido).ejecutar(1)

    assert resultado == [
        PartidoResumenDTO(1, "2026-05-21", "Cancha Atenas", "PROVINCIAL U21", 2026, "Atenas", "Universitario", "U21"),
        PartidoResumenDTO(2, "2026-06-20", None, "PROVINCIAL U21", 2026, "Universitario", "Atenas", None),
    ]
    repo_partido.resumen_por_club.assert_called_once_with(1)


def test_listar_partidos_sin_partidos_devuelve_lista_vacia(repo_partido):
    repo_partido.resumen_por_club.return_value = []

    assert ListarPartidosPorClubUseCase(repo_partido).ejecutar(1) == []


def test_obtener_boxscore_partido_devuelve_filas_dto(repo_partido):
    repo_partido.boxscore_por_partido.return_value = [
        BoxscoreFila(
            idPartido=1,
            idJugador=10,
            idClub=1,
            nombreJugador="Pepe Argento",
            nombreClub="Atenas",
            minutosJugados=25.5,
            puntos=14,
            t2c=4,
            t2l=7,
            t3c=2,
            t3l=5,
            t1c=0,
            t1l=2,
            rebotesDef=6,
            rebotesOf=2,
            rebotesTotales=8,
            asistencias=3,
            recuperos=1,
            perdidas=2,
            taponesRecibidos=0,
            taponesRealizados=1,
            faltasRecibidas=3,
            faltasCometidas=2,
        )
    ]

    resultado = ObtenerBoxscorePartidoUseCase(repo_partido).ejecutar(1)

    assert resultado == [
        BoxscoreFilaDTO(
            idPartido=1,
            idJugador=10,
            idClub=1,
            nombreJugador="Pepe Argento",
            nombreClub="Atenas",
            minutosJugados=25.5,
            puntos=14,
            t2c=4,
            t2l=7,
            t3c=2,
            t3l=5,
            t1c=0,
            t1l=2,
            rebotesDef=6,
            rebotesOf=2,
            rebotesTotales=8,
            asistencias=3,
            recuperos=1,
            perdidas=2,
            taponesRecibidos=0,
            taponesRealizados=1,
            faltasRecibidas=3,
            faltasCometidas=2,
        )
    ]
    repo_partido.boxscore_por_partido.assert_called_once_with(1)


def test_obtener_boxscore_partido_sin_datos_devuelve_lista_vacia(repo_partido):
    repo_partido.boxscore_por_partido.return_value = []

    assert ObtenerBoxscorePartidoUseCase(repo_partido).ejecutar(999) == []
