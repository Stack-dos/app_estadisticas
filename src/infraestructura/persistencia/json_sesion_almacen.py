import json
from dataclasses import asdict
from pathlib import Path

from aplicacion.dtos.session_dto import SessionDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from infraestructura.logger import get_logger

logger = get_logger(__name__)

CAMPOS = {"usuario_id", "email", "club_activo_id"}


class JsonSesionAlmacen(SesionAlmacen):
    """Guarda la sesion recordada en un archivo JSON (por defecto `~/.statspro/session.json`).

    El archivo vive fuera de la app y cualquiera lo puede editar: `cargar` lo valida y ante cualquier
    problema devuelve None (la app pide login, sin traceback: AC4). Nunca se loguea su contenido (tiene
    un email); solo la ruta y el tipo de error.

    Guardar y borrar son "mejor esfuerzo": si el disco falla, se loguea y la app sigue. Que no se pueda
    recordar la sesion no debe impedir iniciarla ni cerrarla.
    """

    def __init__(self, ruta: Path):
        """
        Args:
            ruta (Path): Archivo de la sesion. Se inyecta para que los tests usen `tmp_path`.
        """
        self._ruta = ruta

    def guardar(self, sesion: SessionDTO) -> None:
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            # encoding explicito: en Windows el default es cp1252 y una "ñ" se leeria mal desde Linux
            self._ruta.write_text(json.dumps(asdict(sesion)), encoding="utf-8")
        except OSError as e:
            logger.warning(f"No se pudo guardar la sesion en {self._ruta} ({type(e).__name__}): no se va a recordar")

    def cargar(self) -> SessionDTO | None:
        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None  # el caso normal: nunca se marco "Recordarme"
        except (OSError, ValueError) as e:  # ValueError incluye JSON roto y bytes que no son UTF-8
            logger.warning(f"No se pudo leer la sesion de {self._ruta} ({type(e).__name__}): se ignora")
            return None

        sesion = _a_sesion(datos)
        if sesion is None:
            logger.warning(f"La sesion de {self._ruta} no tiene el formato esperado: se ignora")
        return sesion

    def borrar(self) -> None:
        try:
            self._ruta.unlink(missing_ok=True)
        except OSError as e:
            logger.error(f"No se pudo borrar la sesion de {self._ruta} ({type(e).__name__}): se va a seguir recordando")


def _a_sesion(datos: object) -> SessionDTO | None:
    """Valida lo leido del archivo (limite de confianza: viene de afuera) y lo convierte en DTO."""
    if not isinstance(datos, dict) or set(datos) != CAMPOS:
        return None
    usuario_id, email, club_activo_id = datos["usuario_id"], datos["email"], datos["club_activo_id"]
    if not _es_id(usuario_id) or not isinstance(email, str) or not (club_activo_id is None or _es_id(club_activo_id)):
        return None
    return SessionDTO(usuario_id=usuario_id, email=email, club_activo_id=club_activo_id)


def _es_id(valor: object) -> bool:
    # bool es subclase de int: sin este chequeo, {"usuario_id": true} pasaria como el id 1
    return isinstance(valor, int) and not isinstance(valor, bool)
