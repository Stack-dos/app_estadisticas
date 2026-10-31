from aplicacion.dtos.auth_dto import RegistrarDTO, UsuarioDTO
from dominio.entidades.usuario import Usuario
from dominio.exceptions import DatoInvalidoError, EmailYaRegistradoError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from dominio.servicios.password_hasher import PasswordHasher
from utils import id_persistido

LONGITUD_MINIMA_PASSWORD = 6


class RegistrarEntrenadorUseCase:
    def __init__(self, repo: UsuarioRepositorio, hasher: PasswordHasher):
        """
        Caso de uso para registrar a un nuevo usuario entrenador.

        Args:
            repo (UsuarioRepositorio): Repositorio de usuarios.
            hasher (PasswordHasher): Servicio de hashing y verificacion de contraseñas.
        """
        self.repo = repo
        self.hasher = hasher

    def ejecutar(self, dto: RegistrarDTO) -> UsuarioDTO | None:
        """
        Registra un entrenador en el sistema tras validar sus datos y hashear la contraseña.

        Args:
            dto (RegistrarDTO): Datos de registro (nombre, email, password).

        Raises:
            TypeError: Si la contraseña, nombre o email no son cadenas de caracteres.
            DatoInvalidoError: Si la contraseña tiene menos de 6 caracteres, el nombre está vacío
                o el email no tiene formato válido.
            EmailYaRegistradoError: Si ya existe un usuario con el mismo email registrado.

        Returns:
            UsuarioDTO | None: DTO del usuario registrado con su ID asignado, o None si no se pudo guardar.
        """
        if not isinstance(dto.password, str):
            raise TypeError(f"password debe ser str, recibido {type(dto.password).__name__}")
        if len(dto.password) < LONGITUD_MINIMA_PASSWORD:
            raise DatoInvalidoError(f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres")

        # Valida nombre y email creando una entidad temporal antes de calcular el hash costoso
        usuario_temp = Usuario(nombre=dto.nombre, email=dto.email, password_hash="dummy")

        if self.repo.encontrar_por_mail(usuario_temp.email) is not None:
            raise EmailYaRegistradoError(f"El email '{usuario_temp.email}' ya esta registrado")

        password_hash = self.hasher.hash(dto.password)
        usuario = Usuario(nombre=usuario_temp.nombre, email=usuario_temp.email, password_hash=password_hash)

        resultado = self.repo.guardar(usuario)
        if resultado is None:
            return None

        return UsuarioDTO(
            idUsuario=id_persistido(resultado.idUsuario, "Usuario"),
            nombre=resultado.nombre,
            email=resultado.email,
        )
