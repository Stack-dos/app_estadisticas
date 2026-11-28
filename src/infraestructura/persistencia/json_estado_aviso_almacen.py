import json
from datetime import date
from pathlib import Path

from aplicacion.dtos.version_dto import EstadoAvisoDTO
from aplicacion.servicios.estado_aviso_almacen import EstadoAvisoAlmacen
from infraestructura.logger import get_logger

logger = get_logger(__name__)

CAMPOS = {"ultimo_chequeo", "tag_omitido"}


class JsonEstadoAvisoAlmacen(EstadoAvisoAlmacen):
    """Guarda el estado del aviso de version nueva en un JSON (por defecto `~/.statspro/aviso_version.json`).

    Mismo criterio que `JsonSesionAlmacen`: el archivo lo puede editar cualquiera, asi que `cargar` lo valida
    y ante cualquier problema devuelve un estado vacio. Lo peor que pasa es una consulta de mas a GitHub o
    volver a avisar una version omitida: nunca un error en pantalla.
    """

    def __init__(self, ruta: Path):
        """
        Args:
            ruta (Path): Archivo del estado. Se inyecta para que los tests usen `tmp_path`.
        """
        self._ruta = ruta

    def cargar(self) -> EstadoAvisoDTO:
        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return EstadoAvisoDTO()  # el caso normal la primera vez
        except (OSError, ValueError) as e:  # ValueError incluye JSON roto y bytes que no son UTF-8
            logger.warning(f"No se pudo leer el estado del aviso de {self._ruta} ({type(e).__name__}): se ignora")
            return EstadoAvisoDTO()

        estado = _a_estado(datos)
        if estado is None:
            logger.warning(f"El estado del aviso de {self._ruta} no tiene el formato esperado: se ignora")
            return EstadoAvisoDTO()
        return estado

    def guardar(self, estado: EstadoAvisoDTO) -> None:
        datos = {
            "ultimo_chequeo": estado.ultimo_chequeo.isoformat() if estado.ultimo_chequeo else None,
            "tag_omitido": estado.tag_omitido,
        }
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            self._ruta.write_text(json.dumps(datos), encoding="utf-8")
        except OSError as e:
            logger.warning(f"No se pudo guardar el estado del aviso en {self._ruta} ({type(e).__name__})")


def _a_estado(datos: object) -> EstadoAvisoDTO | None:
    """Valida lo leido del archivo (limite de confianza: viene de afuera) y lo convierte en DTO."""
    if not isinstance(datos, dict) or set(datos) != CAMPOS:
        return None
    ultimo, tag = datos["ultimo_chequeo"], datos["tag_omitido"]
    if not (ultimo is None or isinstance(ultimo, str)) or not (tag is None or isinstance(tag, str)):
        return None
    try:
        fecha = date.fromisoformat(ultimo) if ultimo is not None else None
    except ValueError:  # "ayer", "2026-13-01"...
        return None
    return EstadoAvisoDTO(ultimo_chequeo=fecha, tag_omitido=tag)
