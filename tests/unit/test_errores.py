"""Tests del manejador comun de errores de la GUI (US-105). Usan un ft.Text suelto, sin ventana."""

import logging

import pytest

from dominio.exceptions import CredencialesInvalidasError, EmailYaRegistradoError
from infraestructura.ui.flet.errores import (
    MENSAJE_ERROR_INESPERADO,
    crear_etiqueta_error,
    ejecutar_mostrando_errores,
)


@pytest.fixture
def etiqueta():
    return crear_etiqueta_error()


def _lanzar(excepcion: Exception):
    def accion() -> None:
        raise excepcion

    return accion


def test_accion_exitosa_se_ejecuta_y_deja_la_etiqueta_vacia(etiqueta):
    llamadas = []

    ejecutar_mostrando_errores(lambda: llamadas.append(1), etiqueta)

    assert llamadas == [1]
    assert etiqueta.value == ""


def test_error_de_dominio_muestra_su_mensaje(etiqueta):
    ejecutar_mostrando_errores(_lanzar(EmailYaRegistradoError("El email 'a@b.com' ya esta registrado")), etiqueta)

    assert etiqueta.value == "El email 'a@b.com' ya esta registrado"


def test_error_de_dominio_queda_en_el_log_como_warning(etiqueta, caplog):
    with caplog.at_level(logging.WARNING):
        ejecutar_mostrando_errores(_lanzar(CredencialesInvalidasError("Email o contraseña incorrectos")), etiqueta)

    assert any(r.levelno == logging.WARNING and "incorrectos" in r.getMessage() for r in caplog.records)


def test_error_inesperado_muestra_mensaje_generico_sin_detalles(etiqueta):
    ejecutar_mostrando_errores(_lanzar(RuntimeError("detalle interno: tabla usuario")), etiqueta)

    assert etiqueta.value == MENSAJE_ERROR_INESPERADO
    assert "tabla usuario" not in etiqueta.value


def test_error_inesperado_deja_el_traceback_en_el_log(etiqueta, caplog):
    with caplog.at_level(logging.ERROR):
        ejecutar_mostrando_errores(_lanzar(RuntimeError("bug")), etiqueta)

    registro = next(r for r in caplog.records if r.levelno == logging.ERROR)
    assert registro.exc_info is not None


def test_un_reintento_exitoso_borra_el_error_anterior(etiqueta):
    ejecutar_mostrando_errores(_lanzar(EmailYaRegistradoError("repetido")), etiqueta)

    ejecutar_mostrando_errores(lambda: None, etiqueta)

    assert etiqueta.value == ""


def test_la_contrasenia_de_la_accion_no_llega_al_log(etiqueta, caplog):
    password = "secreta123"

    def accion() -> None:
        _ = password  # la accion usa la contraseña, pero el manejador solo loguea la excepcion
        raise CredencialesInvalidasError("Email o contraseña incorrectos")

    with caplog.at_level(logging.DEBUG):
        ejecutar_mostrando_errores(accion, etiqueta)

    assert password not in caplog.text
