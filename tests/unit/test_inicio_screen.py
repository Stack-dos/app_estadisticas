"""Tests de la pantalla principal (US-105, AC3) sin ventana."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.screens.inicio_screen import crear_inicio_view


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager()
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


def test_saluda_al_usuario_de_la_sesion(page, sesion):
    vista = crear_inicio_view(page, sesion)

    assert any(isinstance(c, ft.Text) and c.value == "Hola, Profesor" for c in vista.controls)


def test_cerrar_sesion_cierra_la_sesion_y_vuelve_al_login(page, sesion):
    vista = crear_inicio_view(page, sesion)

    boton(vista, "Cerrar sesión").on_click()

    assert sesion.is_authenticated() is False
    page.navigate.assert_called_once_with("/login")


def test_sin_sesion_no_se_puede_construir(page):
    # La ruta protegida nunca deberia llegar aca sin sesion: si llega, es un bug y falla fuerte.
    with pytest.raises(RuntimeError):
        crear_inicio_view(page, SessionManager())
