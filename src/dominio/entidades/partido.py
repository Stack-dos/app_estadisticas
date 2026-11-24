from dataclasses import dataclass

from dominio.exceptions import DatoInvalidoError


@dataclass
class PartidoResumen:
    """Vista de lectura de un partido, con los nombres (no los ids) de la competencia y de los clubes.

    Es lo que devuelve el repositorio a partir de la vista SQL `v_partidos_resumen`: sirve para mostrar
    listados. No se construye para guardar (para eso esta `Partido`), por eso no valida sus campos.
    """

    idPartido: int
    fecha: str
    estadio: str | None
    competencia: str
    anioCompetencia: int
    clubLocal: str
    clubVisitante: str
    categoria: str | None = None


@dataclass
class BoxscoreFila:
    """Vista de lectura de una fila del boxscore de un partido, con nombres de jugador y club.

    Es lo que devuelve el repositorio a partir de la vista SQL `v_boxscore_completo`: sirve para
    mostrar el detalle estadistico de un partido. No se construye para guardar (para eso esta
    `JugadorPartido`), por eso no valida sus campos.
    """

    idPartido: int
    idJugador: int
    idClub: int
    nombreJugador: str
    nombreClub: str
    minutosJugados: float
    puntos: int
    t2c: int
    t2l: int
    t3c: int
    t3l: int
    t1c: int
    t1l: int
    rebotesDef: int
    rebotesOf: int
    rebotesTotales: int
    asistencias: int
    recuperos: int
    perdidas: int
    taponesRecibidos: int
    taponesRealizados: int
    faltasRecibidas: int
    faltasCometidas: int


@dataclass
class Partido:
    fecha: str
    estadio: str | None
    idCompetencia: int
    idClubLocal: int
    idClubVisitante: int
    idPartido: int | None = None

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del partido.
        Raises:
            TypeError: Si la fecha no es una cadena de caracteres.
            TypeError: Si el estadio no es una cadena de caracteres o None.
            TypeError: Si el ID de la competencia no es un entero.
            TypeError: Si el ID del club local no es un entero.
            TypeError: Si el ID del club visitante no es un entero.
            TypeError: Si el ID del partido no es un entero o None.
        """
        if not isinstance(self.fecha, str):
            raise TypeError(f"fecha debe ser str, recibido {type(self.fecha).__name__}")
        if self.estadio is not None and not isinstance(self.estadio, str):
            raise TypeError(f"estadio debe ser str, recibido {type(self.estadio).__name__}")
        if not isinstance(self.idCompetencia, int):
            raise TypeError(f"idCompetencia debe ser int, recibido {type(self.idCompetencia).__name__}")
        if not isinstance(self.idClubLocal, int):
            raise TypeError(f"idClubLocal debe ser int, recibido {type(self.idClubLocal).__name__}")
        if not isinstance(self.idClubVisitante, int):
            raise TypeError(f"idClubVisitante debe ser int, recibido {type(self.idClubVisitante).__name__}")
        if self.idPartido is not None and not isinstance(self.idPartido, int):
            raise TypeError(f"idPartido debe ser int o None, recibido {type(self.idPartido).__name__}")


@dataclass
class JugadorPartido:
    idJugador: int
    idPartido: int
    idClub: int
    minutosJugados: float = 0
    puntos: int = 0
    t2c: int = 0
    t2l: int = 0
    t3c: int = 0
    t3l: int = 0
    t1c: int = 0
    t1l: int = 0
    rebotesDef: int = 0
    rebotesOf: int = 0
    asistencias: int = 0
    recuperos: int = 0
    perdidas: int = 0
    taponesRecibidos: int = 0
    taponesRealizados: int = 0
    faltasRecibidas: int = 0
    faltasCometidas: int = 0

    @property
    def rebotes_totales(self) -> int:
        """Rebotes defensivos + ofensivos (es lo mismo que calcula la vista `v_boxscore_completo`)."""
        return self.rebotesDef + self.rebotesOf

    def __post_init__(self) -> None:
        """
        Funcion que se encarga de validar los datos del jugador del partido.
        Raises:
            TypeError: Si el ID del jugador no es un entero.
            TypeError: Si el ID del partido no es un entero.
            TypeError: Si el ID del club no es un entero.
            TypeError: Si los minutos jugados no son un float.
            DatoInvalidoError: Si los minutos jugados son negativos o mayores a 48.
            DatoInvalidoError: Si los puntos son negativos o distintos de T2C*2 + T3C*3 + T1C.
            DatoInvalidoError: Si T2C es mayor que T2L.
            DatoInvalidoError: Si T3C es mayor que T3L.
            DatoInvalidoError: Si T1C es mayor que T1L.
            DatoInvalidoError: Si los rebotes defensivos son negativos.
            DatoInvalidoError: Si los rebotes ofensivos son negativos.
            DatoInvalidoError: Si las asistencias son negativas.
            DatoInvalidoError: Si los recuperos son negativos.
            DatoInvalidoError: Si las perdidas son negativas.
            DatoInvalidoError: Si los tapones recibidos son negativos.
            DatoInvalidoError: Si los tapones realizados son negativos.
            DatoInvalidoError: Si las faltas recibidas son negativas.
            DatoInvalidoError: Si las faltas cometidas son negativas.

        """
        if not isinstance(self.idJugador, int):
            raise TypeError(f"idJugador debe ser int, recibido {type(self.idJugador).__name__}")
        if not isinstance(self.idPartido, int):
            raise TypeError(f"idPartido debe ser int, recibido {type(self.idPartido).__name__}")
        if not isinstance(self.idClub, int):
            raise TypeError(f"idClub debe ser int, recibido {type(self.idClub).__name__}")
        if self.minutosJugados < 0.0 or self.minutosJugados > 48.0:
            raise DatoInvalidoError(
                f"Minutos Jugados no puede ser menos a 0 o mayor a 48.0 - Valor actual: {self.minutosJugados}"
            )
        if self.puntos < 0 or self.puntos != (self.t2c * 2 + self.t3c * 3 + self.t1c):
            raise DatoInvalidoError(
                f"Puntos no puede ser 0 o distinto de T2C*2 + T3C*3 + T1C - Valor actual {self.puntos}"
            )
        if self.t2c > self.t2l:
            raise DatoInvalidoError(f"T2C ({self.t2c}) no puede ser mayor que T2L ({self.t2l})")
        if self.t3c > self.t3l:
            raise DatoInvalidoError(f"T3C ({self.t3c}) no puede ser mayor que T3L ({self.t3l})")
        if self.t1c > self.t1l:
            raise DatoInvalidoError(f"T1C ({self.t1c}) no puede ser mayor que T1L ({self.t1l})")
        if self.rebotesDef < 0:
            raise DatoInvalidoError(f"Rebotes defensivos no puede ser < 0 - Valor actual: {self.rebotesDef}")
        if self.rebotesOf < 0:
            raise DatoInvalidoError(f"Rebotes ofensivos no puede ser < 0 - Valor actual: {self.rebotesOf}")
        if self.asistencias < 0:
            raise DatoInvalidoError(f"Asistencias no puede ser < 0 - Valor actual: {self.asistencias}")
        if self.recuperos < 0:
            raise DatoInvalidoError(f"Recuperos no puede ser < 0 - Valor actual: {self.recuperos}")
        if self.perdidas < 0:
            raise DatoInvalidoError(f"Perdidas no puede ser < 0 - Valor actual: {self.perdidas}")
        if self.taponesRecibidos < 0:
            raise DatoInvalidoError(f"Tapones Recibidos no puede ser < 0 - Valor actual: {self.taponesRecibidos}")
        if self.taponesRealizados < 0:
            raise DatoInvalidoError(f"Tapones Realizados no puede ser < 0 - Valor actual: {self.taponesRealizados}")
        if self.faltasRecibidas < 0:
            raise DatoInvalidoError(f"Faltas Recibidas no puede ser < 0 - Valor actual: {self.faltasRecibidas}")
        if self.faltasCometidas < 0:
            raise DatoInvalidoError(f"Faltas Cometidas no puede ser < 0 - Valor actual: {self.faltasCometidas}")
