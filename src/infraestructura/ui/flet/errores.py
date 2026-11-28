"""Manejador comun de errores de la GUI (US-105).

Si un handler de Flet lanza una excepcion que nadie atrapa, Flet cierra la sesion y muestra el
traceback en la ventana. Las pantallas envuelven en `ejecutar_mostrando_errores` cada accion que
llama a un caso de uso, asi el error se muestra junto al formulario y la app sigue andando.

Desde la US-110 tambien es el punto donde nace cada accion del usuario: abre su correlation_id y
loguea el inicio y el fin (resultado y duracion).
"""

import time
from collections.abc import Callable

import flet as ft

from dominio.exceptions import ErrorDeDominio
from infraestructura.logger import get_logger
from infraestructura.observabilidad import nueva_accion

logger = get_logger(__name__)

MENSAJE_ERROR_INESPERADO = "Ocurrió un error inesperado. El detalle quedó en logs/app.log."


def crear_etiqueta_error() -> ft.Text:
    """
    Crea el texto donde cada formulario muestra sus errores (va debajo del formulario).

    Returns:
        ft.Text: Texto vacio, con el color de error del tema.
    """
    return ft.Text(value="", color=ft.Colors.ERROR)


def ejecutar_mostrando_errores(accion: Callable[[], None], etiqueta: ft.Text, *, nombre: str) -> None:
    """
    Ejecuta una accion de la interfaz y muestra en `etiqueta` el error que lance, si lanza alguno.

    - `ErrorDeDominio` (el usuario se equivoco): se muestra su mensaje, que ya esta escrito para el usuario.
    - Cualquier otra excepcion es un bug: el usuario ve un mensaje generico y el traceback va al log.
      Atrapar `Exception` se justifica solo aca, en el borde de la app: si no, Flet cierra la sesion.

    No llama a `update()`: lo hace el handler de la pantalla (asi se testea con un `ft.Text` suelto).

    Args:
        accion (Callable[[], None]): Lo que hay que hacer (llamar al caso de uso, navegar...).
        etiqueta (ft.Text): Donde se muestra el error. Se limpia antes de ejecutar.
        nombre (str): Nombre de la accion para el log, `pantalla.que_hace` (p. ej. "clubes.crear").
    """
    etiqueta.value = ""
    pantalla = nombre.split(".")[0]
    with nueva_accion(nombre):
        logger.info("Inicio de %s", nombre, extra={"evento": "accion_inicio", "pantalla": pantalla})
        inicio = time.perf_counter()
        resultado = "ok"
        try:
            accion()
        except ErrorDeDominio as e:
            resultado = "error_dominio"
            logger.warning(
                "Error de dominio en la GUI: %s", e, extra={"evento": "error_dominio", "tipo": type(e).__name__}
            )
            etiqueta.value = str(e)
        except Exception:
            resultado = "error"
            logger.exception("Error inesperado en la GUI", extra={"evento": "error_inesperado"})
            etiqueta.value = MENSAJE_ERROR_INESPERADO
        logger.info(
            "Fin de %s: %s",
            nombre,
            resultado,
            extra={
                "evento": "accion_fin",
                "pantalla": pantalla,
                "resultado": resultado,
                "duracion_ms": round((time.perf_counter() - inicio) * 1000, 1),
            },
        )
