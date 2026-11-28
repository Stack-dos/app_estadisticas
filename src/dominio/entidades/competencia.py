from dataclasses import dataclass

from dominio.exceptions import DatoInvalidoError


@dataclass
class Competencia:
    nombre: str
    anio: int
    tipo: str | None = None
    idCompetencia: int | None = None

    def __post_init__(self) -> None:
        """Funcion que valida los tipos de los atributos de la clase Competencia
        Raises:
            TypeError: Si algún atributo no es del tipo esperado.
            TypeError: Si el año no es un entero.
            TypeError: Si el tipo no es una cadena de caracteres o None.
            TypeError: Si el ID de la competencia no es un entero o None.
            DatoInvalidoError: Si el nombre esta vacio.
            DatoInvalidoError: Si el año es menor o igual que 1900 (mismo criterio que el CHECK del schema).
        """
        if not isinstance(self.nombre, str):
            raise TypeError(f"nombre debe ser str, recibido {type(self.nombre).__name__}")
        if not isinstance(self.anio, int):
            raise TypeError(f"anio debe ser int, recibido {type(self.anio).__name__}")
        if self.tipo is not None and not isinstance(self.tipo, str):
            raise TypeError(f"tipo debe ser str o None, recibido {type(self.tipo).__name__}")
        if self.idCompetencia is not None and not isinstance(self.idCompetencia, int):
            raise TypeError(f"idCompetencia debe ser int o None, recibido {type(self.idCompetencia).__name__}")
        if not self.nombre.strip():
            raise DatoInvalidoError("El nombre de la competencia no puede estar vacio")
        if self.anio <= 1900:
            raise DatoInvalidoError(f"Año debe ser mayor que 1900 - Valor actual: {self.anio}")


@dataclass
class Categoria:
    nombre: str
    idCategoria: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que valida los tipos de los atributos de la clase Categoria
        Raises:
            TypeError: Si el nombre no es una cadena de caracteres.
            TypeError: Si el ID de la categoria no es un entero o None.
            DatoInvalidoError: Si el nombre esta vacio.
        """
        if not isinstance(self.nombre, str):
            raise TypeError(f"nombre debe ser str, recibido {type(self.nombre).__name__}")
        if self.idCategoria is not None and not isinstance(self.idCategoria, int):
            raise TypeError(f"idCategoria debe ser int o None, recibido {type(self.idCategoria).__name__}")
        if not self.nombre.strip():
            raise DatoInvalidoError("El nombre de la categoria no puede estar vacio")


@dataclass
class Inscripcion:
    idClub: int
    idCategoria: int
    idCompetencia: int
    idInscripcion: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que valida los tipos de los atributos de la clase Inscripcion
        Raises:
            TypeError: Si el ID del club no es un entero.
            TypeError: Si el ID de la categoria no es un entero.
            TypeError: Si el ID de la competencia no es un entero.
            TypeError: Si el ID de la inscripcion no es un entero o None.
        """
        if not isinstance(self.idClub, int):
            raise TypeError(f"idClub debe ser int, recibido {type(self.idClub).__name__}")
        if not isinstance(self.idCategoria, int):
            raise TypeError(f"idCategoria debe ser int, recibido {type(self.idCategoria).__name__}")
        if not isinstance(self.idCompetencia, int):
            raise TypeError(f"idCompetencia debe ser int, recibido {type(self.idCompetencia).__name__}")
        if self.idInscripcion is not None and not isinstance(self.idInscripcion, int):
            raise TypeError(f"idInscripcion debe ser int o None, recibido {type(self.idInscripcion).__name__}")


@dataclass
class ListaBuenaFe:
    fechaPresentacion: str
    idInscripcion: int
    idListaBuenaFe: int | None = None

    def __post_init__(self) -> None:
        """Funcion que valida los tipos de los atributos de la clase ListaBuenaFe

        Raises:
            TypeError: Si la fecha de presentacion no es una cadena de caracteres.
            TypeError: Si el ID de la inscripcion no es un entero.
            TypeError: Si el ID de la lista de buena fe no es un entero o None.
        """
        if not isinstance(self.fechaPresentacion, str):
            raise TypeError(f"fechaPresentacion debe ser str, recibido {type(self.fechaPresentacion).__name__}")
        if not isinstance(self.idInscripcion, int):
            raise TypeError(f"idInscripcion debe ser int, recibido {type(self.idInscripcion).__name__}")
        if self.idListaBuenaFe is not None and not isinstance(self.idListaBuenaFe, int):
            raise TypeError(f"idListaBuenaFe debe ser int o None, recibido {type(self.idListaBuenaFe).__name__}")


@dataclass
class JugadorListaBuenaFe:
    idJugador: int
    idListaBuenaFe: int

    """Clase que representa un jugador en una lista de buena fe."""

    def __post_init__(self) -> None:
        """Funcion que valida los tipos de los atributos de la clase JugadorListaBuenaFe.
        Raises:
            TypeError: Si algún atributo no es del tipo esperado.
            TypeError: Si el ID del jugador no es un entero.
            TypeError: Si el ID de la lista de buena fe no es un entero.
        """
        if not isinstance(self.idJugador, int):
            raise TypeError(f"idJugador debe ser int, recibido {type(self.idJugador).__name__}")
        if not isinstance(self.idListaBuenaFe, int):
            raise TypeError(f"idListaBuenaFe debe ser int, recibido {type(self.idListaBuenaFe).__name__}")
