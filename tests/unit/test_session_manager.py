"""Tests unitarios del SessionManager en memoria (US-105)."""

import pytest

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.servicios.session_manager import SessionManager


@pytest.fixture
def sesion():
    return SessionManager()


@pytest.fixture
def usuario():
    return UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")


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
