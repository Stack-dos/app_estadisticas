"""Menu lateral de las pantallas internas (US-111): logo arriba y un destino por seccion.

Reemplaza a los botones "Inicio" y "Clubes" que tenia la barra superior (US-106). Cada US que suma una
seccion (Jugadores, Torneos, Partidos, Estadisticas...) agrega su fila a `DESTINOS`.

US-114: abajo del menu va el boton "Guía" (`crear_boton_guia`), que abre el manual de uso.
"""

from dataclasses import dataclass

import flet as ft

from infraestructura.ui.flet.estilo import LOGO, NOMBRE_APP, TAMANIO_LOGO_MENU


@dataclass(frozen=True)
class Destino:
    """Una entrada del menu: a que ruta va, que dice, que icono usa y que sub-rutas agrupa."""

    ruta: str
    texto: str
    icono: ft.IconData
    icono_elegido: ft.IconData
    subrutas: tuple[str, ...] = ()


DESTINOS = (
    Destino("/inicio", "Inicio", ft.Icons.HOME_OUTLINED, ft.Icons.HOME),
    Destino("/clubes", "Mis clubes", ft.Icons.SHIELD_OUTLINED, ft.Icons.SHIELD),
    Destino("/jugadores", "Jugadores", ft.Icons.GROUPS_OUTLINED, ft.Icons.GROUPS),
    Destino(
        "/partidos",
        "Partidos",
        ft.Icons.SPORTS_BASKETBALL_OUTLINED,
        ft.Icons.SPORTS_BASKETBALL,
        subrutas=("/partidos/cargar", "/partidos/editar", "/partidos/ver"),
    ),
    Destino(
        "/competencias",
        "Torneos",
        ft.Icons.EMOJI_EVENTS_OUTLINED,
        ft.Icons.EMOJI_EVENTS,
        subrutas=("/categorias", "/inscripciones", "/listas"),
    ),
)


def _indice_destino(ruta_actual: str) -> int | None:
    for indice, destino in enumerate(DESTINOS):
        # "/partidos/editar/5" cae en la subruta "/partidos/editar": las rutas con id comparan el comienzo
        if ruta_actual == destino.ruta or any(
            ruta_actual == sub or ruta_actual.startswith(sub + "/") for sub in destino.subrutas
        ):
            return indice
    return None


def crear_menu_lateral(page: ft.Page, ruta_actual: str) -> ft.NavigationRail:
    """
    Arma el menu con el destino de `ruta_actual` marcado.

    Args:
        page (ft.Page): La ventana, para navegar.
        ruta_actual (str): La ruta de la pantalla que lo muestra.

    Returns:
        ft.NavigationRail: El menu, para el costado izquierdo de la pantalla.
    """
    rutas = [d.ruta for d in DESTINOS]

    def al_elegir() -> None:
        """Handler de `on_change`: Flet ya actualizo `selected_index` con el destino elegido."""
        if menu.selected_index is not None:
            page.navigate(rutas[menu.selected_index])

    menu = ft.NavigationRail(
        selected_index=_indice_destino(ruta_actual),
        label_type=ft.NavigationRailLabelType.ALL,
        leading=ft.Image(src=LOGO, width=TAMANIO_LOGO_MENU, height=TAMANIO_LOGO_MENU, semantics_label=NOMBRE_APP),
        destinations=[
            ft.NavigationRailDestination(icon=d.icono, selected_icon=d.icono_elegido, label=d.texto) for d in DESTINOS
        ],
        on_change=al_elegir,
    )
    return menu


CLAVE_BOTON_GUIA = "boton_guia"


def crear_boton_guia(page: ft.Page) -> ft.TextButton:
    """
    Boton "Guía" del pie del menu: abre el manual de uso ("/guia").

    Args:
        page (ft.Page): La ventana, para navegar.

    Returns:
        ft.TextButton: El boton, para debajo del menu lateral.
    """
    return ft.TextButton(
        "Guía",
        key=CLAVE_BOTON_GUIA,
        icon=ft.Icons.HELP_OUTLINE,
        tooltip="Cómo se usa la aplicación",
        on_click=lambda: page.navigate("/guia"),
    )
