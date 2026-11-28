from dataclasses import dataclass


@dataclass
class RegistrarDTO:
    """Entra a RegistrarEntrenadorUseCase.ejecutar()"""

    nombre: str
    email: str
    password: str


@dataclass
class LoginDTO:
    """Entra a LoginLocalUseCase.ejecutar()"""

    email: str
    password: str


@dataclass
class UsuarioDTO:
    """Sale de RegistrarEntrenadorUseCase / LoginLocalUseCase"""

    idUsuario: int
    nombre: str
    email: str

    @property
    def id(self) -> int:
        return self.idUsuario
