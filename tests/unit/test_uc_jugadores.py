"""Tests unitarios de los casos de uso de jugadores, con repositorios falsos (`unittest.mock`).

`MagicMock(spec=JugadorRepositorio)` crea un objeto que solo acepta los metodos que tiene la interfaz
real: si el caso de uso llamara a un metodo que no existe, el test fallaria. Ningun test toca SQLite.
"""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_jugadores_todos import ListarJugadoresTodosUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.club_dto import DesvincularJugadorDTO, VincularJugadorClubDTO, VinculoDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, EditarJugadorDTO, JugadorConClubDTO, JugadorDTO
from dominio.entidades.club import Club
from dominio.entidades.jugador import Jugador, JugadorClub, JugadorConClub
from dominio.exceptions import (
    ClubNoEncontradoError,
    DatoInvalidoError,
    JugadorEnUsoError,
    JugadorNoEncontradoError,
    JugadorSinVinculoActivoError,
    VinculoActivoExistenteError,
    VinculoSuperpuestoError,
)
from dominio.repositorios.club_repositorio import ClubRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio


@pytest.fixture
def repo_jugador():
    return MagicMock(spec=JugadorRepositorio)


@pytest.fixture
def repo_club():
    return MagicMock(spec=ClubRepositorio)


# ----------------------------------------------------------------------------- RegistrarJugador


def _dto_jugador(**overrides) -> CrearJugadorDTO:
    datos = {"nombre": "Manu", "apellido": "Ginobili", "anioNacimiento": 1977}
    return CrearJugadorDTO(**{**datos, **overrides})


def test_registrar_jugador_devuelve_el_dto_con_el_id_asignado(repo_jugador):
    repo_jugador.guardar.return_value = Jugador("Manu", "Ginobili", 1977, idJugador=7)

    resultado = RegistrarJugadorUseCase(repo_jugador).ejecutar(_dto_jugador())

    assert resultado == JugadorDTO(nombre_completo="Manu Ginobili", id=7, anioNacimiento=1977)
    # El caso de uso le entrega al repositorio una entidad todavia sin id
    repo_jugador.guardar.assert_called_once_with(jugador=Jugador("Manu", "Ginobili", 1977))


def test_registrar_jugador_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_jugador):
    repo_jugador.guardar.return_value = None

    assert RegistrarJugadorUseCase(repo_jugador).ejecutar(_dto_jugador()) is None


def test_registrar_jugador_con_dato_de_tipo_invalido_no_llega_al_repositorio(repo_jugador):
    with pytest.raises(TypeError):
        RegistrarJugadorUseCase(repo_jugador).ejecutar(_dto_jugador(anioNacimiento="no-es-un-numero"))

    repo_jugador.guardar.assert_not_called()


def test_registrar_jugador_sin_anio_de_nacimiento_es_valido(repo_jugador):
    repo_jugador.guardar.return_value = Jugador("Manu", "Ginobili", None, idJugador=7)

    resultado = RegistrarJugadorUseCase(repo_jugador).ejecutar(_dto_jugador(anioNacimiento=None))

    assert resultado == JugadorDTO(nombre_completo="Manu Ginobili", id=7, anioNacimiento=None)


# ------------------------------------------------------------------ VincularJugadorAClub


def _dto_vinculo(**overrides) -> VincularJugadorClubDTO:
    datos = {"idJugador": 1, "idClub": 2, "fechaDesde": "2026-01-01"}
    return VincularJugadorClubDTO(**{**datos, **overrides})


def _preparar_vinculo(repo_jugador, repo_club, **overrides):
    """Configura los mocks para el camino feliz; cada test pisa (override) lo que quiere romper."""
    config = {
        "jugador": Jugador("Manu", "Ginobili", 1977, idJugador=1),
        "club": Club("Atenas", idClub=2),
        "club_activo": None,
        "historial": [],
        **overrides,
    }
    repo_jugador.buscar_por_id.return_value = config["jugador"]
    repo_club.buscar_por_id.return_value = config["club"]
    repo_jugador.club_activo.return_value = config["club_activo"]
    repo_jugador.historial_vinculos.return_value = config["historial"]


def test_vincular_jugador_guarda_el_vinculo_vigente(repo_jugador, repo_club):
    _preparar_vinculo(repo_jugador, repo_club)
    repo_jugador.link_to_club.return_value = JugadorClub("2026-01-01", None, idJugador=1, idClub=2)

    resultado = VincularJugadorAClubUseCase(repo_jugador, repo_club).ejecutar(_dto_vinculo())

    assert resultado == VinculoDTO(idJugador=1, idClub=2, fechaDesde="2026-01-01", fechaHasta=None)
    # fechaHasta=None significa "vinculo vigente"
    repo_jugador.link_to_club.assert_called_once_with(JugadorClub("2026-01-01", None, idJugador=1, idClub=2))


@pytest.mark.parametrize(
    "overrides, excepcion, fragmento",
    [
        pytest.param({"jugador": None}, JugadorNoEncontradoError, "idJugador=1", id="jugador-inexistente"),
        pytest.param({"club": None}, ClubNoEncontradoError, "idClub=2", id="club-inexistente"),
        pytest.param(
            {"club_activo": Club("Instituto", idClub=9)},
            VinculoActivoExistenteError,
            "idClub=9",
            id="ya-tiene-club-activo",
        ),
        pytest.param(
            {"historial": [JugadorClub("2025-06-01", "2026-03-01", idJugador=1, idClub=9)]},
            VinculoSuperpuestoError,
            "2026-03-01",
            id="empieza-antes-de-que-termine-el-vinculo-anterior",
        ),
        pytest.param(
            {"historial": [JugadorClub("2026-01-01", "2026-01-01", idJugador=1, idClub=2)]},
            VinculoSuperpuestoError,
            "2026-01-01",
            id="revinculacion-mismo-club-y-misma-fecha-inicio",
        ),
    ],
)
def test_vincular_jugador_que_rompe_una_regla_lanza_excepcion_y_no_guarda(
    repo_jugador, repo_club, overrides, excepcion, fragmento
):
    _preparar_vinculo(repo_jugador, repo_club, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        VincularJugadorAClubUseCase(repo_jugador, repo_club).ejecutar(_dto_vinculo())

    repo_jugador.link_to_club.assert_not_called()


def test_vincular_jugador_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_jugador, repo_club):
    _preparar_vinculo(repo_jugador, repo_club)
    repo_jugador.link_to_club.return_value = None

    assert VincularJugadorAClubUseCase(repo_jugador, repo_club).ejecutar(_dto_vinculo()) is None


# ------------------------------------------------------------------ ListarJugadoresClub


def test_listar_jugadores_convierte_cada_jugador_en_dto(repo_jugador):
    repo_jugador.buscar_por_club.return_value = [
        Jugador("Manu", "Ginobili", 1977, idJugador=1),
        Jugador("Pepe", "Argento", 1980, idJugador=2),
    ]

    resultado = ListarJugadoresClubUseCase(repo_jugador).ejecutar(5)

    assert resultado == [
        JugadorDTO(nombre_completo="Manu Ginobili", id=1, anioNacimiento=1977),
        JugadorDTO(nombre_completo="Pepe Argento", id=2, anioNacimiento=1980),
    ]
    repo_jugador.buscar_por_club.assert_called_once_with(idClub=5)


@pytest.mark.parametrize("sin_resultados", [None, []], ids=["repo-devuelve-None", "repo-devuelve-lista-vacia"])
def test_listar_jugadores_sin_resultados_devuelve_lista_vacia(repo_jugador, sin_resultados):
    repo_jugador.buscar_por_club.return_value = sin_resultados

    assert ListarJugadoresClubUseCase(repo_jugador).ejecutar(5) == []


def test_listar_jugadores_con_un_jugador_sin_id_es_un_error_del_repositorio(repo_jugador):
    repo_jugador.buscar_por_club.return_value = [Jugador("Manu", "Ginobili", 1977)]

    with pytest.raises(RuntimeError, match="Jugador"):
        ListarJugadoresClubUseCase(repo_jugador).ejecutar(5)


@pytest.mark.parametrize(
    "fecha_desde",
    [
        pytest.param("2026-03-01", id="el-mismo-dia-que-termino-el-anterior"),
        pytest.param("2026-03-02", id="despues-de-que-termino-el-anterior"),
    ],
)
def test_vincular_jugador_que_ya_se_fue_de_otro_club_puede_vincularse_de_nuevo(repo_jugador, repo_club, fecha_desde):
    _preparar_vinculo(
        repo_jugador,
        repo_club,
        historial=[JugadorClub("2025-06-01", "2026-03-01", idJugador=1, idClub=9)],
    )
    repo_jugador.link_to_club.return_value = JugadorClub(fecha_desde, None, idJugador=1, idClub=2)

    resultado = VincularJugadorAClubUseCase(repo_jugador, repo_club).ejecutar(_dto_vinculo(fechaDesde=fecha_desde))

    assert resultado == VinculoDTO(idJugador=1, idClub=2, fechaDesde=fecha_desde, fechaHasta=None)


# ------------------------------------------------------------------ DesvincularJugadorDeClub


def _preparar_desvinculo(repo_jugador, **overrides):
    """Escenario feliz: el jugador 1 existe y juega en el club 2 desde el 2026-01-01."""
    config = {
        "jugador": Jugador("Manu", "Ginobili", 1977, idJugador=1),
        "historial": [JugadorClub("2026-01-01", None, idJugador=1, idClub=2)],
        **overrides,
    }
    repo_jugador.buscar_por_id.return_value = config["jugador"]
    repo_jugador.historial_vinculos.return_value = config["historial"]


def test_desvincular_jugador_cierra_el_vinculo_vigente(repo_jugador):
    _preparar_desvinculo(repo_jugador)
    repo_jugador.cerrar_vinculo.return_value = JugadorClub("2026-01-01", "2026-06-30", idJugador=1, idClub=2)

    resultado = DesvincularJugadorDeClubUseCase(repo_jugador).ejecutar(
        DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30")
    )

    assert resultado == VinculoDTO(idJugador=1, idClub=2, fechaDesde="2026-01-01", fechaHasta="2026-06-30")
    repo_jugador.cerrar_vinculo.assert_called_once_with(1, "2026-06-30")


@pytest.mark.parametrize(
    "overrides, excepcion, fragmento",
    [
        pytest.param({"jugador": None}, JugadorNoEncontradoError, "idJugador=1", id="jugador-inexistente"),
        pytest.param({"historial": []}, JugadorSinVinculoActivoError, "idJugador=1", id="nunca-estuvo-en-un-club"),
        pytest.param(
            {"historial": [JugadorClub("2025-01-01", "2025-12-31", idJugador=1, idClub=2)]},
            JugadorSinVinculoActivoError,
            "no tiene un club activo",
            id="su-unico-vinculo-ya-estaba-cerrado",
        ),
    ],
)
def test_desvincular_jugador_que_rompe_una_regla_lanza_excepcion_y_no_guarda(
    repo_jugador, overrides, excepcion, fragmento
):
    _preparar_desvinculo(repo_jugador, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        DesvincularJugadorDeClubUseCase(repo_jugador).ejecutar(
            DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30")
        )

    repo_jugador.cerrar_vinculo.assert_not_called()


def test_desvincular_jugador_con_fecha_de_baja_anterior_al_inicio_lanza_excepcion(repo_jugador):
    _preparar_desvinculo(repo_jugador)

    with pytest.raises(DatoInvalidoError, match="anterior"):
        DesvincularJugadorDeClubUseCase(repo_jugador).ejecutar(
            DesvincularJugadorDTO(idJugador=1, fechaHasta="2025-12-31")
        )

    repo_jugador.cerrar_vinculo.assert_not_called()


def test_desvincular_jugador_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_jugador):
    _preparar_desvinculo(repo_jugador)
    repo_jugador.cerrar_vinculo.return_value = None

    resultado = DesvincularJugadorDeClubUseCase(repo_jugador).ejecutar(
        DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30")
    )

    assert resultado is None


# ------------------------------------------------------------------ BuscarJugadoresPorNombre


def test_buscar_jugadores_por_nombre_devuelve_dtos(repo_jugador):
    repo_jugador.buscar_por_nombre.return_value = [
        Jugador("Manu", "Ginobili", 1977, idJugador=7),
        Jugador("Leandro", "Ginobili", None, idJugador=8),
    ]

    resultado = BuscarJugadoresPorNombreUseCase(repo_jugador).ejecutar("  Ginobili  ")

    assert resultado == [
        JugadorDTO(nombre_completo="Manu Ginobili", id=7, anioNacimiento=1977),
        JugadorDTO(nombre_completo="Leandro Ginobili", id=8, anioNacimiento=None),
    ]
    repo_jugador.buscar_por_nombre.assert_called_once_with("Ginobili")


def test_buscar_jugadores_con_texto_vacio_no_consulta_el_repositorio(repo_jugador):
    assert BuscarJugadoresPorNombreUseCase(repo_jugador).ejecutar("   ") == []
    repo_jugador.buscar_por_nombre.assert_not_called()


def test_buscar_jugadores_sin_coincidencias_devuelve_lista_vacia(repo_jugador):
    repo_jugador.buscar_por_nombre.return_value = []

    assert BuscarJugadoresPorNombreUseCase(repo_jugador).ejecutar("Desconocido") == []


# ------------------------------------------------------------------ EditarJugador


def test_editar_jugador_actualiza_y_devuelve_dto(repo_jugador):
    repo_jugador.buscar_por_id.return_value = Jugador("Pepe", "Argento", 1980, idJugador=1)
    repo_jugador.actualizar.return_value = Jugador("José", "Argento", 1981, idJugador=1)

    resultado = EditarJugadorUseCase(repo_jugador).ejecutar(
        EditarJugadorDTO(idJugador=1, nombre="José", apellido="Argento", anioNacimiento=1981)
    )

    assert resultado == JugadorDTO(nombre_completo="José Argento", id=1, anioNacimiento=1981)
    assert resultado.nombre == "José"
    assert resultado.apellido == "Argento"
    repo_jugador.actualizar.assert_called_once_with(Jugador("José", "Argento", 1981, idJugador=1))


def test_editar_jugador_inexistente_lanza_error(repo_jugador):
    repo_jugador.buscar_por_id.return_value = None

    with pytest.raises(JugadorNoEncontradoError, match="idJugador=99"):
        EditarJugadorUseCase(repo_jugador).ejecutar(EditarJugadorDTO(idJugador=99, nombre="Pepe", apellido="Argento"))

    repo_jugador.actualizar.assert_not_called()


def test_editar_jugador_con_datos_invalidos_no_llama_al_repositorio(repo_jugador):
    repo_jugador.buscar_por_id.return_value = Jugador("Pepe", "Argento", 1980, idJugador=1)

    with pytest.raises(DatoInvalidoError):
        EditarJugadorUseCase(repo_jugador).ejecutar(EditarJugadorDTO(idJugador=1, nombre="", apellido="Argento"))

    repo_jugador.actualizar.assert_not_called()


# ------------------------------------------------------------------ EliminarJugador


def test_eliminar_jugador_sin_uso_llama_al_repositorio(repo_jugador):
    repo_jugador.buscar_por_id.return_value = Jugador("Pepe", "Argento", 1980, idJugador=1)
    repo_jugador.jugador_en_uso.return_value = False
    repo_jugador.eliminar.return_value = True

    assert EliminarJugadorUseCase(repo_jugador).ejecutar(1) is True
    repo_jugador.eliminar.assert_called_once_with(1)


def test_eliminar_jugador_inexistente_lanza_error(repo_jugador):
    repo_jugador.buscar_por_id.return_value = None

    with pytest.raises(JugadorNoEncontradoError, match="idJugador=99"):
        EliminarJugadorUseCase(repo_jugador).ejecutar(99)

    repo_jugador.eliminar.assert_not_called()


def test_eliminar_jugador_en_uso_lanza_error_y_no_borra(repo_jugador):
    repo_jugador.buscar_por_id.return_value = Jugador("Pepe", "Argento", 1980, idJugador=1)
    repo_jugador.jugador_en_uso.return_value = True

    with pytest.raises(JugadorEnUsoError, match="idJugador=1"):
        EliminarJugadorUseCase(repo_jugador).ejecutar(1)

    repo_jugador.eliminar.assert_not_called()


def test_listar_jugadores_todos_devuelve_cada_jugador_con_su_club():
    repo = MagicMock(spec=JugadorRepositorio)
    repo.listar_con_club_actual.return_value = [
        JugadorConClub(Jugador("Manu", "Ginobili", 1977, idJugador=7), "Atenas"),
        JugadorConClub(Jugador("Facu", "Campazzo", idJugador=10), None),
    ]

    resultado = ListarJugadoresTodosUseCase(repo).ejecutar()

    assert resultado == [
        JugadorConClubDTO("Manu Ginobili", 7, 1977, "Atenas"),
        JugadorConClubDTO("Facu Campazzo", 10, None, None),
    ]
