import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import date

from aplicacion.dtos.version_dto import VersionPublicadaDTO
from aplicacion.servicios.estado_aviso_almacen import EstadoAvisoAlmacen
from aplicacion.servicios.fuente_de_versiones import FuenteDeVersiones
from dominio.versiones import hay_version_nueva

# logging de la biblioteca estandar (no infraestructura.logger): la aplicacion no importa infraestructura
logger = logging.getLogger(__name__)


class BuscarActualizacionUseCase:
    """Al abrir la app, decide si hay que avisar que salio una version nueva (spike de aviso de version nueva).

    Reglas (punto 4.4 del spike): se consulta como maximo una vez por dia, una version omitida no se vuelve
    a avisar (la siguiente si) y nunca lanza: sin internet o con GitHub caido, simplemente no hay aviso.
    """

    def __init__(
        self,
        fuente: FuenteDeVersiones,
        almacen: EstadoAvisoAlmacen,
        version_instalada: str,
        hoy: Callable[[], date] = date.today,
    ):
        """
        Args:
            fuente (FuenteDeVersiones): De donde se saca el ultimo release estable.
            almacen (EstadoAvisoAlmacen): Donde se recuerda el ultimo chequeo y la version omitida.
            version_instalada (str): La version que esta corriendo (`config.version.VERSION`).
            hoy (Callable[[], date]): Devuelve la fecha de hoy. Se inyecta para que los tests elijan el dia.
        """
        self.fuente = fuente
        self.almacen = almacen
        self.version_instalada = version_instalada
        self.hoy = hoy

    def ejecutar(self) -> VersionPublicadaDTO | None:
        """
        Returns:
            VersionPublicadaDTO | None: La version a avisar, o None si no hay que mostrar nada.
        """
        estado = self.almacen.cargar()
        hoy = self.hoy()
        # == y no >=: si el reloj de la PC se atraso, un "ultimo chequeo" en el futuro no frena la consulta
        if estado.ultimo_chequeo == hoy:
            logger.debug("Ya se busco una version nueva hoy: no se consulta")
            return None

        publicada = self.fuente.ultima_version_publicada()
        # Se guarda aunque la consulta haya fallado: "una vez por dia" vale tambien sin internet, asi un
        # GitHub caido no se consulta en cada arranque. Se pierde, como mucho, un dia de aviso.
        self.almacen.guardar(replace(estado, ultimo_chequeo=hoy))

        if publicada is None or not hay_version_nueva(self.version_instalada, publicada.tag):
            return None
        if publicada.tag == estado.tag_omitido:
            logger.info(f"Hay una version nueva ({publicada.tag}) pero el usuario la omitio: no se avisa")
            return None
        logger.info(f"Hay una version nueva: {publicada.tag} (instalada: {self.version_instalada})")
        return publicada
