"""Tests unitarios de los casos de uso de la lista de buena fe, con repositorios falsos (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.lista_buena_fe_dto import AgregarJugadorListaDTO, JugadorEnListaDTO, QuitarJugadorListaDTO
from dominio.entidades.club import Club
from dominio.entidades.competencia import Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.entidades.jugador import Jugador
from dominio.exceptions import (
    InscripcionNoEncontradaError,
    JugadorNoEncontradoError,
    JugadorNoEstaEnListaError,
    JugadorNoPerteneceAlClubError,
    JugadorYaEnListaError,
    ListaBuenaFeNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio


@pytest.fixture
def repo_competencia():
    return MagicMock(spec=CompetenciaRepositorio)


@pytest.fixture
def repo_jugador():
    return MagicMock(spec=JugadorRepositorio)


def _preparar(repo_competencia, repo_jugador, **overrides):
    """Configura los mocks para el camino feliz; cada test pisa (override) lo que quiere romper.

    Escenario: la inscripcion 5 es del club 1, su lista es la 7, y el jugador 3 juega actualmente en el club 1.
    """
    config = {
        "inscripcion": Inscripcion(idClub=1, idCategoria=1, idCompetencia=1, idInscripcion=5),
        "lista": ListaBuenaFe("2026-03-01", 5, idListaBuenaFe=7),
        "jugador": Jugador("Manu", "Ginobili", 1977, idJugador=3),
        "club_activo": Club("Atenas", idClub=1),
        "habilitados": [],
        **overrides,
    }
    repo_competencia.buscar_inscripcion_por_id.return_value = config["inscripcion"]
    repo_competencia.obtener_lista_por_inscripcion.return_value = config["lista"]
    repo_competencia.obtener_jugadores_lista.return_value = config["habilitados"]
    repo_jugador.buscar_por_id.return_value = config["jugador"]
    repo_jugador.club_activo.return_value = config["club_activo"]


# ------------------------------------------------------------------ AgregarJugadorAListaBuenaFe


def _dto(**overrides) -> AgregarJugadorListaDTO:
    return AgregarJugadorListaDTO(**{"idInscripcion": 5, "idJugador": 3, **overrides})


def test_agregar_jugador_a_la_lista_devuelve_la_confirmacion(repo_competencia, repo_jugador):
    _preparar(repo_competencia, repo_jugador)
    repo_competencia.agregar_jugador_lista.return_value = JugadorListaBuenaFe(idJugador=3, idListaBuenaFe=7)

    resultado = AgregarJugadorAListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(_dto())

    assert resultado == JugadorEnListaDTO(idListaBuenaFe=7, idInscripcion=5, idJugador=3)
    repo_competencia.agregar_jugador_lista.assert_called_once_with(3, 7)


@pytest.mark.parametrize(
    "overrides, excepcion, fragmento",
    [
        pytest.param(
            {"inscripcion": None}, InscripcionNoEncontradaError, "idInscripcion=5", id="inscripcion-inexistente"
        ),
        pytest.param({"lista": None}, ListaBuenaFeNoEncontradaError, "idInscripcion=5", id="inscripcion-sin-lista"),
        pytest.param({"jugador": None}, JugadorNoEncontradoError, "idJugador=3", id="jugador-inexistente"),
        pytest.param({"club_activo": None}, JugadorNoPerteneceAlClubError, "idJugador=3", id="jugador-sin-club-activo"),
        pytest.param(
            {"club_activo": Club("Instituto", idClub=2)},
            JugadorNoPerteneceAlClubError,
            "idClub=1",
            id="jugador-de-otro-club",
        ),
        pytest.param(
            {"habilitados": [JugadorListaBuenaFe(idJugador=3, idListaBuenaFe=7)]},
            JugadorYaEnListaError,
            "idListaBuenaFe=7",
            id="jugador-ya-habilitado",
        ),
    ],
)
def test_agregar_jugador_que_rompe_una_regla_lanza_excepcion_y_no_guarda(
    repo_competencia, repo_jugador, overrides, excepcion, fragmento
):
    _preparar(repo_competencia, repo_jugador, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        AgregarJugadorAListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(_dto())

    repo_competencia.agregar_jugador_lista.assert_not_called()


def test_agregar_jugador_con_otros_jugadores_ya_en_la_lista_es_valido(repo_competencia, repo_jugador):
    """Que ya haya jugadores en la lista no es un problema: solo importa que no este el mismo jugador."""
    _preparar(repo_competencia, repo_jugador, habilitados=[JugadorListaBuenaFe(idJugador=99, idListaBuenaFe=7)])
    repo_competencia.agregar_jugador_lista.return_value = JugadorListaBuenaFe(idJugador=3, idListaBuenaFe=7)

    resultado = AgregarJugadorAListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(_dto())

    assert resultado is not None


def test_agregar_jugador_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_competencia, repo_jugador):
    _preparar(repo_competencia, repo_jugador)
    repo_competencia.agregar_jugador_lista.return_value = None

    assert AgregarJugadorAListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(_dto()) is None


# ------------------------------------------------------------------ ListarListaBuenaFe


def test_listar_lista_muestra_el_nombre_de_cada_jugador_habilitado(repo_competencia, repo_jugador):
    _preparar(
        repo_competencia,
        repo_jugador,
        habilitados=[JugadorListaBuenaFe(3, 7), JugadorListaBuenaFe(4, 7)],
    )
    repo_jugador.buscar_por_id.side_effect = [
        Jugador("Manu", "Ginobili", 1977, idJugador=3),
        Jugador("Pepe", "Argento", 1980, idJugador=4),
    ]

    resultado = ListarListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(5)

    assert resultado == [
        JugadorDTO(nombre_completo="Manu Ginobili", id=3, anioNacimiento=1977),
        JugadorDTO(nombre_completo="Pepe Argento", id=4, anioNacimiento=1980),
    ]
    repo_competencia.obtener_jugadores_lista.assert_called_once_with(7)


def test_listar_lista_sin_jugadores_devuelve_lista_vacia(repo_competencia, repo_jugador):
    _preparar(repo_competencia, repo_jugador, habilitados=[])

    assert ListarListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(5) == []


@pytest.mark.parametrize(
    "overrides, excepcion",
    [
        pytest.param({"inscripcion": None}, InscripcionNoEncontradaError, id="inscripcion-inexistente"),
        pytest.param({"lista": None}, ListaBuenaFeNoEncontradaError, id="inscripcion-sin-lista"),
        pytest.param(
            {"habilitados": [JugadorListaBuenaFe(3, 7)], "jugador": None},
            JugadorNoEncontradoError,
            id="jugador-de-la-lista-inexistente",
        ),
    ],
)
def test_listar_lista_que_rompe_una_regla_lanza_excepcion(repo_competencia, repo_jugador, overrides, excepcion):
    _preparar(repo_competencia, repo_jugador, **overrides)

    with pytest.raises(excepcion):
        ListarListaBuenaFeUseCase(repo_competencia, repo_jugador).ejecutar(5)


# ------------------------------------------------------------------ QuitarJugadorDeListaBuenaFe


def _dto_quitar(**overrides) -> QuitarJugadorListaDTO:
    return QuitarJugadorListaDTO(**{"idInscripcion": 5, "idJugador": 3, **overrides})


def test_quitar_jugador_de_la_lista_devuelve_la_confirmacion(repo_competencia, repo_jugador):
    _preparar(repo_competencia, repo_jugador, habilitados=[JugadorListaBuenaFe(3, 7)])
    repo_competencia.quitar_jugador_lista.return_value = True

    resultado = QuitarJugadorDeListaBuenaFeUseCase(repo_competencia).ejecutar(_dto_quitar())

    assert resultado == JugadorEnListaDTO(idListaBuenaFe=7, idInscripcion=5, idJugador=3)
    repo_competencia.quitar_jugador_lista.assert_called_once_with(3, 7)


@pytest.mark.parametrize(
    "overrides, excepcion, fragmento",
    [
        pytest.param(
            {"inscripcion": None}, InscripcionNoEncontradaError, "idInscripcion=5", id="inscripcion-inexistente"
        ),
        pytest.param({"lista": None}, ListaBuenaFeNoEncontradaError, "idInscripcion=5", id="inscripcion-sin-lista"),
        pytest.param({"habilitados": []}, JugadorNoEstaEnListaError, "idJugador=3", id="lista-vacia"),
        pytest.param(
            {"habilitados": [JugadorListaBuenaFe(99, 7)]},
            JugadorNoEstaEnListaError,
            "idListaBuenaFe=7",
            id="el-jugador-no-esta-en-la-lista",
        ),
    ],
)
def test_quitar_jugador_que_rompe_una_regla_lanza_excepcion_y_no_borra(
    repo_competencia, repo_jugador, overrides, excepcion, fragmento
):
    _preparar(repo_competencia, repo_jugador, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        QuitarJugadorDeListaBuenaFeUseCase(repo_competencia).ejecutar(_dto_quitar())

    repo_competencia.quitar_jugador_lista.assert_not_called()


def test_quitar_jugador_devuelve_none_si_el_repositorio_no_pudo_borrar(repo_competencia, repo_jugador):
    _preparar(repo_competencia, repo_jugador, habilitados=[JugadorListaBuenaFe(3, 7)])
    repo_competencia.quitar_jugador_lista.return_value = False

    assert QuitarJugadorDeListaBuenaFeUseCase(repo_competencia).ejecutar(_dto_quitar()) is None
