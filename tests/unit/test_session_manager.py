"""Tests unitarios del SessionManager (US-105 en memoria; US-106 club activo y "Recordarme").

El almacén es un mock: acá se prueba *cuándo* se guarda o se borra la sesión, no cómo se escribe el archivo
(eso está en `tests/integration/test_json_sesion_almacen.py`).
"""

from unittest.mock import MagicMock

import pytest

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.session_dto import SessionDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager

ATENAS = ClubDTO(idClub=7, nombre="Atenas")


@pytest.fixture
def almacen():
    return MagicMock(spec=SesionAlmacen)


@pytest.fixture
def sesion(almacen):
    return SessionManager(almacen)


@pytest.fixture
def usuario():
    return UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")


# ----------------------------------------------------------------------------- sesión en memoria (US-105)


def test_sesion_nueva_no_esta_autenticada(sesion):
    assert sesion.is_authenticated() is False


def test_iniciar_sesion_autentica_y_guarda_el_usuario(sesion, usuario):
    sesion.iniciar_sesion(usuario)

    assert sesion.is_authenticated() is True
    assert sesion.usuario_actual() == usuario


def test_cerrar_sesion_deja_de_estar_autenticada(sesion, usuario):
    sesion.iniciar_sesion(usuario)

    sesion.cerrar_sesion()

    assert sesion.is_authenticated() is False


def test_cerrar_sesion_dos_veces_no_falla(sesion, usuario):
    sesion.iniciar_sesion(usuario)

    sesion.cerrar_sesion()
    sesion.cerrar_sesion()

    assert sesion.is_authenticated() is False


def test_cerrar_sesion_sin_haber_iniciado_no_falla(sesion):
    sesion.cerrar_sesion()

    assert sesion.is_authenticated() is False


def test_usuario_actual_sin_sesion_lanza_runtime_error(sesion):
    with pytest.raises(RuntimeError):
        sesion.usuario_actual()


def test_usuario_actual_despues_de_cerrar_sesion_lanza_runtime_error(sesion, usuario):
    sesion.iniciar_sesion(usuario)
    sesion.cerrar_sesion()

    with pytest.raises(RuntimeError):
        sesion.usuario_actual()


def test_iniciar_sesion_con_otro_usuario_reemplaza_al_anterior(sesion, usuario):
    otro = UsuarioDTO(idUsuario=2, nombre="Ayudante", email="ayudante@test.com")
    sesion.iniciar_sesion(usuario)

    sesion.iniciar_sesion(otro)

    assert sesion.usuario_actual() == otro


# ----------------------------------------------------------------------------- club activo (US-106, paso 3)


def test_recien_logueado_no_hay_club_activo(sesion, usuario):
    sesion.iniciar_sesion(usuario)

    assert sesion.club_activo() is None


def test_set_active_club_cambia_el_club_activo(sesion, usuario):
    sesion.iniciar_sesion(usuario)

    sesion.set_active_club(ATENAS)

    assert sesion.club_activo() == ATENAS


def test_set_active_club_sin_sesion_lanza_runtime_error(sesion):
    with pytest.raises(RuntimeError):
        sesion.set_active_club(ATENAS)

    assert sesion.club_activo() is None


def test_cerrar_sesion_olvida_el_club_activo(sesion, usuario):
    sesion.iniciar_sesion(usuario)
    sesion.set_active_club(ATENAS)

    sesion.cerrar_sesion()

    assert sesion.club_activo() is None


def test_iniciar_sesion_con_otro_usuario_no_hereda_el_club_del_anterior(sesion, usuario):
    sesion.iniciar_sesion(usuario)
    sesion.set_active_club(ATENAS)

    sesion.iniciar_sesion(UsuarioDTO(idUsuario=2, nombre="Ayudante", email="ayudante@test.com"))

    assert sesion.club_activo() is None


# ----------------------------------------------------------------------------- "Recordarme" (US-106, paso 4)


def test_iniciar_sesion_con_recordar_guarda_la_sesion_sin_club(sesion, almacen, usuario):
    sesion.iniciar_sesion(usuario, recordar=True)

    almacen.guardar.assert_called_once_with(SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=None))
    almacen.borrar.assert_not_called()


def test_iniciar_sesion_sin_recordar_borra_la_sesion_guardada_antes(sesion, almacen, usuario):
    """AC1: un inicio de sesión sin "Recordarme" no deja recordada una sesión anterior."""
    sesion.iniciar_sesion(usuario)

    almacen.borrar.assert_called_once_with()
    almacen.guardar.assert_not_called()


def test_con_recordar_elegir_club_guarda_la_sesion_con_el_club(sesion, almacen, usuario):
    sesion.iniciar_sesion(usuario, recordar=True)

    sesion.set_active_club(ATENAS)

    assert almacen.guardar.call_args.args == (SessionDTO(usuario_id=1, email="profe@test.com", club_activo_id=7),)


def test_sin_recordar_elegir_club_no_guarda_nada(sesion, almacen, usuario):
    sesion.iniciar_sesion(usuario)

    sesion.set_active_club(ATENAS)

    almacen.guardar.assert_not_called()


def test_cerrar_sesion_borra_la_sesion_guardada(sesion, almacen, usuario):
    sesion.iniciar_sesion(usuario, recordar=True)

    sesion.cerrar_sesion()

    almacen.borrar.assert_called_once_with()


def test_despues_de_cerrar_sesion_un_login_sin_recordar_no_guarda(sesion, almacen, usuario):
    """El "Recordarme" de la sesión anterior no se arrastra a la siguiente."""
    sesion.iniciar_sesion(usuario, recordar=True)
    sesion.cerrar_sesion()
    almacen.reset_mock()

    sesion.iniciar_sesion(usuario)
    sesion.set_active_club(ATENAS)

    almacen.guardar.assert_not_called()
