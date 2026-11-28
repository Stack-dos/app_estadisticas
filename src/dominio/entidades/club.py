from dataclasses import dataclass

from dominio.exceptions import DatoInvalidoError


@dataclass
class Club:
    nombre: str
    idClub: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del club.
        Raises:
            TypeError: Si el nombre no es una cadena de caracteres.
            TypeError: Si el ID del club no es un entero o None.
            DatoInvalidoError: Si el nombre esta vacio (o son solo espacios).
        """
        if not isinstance(self.nombre, str):
            raise TypeError(f"nombre debe ser str, recibido {type(self.nombre).__name__}")
        if self.idClub is not None and not isinstance(self.idClub, int):
            raise TypeError(f"idClub debe ser int o None, recibido {type(self.idClub).__name__}")
        if not self.nombre.strip():
            raise DatoInvalidoError("El nombre del club no puede estar vacio")


@dataclass
class UsuarioClub:
    rol: str
    idUsuario: int | None = None
    idClub: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del usuario del club.
        Raises:
            TypeError: Si el rol no es una cadena de caracteres.
            TypeError: Si el ID del usuario no es un entero o None.
            TypeError: Si el ID del club no es un entero o None.
        """
        if not isinstance(self.rol, str):
            raise TypeError(f"rol debe ser str, recibido {type(self.rol).__name__}")
        if self.idUsuario is not None and not isinstance(self.idUsuario, int):
            raise TypeError(f"idUsuario debe ser int o None, recibido {type(self.idUsuario).__name__}")
        if self.idClub is not None and not isinstance(self.idClub, int):
            raise TypeError(f"idClub debe ser int o None, recibido {type(self.idClub).__name__}")
