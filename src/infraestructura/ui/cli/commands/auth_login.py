import argparse

from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.dtos.auth_dto import LoginDTO
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.persistencia.database_manager import abrir_conexion
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher


def ejecutar(
    args: argparse.Namespace,
    repo: UsuarioRepositorio | None = None,
    hasher: PasswordHasher | None = None,
) -> None:
    """Comando `auth login`: inicia sesion local con credenciales.

    Args:
        args (argparse.Namespace): Argumentos parseados (email, password).
        repo (UsuarioRepositorio | None): Repositorio a usar. En produccion no se pasa (se arma contra
            SQLite real); en los tests se inyecta uno falso.
        hasher (PasswordHasher | None): Hasher a usar. En produccion no se pasa; en tests se inyecta uno mock.
    """
    if repo is None:
        repo = SqliteUsuarioRepositorio(conexion=abrir_conexion())
    if hasher is None:
        hasher = Pbkdf2PasswordHasher()

    dto = LoginDTO(email=args.email, password=args.password)
    usuario = LoginLocalUseCase(repo, hasher).ejecutar(dto)
    print(f"Inicio de sesion exitoso: {usuario.nombre} ({usuario.email})")
