"""Tests unitarios del caso de uso de partidos, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.partido_dto import (
    BoxscoreDTO,
    BoxscoreFilaDTO,
    CuartoDTO,
    EstadisticaInputDTO,
    PartidoDTO,
    PartidoResumenDTO,
)
from dominio.entidades.competencia import Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.entidades.partido import BoxscoreFila, JugadorPartido, Partido, PartidoCuarto, PartidoResumen
from dominio.exceptions import (
    CuartosInconsistentesError,
    DatoInvalidoError,
    InscripcionNoEncontradaError,
    JugadorNoEstaEnListaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
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


# ------------------------------------------------------------------ CargarPartido (US-108)


@pytest.fixture
def repo_competencia_con_listas():
    """Mock de CompetenciaRepositorio con clubes 1 (local) y 2 (visitante) inscriptos en comp=1, cat=1.

    El club 1 tambien tiene inscripcion en cat=2 con el jugador 99 (para probar AC6).
    """
    repo = MagicMock(spec=CompetenciaRepositorio)

    def _inscripciones(id_club: int):
        if id_club == 1:
            return [
                Inscripcion(idClub=1, idCategoria=1, idCompetencia=1, idInscripcion=10),
                Inscripcion(idClub=1, idCategoria=2, idCompetencia=1, idInscripcion=11),
            ]
        if id_club == 2:
            return [Inscripcion(idClub=2, idCategoria=1, idCompetencia=1, idInscripcion=20)]
        return []

    def _lista(id_inscripcion: int):
        return {
            10: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=10, idListaBuenaFe=100),
            11: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=11, idListaBuenaFe=101),
            20: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=20, idListaBuenaFe=200),
        }.get(id_inscripcion)

    def _jugadores(id_lista: int):
        return {
            100: [JugadorListaBuenaFe(idJugador=1, idListaBuenaFe=100)],
            101: [JugadorListaBuenaFe(idJugador=99, idListaBuenaFe=101)],
            200: [JugadorListaBuenaFe(idJugador=6, idListaBuenaFe=200)],
        }.get(id_lista, [])

    repo.obtener_inscripciones_por_club.side_effect = _inscripciones
    repo.obtener_lista_por_inscripcion.side_effect = _lista
    repo.obtener_jugadores_lista.side_effect = _jugadores
    return repo


def _datos_partido_valido(cuartos: list[CuartoDTO] | None = None):
    partido_dto = PartidoDTO(
        fecha="2026-08-10",
        estadio="Estadio Atenas",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=1,
        idClubVisitante=2,
        cuartos=cuartos or [],
    )
    box_local = BoxscoreDTO(
        idClub=1,
        estadisticas=[EstadisticaInputDTO(idJugador=1, minutosJugados=20.0, puntos=10, t2c=5, t2l=8)],
    )
    box_visitante = BoxscoreDTO(
        idClub=2,
        estadisticas=[EstadisticaInputDTO(idJugador=6, minutosJugados=22.0, puntos=8, t2c=4, t2l=7)],
    )
    return partido_dto, box_local, box_visitante


def test_cargar_partido_sin_cuartos_traduce_y_guarda_atomicamente(repo_partido, repo_competencia_con_listas):
    partido_dto, box_local, box_visitante = _datos_partido_valido()
    partido_persistido = Partido(
        fecha="2026-08-10",
        estadio="Estadio Atenas",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=1,
        idClubVisitante=2,
        idPartido=42,
    )
    repo_partido.save_with_boxscore.return_value = (partido_persistido, [])

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)
    resultado = uc.ejecutar(partido_dto, box_local, box_visitante)

    assert resultado is not None
    assert resultado.idPartido == 42
    assert resultado.idCategoria == 1
    repo_partido.save_with_boxscore.assert_called_once_with(
        partido=Partido(
            fecha="2026-08-10",
            estadio="Estadio Atenas",
            idCompetencia=1,
            idCategoria=1,
            idClubLocal=1,
            idClubVisitante=2,
        ),
        boxscore=[
            JugadorPartido(idJugador=1, idPartido=0, idClub=1, minutosJugados=20.0, puntos=10, t2c=5, t2l=8),
            JugadorPartido(idJugador=6, idPartido=0, idClub=2, minutosJugados=22.0, puntos=8, t2c=4, t2l=7),
        ],
        cuartos=None,
    )


def test_cargar_partido_devuelve_none_si_repositorio_revierte(repo_partido, repo_competencia_con_listas):
    partido_dto, box_local, box_visitante = _datos_partido_valido()
    repo_partido.save_with_boxscore.return_value = None

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)

    assert uc.ejecutar(partido_dto, box_local, box_visitante) is None


@pytest.mark.parametrize(
    "rol_roto, id_jugador_invalido, texto_esperado",
    [
        pytest.param("local", 999, "idJugador=999.*local", id="jugador-fuera-de-lista-local"),
        pytest.param("visitante", 888, "idJugador=888.*visitante", id="jugador-fuera-de-lista-visitante"),
        pytest.param("local", 99, "idJugador=99.*local", id="jugador-de-otra-categoria-AC6"),
    ],
)
def test_cargar_partido_rechaza_jugador_no_habilitado_antes_de_persistir(
    repo_partido, repo_competencia_con_listas, rol_roto, id_jugador_invalido, texto_esperado
):
    partido_dto, box_local, box_visitante = _datos_partido_valido()
    if rol_roto == "local":
        box_local.estadisticas.append(EstadisticaInputDTO(idJugador=id_jugador_invalido))
    else:
        box_visitante.estadisticas.append(EstadisticaInputDTO(idJugador=id_jugador_invalido))

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)

    with pytest.raises(JugadorNoEstaEnListaError, match=texto_esperado):
        uc.ejecutar(partido_dto, box_local, box_visitante)

    repo_partido.save_with_boxscore.assert_not_called()


def test_cargar_partido_rechaza_club_sin_inscripcion_en_esa_categoria(repo_partido, repo_competencia_con_listas):
    partido_dto, box_local, box_visitante = _datos_partido_valido()
    partido_dto.idCategoria = 2  # el club 2 no esta inscripto en categoria 2
    box_local.estadisticas = [EstadisticaInputDTO(idJugador=99, minutosJugados=20.0, puntos=10, t2c=5, t2l=8)]

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)

    with pytest.raises(InscripcionNoEncontradaError, match="visitante"):
        uc.ejecutar(partido_dto, box_local, box_visitante)

    repo_partido.save_with_boxscore.assert_not_called()


def test_cargar_partido_rechaza_mismo_club_local_y_visitante(repo_partido, repo_competencia_con_listas):
    partido_dto, box_local, box_visitante = _datos_partido_valido()
    partido_dto.idClubVisitante = 1

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)

    with pytest.raises(DatoInvalidoError, match="no pueden ser el mismo"):
        uc.ejecutar(partido_dto, box_local, box_visitante)

    repo_partido.save_with_boxscore.assert_not_called()


def test_cargar_partido_con_cuatro_cuartos_y_prorroga_validos_AC7(repo_partido, repo_competencia_con_listas):
    cuartos = [
        # Local suma 10 en 5 periodos (4 cuartos + 1 prorroga)
        CuartoDTO(idClub=1, nroCuarto=1, puntos=2),
        CuartoDTO(idClub=1, nroCuarto=2, puntos=2),
        CuartoDTO(idClub=1, nroCuarto=3, puntos=2),
        CuartoDTO(idClub=1, nroCuarto=4, puntos=2),
        CuartoDTO(idClub=1, nroCuarto=5, puntos=2),
        # Visitante suma 8 en 5 periodos
        CuartoDTO(idClub=2, nroCuarto=1, puntos=2),
        CuartoDTO(idClub=2, nroCuarto=2, puntos=2),
        CuartoDTO(idClub=2, nroCuarto=3, puntos=2),
        CuartoDTO(idClub=2, nroCuarto=4, puntos=2),
        CuartoDTO(idClub=2, nroCuarto=5, puntos=0),
    ]
    partido_dto, box_local, box_visitante = _datos_partido_valido(cuartos=cuartos)
    repo_partido.save_with_boxscore.return_value = (
        Partido("2026-08-10", "Estadio Atenas", 1, 1, 1, 2, idPartido=50),
        [],
    )

    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)
    resultado = uc.ejecutar(partido_dto, box_local, box_visitante)

    assert resultado is not None
    assert resultado.idPartido == 50
    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert len(kwargs["cuartos"]) == 10
    assert kwargs["cuartos"][0] == PartidoCuarto(idClub=1, nroCuarto=1, puntos=2)


@pytest.mark.parametrize(
    "cuartos, mensaje_esperado",
    [
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=5),
            ],
            "visitante",
            id="cuartos-de-un-solo-equipo",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=1, puntos=8),
            ],
            "distinta cantidad",
            id="distinta-cantidad-de-periodos",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=4),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=4),  # suma 8, faltan 2 para 10
                CuartoDTO(idClub=2, nroCuarto=1, puntos=4),
                CuartoDTO(idClub=2, nroCuarto=2, puntos=4),
            ],
            r"local.*faltan 2",
            id="suma-local-menor-al-boxscore",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=2, puntos=6),  # suma 11, sobran 3 sobre 8
            ],
            r"visitante.*sobran 3",
            id="suma-visitante-mayor-al-boxscore",
        ),
    ],
)
def test_cargar_partido_rechaza_cuartos_inconsistentes_AC7(
    repo_partido, repo_competencia_con_listas, cuartos, mensaje_esperado
):
    partido_dto, box_local, box_visitante = _datos_partido_valido(cuartos=cuartos)
    uc = CargarPartidoUseCase(repo_partido, repo_competencia_con_listas)

    with pytest.raises(CuartosInconsistentesError, match=mensaje_esperado):
        uc.ejecutar(partido_dto, box_local, box_visitante)

    repo_partido.save_with_boxscore.assert_not_called()
