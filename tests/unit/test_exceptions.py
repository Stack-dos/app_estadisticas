"""Tests de las excepciones de dominio (`dominio/exceptions.py`)."""

import inspect

import pytest

from dominio import exceptions
from dominio.exceptions import ClubNoEncontradoError, ErrorDeDominio, JugadorNoEncontradoError


def _excepciones_del_modulo():
    """Todas las clases definidas en dominio/exceptions.py: si mañana se agrega una, entra sola al test."""
    return [
        clase for _, clase in inspect.getmembers(exceptions, inspect.isclass) if clase.__module__ == exceptions.__name__
    ]


EXCEPCIONES_HIJAS = [c for c in _excepciones_del_modulo() if c is not ErrorDeDominio]


def test_error_de_dominio_es_una_excepcion_normal():
    assert issubclass(ErrorDeDominio, Exception)


@pytest.mark.parametrize("excepcion", EXCEPCIONES_HIJAS, ids=lambda c: c.__name__)
def test_toda_excepcion_de_dominio_hereda_de_error_de_dominio(excepcion):
    assert issubclass(excepcion, ErrorDeDominio)


@pytest.mark.parametrize("excepcion", EXCEPCIONES_HIJAS, ids=lambda c: c.__name__)
def test_se_captura_con_la_clase_base_y_conserva_el_mensaje(excepcion):
    # Asi captura la CLI todos los errores de negocio con un unico `except ErrorDeDominio`
    with pytest.raises(ErrorDeDominio) as info:
        raise excepcion("mensaje de prueba")

    assert isinstance(info.value, excepcion)
    assert str(info.value) == "mensaje de prueba"


def test_capturar_una_excepcion_no_captura_a_las_demas():
    with pytest.raises(ClubNoEncontradoError):
        try:
            raise ClubNoEncontradoError("no existe el club")
        except JugadorNoEncontradoError:  # pragma: no cover - no debe entrar aca
            pytest.fail("JugadorNoEncontradoError no deberia capturar a ClubNoEncontradoError")
