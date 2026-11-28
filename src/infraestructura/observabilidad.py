"""Observabilidad (US-110): correlation_id por accion, logs JSON y redaccion de secretos.

Las tres piezas se enganchan a los *handlers* de `logger.py`, no a los loggers: los filtros de un logger
no se aplican a los registros que llegan propagados desde loggers hijos (`aplicacion.casos_uso.x`),
los de un handler si.

- `nueva_accion(nombre)`: abre el contexto de una accion del usuario. Todo lo que se loguee adentro (la
  pantalla, el caso de uso, el repositorio) sale con el mismo `correlation_id`, sin pasarlo por parametro:
  viaja en una `ContextVar`. La capa de aplicacion usa `logging` de la biblioteca estandar y no sabe nada
  de esto; el id se agrega recien en el handler.
- `FiltroContexto`: copia `correlation_id` y `accion` al registro.
- `FiltroSecretos`: tapa contraseñas, hashes, tokens y emails en el mensaje, los extras y el traceback.
- `FormateadorJson`: una linea JSON por registro.
"""

import contextlib
import json
import logging
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime

TAPADO = "***"

# Atributos que todo LogRecord ya trae: lo que no este aca vino por `extra=` y va al JSON.
_ATRIBUTOS_ESTANDAR = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "correlation_id",
    "accion",
}
_CLAVES_SECRETAS = ("password", "contraseña", "contrasena", "hash", "token", "salt", "secret")
# `clave=valor` o `"clave": "valor"`, con la clave secreta en cualquier parte del nombre (password_hash).
_RE_CLAVE_VALOR = re.compile(
    rf"""(?P<clave>\w*(?:{"|".join(_CLAVES_SECRETAS)})\w*)(?P<sep>['"]?\s*[=:]\s*)(?P<comilla>['"]?)[^\s,'"}})\]]+""",
    re.IGNORECASE,
)
_RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


@dataclass(frozen=True)
class ContextoAccion:
    correlation_id: str
    accion: str


_contexto: ContextVar[ContextoAccion | None] = ContextVar("contexto_accion", default=None)


def contexto_actual() -> ContextoAccion | None:
    """La accion en curso, o None si el log sale fuera de una (p. ej. al cerrar la app)."""
    return _contexto.get()


@contextmanager
def nueva_accion(nombre: str) -> Iterator[ContextoAccion]:
    """
    Abre una accion con un correlation_id nuevo (UUIDv4) y la cierra al salir, aunque haya excepcion.

    Si ya hay una accion abierta (Guardar navega a otra pantalla), sigue la de afuera: es el mismo clic
    del usuario y conviene verlo con un solo id.

    Args:
        nombre (str): Nombre de la accion, `pantalla.que_hace` (p. ej. "clubes.crear").

    Yields:
        ContextoAccion: El contexto que quedo activo.
    """
    actual = _contexto.get()
    if actual is not None:
        yield actual
        return
    contexto = ContextoAccion(correlation_id=str(uuid.uuid4()), accion=nombre)
    token = _contexto.set(contexto)
    try:
        yield contexto
    finally:
        _contexto.reset(token)


def redactar(texto: str) -> str:
    """Tapa los valores de claves secretas (`password=...`) y los emails de un texto."""
    texto = _RE_CLAVE_VALOR.sub(lambda m: f"{m['clave']}{m['sep']}{m['comilla']}{TAPADO}", texto)
    return _RE_EMAIL.sub(TAPADO, texto)


def _es_secreta(clave: str) -> bool:
    return any(s in clave.lower() for s in _CLAVES_SECRETAS)


def extras(record: logging.LogRecord) -> dict[str, object]:
    """Los campos que el registro trae por `extra=`."""
    return {k: v for k, v in record.__dict__.items() if k not in _ATRIBUTOS_ESTANDAR}


class FiltroContexto(logging.Filter):
    """Agrega `correlation_id` y `accion` (None fuera de una accion) a cada registro."""

    def filter(self, record: logging.LogRecord) -> bool:
        contexto = _contexto.get()
        record.correlation_id = contexto.correlation_id if contexto else None
        record.accion = contexto.accion if contexto else None
        return True


class FiltroSecretos(logging.Filter):
    """Redacta el registro antes de que lo escriba cualquier formatter: mensaje, extras y traceback."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Si los args no cierran con el mensaje, que lo reporte el handler: un log roto no corta la accion.
        with contextlib.suppress(Exception):
            record.msg = redactar(record.getMessage())
            record.args = None
        for clave, valor in extras(record).items():
            if _es_secreta(clave):
                setattr(record, clave, TAPADO)
            elif isinstance(valor, str):
                setattr(record, clave, redactar(valor))
        if record.exc_info and not record.exc_text:
            # Formatter.format usa exc_text si ya esta: asi el traceback sale redactado.
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = redactar(record.exc_text)
        return True


class FormateadorJson(logging.Formatter):
    """Una linea JSON por registro: ts (UTC, ISO 8601), nivel, logger, mensaje, contexto, extras y exc."""

    def format(self, record: logging.LogRecord) -> str:
        datos: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "nivel": record.levelname,
            "logger": record.name,
            "mensaje": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", None),
            "accion": getattr(record, "accion", None),
            **extras(record),
        }
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            datos["exc"] = record.exc_text
        return json.dumps(datos, ensure_ascii=False, default=str)
