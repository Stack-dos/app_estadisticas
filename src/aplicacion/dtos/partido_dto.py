from dataclasses import dataclass


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
