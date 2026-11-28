from abc import ABC, abstractmethod

from dominio.entidades.usuario import Usuario


class UsuarioRepositorio(ABC):
    @abstractmethod
    def encontrar_por_mail(self, email: str) -> Usuario | None:
        "Busca un usuario por el mail"
        pass

    @abstractmethod
    def encontrar_por_id(self, id: int) -> Usuario | None:
        "Busca usuario por id"
        pass

    @abstractmethod
    def guardar(self, us_aux: Usuario) -> Usuario | None:
        pass
