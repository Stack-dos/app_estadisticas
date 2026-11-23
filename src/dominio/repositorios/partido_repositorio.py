from abc import ABC, abstractmethod

from dominio.entidades.partido import BoxscoreFila, JugadorPartido, Partido, PartidoResumen


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
        self, partido: Partido, boxscore: list[JugadorPartido]
    ) -> tuple[Partido, list[JugadorPartido]] | None:
        """Guarda el partido y su boxscore en una única transacción atómica."""
        pass

    @abstractmethod
    def resumen_por_club(self, id_club: int) -> list[PartidoResumen]:
        "Lista los partidos de un club (local o visitante) con los nombres de la competencia y de los clubes"
        pass

    @abstractmethod
    def boxscore_por_partido(self, id_partido: int) -> list[BoxscoreFila]:
        "Devuelve el boxscore completo de un partido desde la vista `v_boxscore_completo`"
        pass
