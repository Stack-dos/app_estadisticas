"""Tests de la pantalla de registro (US-105, AC2) sin ventana.

`page` y los casos de uso son mocks; los campos se cargan a mano (`campo.value = ...`) y el handler
se llama directo (`boton.on_click()`), como haria Flet al recibir el clic.
"""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, etiqueta_error

from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import RegistrarDTO, UsuarioDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError, EmailYaRegistradoError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.registro_screen import crear_registro_view

USUARIO = UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def registrar_uc():
    uc = MagicMock(spec=RegistrarEntrenadorUseCase)
    uc.ejecutar.return_value = USUARIO
    return uc


@pytest.fixture
def sesion():
    return SessionManager()


@pytest.fixture
def vista(page, registrar_uc, sesion):
    vista = crear_registro_view(page, registrar_uc, sesion)
    campo(vista, "Nombre").value = "Profesor"
    campo(vista, "Email").value = "profe@test.com"
    campo(vista, "Contraseña").value = "secreta123"
    return vista


def test_la_contrasenia_se_muestra_oculta(vista):
    assert campo(vista, "Contraseña").password is True


def test_registro_exitoso_inicia_sesion_y_navega_al_inicio(vista, page, registrar_uc, sesion):
    boton(vista, "Registrarme").on_click()

    registrar_uc.ejecutar.assert_called_once_with(
        RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123")
    )
    assert sesion.usuario_actual() == USUARIO
    page.navigate.assert_called_once_with("/inicio")
    assert etiqueta_error(vista).value == ""


def test_enter_en_la_contrasenia_registra_igual_que_el_boton(vista, page, registrar_uc):
    campo(vista, "Contraseña").on_submit()

    registrar_uc.ejecutar.assert_called_once()
    page.navigate.assert_called_once_with("/inicio")


@pytest.mark.parametrize(
    "error",
    [
        EmailYaRegistradoError("El email 'profe@test.com' ya esta registrado"),
        DatoInvalidoError("La contraseña debe tener al menos 8 caracteres"),
    ],
)
def test_error_de_dominio_se_muestra_y_no_navega(vista, page, registrar_uc, sesion, error):
    registrar_uc.ejecutar.side_effect = error

    boton(vista, "Registrarme").on_click()

    assert etiqueta_error(vista).value == str(error)
    assert sesion.is_authenticated() is False
    page.navigate.assert_not_called()
    page.update.assert_called_once()


def test_error_inesperado_muestra_mensaje_generico_y_no_navega(vista, page, registrar_uc):
    registrar_uc.ejecutar.side_effect = RuntimeError("bug")

    boton(vista, "Registrarme").on_click()

    assert etiqueta_error(vista).value == MENSAJE_ERROR_INESPERADO
    page.navigate.assert_not_called()


def test_si_el_caso_de_uso_devuelve_none_no_inicia_sesion_ni_navega(vista, page, registrar_uc, sesion):
    registrar_uc.ejecutar.return_value = None

    boton(vista, "Registrarme").on_click()

    assert etiqueta_error(vista).value == MENSAJE_ERROR_INESPERADO
    assert sesion.is_authenticated() is False
    page.navigate.assert_not_called()
