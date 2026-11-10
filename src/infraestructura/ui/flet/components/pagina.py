"""Pagina comun (US-111, AC2): como se arma cada pantalla.

Tres piezas, de adentro hacia afuera:

- `crear_pagina`: el contenido. Titulo, subtitulo, controles y un panel lateral opcional, con margen
  y un ancho maximo para que no se estire de borde a borde en una ventana maximizada.
- `crear_vista_interna`: las pantallas con sesion. Barra superior, menu lateral a la izquierda y el
  contenido a la derecha, con desplazamiento vertical (scroll) si no entra.
- `crear_vista_acceso`: login y registro. Panel de marca (logo y nombre) a la izquierda y el
  formulario centrado a la derecha.
"""

from collections.abc import Sequence

import flet as ft

from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.barra_superior import crear_barra_superior
from infraestructura.ui.flet.components.menu_lateral import crear_menu_lateral
from infraestructura.ui.flet.estilo import (
    ANCHO_FORMULARIO,
    ANCHO_MAXIMO,
    ESPACIO,
    ESPACIO_CHICO,
    ESPACIO_GRANDE,
    LEMA_APP,
    LOGO_BLANCO,
    NOMBRE_APP,
    RADIO,
    TAMANIO_LOGO_MARCA,
    TAMANIO_MARCA,
    TAMANIO_TITULO,
)


def crear_encabezado(titulo: str, subtitulo: str | None = None) -> ft.Column:
    """Titulo de la pantalla y, si hay, una linea de contexto debajo."""
    controles: list[ft.Control] = [ft.Text(titulo, size=TAMANIO_TITULO, weight=ft.FontWeight.W_600)]
    if subtitulo:
        controles.append(ft.Text(subtitulo, color=ft.Colors.ON_SURFACE_VARIANT))
    return ft.Column(controles, spacing=0)


def crear_pagina(
    titulo: str,
    controles: Sequence[ft.Control],
    *,
    subtitulo: str | None = None,
    lateral: ft.Control | None = None,
) -> ft.Container:
    """
    Arma el contenido de una pantalla interna.

    Args:
        titulo (str): Titulo de la pantalla.
        controles (Sequence[ft.Control]): El contenido, de arriba hacia abajo.
        subtitulo (str | None): Linea de contexto debajo del titulo.
        lateral (ft.Control | None): Panel a la derecha del contenido (por ejemplo, el alta de un
            formulario junto al listado). Va sobre un fondo apenas distinto.

    Returns:
        ft.Container: El contenido con margen y ancho maximo.
    """
    cuerpo: ft.Control = ft.Column(list(controles), spacing=ESPACIO)
    if lateral is not None:
        panel = ft.Container(
            content=lateral,
            width=ANCHO_FORMULARIO,
            padding=ESPACIO,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border_radius=RADIO,
        )
        cuerpo = ft.Row(
            [ft.Container(content=cuerpo, expand=True), panel],
            spacing=ESPACIO_GRANDE,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    return ft.Container(
        content=ft.Column([crear_encabezado(titulo, subtitulo), cuerpo], spacing=ESPACIO_GRANDE),
        max_width=ANCHO_MAXIMO,
        padding=ESPACIO_GRANDE,
    )


def crear_vista_interna(page: ft.Page, sesion: SessionManager, ruta: str, contenido: ft.Control) -> ft.View:
    """
    Arma una pantalla con sesion: barra superior, menu lateral y el contenido con scroll.

    Args:
        page (ft.Page): La ventana, para navegar.
        sesion (SessionManager): Para la barra (club activo, cerrar sesion).
        ruta (str): La ruta de la pantalla; marca su destino en el menu.
        contenido (ft.Control): Lo que arma `crear_pagina`.

    Returns:
        ft.View: La pantalla, para la tabla de rutas.
    """
    return ft.View(
        route=ruta,
        appbar=crear_barra_superior(page, sesion),
        padding=0,
        controls=[
            ft.Row(
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    crear_menu_lateral(page, ruta),
                    ft.VerticalDivider(width=1),
                    # START: el contenido queda arriba a la izquierda, con su ancho maximo
                    ft.Column([contenido], expand=True, scroll=ft.ScrollMode.AUTO),
                ],
            )
        ],
    )


def crear_vista_acceso(ruta: str, titulo: str, subtitulo: str, formulario: ft.Control) -> ft.View:
    """
    Arma login y registro: marca a la izquierda, formulario centrado a la derecha.

    Args:
        ruta (str): "/login" o "/registro".
        titulo (str): Titulo sobre el formulario.
        subtitulo (str): Para que sirve la pantalla, en una linea.
        formulario (ft.Control): Lo que arma `crear_formulario`.

    Returns:
        ft.View: La pantalla, para la tabla de rutas.
    """
    marca = ft.Container(
        expand=2,
        bgcolor=ft.Colors.PRIMARY,
        padding=ESPACIO_GRANDE,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            tight=True,
            spacing=ESPACIO_CHICO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Image(src=LOGO_BLANCO, width=TAMANIO_LOGO_MARCA, height=TAMANIO_LOGO_MARCA),
                ft.Text(NOMBRE_APP, size=TAMANIO_MARCA, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_PRIMARY),
                ft.Text(LEMA_APP, color=ft.Colors.ON_PRIMARY),
            ],
        ),
    )
    # Sin scroll a proposito: una Column con scroll no puede centrar en vertical (adentro de un scroll la
    # altura no tiene limite, asi que no hay "centro"). El formulario mas alto (registro) entra en el alto
    # minimo de la ventana.
    lado_formulario = ft.Column(
        expand=3,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ESPACIO_GRANDE,
                # Mismo ancho que el formulario: si no, un subtitulo largo estiraria la columna
                content=ft.Column(
                    [crear_encabezado(titulo, subtitulo), formulario],
                    width=ANCHO_FORMULARIO,
                    spacing=ESPACIO_GRANDE,
                ),
            )
        ],
    )
    return ft.View(
        route=ruta,
        padding=0,
        controls=[ft.Row([marca, lado_formulario], expand=True, spacing=0)],
    )
