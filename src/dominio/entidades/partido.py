from dataclasses import dataclass, field

from dominio.entidades.jugador import Jugador
from dominio.exceptions import DatoInvalidoError

# Planilla de un partido (US-114): FIBA permite hasta 12 jugadores por equipo y un equipo necesita 5 para
# empezar. El maximo se valida; el minimo solo avisa, porque un partido real jugado con menos se carga igual.
MAX_JUGADORES_PARTIDO = 12
MIN_JUGADORES_PARTIDO = 5

# Id provisorio del club rival que todavia no existe (US-114): el repositorio lo crea dentro de la misma
# transaccion del partido y reemplaza este id por el real en el partido, el boxscore, los cuartos y los totales.
ID_CLUB_NUEVO = 0


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
    puntosLocal: int | None = None
    puntosVisitante: int | None = None


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
class PartidoCuarto:
    """Puntos anotados por un club en un periodo (cuarto o prorroga) de un partido."""

    idClub: int
    nroCuarto: int
    puntos: int
    idPartido: int | None = None

    def __post_init__(self) -> None:
        """Valida los tipos y rangos de un cuarto del partido."""
        if not isinstance(self.idClub, int) or isinstance(self.idClub, bool):
            raise TypeError(f"idClub debe ser int, recibido {type(self.idClub).__name__}")
        if not isinstance(self.nroCuarto, int) or isinstance(self.nroCuarto, bool):
            raise TypeError(f"nroCuarto debe ser int, recibido {type(self.nroCuarto).__name__}")
        if not isinstance(self.puntos, int) or isinstance(self.puntos, bool):
            raise TypeError(f"puntos debe ser int, recibido {type(self.puntos).__name__}")
        if self.idPartido is not None and (not isinstance(self.idPartido, int) or isinstance(self.idPartido, bool)):
            raise TypeError(f"idPartido debe ser int o None, recibido {type(self.idPartido).__name__}")
        if self.nroCuarto < 1:
            raise DatoInvalidoError(f"nroCuarto debe ser >= 1 - Valor actual: {self.nroCuarto}")
        if self.puntos < 0:
            raise DatoInvalidoError(f"puntos de cuarto no puede ser < 0 - Valor actual: {self.puntos}")


@dataclass
class Partido:
    fecha: str
    estadio: str | None
    idCompetencia: int
    idCategoria: int
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
            TypeError: Si el ID de la categoria no es un entero.
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
        if not isinstance(self.idCategoria, int):
            raise TypeError(f"idCategoria debe ser int, recibido {type(self.idCategoria).__name__}")
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


# Campos de estadistica que comparten el boxscore por jugador y los totales de equipo (sin minutos).
CAMPOS_CONTEO_EQUIPO = (
    "t2c",
    "t2l",
    "t3c",
    "t3l",
    "t1c",
    "t1l",
    "rebotesDef",
    "rebotesOf",
    "asistencias",
    "recuperos",
    "perdidas",
    "taponesRecibidos",
    "taponesRealizados",
    "faltasRecibidas",
    "faltasCometidas",
)


@dataclass
class EstadisticaEquipo:
    """Totales de un equipo en un partido cuando no se cargo su boxscore por jugador (US-113).

    Es la fila "Equipo Rival" de la planilla: puntos, tiros, rebotes, etc. del equipo entero. Si se
    cargaron tiros, los puntos tienen que cerrar con ellos (2*T2C + 3*T3C + T1C). Si todos los tiros
    estan en 0 se acepta cualquier puntaje: es el caso en que del rival solo se conoce el resultado.
    """

    idClub: int
    puntos: int
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
    idPartido: int | None = None

    @property
    def tiene_tiros(self) -> bool:
        """Si se cargo algun tiro (convertido o lanzado); si no, solo se conoce el puntaje."""
        return any(getattr(self, c) for c in ("t2c", "t2l", "t3c", "t3l", "t1c", "t1l"))

    def __post_init__(self) -> None:
        """
        Valida tipos, rangos y coherencia de los totales.

        Raises:
            TypeError: Si algun campo no es int (los bool no cuentan como int).
            DatoInvalidoError: Si hay valores negativos, convertidos > lanzados, o puntos que no cierran
                con los tiros cargados.
        """
        for nombre in ("idClub", "puntos", *CAMPOS_CONTEO_EQUIPO):
            valor = getattr(self, nombre)
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise TypeError(f"{nombre} debe ser int, recibido {type(valor).__name__}")
            if valor < 0:
                raise DatoInvalidoError(f"{nombre} del equipo no puede ser negativo - Valor actual: {valor}")
        if self.idPartido is not None and (not isinstance(self.idPartido, int) or isinstance(self.idPartido, bool)):
            raise TypeError(f"idPartido debe ser int o None, recibido {type(self.idPartido).__name__}")
        for conv, lanz, etiqueta in (("t2c", "t2l", "T2"), ("t3c", "t3l", "T3"), ("t1c", "t1l", "T1")):
            if getattr(self, conv) > getattr(self, lanz):
                raise DatoInvalidoError(
                    f"{etiqueta}: convertidos ({getattr(self, conv)}) no puede ser mayor que lanzados "
                    f"({getattr(self, lanz)})"
                )
        if self.tiene_tiros:
            esperado = self.t2c * 2 + self.t3c * 3 + self.t1c
            if self.puntos != esperado:
                raise DatoInvalidoError(
                    f"Los puntos del equipo ({self.puntos}) no cierran con los tiros convertidos "
                    f"(2*T2C + 3*T3C + T1C = {esperado})"
                )


@dataclass
class TotalesEquipoFila:
    """Vista de lectura de `v_totales_equipo_partido`: los totales de un equipo en un partido.

    `origen` dice de donde salen: "boxscore" (suma de los jugadores) o "totales" (cargados a mano).
    """

    idPartido: int
    idClub: int
    nombreClub: str
    origen: str
    puntos: int
    t2c: int
    t2l: int
    t3c: int
    t3l: int
    t1c: int
    t1l: int
    rebotesDef: int
    rebotesOf: int
    asistencias: int
    recuperos: int
    perdidas: int
    taponesRecibidos: int
    taponesRealizados: int
    faltasRecibidas: int
    faltasCometidas: int


@dataclass
class JugadorRivalNuevo:
    """Un jugador del rival que todavia no existe en la base: se crea al guardar el partido (US-113).

    `estadistica.idJugador` es un marcador (0): el repositorio lo reemplaza por el id real del jugador
    que inserta, dentro de la misma transaccion.
    """

    jugador: Jugador
    estadistica: JugadorPartido


@dataclass
class AltaPlantelRival:
    """Lo que hay que dar de alta del rival para que su boxscore cumpla la regla de la lista de buena fe.

    Todo se escribe en la misma transaccion que el partido: si algo falla no queda nada a medias.

    - Si `idListaBuenaFe` es None, el rival no estaba inscripto: se crea la inscripcion y su lista.
    - `habilitar`: jugadores que ya son del club rival pero no estaban en la lista.
    - `nuevos`: jugadores que no existian; se crean, se vinculan al club desde la fecha del partido y se
      agregan a la lista.
    """

    idClub: int
    idCompetencia: int
    idCategoria: int
    fecha: str
    idListaBuenaFe: int | None = None
    habilitar: list[int] = field(default_factory=list)
    nuevos: list[JugadorRivalNuevo] = field(default_factory=list)


@dataclass
class LiderClub:
    """Vista de lectura de `v_lideres_club`: promedios de un jugador en los partidos de su club."""

    idJugador: int
    nombreJugador: str
    partidosJugados: int
    puntosPromedio: float
    rebotesPromedio: float
    asistenciasPromedio: float
