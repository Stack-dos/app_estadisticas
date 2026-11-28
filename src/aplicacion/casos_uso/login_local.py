import logging

from aplicacion.dtos.auth_dto import LoginDTO, UsuarioDTO
from dominio.entidades.usuario import normalizar_email
from dominio.exceptions import CredencialesInvalidasError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher
from utils import id_persistido

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class LoginLocalUseCase:
    def __init__(self, repo: UsuarioRepositorio, hasher: PasswordHasher):
        """
        Caso de uso para autenticar a un usuario de forma local con email y contraseña.

        Args:
            repo (UsuarioRepositorio): Repositorio de usuarios.
            hasher (PasswordHasher): Servicio de hashing y verificacion de contraseñas.
        """
        self.repo = repo
        self.hasher = hasher

    def ejecutar(self, dto: LoginDTO) -> UsuarioDTO:
        """
        Autentica las credenciales de un usuario.

        Args:
            dto (LoginDTO): Datos de login (email, password).

        Raises:
            TypeError: Si el email o password no son cadenas de caracteres.
            CredencialesInvalidasError: Si el usuario no existe o la contraseña no coincide
                (mensaje genérico para no filtrar existencia de emails).

        Returns:
            UsuarioDTO: DTO del usuario autenticado.
        """
        if not isinstance(dto.email, str):
            raise TypeError(f"email debe ser str, recibido {type(dto.email).__name__}")
        if not isinstance(dto.password, str):
            raise TypeError(f"password debe ser str, recibido {type(dto.password).__name__}")

        email_normalizado = normalizar_email(dto.email)
        usuario = self.repo.encontrar_por_mail(email_normalizado)

        if usuario is None or not self.hasher.verify(dto.password, usuario.password_hash):
            # Sin el email: es un dato personal y diria que cuentas existen.
            logger.warning("Login fallido", extra={"evento": "login_fallido"})
            raise CredencialesInvalidasError("Email o contraseña incorrectos")

        logger.info("Login correcto", extra={"evento": "login_ok", "id_usuario": usuario.idUsuario})
        return UsuarioDTO(
            idUsuario=id_persistido(usuario.idUsuario, "Usuario"),
            nombre=usuario.nombre,
            email=usuario.email,
        )
