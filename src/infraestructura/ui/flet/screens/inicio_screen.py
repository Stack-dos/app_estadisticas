"""Pantalla principal, solo con sesion (US-105, AC3).

Todavia no tiene secciones: el menu lo llenan la US-106 (club activo) y la US-107 (pantallas de
gestion). Por ahora saluda al usuario y permite cerrar la sesion.
"""

import flet as ft

from aplicacion.servicios.session_manager import SessionManager


def crear_inicio_view(page: ft.Page, sesion: SessionManager) -> ft.View:
    """
    Arma la pantalla principal. Solo se construye con sesion iniciada (lo garantiza la ruta protegida).

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        sesion (SessionManager): Sesion en memoria: de ahi sale el nombre y se cierra al salir.

    Returns:
        ft.View: La pantalla, para la ruta "/inicio".
    """
    usuario = sesion.usuario_actual()

    def cerrar_sesion() -> None:
        """Handler de "Cerrar sesion": cierra la sesion y vuelve al login."""
        sesion.cerrar_sesion()
        page.navigate("/login")

    return ft.View(
        route="/inicio",
        appbar=ft.AppBar(
            title=ft.Text("StatsPro"),
            actions=[ft.TextButton("Cerrar sesión", on_click=cerrar_sesion)],
        ),
        controls=[ft.Text(f"Hola, {usuario.nombre}", size=24)],
    )
