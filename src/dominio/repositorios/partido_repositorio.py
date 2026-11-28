from abc import ABC, abstractmethod

from dominio.entidades.club import Club
from dominio.entidades.partido import (
    AltaPlantelRival,
    BoxscoreFila,
    EstadisticaEquipo,
    JugadorPartido,
    LiderClub,
    Partido,
    PartidoCuarto,
    PartidoResumen,
    TotalesEquipoFila,
)


class PartidoRepositorio(ABC):
    "Maneja partido y jugadorPartido"

    @abstractmethod
    def buscar_por_club(self, id_club: int) -> list[Partido] | None:
        "Busca todos los partidos linkeados a un club"
        pass

    @abstractmethod
    def buscar_por_id(self, idPartido: int) -> Partido | None:
        "Busca la informacion de un partido"
        pass

    @abstractmethod
    def guardar_partido(self, partido: Partido) -> Partido | None:
        pass

    @abstractmethod
    def guardar_boxscore(self, boxscore: JugadorPartido) -> JugadorPartido | None:
        pass

    @abstractmethod
    def save_with_boxscore(
        self,
        partido: Partido,
        boxscore: list[JugadorPartido],
        cuartos: list[PartidoCuarto] | None = None,
        totales: list[EstadisticaEquipo] | None = None,
        alta_rival: AltaPlantelRival | None = None,
        club_rival_nuevo: Club | None = None,
    ) -> tuple[Partido, list[JugadorPartido]] | None:
        """Guarda el partido, su boxscore y opcionalmente los cuartos en una única transacción atómica.

        US-113: tambien puede guardar los totales de un equipo sin boxscore (`totales`) y dar de alta lo que
        falte del plantel rival (`alta_rival`: inscripcion, lista, jugadores nuevos) en la misma transaccion.
        US-114: si `partido.idPartido` tiene valor, reemplaza ese partido (edicion) en vez de crear otro; si
        viene `club_rival_nuevo`, lo crea en la misma transaccion y usa su id donde aparezca `ID_CLUB_NUEVO`.
        """
        pass

    @abstractmethod
    def eliminar(self, id_partido: int) -> bool:
        "Elimina un partido con su boxscore, cuartos y totales (US-114). False si no existia o fallo"
        pass

    @abstractmethod
    def cuartos_por_partido(self, id_partido: int) -> list[PartidoCuarto]:
        "Puntos por cuarto de un partido, por club y periodo (US-114, para editarlo)"
        pass

    @abstractmethod
    def resumen_por_club(self, id_club: int) -> list[PartidoResumen]:
        "Lista los partidos de un club (local o visitante) con los nombres de la competencia y de los clubes"
        pass

    @abstractmethod
    def boxscore_por_partido(self, id_partido: int) -> list[BoxscoreFila]:
        "Devuelve el boxscore completo de un partido desde la vista `v_boxscore_completo`"
        pass

    @abstractmethod
    def totales_por_partido(self, id_partido: int) -> list[TotalesEquipoFila]:
        "Devuelve los totales de cada equipo del partido desde la vista `v_totales_equipo_partido` (US-113)"
        pass

    @abstractmethod
    def lideres_por_club(self, id_club: int, limite: int) -> list[LiderClub]:
        "Devuelve los jugadores del club con mejor promedio de puntos, desde la vista `v_lideres_club` (US-113)"
        pass
