"""Tests unitarios de los casos de uso de clubes, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO
from dominio.entidades.club import Club
from dominio.exceptions import ClubNoEncontradoError
from dominio.repositorios.club_repositorio import ClubRepositorio


@pytest.fixture
def repo_club():
    return MagicMock(spec=ClubRepositorio)


# ----------------------------------------------------------------------------- CrearClub


def test_crear_club_devuelve_el_dto_con_el_id_asignado(repo_club):
    repo_club.guardar.return_value = Club("Atenas", idClub=3)

    resultado = CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas"))

    assert resultado == ClubDTO(idClub=3, nombre="Atenas")
    repo_club.guardar.assert_called_once_with(club=Club("Atenas"))


def test_crear_club_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_club):
    repo_club.guardar.return_value = None

    assert CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas")) is None


def test_crear_club_con_nombre_de_tipo_invalido_no_llega_al_repositorio(repo_club):
    with pytest.raises(TypeError):
        CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre=None))

    repo_club.guardar.assert_not_called()


# ------------------------------------------------------------------ ListarClubesUsuario


def test_listar_clubes_usuario_convierte_cada_club_en_dto(repo_club):
    repo_club.buscar_por_id_usuario.return_value = [Club("Atenas", idClub=1), Club("Instituto", idClub=2)]

    resultado = ListarClubesUsuarioUseCase(repo_club).ejecutar(10)

    assert resultado == [ClubDTO(1, "Atenas"), ClubDTO(2, "Instituto")]
    repo_club.buscar_por_id_usuario.assert_called_once_with(10)


@pytest.mark.parametrize("sin_resultados", [None, []], ids=["repo-devuelve-None", "repo-devuelve-lista-vacia"])
def test_listar_clubes_usuario_sin_resultados_devuelve_lista_vacia(repo_club, sin_resultados):
    repo_club.buscar_por_id_usuario.return_value = sin_resultados

    assert ListarClubesUsuarioUseCase(repo_club).ejecutar(10) == []


# ------------------------------------------------------------------ CambiarClubActivo


def test_cambiar_club_activo_devuelve_el_club_si_el_usuario_pertenece(repo_club):
    repo_club.buscar_por_id_usuario.return_value = [Club("Atenas", idClub=1), Club("Instituto", idClub=2)]

    resultado = CambiarClubActivoUseCase(repo_club).ejecutar(idUsuario=10, idClub=2)

    assert resultado == ClubDTO(idClub=2, nombre="Instituto")


@pytest.mark.parametrize(
    "clubes_del_usuario",
    [
        pytest.param([Club("Atenas", idClub=1)], id="el-club-es-de-otro-usuario"),
        pytest.param(None, id="el-usuario-no-tiene-clubes"),
    ],
)
def test_cambiar_club_activo_sin_acceso_lanza_club_no_encontrado(repo_club, clubes_del_usuario):
    repo_club.buscar_por_id_usuario.return_value = clubes_del_usuario

    with pytest.raises(ClubNoEncontradoError, match=r"idUsuario=10.*idClub=2"):
        CambiarClubActivoUseCase(repo_club).ejecutar(idUsuario=10, idClub=2)
