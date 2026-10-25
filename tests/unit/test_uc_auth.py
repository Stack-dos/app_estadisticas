"""Tests unitarios de los casos de uso de autenticacion (US-104), con mocks de repositorio y hasher."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import LoginDTO, RegistrarDTO, UsuarioDTO
from dominio.entidades.usuario import Usuario
from dominio.exceptions import CredencialesInvalidasError, DatoInvalidoError, EmailYaRegistradoError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher


@pytest.fixture
def repo_usuario():
    return MagicMock(spec=UsuarioRepositorio)


@pytest.fixture
def hasher():
    return MagicMock(spec=PasswordHasher)


# ----------------------------------------------------------------------------- RegistrarEntrenadorUseCase


def test_registrar_entrenador_exitoso_devuelve_dto_y_hashea_contrasenia(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = None
    hasher.hash.return_value = "pbkdf2_sha256$1000$salt$hash"
    repo_usuario.guardar.return_value = Usuario(
        nombre="Profesor",
        email="profe@test.com",
        password_hash="pbkdf2_sha256$1000$salt$hash",
        idUsuario=1,
    )

    dto = RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123")
    resultado = RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    assert resultado == UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")
    repo_usuario.encontrar_por_mail.assert_called_once_with("profe@test.com")
    hasher.hash.assert_called_once_with("secreta123")

    guardado = repo_usuario.guardar.call_args.args[0]
    assert guardado.nombre == "Profesor"
    assert guardado.email == "profe@test.com"
    assert guardado.password_hash == "pbkdf2_sha256$1000$salt$hash"
    assert "secreta123" not in guardado.password_hash


@pytest.mark.parametrize("password_corta", ["", "1", "12", "123", "1234", "12345"])
def test_registrar_entrenador_con_password_corta_lanza_dato_invalido_y_no_guarda(repo_usuario, hasher, password_corta):
    dto = RegistrarDTO(nombre="Profesor", email="profe@test.com", password=password_corta)

    with pytest.raises(DatoInvalidoError, match="al menos 6 caracteres"):
        RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    repo_usuario.encontrar_por_mail.assert_not_called()
    hasher.hash.assert_not_called()
    repo_usuario.guardar.assert_not_called()


def test_registrar_entrenador_con_email_duplicado_lanza_email_ya_registrado(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = Usuario("Existente", "profe@test.com", "hash", idUsuario=9)
    dto = RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123")

    with pytest.raises(EmailYaRegistradoError, match="ya esta registrado"):
        RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    hasher.hash.assert_not_called()
    repo_usuario.guardar.assert_not_called()


def test_registrar_entrenador_normaliza_email_antes_de_buscar_y_guardar(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = None
    hasher.hash.return_value = "hash123"
    repo_usuario.guardar.return_value = Usuario(
        nombre="Profesor",
        email="profe@test.com",
        password_hash="hash123",
        idUsuario=1,
    )

    dto = RegistrarDTO(nombre="Profesor", email="  Profe@Test.COM  ", password="secreta123")
    resultado = RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    assert resultado == UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com")
    repo_usuario.encontrar_por_mail.assert_called_once_with("profe@test.com")


@pytest.mark.parametrize(
    "nombre, email",
    [
        ("", "profe@test.com"),
        ("   ", "profe@test.com"),
        ("Profesor", ""),
        ("Profesor", "email_invalido"),
        ("Profesor", "sin_arroba.com"),
    ],
)
def test_registrar_entrenador_con_datos_invalidos_lanza_dato_invalido(repo_usuario, hasher, nombre, email):
    dto = RegistrarDTO(nombre=nombre, email=email, password="secreta123")

    with pytest.raises(DatoInvalidoError):
        RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    hasher.hash.assert_not_called()
    repo_usuario.guardar.assert_not_called()


@pytest.mark.parametrize(
    "dto",
    [
        RegistrarDTO(nombre=None, email="profe@test.com", password="secreta123"),  # type: ignore[arg-type]
        RegistrarDTO(nombre="Profesor", email=None, password="secreta123"),  # type: ignore[arg-type]
        RegistrarDTO(nombre="Profesor", email="profe@test.com", password=None),  # type: ignore[arg-type]
    ],
)
def test_registrar_entrenador_con_tipos_invalidos_lanza_type_error(repo_usuario, hasher, dto):
    with pytest.raises(TypeError):
        RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)


def test_registrar_entrenador_devuelve_none_si_repo_no_pudo_guardar(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = None
    hasher.hash.return_value = "hash123"
    repo_usuario.guardar.return_value = None

    dto = RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123")
    resultado = RegistrarEntrenadorUseCase(repo_usuario, hasher).ejecutar(dto)

    assert resultado is None


# ----------------------------------------------------------------------------- LoginLocalUseCase


def test_login_local_exitoso_devuelve_dto(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = Usuario(
        nombre="Profesor",
        email="profe@test.com",
        password_hash="hash_guardado",
        idUsuario=5,
    )
    hasher.verify.return_value = True

    dto = LoginDTO(email="profe@test.com", password="secreta123")
    resultado = LoginLocalUseCase(repo_usuario, hasher).ejecutar(dto)

    assert resultado == UsuarioDTO(idUsuario=5, nombre="Profesor", email="profe@test.com")
    repo_usuario.encontrar_por_mail.assert_called_once_with("profe@test.com")
    hasher.verify.assert_called_once_with("secreta123", "hash_guardado")


def test_login_local_con_email_inexistente_lanza_credenciales_invalidas(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = None

    dto = LoginDTO(email="nadie@test.com", password="secreta123")

    with pytest.raises(CredencialesInvalidasError, match="Email o contraseña incorrectos"):
        LoginLocalUseCase(repo_usuario, hasher).ejecutar(dto)

    hasher.verify.assert_not_called()


def test_login_local_con_password_incorrecta_lanza_credenciales_invalidas(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = Usuario(
        nombre="Profesor",
        email="profe@test.com",
        password_hash="hash_guardado",
        idUsuario=5,
    )
    hasher.verify.return_value = False

    dto = LoginDTO(email="profe@test.com", password="password_equivocada")

    with pytest.raises(CredencialesInvalidasError, match="Email o contraseña incorrectos"):
        LoginLocalUseCase(repo_usuario, hasher).ejecutar(dto)


def test_login_local_normaliza_email_antes_de_buscar(repo_usuario, hasher):
    repo_usuario.encontrar_por_mail.return_value = Usuario(
        nombre="Profesor",
        email="profe@test.com",
        password_hash="hash_guardado",
        idUsuario=5,
    )
    hasher.verify.return_value = True

    dto = LoginDTO(email="  PROFE@Test.COM  ", password="secreta123")
    LoginLocalUseCase(repo_usuario, hasher).ejecutar(dto)

    repo_usuario.encontrar_por_mail.assert_called_once_with("profe@test.com")


@pytest.mark.parametrize(
    "dto",
    [
        LoginDTO(email=None, password="secreta123"),  # type: ignore[arg-type]
        LoginDTO(email="profe@test.com", password=None),  # type: ignore[arg-type]
    ],
)
def test_login_local_con_tipos_invalidos_lanza_type_error(repo_usuario, hasher, dto):
    with pytest.raises(TypeError):
        LoginLocalUseCase(repo_usuario, hasher).ejecutar(dto)
