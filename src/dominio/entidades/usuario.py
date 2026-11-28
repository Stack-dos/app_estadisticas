import re
from dataclasses import dataclass

from dominio.exceptions import DatoInvalidoError

# Chequeo minimo de forma (algo@algo.algo, sin espacios): no pretende validar que el email exista
_FORMATO_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def normalizar_email(email: str) -> str:
    """
    Devuelve el email sin espacios en los extremos y en minusculas.

    El UNIQUE de la tabla `usuario` distingue mayusculas: sin esto "Nico@x.com" y "nico@x.com" serian
    dos cuentas distintas. Hay que usarla tambien antes de buscar un usuario por email.

    Args:
        email (str): Email tal como lo ingreso el usuario.

    Returns:
        str: El email normalizado.
    """
    return email.strip().lower()


@dataclass
class Usuario:
    nombre: str
    email: str
    password_hash: str
    idUsuario: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del usuario. El email queda guardado normalizado
        (sin espacios en los extremos y en minusculas).
        Raises:
            TypeError: Si el nombre no es una cadena de caracteres.
            TypeError: Si el email no es una cadena de caracteres.
            TypeError: Si el hash del password no es una cadena de caracteres.
            TypeError: Si el ID del usuario no es un entero o None.
            DatoInvalidoError: Si el nombre esta vacio (o son solo espacios).
            DatoInvalidoError: Si el email esta vacio o no tiene forma de email.
        """
        if not isinstance(self.nombre, str):
            raise TypeError(f"nombre debe ser str, recibido {type(self.nombre).__name__}")
        if not isinstance(self.email, str):
            raise TypeError(f"Email debe ser str, recibido {type(self.email).__name__}")
        if not isinstance(self.password_hash, str):
            raise TypeError(f"password_hash debe ser str, recibido {type(self.password_hash).__name__}")
        if self.idUsuario is not None and not isinstance(self.idUsuario, int):
            raise TypeError(f"idUsuario debe ser int o None, recibido {type(self.idUsuario).__name__}")
        if not self.nombre.strip():
            raise DatoInvalidoError("El nombre del usuario no puede estar vacio")
        self.email = normalizar_email(self.email)
        if not self.email:
            raise DatoInvalidoError("El email del usuario no puede estar vacio")
        if not _FORMATO_EMAIL.fullmatch(self.email):
            raise DatoInvalidoError(f"El email '{self.email}' no tiene un formato valido")
