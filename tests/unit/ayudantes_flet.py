"""Ayudantes para testear pantallas de Flet sin ventana: buscan controles por tipo y texto, no por posicion.

Asi un test no se rompe si se reordena el formulario. Se importan directo (`from ayudantes_flet import ...`)
porque pytest agrega la carpeta del test al `sys.path`.
"""

import flet as ft


def campo(vista: ft.View, label: str) -> ft.TextField:
    return next(c for c in vista.controls if isinstance(c, ft.TextField) and c.label == label)


def boton(vista: ft.View, texto: str) -> ft.Button | ft.TextButton:
    """Busca un boton por su texto, en los controles y en las acciones de la `AppBar`."""
    acciones = list(vista.appbar.actions or []) if isinstance(vista.appbar, ft.AppBar) else []
    return next(
        c for c in [*vista.controls, *acciones] if isinstance(c, ft.Button | ft.TextButton) and c.content == texto
    )


def casilla(vista: ft.View, label: str) -> ft.Checkbox:
    return next(c for c in vista.controls if isinstance(c, ft.Checkbox) and c.label == label)


def textos(vista: ft.View) -> list[str]:
    """Todos los textos sueltos de la pantalla (no los de botones ni campos)."""
    return [c.value for c in vista.controls if isinstance(c, ft.Text) and isinstance(c.value, str)]


def etiqueta_error(vista: ft.View) -> ft.Text:
    return next(c for c in vista.controls if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR)
