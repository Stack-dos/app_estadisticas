"""Tabla reutilizable de la GUI (US-107): encabezados y filas con estilo uniforme y filas alternadas.

Usa colores y espaciados de `estilo.py` (US-111): una fila si y otra no con fondo `SURFACE_CONTAINER_LOW` y,
desde la US-114, el encabezado con fondo de color (`SECONDARY_CONTAINER`, la opcion "Encabezado con fondo" de
la maqueta), que en modo oscuro separa bien los titulos de los datos.
La usan las pantallas de gestion (US-107, US-112) y los reportes/tablas de estadisticas (Hito 2 y 3).
"""

from collections.abc import Sequence

import flet as ft

from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, ESPACIO_GRANDE, RADIO

Celda = str | ft.Control


def crear_tabla_datos(
    columnas: Sequence[str],
    filas: Sequence[Sequence[Celda]],
    *,
    mensaje_vacio: str = "Sin datos para mostrar.",
    clave: str | None = None,
) -> ft.Control:
    """
    Arma una tabla legible con filas alternadas a partir de encabezados y filas ya formateadas.

    Args:
        columnas (Sequence[str]): Nombres de las columnas.
        filas (Sequence[Sequence[Celda]]): Filas de la tabla. Cada celda puede ser texto o un `ft.Control`
            (por ejemplo, un boton de accion).
        mensaje_vacio (str): Texto a mostrar cuando `filas` esta vacia.
        clave (str | None): `key` opcional del control devuelto para localizarlo en tests.

    Returns:
        ft.Control: Una `ft.Row` con la `ft.DataTable` a todo el ancho cuando hay filas (la `clave` va en la
            tabla), o un `ft.Container` con el `mensaje_vacio`.
    """
    if not filas:
        return ft.Container(
            content=ft.Text(mensaje_vacio, color=ft.Colors.ON_SURFACE_VARIANT),
            padding=ESPACIO_CHICO,
            key=clave,
        )

    columnas_dt = [
        ft.DataColumn(label=ft.Text(nombre, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SECONDARY_CONTAINER))
        for nombre in columnas
    ]
    filas_dt = [
        ft.DataRow(
            cells=[ft.DataCell(ft.Text(celda) if isinstance(celda, str) else celda) for celda in fila],
            color=ft.Colors.SURFACE_CONTAINER_LOW if indice % 2 == 1 else None,
        )
        for indice, fila in enumerate(filas)
    ]
    tabla = ft.DataTable(
        key=clave,
        expand=True,
        columns=columnas_dt,
        rows=filas_dt,
        column_spacing=ESPACIO_GRANDE,
        horizontal_margin=ESPACIO,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIO,
        heading_row_color=ft.Colors.SECONDARY_CONTAINER,
    )
    # Una DataTable sola mide lo que su contenido; `expand` dentro de una Row la estira al ancho disponible.
    return ft.Row([tabla])
