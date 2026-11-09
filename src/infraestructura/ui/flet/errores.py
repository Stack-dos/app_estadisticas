"""Manejador comun de errores de la GUI (US-105).

Si un handler de Flet lanza una excepcion que nadie atrapa, Flet cierra la sesion y muestra el
traceback en la ventana. Las pantallas envuelven en `ejecutar_mostrando_errores` cada accion que
llama a un caso de uso, asi el error se muestra junto al formulario y la app sigue andando.
"""

from collections.abc import Callable

import flet as ft

from dominio.exceptions import ErrorDeDominio
from infraestructura.logger import get_logger

logger = get_logger(__name__)

MENSAJE_ERROR_INESPERADO = "Ocurrió un error inesperado. El detalle quedó en logs/app.log."


def crear_etiqueta_error() -> ft.Text:
    """
    Crea el texto donde cada formulario muestra sus errores (va debajo del formulario).

    Returns:
        ft.Text: Texto vacio, con el color de error del tema.
    """
    return ft.Text(value="", color=ft.Colors.ERROR)


def ejecutar_mostrando_errores(accion: Callable[[], None], etiqueta: ft.Text) -> None:
    """
    Ejecuta una accion de la interfaz y muestra en `etiqueta` el error que lance, si lanza alguno.

    - `ErrorDeDominio` (el usuario se equivoco): se muestra su mensaje, que ya esta escrito para el usuario.
    - Cualquier otra excepcion es un bug: el usuario ve un mensaje generico y el traceback va al log.
      Atrapar `Exception` se justifica solo aca, en el borde de la app: si no, Flet cierra la sesion.

    No llama a `update()`: lo hace el handler de la pantalla (asi se testea con un `ft.Text` suelto).

    Args:
        accion (Callable[[], None]): Lo que hay que hacer (llamar al caso de uso, navegar...).
        etiqueta (ft.Text): Donde se muestra el error. Se limpia antes de ejecutar.
    """
    etiqueta.value = ""
    try:
        accion()
    except ErrorDeDominio as e:
        logger.warning(f"Error de dominio en la GUI: {e}")
        etiqueta.value = str(e)
    except Exception:
        logger.exception("Error inesperado en la GUI")
        etiqueta.value = MENSAJE_ERROR_INESPERADO
