"""Formulario comun (US-111, AC3): todos los formularios se ven y se usan igual.

Campos en columna con el ancho del tema, la etiqueta de error debajo de los campos, el boton principal
destacado y de ancho completo, y los secundarios como texto debajo. Enter en el ultimo campo de texto
hace lo mismo que el boton principal.
"""

from collections.abc import Callable, Sequence

import flet as ft

from infraestructura.ui.flet.estilo import ANCHO_FORMULARIO, ESPACIO


def crear_formulario(
    campos: Sequence[ft.Control],
    error: ft.Text,
    texto_principal: str,
    al_enviar: Callable[[], None],
    secundarios: Sequence[ft.Control] = (),
    ancho: int | None = ANCHO_FORMULARIO,
) -> ft.Column:
    """
    Arma el formulario y conecta el Enter del ultimo campo de texto con `al_enviar`.

    Args:
        campos (Sequence[ft.Control]): Campos en el orden en que se completan (pueden ir casillas).
        error (ft.Text): La etiqueta de `crear_etiqueta_error()`, que la pantalla sigue usando.
        texto_principal (str): Texto del boton principal ("Ingresar", "Crear club"...).
        al_enviar (Callable[[], None]): Handler del boton principal y del Enter.
        secundarios (Sequence[ft.Control]): Acciones secundarias (`ft.TextButton`), debajo del principal.
        ancho (int | None): Ancho del formulario; `None` ocupa el ancho de donde se lo ponga (un panel).

    Returns:
        ft.Column: El formulario armado.
    """
    textos = [c for c in campos if isinstance(c, ft.TextField)]
    if textos:
        textos[-1].on_submit = al_enviar
    return ft.Column(
        width=ancho,
        spacing=ESPACIO,
        # STRETCH: el boton principal ocupa todo el ancho, igual que los campos
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        controls=[*campos, error, ft.FilledButton(texto_principal, on_click=al_enviar), *secundarios],
    )
