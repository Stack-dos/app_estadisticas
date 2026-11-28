import logging
from dataclasses import replace

from aplicacion.servicios.estado_aviso_almacen import EstadoAvisoAlmacen

logger = logging.getLogger(__name__)


class OmitirVersionUseCase:
    """Boton "Omitir esta version" del aviso de version nueva: ese tag no se vuelve a avisar, el siguiente si.

    Se guarda un solo tag: omitir la v1.0.2 reemplaza a la v1.0.1 omitida antes, que igual ya no se avisaria
    (la API solo devuelve el ultimo release).
    """

    def __init__(self, almacen: EstadoAvisoAlmacen):
        """
        Args:
            almacen (EstadoAvisoAlmacen): Donde se recuerda la version omitida.
        """
        self.almacen = almacen

    def ejecutar(self, tag: str) -> None:
        """
        Args:
            tag (str): El tag que el usuario no quiere que se le vuelva a avisar (por ejemplo `"v1.0.1"`).
        """
        self.almacen.guardar(replace(self.almacen.cargar(), tag_omitido=tag))
        logger.info(f"El usuario omitio la version {tag}")
