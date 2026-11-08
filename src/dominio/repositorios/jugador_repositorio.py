from abc import ABC, abstractmethod

from dominio.entidades.club import Club
from dominio.entidades.jugador import Jugador, JugadorClub


class JugadorRepositorio(ABC):
    "Maneja Jugador y JugadorClub"

    @abstractmethod
    def buscar_por_id(self, id_jugador: int) -> Jugador | None:
        "Busca un jugador por id"
        pass

    @abstractmethod
    def buscar_por_club(self, idClub: int) -> list[Jugador] | None:
        "Busca los jugadores actuales de un club (vinculo vigente, sin fechaHasta)"
        pass

    @abstractmethod
    def guardar(self, jugador: Jugador) -> Jugador | None:
        pass

    @abstractmethod
    def link_to_club(self, jc: JugadorClub) -> JugadorClub | None:
        "Vincula un jugador con un club, verificando link con otro club"
        pass

    @abstractmethod
    def club_activo(self, id_jugador: int) -> Club | None:
        "Devuelve el club activo de un jugador"
        pass

    @abstractmethod
    def historial_vinculos(self, id_jugador: int) -> list[JugadorClub]:
        "Devuelve todos los vinculos de un jugador con clubes (vigentes y cerrados), del mas antiguo al mas reciente"
        pass

    @abstractmethod
    def cerrar_vinculo(self, id_jugador: int, fecha_hasta: str) -> JugadorClub | None:
        "Cierra el vinculo vigente de un jugador cargando su fechaHasta. None si no habia vinculo vigente o fallo"
        pass
