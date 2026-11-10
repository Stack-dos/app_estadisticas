"""Pantalla principal, solo con sesion (US-105, AC3; club activo de la US-106).

Todavia no tiene secciones: las pantallas de gestion llegan con las US-107 y US-112. Saluda al usuario
y, si no eligio un club, lo invita a hacerlo. Cerrar sesion esta en la barra superior compartida.
"""

import flet as ft

from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna


def crear_inicio_view(page: ft.Page, sesion: SessionManager) -> ft.View:
    """
    Arma la pantalla principal. Solo se construye con sesion iniciada (lo garantiza la ruta protegida).

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        sesion (SessionManager): Sesion en memoria: de ahi salen el nombre y el club activo.

    Returns:
        ft.View: La pantalla, para la ruta "/inicio".
    """
    usuario = sesion.usuario_actual()
    club = sesion.club_activo()
    controles: list[ft.Control] = []
    if club is None:
        controles += [
            ft.Text("Elegí un club para empezar."),
            ft.FilledButton("Elegir club", on_click=lambda: page.navigate("/clubes")),
        ]
    subtitulo = f"Club activo: {club.nombre}." if club is not None else None
    contenido = crear_pagina(f"Hola, {usuario.nombre}", controles, subtitulo=subtitulo)
    return crear_vista_interna(page, sesion, "/inicio", contenido)
