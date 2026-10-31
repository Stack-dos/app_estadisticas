import argparse

from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import RegistrarDTO
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.persistencia.database_manager import abrir_conexion
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from utils import abortar


def ejecutar(
    args: argparse.Namespace,
    repo: UsuarioRepositorio | None = None,
    hasher: PasswordHasher | None = None,
) -> None:
    """Comando `auth register`: registra un nuevo usuario entrenador.

    Args:
        args (argparse.Namespace): Argumentos parseados (nombre, email, password).
        repo (UsuarioRepositorio | None): Repositorio a usar. En produccion no se pasa (se arma contra
            SQLite real); en los tests se inyecta uno falso.
        hasher (PasswordHasher | None): Hasher a usar. En produccion no se pasa; en tests se inyecta uno mock.
    """
    if repo is None:
        repo = SqliteUsuarioRepositorio(conexion=abrir_conexion())
    if hasher is None:
        hasher = Pbkdf2PasswordHasher()

    dto = RegistrarDTO(nombre=args.nombre, email=args.email, password=args.password)
    usuario = RegistrarEntrenadorUseCase(repo, hasher).ejecutar(dto)
    if usuario is None:
        abortar("no se pudo registrar el usuario")
    print(f"Usuario registrado: {usuario.nombre} ({usuario.email}) (id={usuario.idUsuario})")
