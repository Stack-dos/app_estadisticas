from abc import ABC, abstractmethod

from aplicacion.dtos.version_dto import VersionPublicadaDTO


class FuenteDeVersiones(ABC):
    """Puerto: de donde se saca la ultima version publicada (spike de aviso de version nueva).

    Vive en la capa de aplicacion, igual que `SesionAlmacen`, porque su contrato usa un DTO. La
    implementacion real (la API de GitHub Releases) esta en `infraestructura/`.
    """

    @abstractmethod
    def ultima_version_publicada(self) -> VersionPublicadaDTO | None:
        "Devuelve el ultimo release estable, o None si no hay o no se pudo saber. Nunca lanza"
        pass
