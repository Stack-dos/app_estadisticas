"""Barra superior compartida por todas las pantallas internas (US-106).

Muestra el club activo y la navegacion comun. Se arma de nuevo con cada pantalla (el router reconstruye
la `View` en cada cambio de ruta), asi que siempre refleja el club actual sin tener que "avisarle" nada.
"""

import flet as ft

from aplicacion.servicios.session_manager import SessionManager

SIN_CLUB = "Sin club elegido"


def crear_barra_superior(page: ft.Page, sesion: SessionManager) -> ft.AppBar:
    """
    Arma la barra: "StatsPro · <club activo>" a la izquierda; Inicio, Clubes y Cerrar sesión a la derecha.

    Args:
        page (ft.Page): La ventana, para navegar.
        sesion (SessionManager): De donde sale el club activo; se cierra con "Cerrar sesión".

    Returns:
        ft.AppBar: La barra, para el `appbar` de la `View`.
    """
    club = sesion.club_activo()

    def cerrar_sesion() -> None:
        """Handler de "Cerrar sesión". El orden importa: con la sesion abierta, el router devolveria a "/inicio"."""
        sesion.cerrar_sesion()
        page.navigate("/login")

    return ft.AppBar(
        title=ft.Text(f"StatsPro · {club.nombre if club is not None else SIN_CLUB}"),
        actions=[
            ft.TextButton("Inicio", on_click=lambda: page.navigate("/inicio")),
            ft.TextButton("Clubes", on_click=lambda: page.navigate("/clubes")),
            ft.TextButton("Cerrar sesión", on_click=cerrar_sesion),
        ],
    )
