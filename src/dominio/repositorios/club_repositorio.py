from abc import ABC, abstractmethod

from dominio.entidades.club import Club, UsuarioClub


class ClubRepositorio(ABC):
    "Maneja Club y UsuarioClub"

    @abstractmethod
    def buscar_por_id_usuario(self, id_usuario: int) -> list[Club] | None:
        "Busca un club por id de usuario"
        pass

    @abstractmethod
    def buscar_por_id(self, id_club: int) -> Club | None:
        "Busca un club por id"
        pass

    @abstractmethod
    def buscar_por_nombre(self, nombre: str) -> list[Club] | None:
        "Busca un club por nombre"
        pass

    @abstractmethod
    def guardar(self, club: Club) -> Club | None:
        "Guarda un Club, si es None, hay un error"
        pass

    @abstractmethod
    def guardar_con_entrenador(self, club: Club, id_usuario: int, rol: str) -> Club | None:
        "Guarda un Club y vincula al usuario como entrenador, todo o nada. Si es None, hay un error"
        pass

    @abstractmethod
    def link_user_to_club(self, us_club: UsuarioClub) -> UsuarioClub | None:
        "Linkea un usuario a un club especifico"
        pass
