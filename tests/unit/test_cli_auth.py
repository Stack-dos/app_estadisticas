"""Tests unitarios de los comandos CLI de autenticacion (`infraestructura/ui/cli/commands/auth_*.py`)."""

import argparse
from unittest.mock import MagicMock

import pytest

from dominio.entidades.usuario import Usuario
from dominio.exceptions import CredencialesInvalidasError, DatoInvalidoError, EmailYaRegistradoError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.ui.cli.commands import auth_login, auth_logout, auth_register


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _repo(**config) -> MagicMock:
    repo = MagicMock(spec=UsuarioRepositorio)
    repo.configure_mock(**config)
    return repo


def _hasher(**config) -> MagicMock:
    hasher = MagicMock(spec=PasswordHasher)
    hasher.configure_mock(**config)
    return hasher


# ----------------------------------------------------------------------------- auth register


def test_auth_register_informa_el_usuario_registrado(capsys):
    repo = _repo(**{"encontrar_por_mail.return_value": None})
    repo.guardar.return_value = Usuario("Profesor", "profe@test.com", "hash", idUsuario=1)
    hasher = _hasher(**{"hash.return_value": "hash"})

    args = _args(nombre="Profesor", email="profe@test.com", password="secreta123")
    auth_register.ejecutar(args, repo=repo, hasher=hasher)

    salida = capsys.readouterr().out
    assert salida == "Usuario registrado: Profesor (profe@test.com) (id=1)\n"


def test_auth_register_falla_guardado_aborta(capsys):
    repo = _repo(**{"encontrar_por_mail.return_value": None, "guardar.return_value": None})
    hasher = _hasher(**{"hash.return_value": "hash"})

    args = _args(nombre="Profesor", email="profe@test.com", password="secreta123")
    with pytest.raises(SystemExit) as info:
        auth_register.ejecutar(args, repo=repo, hasher=hasher)

    assert info.value.code == 1
    assert "Error: no se pudo registrar el usuario" in capsys.readouterr().err


def test_auth_register_no_atrapa_error_de_dominio():
    repo = _repo(**{"encontrar_por_mail.return_value": Usuario("Existente", "profe@test.com", "hash", idUsuario=1)})
    hasher = _hasher()

    args = _args(nombre="Profesor", email="profe@test.com", password="secreta123")
    with pytest.raises(EmailYaRegistradoError):
        auth_register.ejecutar(args, repo=repo, hasher=hasher)


def test_auth_register_password_corta_lanza_error_de_dominio():
    repo = _repo()
    hasher = _hasher()

    args = _args(nombre="Profesor", email="profe@test.com", password="123")
    with pytest.raises(DatoInvalidoError):
        auth_register.ejecutar(args, repo=repo, hasher=hasher)


# ----------------------------------------------------------------------------- auth login


def test_auth_login_informa_inicio_exitoso(capsys):
    repo = _repo(**{"encontrar_por_mail.return_value": Usuario("Profesor", "profe@test.com", "hash", idUsuario=1)})
    hasher = _hasher(**{"verify.return_value": True})

    args = _args(email="profe@test.com", password="secreta123")
    auth_login.ejecutar(args, repo=repo, hasher=hasher)

    salida = capsys.readouterr().out
    assert salida == "Inicio de sesion exitoso: Profesor (profe@test.com)\n"


def test_auth_login_credenciales_invalidas_no_se_atrapan():
    repo = _repo(**{"encontrar_por_mail.return_value": None})
    hasher = _hasher()

    args = _args(email="profe@test.com", password="password_incorrecta")
    with pytest.raises(CredencialesInvalidasError):
        auth_login.ejecutar(args, repo=repo, hasher=hasher)


# ----------------------------------------------------------------------------- auth logout


def test_auth_logout_informa_que_no_hay_sesion(capsys):
    args = _args()
    auth_logout.ejecutar(args)

    salida = capsys.readouterr().out
    assert "no hay sesión que cerrar" in salida.lower()
