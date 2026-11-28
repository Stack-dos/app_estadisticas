"""Pantalla "Guía" (US-114): el manual de uso, escrito para el entrenador, en `src/assets/guia.md`.

El texto vive en un archivo Markdown y no en el codigo: se corrige o se amplia sin tocar Python, y
`ft.Markdown` lo dibuja con titulos, listas y negritas. Se abre con o sin sesion: con sesion se ve dentro
de la app (menu y barra); sin sesion (desde el login) es una pantalla suelta con "Volver".
"""

from pathlib import Path

import flet as ft

import config.rutas as r
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.estilo import ESPACIO_GRANDE

RUTA_GUIA = "/guia"
CLAVE_TEXTO_GUIA = "texto_guia"
GUIA_NO_ENCONTRADA = "No se encontró el manual de uso (falta el archivo guia.md)."


def leer_guia(ruta: str = r.GUIA_MD) -> str:
    """
    Lee el manual en Markdown.

    Args:
        ruta (str): Donde esta el archivo (en los tests, uno temporal).

    Returns:
        str: El texto del manual, o un aviso si el archivo no esta.
    """
    try:
        return Path(ruta).read_text(encoding="utf-8")
    except OSError:
        return GUIA_NO_ENCONTRADA


def crear_guia_view(page: ft.Page, sesion: SessionManager, ruta_md: str = r.GUIA_MD) -> ft.View:
    """
    Arma la pantalla del manual de uso.

    Args:
        page (ft.Page): La ventana, para navegar.
        sesion (SessionManager): Decide si se muestra dentro de la app o suelta.
        ruta_md (str): El archivo del manual.

    Returns:
        ft.View: La pantalla para la ruta "/guia".
    """
    texto = ft.Markdown(
        leer_guia(ruta_md),
        key=CLAVE_TEXTO_GUIA,
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )
    if sesion.is_authenticated():
        return crear_vista_interna(page, sesion, RUTA_GUIA, crear_pagina("Guía de uso", [texto]))
    return ft.View(
        route=RUTA_GUIA,
        padding=ESPACIO_GRANDE,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.TextButton("Volver", icon=ft.Icons.ARROW_BACK, on_click=lambda: page.navigate("/login")),
            texto,
        ],
    )
