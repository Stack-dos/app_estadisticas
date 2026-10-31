"""Tests de integracion del flujo completo de autenticacion (US-104) sobre SQLite (:memory:).

Valida que el registro y el login funcionen de punta a punta con repositorios reales,
que las contraseñas nunca se guarden en texto plano y que se use salt dinamico con PBKDF2.
"""

import pytest

from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import LoginDTO, RegistrarDTO
from dominio.exceptions import CredencialesInvalidasError, DatoInvalidoError, EmailYaRegistradoError
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher

ITERACIONES_RAPIDAS = 1_000


@pytest.fixture
def hasher_test():
    return Pbkdf2PasswordHasher(iteraciones=ITERACIONES_RAPIDAS)


def test_flujo_completo_registro_y_login_valida_hashing_y_salt_dinamico(db_conexion, hasher_test):
    repo = SqliteUsuarioRepositorio(db_conexion)
    uc_registro = RegistrarEntrenadorUseCase(repo, hasher_test)
    uc_login = LoginLocalUseCase(repo, hasher_test)

    password_plana = "SpursChamp2014"
    dto_registro = RegistrarDTO(nombre="Gregg Popovich", email="pop@spurs.com", password=password_plana)

    # 1. Registro exitoso
    usuario_creado = uc_registro.ejecutar(dto_registro)
    assert usuario_creado is not None
    assert usuario_creado.idUsuario is not None
    assert usuario_creado.nombre == "Gregg Popovich"
    assert usuario_creado.email == "pop@spurs.com"

    # 2. Validacion en base de datos real: NUNCA en texto plano, formato PBKDF2 con salt
    cursor = db_conexion.cursor()
    cursor.execute("SELECT email, contrasenia FROM usuario WHERE idUsuario = ?", (usuario_creado.idUsuario,))
    fila = cursor.fetchone()
    assert fila is not None
    assert fila["email"] == "pop@spurs.com"

    hash_almacenado = fila["contrasenia"]
    assert password_plana not in hash_almacenado
    assert hash_almacenado.startswith(f"pbkdf2_sha256${ITERACIONES_RAPIDAS}$")
    partes = hash_almacenado.split("$")
    assert len(partes) == 4
    algoritmo, iters, salt, derivado = partes
    assert algoritmo == "pbkdf2_sha256"
    assert iters == str(ITERACIONES_RAPIDAS)
    assert len(salt) > 0
    assert len(derivado) > 0

    # 3. Login exitoso con credenciales correctas
    dto_login = LoginDTO(email="pop@spurs.com", password=password_plana)
    usuario_logueado = uc_login.ejecutar(dto_login)
    assert usuario_logueado.idUsuario == usuario_creado.idUsuario
    assert usuario_logueado.nombre == "Gregg Popovich"
    assert usuario_logueado.email == "pop@spurs.com"

    # 4. Login fallido por contraseña incorrecta
    with pytest.raises(CredencialesInvalidasError, match="Email o contraseña incorrectos"):
        uc_login.ejecutar(LoginDTO(email="pop@spurs.com", password="password_incorrecta"))

    # 5. Login fallido por email inexistente
    with pytest.raises(CredencialesInvalidasError, match="Email o contraseña incorrectos"):
        uc_login.ejecutar(LoginDTO(email="nadie@spurs.com", password=password_plana))

    # 6. Intento de registro con email duplicado falla
    with pytest.raises(EmailYaRegistradoError):
        uc_registro.ejecutar(RegistrarDTO(nombre="Otro Coach", email="pop@spurs.com", password="otraPassword123"))


def test_dos_usuarios_con_misma_contrasenia_tienen_hashes_distintos_en_bd(db_conexion, hasher_test):
    repo = SqliteUsuarioRepositorio(db_conexion)
    uc_registro = RegistrarEntrenadorUseCase(repo, hasher_test)
    uc_login = LoginLocalUseCase(repo, hasher_test)

    misma_password = "passwordComun123"

    u1 = uc_registro.ejecutar(RegistrarDTO(nombre="Entrenador Uno", email="u1@test.com", password=misma_password))
    u2 = uc_registro.ejecutar(RegistrarDTO(nombre="Entrenador Dos", email="u2@test.com", password=misma_password))

    assert u1 is not None and u2 is not None

    cursor = db_conexion.cursor()
    cursor.execute("SELECT contrasenia FROM usuario WHERE idUsuario = ?", (u1.idUsuario,))
    hash_u1 = cursor.fetchone()["contrasenia"]

    cursor.execute("SELECT contrasenia FROM usuario WHERE idUsuario = ?", (u2.idUsuario,))
    hash_u2 = cursor.fetchone()["contrasenia"]

    # El salt dinamico garantiza que dos hashes de la misma contraseña difieran
    assert hash_u1 != hash_u2

    # Ambos verifican correctamente su respectivo hash
    assert uc_login.ejecutar(LoginDTO(email="u1@test.com", password=misma_password)).idUsuario == u1.idUsuario
    assert uc_login.ejecutar(LoginDTO(email="u2@test.com", password=misma_password)).idUsuario == u2.idUsuario


def test_login_con_normalizacion_de_email_en_bd(db_conexion, hasher_test):
    repo = SqliteUsuarioRepositorio(db_conexion)
    uc_registro = RegistrarEntrenadorUseCase(repo, hasher_test)
    uc_login = LoginLocalUseCase(repo, hasher_test)

    uc_registro.ejecutar(RegistrarDTO(nombre="Coach K", email="Coach.K@Duke.EDU", password="DukeBlueDevils1"))

    # Verifica que el email guardado quedó normalizado
    cursor = db_conexion.cursor()
    cursor.execute("SELECT email FROM usuario WHERE email = 'coach.k@duke.edu'")
    assert cursor.fetchone() is not None

    # Login con mayusculas o espacios debe funcionar
    logueado = uc_login.ejecutar(LoginDTO(email="  COACH.K@duke.edu  ", password="DukeBlueDevils1"))
    assert logueado.nombre == "Coach K"
    assert logueado.email == "coach.k@duke.edu"


def test_registro_password_corta_no_persiste_en_base(db_conexion, hasher_test):
    repo = SqliteUsuarioRepositorio(db_conexion)
    uc_registro = RegistrarEntrenadorUseCase(repo, hasher_test)

    with pytest.raises(DatoInvalidoError):
        uc_registro.ejecutar(RegistrarDTO(nombre="Coach", email="coach@test.com", password="12345"))

    cursor = db_conexion.cursor()
    cursor.execute("SELECT COUNT(*) as cant FROM usuario WHERE email = 'coach@test.com'")
    assert cursor.fetchone()["cant"] == 0


def test_flujo_cli_auth_e2e(tmp_path, monkeypatch, capsys):
    import sys

    import config.rutas as rutas
    import main

    db_temporal = tmp_path / "e2e_auth.db"
    monkeypatch.setattr(rutas, "DB_FILE", str(db_temporal))

    def run_cli(*argv):
        monkeypatch.setattr(sys, "argv", ["stats", *argv])
        capsys.readouterr()
        codigo = 0
        try:
            main.main()
        except SystemExit as s:
            codigo = s.code
        capturado = capsys.readouterr()
        return codigo, capturado.out, capturado.err

    # 1. Registro via CLI sin mocks
    cod, out, err = run_cli(
        "auth", "register", "--nombre", "Steve Kerr", "--email", "kerr@warriors.com", "--password", "warriors2022"
    )
    assert cod == 0
    assert out == "Usuario registrado: Steve Kerr (kerr@warriors.com) (id=1)\n"

    # 2. Login via CLI sin mocks
    cod, out, err = run_cli("auth", "login", "--email", "kerr@warriors.com", "--password", "warriors2022")
    assert cod == 0
    assert out == "Inicio de sesion exitoso: Steve Kerr (kerr@warriors.com)\n"

    # 3. Login fallido por contraseña incorrecta
    cod, out, err = run_cli("auth", "login", "--email", "kerr@warriors.com", "--password", "password_invalida")
    assert cod == 1
    assert "Error: Email o contraseña incorrectos" in err

    # 4. Logout
    cod, out, err = run_cli("auth", "logout")
    assert cod == 0
    assert "no hay sesión que cerrar" in out.lower()
