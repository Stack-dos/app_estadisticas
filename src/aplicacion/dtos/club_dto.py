from dataclasses import dataclass


@dataclass
class CrearClubDTO:
    """Imgresaa CrearClubUseCase.ejecutar()"""

    nombre: str


@dataclass
class ClubDTO:
    """Sale de CrearClubuseCase / ListarClubesUsuarioUseCase"""

    idClub: int
    nombre: str


@dataclass
class RenombrarClubDTO:
    """Entra a RenombrarClubUseCase (US-114): corregir el nombre de un club rival"""

    idClub: int
    nombre: str


@dataclass
class VincularJugadorClubDTO:
    """entra a VincularJugadorAClubUseCase"""

    idJugador: int
    idClub: int
    fechaDesde: str


@dataclass
class DesvincularJugadorDTO:
    """entra a DesvincularJugadorDeClubUseCase"""

    idJugador: int
    fechaHasta: str


@dataclass
class VinculoDTO:
    """Sale de VincularJugadorAClubUseCase (fechaHasta=None: vinculo vigente) y de DesvincularJugadorDeClubUseCase"""

    idJugador: int
    idClub: int
    fechaDesde: str
    fechaHasta: str | None
