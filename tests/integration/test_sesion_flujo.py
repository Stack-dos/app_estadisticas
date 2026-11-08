"""Test de integracion del cableado de la GUI (US-105): registro -> login -> sesion, sin ventana.

Usa `construir_dependencias` de `app.py` con SQLite (:memory:) y repositorios reales, asi prueba
el mismo armado que usa la aplicacion.
"""

import pytest

from aplicacion.dtos.auth_dto import LoginDTO, RegistrarDTO
from dominio.exceptions import CredencialesInvalidasError
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.app import construir_dependencias


@pytest.fixture
def deps(db_conexion, tmp_path):
    return construir_dependencias(
        db_conexion, Pbkdf2PasswordHasher(iteraciones=1_000), JsonSesionAlmacen(tmp_path / "session.json")
    )


def test_dependencias_arrancan_sin_sesion(deps):
    assert deps.sesion.is_authenticated() is False


def test_flujo_registro_login_e_inicio_de_sesion(deps):
    deps.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))

    usuario = deps.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="secreta123"))
    deps.sesion.iniciar_sesion(usuario)

    assert deps.sesion.is_authenticated() is True
    assert deps.sesion.usuario_actual().email == "profe@test.com"


def test_cerrar_sesion_despues_del_login(deps):
    deps.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))
    deps.sesion.iniciar_sesion(deps.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="secreta123")))

    deps.sesion.cerrar_sesion()

    assert deps.sesion.is_authenticated() is False


def test_login_con_contrasenia_incorrecta_no_abre_la_sesion(deps):
    """Reemplaza el paso "login fallido" del test e2e de la CLI de auth (borrado en la US-105)."""
    deps.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))

    with pytest.raises(CredencialesInvalidasError, match="Email o contraseña incorrectos"):
        deps.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="otra_clave"))

    assert deps.sesion.is_authenticated() is False
