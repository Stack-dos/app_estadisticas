"""Ayudantes para testear pantallas de Flet sin ventana: buscan controles por tipo y texto, no por posicion.

Asi un test no se rompe si se reordena el formulario o si un control queda envuelto en otro (desde la
US-111 los campos viven dentro de `crear_formulario` y de `crear_pagina`): se recorre el arbol completo.
Se importan directo (`from ayudantes_flet import ...`) porque pytest agrega la carpeta del test al `sys.path`.
"""

from collections.abc import Iterator

import flet as ft

# Atributos donde un control de Flet guarda a sus hijos. `content` de un boton puede ser un str: se ignora.
_HIJOS = ("appbar", "controls", "content", "leading", "title", "subtitle", "trailing", "actions")


def controles(raiz: ft.BaseControl) -> Iterator[ft.BaseControl]:
    """Recorre en profundidad `raiz` y todos sus descendientes, en orden de aparicion."""
    yield raiz
    for atributo in _HIJOS:
        valor = getattr(raiz, atributo, None)
        hijos = valor if isinstance(valor, list) else [valor]
        for hijo in hijos:
            if isinstance(hijo, ft.BaseControl):
                yield from controles(hijo)


def campo(vista: ft.View, label: str) -> ft.TextField:
    return next(c for c in controles(vista) if isinstance(c, ft.TextField) and c.label == label)


def boton(vista: ft.View, texto: str) -> ft.Button | ft.TextButton:
    """Busca un boton por su texto en toda la pantalla, incluidas las acciones de la `AppBar`."""
    return next(c for c in controles(vista) if isinstance(c, ft.Button | ft.TextButton) and c.content == texto)


def casilla(vista: ft.View, label: str) -> ft.Checkbox:
    return next(c for c in controles(vista) if isinstance(c, ft.Checkbox) and c.label == label)


def textos(vista: ft.View) -> list[str]:
    """Todos los textos de la pantalla (no los de botones ni campos, que no son `ft.Text`)."""
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and isinstance(c.value, str)]


def etiqueta_error(vista: ft.View) -> ft.Text:
    return next(c for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR)


def por_clave(vista: ft.View, clave: str) -> ft.BaseControl:
    """Busca el control con esa `key` (para los que no tienen texto propio, como una lista)."""
    return next(c for c in controles(vista) if c.key == clave)
