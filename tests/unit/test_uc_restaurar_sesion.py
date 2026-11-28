"""Tests unitarios de RestaurarSesionUseCase (US-106): almacen, repositorio y caso de uso de club son mocks.

La sesion es un SessionManager real (con el mismo almacen mock): asi se verifica el estado final, no
solo las llamadas.
"""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.restaurar_sesion import RestaurarSesionUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.session_dto import SessionDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.usuario import Usuario
from dominio.exceptions import ClubNoEncontradoError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio

PROFE = Usuario(nombre="Profesor", email="profe@test.com", password_hash="hash", idUsuario=1)
ATENAS = ClubDTO(idClub=7, nombre="Atenas")


@pytest.fixture
def almacen():
    almacen = MagicMock(spec=SesionAlmacen)
    almacen.cargar.return_value = SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=7)
    return almacen


@pytest.fixture
def repo_usuario():
    repo = MagicMock(spec=UsuarioRepositorio)
    repo.encontrar_por_id.return_value = PROFE
    return repo


@pytest.fixture
def cambiar_club_uc():
    uc = MagicMock(spec=CambiarClubActivoUseCase)
    uc.ejecutar.return_value = ATENAS
    return uc


@pytest.fixture
def sesion(almacen):
    return SessionManager(almacen)


@pytest.fixture
def restaurar(almacen, repo_usuario, cambiar_club_uc, sesion):
    return RestaurarSesionUseCase(almacen, repo_usuario, cambiar_club_uc, sesion)


def test_sin_sesion_recordada_no_abre_sesion(restaurar, almacen, sesion, repo_usuario):
    almacen.cargar.return_value = None

    restaurar.ejecutar()

    assert sesion.is_authenticated() is False
    repo_usuario.encontrar_por_id.assert_not_called()


def test_restaura_el_usuario_y_el_club(restaurar, sesion, cambiar_club_uc):
    restaurar.ejecutar()

    assert sesion.usuario_actual() == UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")
    assert sesion.club_activo() == ATENAS
    cambiar_club_uc.ejecutar.assert_called_once_with(1, 7)  # el club se revalida, no se cree al archivo


def test_la_sesion_restaurada_se_sigue_recordando(restaurar, almacen):
    restaurar.ejecutar()

    assert almacen.guardar.call_args.args == (SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=7),)


def test_usuario_que_ya_no_existe_descarta_la_sesion(restaurar, repo_usuario, almacen, sesion):
    """AC4: un archivo con un usuario que ya no existe se ignora y se pide login."""
    repo_usuario.encontrar_por_id.return_value = None

    restaurar.ejecutar()

    assert sesion.is_authenticated() is False
    almacen.borrar.assert_called_once_with()


def test_mismo_id_con_otro_email_descarta_la_sesion(restaurar, repo_usuario, almacen, sesion):
    """Si la base se recreo, el id 1 puede ser de otra persona: no hay que entrar con su cuenta."""
    repo_usuario.encontrar_por_id.return_value = Usuario(
        nombre="Otra persona", email="otra@test.com", password_hash="hash", idUsuario=1
    )

    restaurar.ejecutar()

    assert sesion.is_authenticated() is False
    almacen.borrar.assert_called_once_with()


def test_club_que_ya_no_es_del_usuario_restaura_la_sesion_sin_club(restaurar, cambiar_club_uc, sesion, almacen):
    cambiar_club_uc.ejecutar.side_effect = ClubNoEncontradoError("sin acceso")

    restaurar.ejecutar()

    assert sesion.is_authenticated() is True
    assert sesion.club_activo() is None
    # el archivo queda reescrito sin el club invalido
    assert almacen.guardar.call_args.args == (SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=None),)


def test_sesion_recordada_sin_club_no_consulta_clubes(restaurar, almacen, cambiar_club_uc, sesion):
    almacen.cargar.return_value = SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=None)

    restaurar.ejecutar()

    assert sesion.is_authenticated() is True
    assert sesion.club_activo() is None
    cambiar_club_uc.ejecutar.assert_not_called()
