from abc import ABC, abstractmethod

from aplicacion.dtos.version_dto import EstadoAvisoDTO


class EstadoAvisoAlmacen(ABC):
    """Puerto: donde se guarda el estado del aviso de version nueva (ultimo chequeo y version omitida).

    Va aparte de la sesion: `SesionAlmacen.borrar` corre al cerrar sesion, y "Omitir esta version" no
    tiene que perderse por eso. La implementacion real (un archivo JSON) esta en `infraestructura/persistencia/`.
    """

    @abstractmethod
    def cargar(self) -> EstadoAvisoDTO:
        "Devuelve el estado guardado, o uno vacio si no hay o no se puede usar. Nunca lanza"
        pass

    @abstractmethod
    def guardar(self, estado: EstadoAvisoDTO) -> None:
        "Guarda el estado, reemplazando el anterior. Si falla, loguea y sigue (nunca lanza)"
        pass
