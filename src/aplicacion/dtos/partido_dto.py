from dataclasses import dataclass, field


@dataclass
class CuartoDTO:
    """Puntos anotados por un club en un periodo (cuarto o prorroga) del partido."""

    idClub: int
    nroCuarto: int
    puntos: int


@dataclass
class EstadisticaInputDTO:
    """Estadistica individual de un jugador para cargar un partido (entra en BoxscoreDTO)."""

    idJugador: int
    minutosJugados: float = 0.0
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


@dataclass
class BoxscoreDTO:
    """Planilla de estadisticas individuales de un equipo (local o visitante) en un partido."""

    idClub: int
    estadisticas: list[EstadisticaInputDTO] = field(default_factory=list)


@dataclass
class PartidoDTO:
    """Entra en CargarPartidoUseCase: datos del partido y, opcionalmente, los puntos por cuarto."""

    fecha: str
    idCompetencia: int
    idCategoria: int
    idClubLocal: int
    idClubVisitante: int
    estadio: str | None = None
    cuartos: list[CuartoDTO] = field(default_factory=list)
    idPartido: int | None = None


@dataclass
class PartidoResumenDTO:
    """Sale de ListarPartidosPorClubUseCase: un partido con los NOMBRES de la competencia y de los clubes"""

    idPartido: int
    fecha: str
    estadio: str | None
    competencia: str
    anioCompetencia: int
    clubLocal: str
    clubVisitante: str
    categoria: str | None = None


@dataclass
class BoxscoreFilaDTO:
    """Sale de ObtenerBoxscorePartidoUseCase: estadistica individual de un jugador en un partido."""

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
