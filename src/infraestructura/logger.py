import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import config.rutas as r
from infraestructura.observabilidad import FiltroContexto, FiltroSecretos, FormateadorJson

# US-110: donde y desde que nivel se loguea, sin tocar codigo (en desarrollo: STATSPRO_LOG_SINK=consola).
VAR_SINK = "STATSPRO_LOG_SINK"
VAR_NIVEL = "STATSPRO_LOG_NIVEL"


def crear_carpeta_logs() -> None:
    """Crea el directorio de logs si no existe.

    Utiliza :data:`config.rutas.LOG_DIR` como ruta destino. La operación es
    idempotente: no lanza excepción si el directorio ya existe.

    Returns:
        None
    """
    os.makedirs(r.LOG_DIR, exist_ok=True)


def crear_handler(sink: str, nivel: str) -> logging.Handler:
    """Arma el handler del sink pedido, con formato JSON, contexto y redaccion de secretos (US-110).

    - ``archivo`` (default): :class:`~logging.handlers.RotatingFileHandler` en ``logs/app.log``; rota a
      los 10 MB y conserva 5 respaldos (``app.log.1`` … ``app.log.5``).
    - ``consola``: ``stderr``, para mirar los logs en vivo mientras se desarrolla.

    Un sink o un nivel desconocido no rompen el arranque: se usa el default (``archivo`` / ``INFO``).

    Args:
        sink (str): ``archivo`` o ``consola``.
        nivel (str): Nombre del nivel minimo (``DEBUG``, ``INFO``, ``WARNING``...).

    Returns:
        logging.Handler: El handler listo para agregar al logger raiz.
    """
    handler: logging.Handler
    if sink.lower() == "consola":
        handler = logging.StreamHandler(sys.stderr)
    else:
        crear_carpeta_logs()
        # A diferencia del FileHandler simple, este no llena el disco.
        handler = RotatingFileHandler(r.APP_LOG_FILE, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    handler.setLevel(logging.getLevelNamesMapping().get(nivel.upper(), logging.INFO))
    # Los filtros van en el handler: los de un logger no ven los registros que propagan sus hijos.
    handler.addFilter(FiltroContexto())
    handler.addFilter(FiltroSecretos())
    handler.setFormatter(FormateadorJson())
    return handler


def configuracion_log() -> logging.Logger:
    """Configura el logger raíz de la aplicación.

    El logger raíz queda en ``DEBUG`` y le agrega el handler de :func:`crear_handler`, con el sink
    y el nivel que digan ``STATSPRO_LOG_SINK`` y ``STATSPRO_LOG_NIVEL`` (default: archivo, INFO).

    Si el logger raíz ya tiene handlers configurados no agrega duplicados y
    retorna directamente.

    Returns:
        logging.Logger: instancia del logger raíz ya configurado.
    """
    # Al no pasarle nombre configura el logger raiz,
    # que es el padre de todos los loggers.
    # Esto hace que cualquier logger que se cree en
    # la aplicación herede esta configuración.
    logger = logging.getLogger()

    # Esto para evitar que hayan handlers duplicados
    # si se llama varias veces a get_logger(). En los tests pytest ya puso los suyos: no se toca.
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.addHandler(crear_handler(os.environ.get(VAR_SINK, "archivo"), os.environ.get(VAR_NIVEL, "INFO")))

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Devuelve un logger listo para usar en cualquier módulo.

    Llama internamente a :func:`configuracion_log` para garantizar que el
    logger raíz esté inicializado antes de retornar el logger solicitado.

    Args:
        name (str | None): Nombre del logger, normalmente ``__name__`` del
            módulo que lo invoca. Si es ``None`` se devuelve el logger raíz.

    Returns:
        logging.Logger: logger con nombre ``name`` que hereda la configuración
        del logger raíz.
    """
    configuracion_log()
    return logging.getLogger(name)
