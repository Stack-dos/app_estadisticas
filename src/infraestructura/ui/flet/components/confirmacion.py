"""Dialogo de confirmacion reutilizable para acciones destructivas de la GUI (US-107)."""

from collections.abc import Callable

import flet as ft


def pedir_confirmacion(
    page: ft.Page,
    titulo: str,
    mensaje: str,
    al_confirmar: Callable[[], None],
    *,
    texto_confirmar: str = "Eliminar",
) -> None:
    """
    Muestra un dialogo modal pidiendo confirmacion antes de ejecutar una accion irreversible.

    Args:
        page (ft.Page): La ventana donde se abre el dialogo (`show_dialog` / `pop_dialog`).
        titulo (str): Titulo del dialogo.
        mensaje (str): Explicacion clara de lo que se va a borrar o dar de baja.
        al_confirmar (Callable[[], None]): Accion a ejecutar si el usuario confirma.
        texto_confirmar (str): Texto del boton de confirmacion.
    """

    def cancelar() -> None:
        page.pop_dialog()

    def confirmar() -> None:
        page.pop_dialog()
        al_confirmar()

    dialogo = ft.AlertDialog(
        modal=True,
        title=ft.Text(titulo),
        content=ft.Text(mensaje),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar),
            ft.FilledButton(texto_confirmar, on_click=confirmar),
        ],
    )
    page.show_dialog(dialogo)
