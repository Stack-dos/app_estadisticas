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
    def listar_todos(self) -> list[Club]:
        "Lista todos los clubes registrados en la base de datos"
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

    @abstractmethod
    def listar_sin_usuario(self) -> list[Club]:
        "Clubes que no son de ningun usuario: los rivales (US-114), ordenados por nombre"
        pass

    @abstractmethod
    def actualizar(self, club: Club) -> Club | None:
        "Cambia el nombre de un club existente (US-114). None si no existe o fallo la base"
        pass

    @abstractmethod
    def eliminar(self, id_club: int) -> bool:
        "Elimina un club; su inscripcion, lista y vinculos caen en cascada (US-114)"
        pass

    @abstractmethod
    def tiene_partidos(self, id_club: int) -> bool:
        "Si el club jugo algun partido cargado (US-114)"
        pass

    @abstractmethod
    def tiene_usuarios(self, id_club: int) -> bool:
        "Si el club es club propio de algun usuario (US-114)"
        pass
