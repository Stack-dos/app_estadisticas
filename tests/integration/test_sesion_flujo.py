"""Test de integracion del cableado de la GUI (US-105 y US-106): registro -> login -> sesion, sin ventana.

Usa `construir_dependencias` de `app.py` con SQLite (:memory:), repositorios reales y el archivo de
sesion en `tmp_path`, asi prueba el mismo armado que usa la aplicacion. Llamar otra vez a
`construir_dependencias` con la misma base y el mismo archivo simula cerrar y reabrir la app.
"""

import pytest

from aplicacion.dtos.auth_dto import LoginDTO, RegistrarDTO
from dominio.exceptions import CredencialesInvalidasError
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.app import construir_dependencias


@pytest.fixture
def abrir_app(db_conexion, tmp_path):
    """Cada llamada simula abrir la app: mismas base y archivo de sesion, objetos nuevos."""
    return lambda: construir_dependencias(
        db_conexion, Pbkdf2PasswordHasher(iteraciones=1_000), JsonSesionAlmacen(tmp_path / "session.json")
    )


@pytest.fixture
def deps(abrir_app):
    return abrir_app()


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


def test_con_recordarme_al_reabrir_la_app_la_sesion_sigue_abierta(abrir_app):
    deps = abrir_app()
    deps.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))
    deps.sesion.iniciar_sesion(
        deps.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="secreta123")), recordar=True
    )

    reabierta = abrir_app()

    assert reabierta.sesion.usuario_actual().email == "profe@test.com"


def test_sin_recordarme_al_reabrir_la_app_hay_que_loguearse(abrir_app):
    deps = abrir_app()
    deps.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))
    deps.sesion.iniciar_sesion(deps.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="secreta123")))

    assert abrir_app().sesion.is_authenticated() is False
