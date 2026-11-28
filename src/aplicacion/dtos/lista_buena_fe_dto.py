from dataclasses import dataclass, field


@dataclass
class AgregarJugadorListaDTO:
    """Entra a AgregarJugadorAListaBuenaFeUseCase.ejecutar()"""

    idInscripcion: int
    idJugador: int


@dataclass
class JugadorEnListaDTO:
    """Sale de Agregar/QuitarJugador...ListaBuenaFeUseCase: confirma en que lista se habilito o se quito al jugador"""

    idListaBuenaFe: int
    idInscripcion: int
    idJugador: int


@dataclass
class QuitarJugadorListaDTO:
    """Entra a QuitarJugadorDeListaBuenaFeUseCase.ejecutar()"""

    idInscripcion: int
    idJugador: int


@dataclass
class AgregarJugadoresListaDTO:
    """Entra a AgregarJugadoresAListaBuenaFeUseCase.ejecutar() (US-113): varios jugadores a la vez"""

    idInscripcion: int
    idJugadores: list[int]


@dataclass
class JugadorRechazadoDTO:
    """Un jugador que no se pudo agregar a la lista, con el motivo (el mensaje del error de dominio)"""

    idJugador: int
    motivo: str


@dataclass
class ResultadoAgregarJugadoresDTO:
    """Sale de AgregarJugadoresAListaBuenaFeUseCase: quienes entraron y quienes no"""

    agregados: list[int] = field(default_factory=list)
    rechazados: list[JugadorRechazadoDTO] = field(default_factory=list)
