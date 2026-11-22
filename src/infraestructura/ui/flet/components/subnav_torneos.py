"""Barra de sub-navegacion de la seccion Torneos (US-107).

Mantiene desacopladas las tres pantallas (`CompetenciasScreen`, `InscripcionesScreen` y `ListaBuenaFeScreen`,
AC1): cada una vive en su archivo y se navega entre ellas por ruta (`page.navigate`).
"""

import flet as ft

from infraestructura.ui.flet.estilo import ESPACIO_CHICO

SUBDESTINOS_TORNEOS: tuple[tuple[str, str], ...] = (
    ("/competencias", "Competencias"),
    ("/inscripciones", "Inscripciones"),
    ("/listas", "Listas de buena fe"),
)


def crear_subnav_torneos(page: ft.Page, ruta_actual: str) -> ft.Row:
    """
    Arma la fila de pestañas/botones para cambiar entre Competencias, Inscripciones y Listas de buena fe.

    Args:
        page (ft.Page): La ventana, para navegar por ruta.
        ruta_actual (str): Ruta de la pantalla activa, cuyo boton queda destacado.

    Returns:
        ft.Row: Fila de botones de navegacion.
    """

    def boton_ruta(ruta: str, texto: str) -> ft.Control:
        if ruta == ruta_actual:
            return ft.FilledButton(texto, on_click=lambda: page.navigate(ruta))
        return ft.TextButton(texto, on_click=lambda: page.navigate(ruta))

    return ft.Row(
        [boton_ruta(ruta, texto) for ruta, texto in SUBDESTINOS_TORNEOS],
        spacing=ESPACIO_CHICO,
        wrap=True,
    )
