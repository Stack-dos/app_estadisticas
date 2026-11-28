import http.client
import json
import urllib.error
import urllib.request

from aplicacion.dtos.version_dto import VersionPublicadaDTO
from aplicacion.servicios.fuente_de_versiones import FuenteDeVersiones
from infraestructura.logger import get_logger

logger = get_logger(__name__)

# Por id y no por nombre: el id no cambia si el repo se renombra o se transfiere (ya paso: nicopinera -> Stack-dos).
# /latest ignora los pre-release (-rc) y los borradores; si no hay ningun release estable responde 404.
URL_ULTIMO_RELEASE = "https://api.github.com/repositories/1181238798/releases/latest"
# La pagina que abre "Descargar" tiene que ser de GitHub: no se abre en el navegador una URL cualquiera
PREFIJO_URL_RELEASE = "https://github.com/"


class GithubReleasesFuente(FuenteDeVersiones):
    """Pregunta a la API publica de GitHub cual es el ultimo release estable.

    Offline-first: sin internet, con un timeout, un 404 o una respuesta rara devuelve None y deja una
    linea en el log. Nunca lanza: que no se pueda saber si hay version nueva no tiene que molestar a nadie.
    """

    def __init__(self, url: str = URL_ULTIMO_RELEASE, timeout: float = 3.0):
        """
        Args:
            url (str): Endpoint de la API. Se inyecta para que los tests usen un servidor local.
            timeout (float): Segundos maximos de espera (para conectar y para cada lectura).
        """
        self._url = url
        self._timeout = timeout

    def ultima_version_publicada(self) -> VersionPublicadaDTO | None:
        # GitHub rechaza pedidos sin User-Agent; va el nombre de la app, nada del usuario
        # S310 (urlopen tambien abre file://) no aplica: la URL es la constante de arriba o la de los tests
        pedido = urllib.request.Request(  # noqa: S310
            self._url, headers={"Accept": "application/vnd.github+json", "User-Agent": "statspro-basketball"}
        )
        try:
            with urllib.request.urlopen(pedido, timeout=self._timeout) as respuesta:  # noqa: S310
                datos = json.load(respuesta)
        except urllib.error.HTTPError as e:  # urlopen lanza (no devuelve) ante un 4xx/5xx
            if e.code == 404:
                logger.info("No hay ningun release estable publicado (404): no hay version nueva")
            else:
                logger.warning(f"La API de releases respondio {e.code}: no se sabe si hay version nueva")
            return None
        # OSError cubre sin red, DNS, conexion rechazada y timeout; ValueError, JSON roto o bytes no UTF-8;
        # HTTPException, una respuesta cortada a la mitad (IncompleteRead no es OSError)
        except (OSError, ValueError, http.client.HTTPException) as e:
            logger.info(f"No se pudo consultar la ultima version ({type(e).__name__}): se sigue sin avisar")
            return None

        version = _a_version(datos)
        if version is None:
            logger.warning("La respuesta de la API de releases no tiene el formato esperado: se ignora")
        return version


def _a_version(datos: object) -> VersionPublicadaDTO | None:
    "Valida la respuesta (viene de afuera) y arma el DTO, o None si le falta algo"
    if not isinstance(datos, dict):
        return None
    tag, url = datos.get("tag_name"), datos.get("html_url")
    if not isinstance(tag, str) or not isinstance(url, str) or not url.startswith(PREFIJO_URL_RELEASE):
        return None
    return VersionPublicadaDTO(tag=tag, url=url)
