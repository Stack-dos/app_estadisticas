"""Tests de la pantalla de login (US-105, AC2 y AC4) sin ventana, con `page` y caso de uso mockeados."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, etiqueta_error

from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.dtos.auth_dto import LoginDTO, UsuarioDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import CredencialesInvalidasError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.login_screen import crear_login_view

USUARIO = UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def login_uc():
    uc = MagicMock(spec=LoginLocalUseCase)
    uc.ejecutar.return_value = USUARIO
    return uc


@pytest.fixture
def sesion():
    return SessionManager(MagicMock(spec=SesionAlmacen))


@pytest.fixture
def vista(page, login_uc, sesion):
    vista = crear_login_view(page, login_uc, sesion)
    campo(vista, "Email").value = "profe@test.com"
    campo(vista, "Contraseña").value = "secreta123"
    return vista


def test_la_contrasenia_se_muestra_oculta(vista):
    assert campo(vista, "Contraseña").password is True


def test_login_exitoso_inicia_sesion_y_navega_al_inicio(vista, page, login_uc, sesion):
    boton(vista, "Ingresar").on_click()

    login_uc.ejecutar.assert_called_once_with(LoginDTO(email="profe@test.com", password="secreta123"))
    assert sesion.usuario_actual() == USUARIO
    page.navigate.assert_called_once_with("/inicio")
    assert etiqueta_error(vista).value == ""


def test_enter_en_la_contrasenia_ingresa_igual_que_el_boton(vista, page, login_uc):
    campo(vista, "Contraseña").on_submit()

    login_uc.ejecutar.assert_called_once()
    page.navigate.assert_called_once_with("/inicio")


def test_credenciales_invalidas_muestran_el_mensaje_generico_y_no_navega(vista, page, login_uc, sesion):
    login_uc.ejecutar.side_effect = CredencialesInvalidasError("Email o contraseña incorrectos")

    boton(vista, "Ingresar").on_click()

    assert etiqueta_error(vista).value == "Email o contraseña incorrectos"
    assert sesion.is_authenticated() is False
    page.navigate.assert_not_called()


def test_error_inesperado_muestra_mensaje_generico_y_no_navega(vista, page, login_uc):
    login_uc.ejecutar.side_effect = RuntimeError("bug")

    boton(vista, "Ingresar").on_click()

    assert etiqueta_error(vista).value == MENSAJE_ERROR_INESPERADO
    page.navigate.assert_not_called()


def test_crear_cuenta_navega_al_registro(vista, page):
    boton(vista, "Crear cuenta").on_click()

    page.navigate.assert_called_once_with("/registro")
