from dataclasses import dataclass
from datetime import date

from dominio.exceptions import DatoInvalidoError

# Un año de nacimiento valido es mayor a este valor (mismo criterio que el año de una Competencia)
ANIO_MINIMO = 1900


@dataclass
class Jugador:
    nombre: str
    apellido: str
    anioNacimiento: int | None = None
    idJugador: int | None = None

    @property
    def nombre_completo(self) -> str:
        """Nombre y apellido juntos, como se muestran en los listados."""
        return f"{self.nombre} {self.apellido}"

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del jugador.
        Raises:
            TypeError: Si el nombre no es una cadena de caracteres.
            TypeError: Si el apellido no es una cadena de caracteres.
            TypeError: Si el año de nacimiento no es un entero o None.
            TypeError: Si el ID del jugador no es un entero o None.
            DatoInvalidoError: Si el nombre o el apellido estan vacios o si el año de nacimiento
                no esta entre 1901 y el año actual.
        """
        if not isinstance(self.nombre, str):
            raise TypeError(f"nombre debe ser str, recibido {type(self.nombre).__name__}")
        if not isinstance(self.apellido, str):
            raise TypeError(f"apellido debe ser str, recibido {type(self.apellido).__name__}")
        if self.anioNacimiento is not None and not isinstance(self.anioNacimiento, int):
            raise TypeError(f"anioNacimiento debe ser int o None, recibido {type(self.anioNacimiento).__name__}")
        if self.idJugador is not None and not isinstance(self.idJugador, int):
            raise TypeError(f"idJugador debe ser int o None, recibido {type(self.idJugador).__name__}")
        if not self.nombre.strip():
            raise DatoInvalidoError("El nombre del jugador no puede estar vacio")
        if not self.apellido.strip():
            raise DatoInvalidoError("El apellido del jugador no puede estar vacio")
        anio_actual = date.today().year
        if self.anioNacimiento is not None and not ANIO_MINIMO < self.anioNacimiento <= anio_actual:
            raise DatoInvalidoError(
                f"El año de nacimiento debe estar entre {ANIO_MINIMO + 1} y {anio_actual} - "
                f"Valor actual: {self.anioNacimiento}"
            )


@dataclass
class JugadorClub:
    fechaDesde: str
    fechaHasta: str | None
    idJugador: int | None = None
    idClub: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del jugador del club.
        Raises:
            TypeError: Si la fecha desde no es una cadena de caracteres.
            TypeError: Si la fecha hasta no es una cadena de caracteres o None.
            TypeError: Si el ID del jugador no es un entero o None.
            TypeError: Si el ID del club no es un entero o None.
        """
        if not isinstance(self.fechaDesde, str):
            raise TypeError(f"fechaDesde debe ser str, recibido {type(self.fechaDesde).__name__}")
        if self.fechaHasta is not None and not isinstance(self.fechaHasta, str):
            raise TypeError(f"fechaHasta debe ser str o None, recibido {type(self.fechaHasta).__name__}")
        if self.idJugador is not None and not isinstance(self.idJugador, int):
            raise TypeError(f"idJugador debe ser int o None, recibido {type(self.idJugador).__name__}")
        if self.idClub is not None and not isinstance(self.idClub, int):
            raise TypeError(f"idClub debe ser int o None, recibido {type(self.idClub).__name__}")
