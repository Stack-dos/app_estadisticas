from abc import ABC, abstractmethod

from aplicacion.dtos.session_dto import SessionDTO


class SesionAlmacen(ABC):
    """Puerto: donde se guarda la sesion recordada (US-106).

    Vive en la capa de aplicacion, al lado del `SessionManager` que lo usa, y no en el dominio como
    `PasswordHasher`: su contrato usa `SessionDTO`, y el dominio no puede importar de la aplicacion.
    La implementacion real (un archivo JSON) esta en `infraestructura/persistencia/`.
    """

    @abstractmethod
    def guardar(self, sesion: SessionDTO) -> None:
        "Guarda la sesion, reemplazando la anterior"
        pass

    @abstractmethod
    def cargar(self) -> SessionDTO | None:
        "Devuelve la sesion guardada, o None si no hay ninguna o no se puede usar. Nunca lanza"
        pass

    @abstractmethod
    def borrar(self) -> None:
        "Borra la sesion guardada. Idempotente: si no hay ninguna, no hace nada"
        pass
