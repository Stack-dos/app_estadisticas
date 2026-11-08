"""Pantalla principal, solo con sesion (US-105, AC3; club activo de la US-106).

Todavia no tiene secciones: las pantallas de gestion llegan con la US-107. Saluda al usuario y, si no
eligio un club, lo invita a hacerlo. Cerrar sesion esta en la barra superior compartida.
"""

import flet as ft

from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.barra_superior import crear_barra_superior


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
    controles: list[ft.BaseControl] = [ft.Text(f"Hola, {usuario.nombre}", size=24)]
    if sesion.club_activo() is None:
        controles += [
            ft.Text("Elegí un club para empezar."),
            ft.Button("Elegir club", on_click=lambda: page.navigate("/clubes")),
        ]

    return ft.View(route="/inicio", appbar=crear_barra_superior(page, sesion), controls=controles)
