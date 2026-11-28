"""Pantalla de detalle de un partido (US-114, separada del listado): resultado, cuartos, totales y boxscore.

Antes el boxscore se abria debajo del listado de partidos. Ahora es una pantalla propia
("/partidos/ver/5"), como en la maqueta, con todas las tablas a todo el ancho:

1. Puntos por cuarto, solo si el partido los tiene cargados.
2. Totales por equipo (`v_totales_equipo_partido`): lo unico que hay del rival si solo se cargaron sus totales.
3. Un boxscore por equipo, con los jugadores que tienen filas cargadas.

Arriba, una tarjeta con el marcador grande (el ganador en el color principal) y si el club activo gano
o perdio. En las tablas, los puntos van resaltados.
"""

import flet as ft

from aplicacion.casos_uso.eliminar_partido import EliminarPartidoUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.partido_dto import BoxscoreFilaDTO, PartidoResumenDTO, TotalesEquipoFilaDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.puntos_por_cuarto import filas_cuartos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO
from infraestructura.ui.flet.screens.carga_partido_screen import ruta_editar_partido

RUTA_DETALLE_PARTIDO = "/partidos/ver"  # lleva el id al final: "/partidos/ver/5"
TABLA_CUARTOS = "tabla_cuartos_partido"
TABLA_TOTALES = "tabla_totales_partido"
TABLA_BOXSCORE = "tabla_boxscore"
TARJETA_MARCADOR = "tarjeta_marcador_partido"
PARTIDO_NO_ENCONTRADO = "No se encontró el partido: puede que se haya eliminado o que no sea de tu club."
SIN_BOXSCORE = "Este partido todavía no tiene estadísticas cargadas en el boxscore."
COLUMNAS_BOXSCORE = (
    "Jugador",
    "Min",
    "PTS",
    "T2",
    "T3",
    "T1",
    "RD",
    "RO",
    "REB",
    "AST",
    "REC",
    "PER",
    "TAP+",
    "TAP-",
    "FR",
    "FC",
)
COLUMNAS_TOTALES = ("Equipo", "Origen", *COLUMNAS_BOXSCORE[2:])
ORIGENES = {"boxscore": "Suma del boxscore", "totales": "Totales cargados"}


def ruta_detalle_partido(id_partido: int) -> str:
    """Ruta de la pantalla de detalle de un partido: "/partidos/ver/5"."""
    return f"{RUTA_DETALLE_PARTIDO}/{id_partido}"


def clave_tabla_boxscore(nombre_club: str) -> str:
    """`key` de la tabla de boxscore de un equipo: hay una por equipo."""
    return f"{TABLA_BOXSCORE} · {nombre_club}"


def fila_totales(tot: TotalesEquipoFilaDTO) -> tuple[str, ...]:
    """Convierte los totales de un equipo en celdas legibles."""
    return (
        tot.nombreClub,
        ORIGENES.get(tot.origen, tot.origen),
        str(tot.puntos),
        f"{tot.t2c}/{tot.t2l}",
        f"{tot.t3c}/{tot.t3l}",
        f"{tot.t1c}/{tot.t1l}",
        str(tot.rebotesDef),
        str(tot.rebotesOf),
        str(tot.rebotesDef + tot.rebotesOf),
        str(tot.asistencias),
        str(tot.recuperos),
        str(tot.perdidas),
        str(tot.taponesRealizados),
        str(tot.taponesRecibidos),
        str(tot.faltasRecibidas),
        str(tot.faltasCometidas),
    )


def fila_boxscore(fila: BoxscoreFilaDTO) -> tuple[str, ...]:
    """Convierte una `BoxscoreFilaDTO` en celdas legibles (el club lo dice el titulo de la tabla)."""
    return (
        fila.nombreJugador,
        f"{fila.minutosJugados:g}",
        str(fila.puntos),
        f"{fila.t2c}/{fila.t2l}",
        f"{fila.t3c}/{fila.t3l}",
        f"{fila.t1c}/{fila.t1l}",
        str(fila.rebotesDef),
        str(fila.rebotesOf),
        str(fila.rebotesTotales),
        str(fila.asistencias),
        str(fila.recuperos),
        str(fila.perdidas),
        str(fila.taponesRealizados),
        str(fila.taponesRecibidos),
        str(fila.faltasRecibidas),
        str(fila.faltasCometidas),
    )


def _titulo_seccion(texto: str) -> ft.Container:
    return ft.Container(
        ft.Text(texto, weight=ft.FontWeight.W_600, size=16, color=ft.Colors.PRIMARY),
        padding=ft.Padding.only(top=ESPACIO),
    )


def resaltar(fila: tuple[str, ...], indice: int) -> tuple[str | ft.Control, ...]:
    """Pone en negrita y en el color principal una celda (los puntos), sin cambiar su texto."""
    return tuple(
        ft.Text(celda, weight=ft.FontWeight.W_700, color=ft.Colors.PRIMARY) if i == indice else celda
        for i, celda in enumerate(fila)
    )


def crear_tarjeta_marcador(resumen: PartidoResumenDTO, nombre_club: str) -> ft.Container:
    """Marcador grande: cada equipo con su condicion, el ganador en color y si el club activo gano o perdio."""
    pts_local, pts_visitante = resumen.puntosLocal, resumen.puntosVisitante
    hay_resultado = pts_local is not None and pts_visitante is not None
    gano_local = pts_local is not None and pts_visitante is not None and pts_local > pts_visitante

    def equipo(nombre: str, condicion: str, alineacion: ft.CrossAxisAlignment) -> ft.Column:
        return ft.Column(
            [
                ft.Text(nombre, size=20, weight=ft.FontWeight.W_600),
                ft.Text(condicion, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=0,
            horizontal_alignment=alineacion,
            expand=True,
        )

    def puntos(valor: int | None, gano: bool) -> ft.Text:
        return ft.Text(
            "—" if valor is None else str(valor),
            size=44,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.PRIMARY if gano else ft.Colors.ON_SURFACE_VARIANT,
        )

    controles: list[ft.Control] = [
        ft.Row(
            [
                equipo(resumen.clubLocal, "Local", ft.CrossAxisAlignment.END),
                puntos(pts_local, hay_resultado and gano_local),
                ft.Text("-", size=32, color=ft.Colors.ON_SURFACE_VARIANT),
                puntos(pts_visitante, hay_resultado and not gano_local),
                equipo(resumen.clubVisitante, "Visitante", ft.CrossAxisAlignment.START),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=ESPACIO,
        )
    ]
    if hay_resultado:
        gano_club = gano_local == (resumen.clubLocal == nombre_club)
        controles.append(
            ft.Container(
                ft.Text(
                    "Victoria" if gano_club else "Derrota",
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_PRIMARY_CONTAINER if gano_club else ft.Colors.ON_ERROR_CONTAINER,
                ),
                bgcolor=ft.Colors.PRIMARY_CONTAINER if gano_club else ft.Colors.ERROR_CONTAINER,
                border_radius=RADIO,
                padding=ft.Padding.symmetric(horizontal=ESPACIO, vertical=4),
            )
        )
    return ft.Container(
        key=TARJETA_MARCADOR,
        content=ft.Column(controles, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=ESPACIO_CHICO),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=RADIO,
        padding=ESPACIO,
    )


def crear_detalle_partido_view(
    page: ft.Page,
    listar_partidos_uc: ListarPartidosPorClubUseCase,
    obtener_partido_uc: ObtenerPartidoUseCase,
    obtener_boxscore_uc: ObtenerBoxscorePartidoUseCase,
    obtener_totales_uc: ObtenerTotalesPartidoUseCase,
    eliminar_partido_uc: EliminarPartidoUseCase,
    sesion: SessionManager,
    id_partido: int,
) -> ft.View:
    """
    Arma la pantalla de detalle de un partido del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        listar_partidos_uc (ListarPartidosPorClubUseCase): Da el resumen (nombres y resultado) del partido.
        obtener_partido_uc (ObtenerPartidoUseCase): Da los ids de los clubes y los cuartos.
        obtener_boxscore_uc (ObtenerBoxscorePartidoUseCase): Boxscore desde `v_boxscore_completo`.
        obtener_totales_uc (ObtenerTotalesPartidoUseCase): Totales por equipo desde `v_totales_equipo_partido`.
        eliminar_partido_uc (EliminarPartidoUseCase): Borra el partido con su boxscore, cuartos y totales.
        sesion (SessionManager): Sesion activa con club elegido.
        id_partido (int): El partido a mostrar.

    Returns:
        ft.View: La pantalla para la ruta "/partidos/ver/{id}".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de detalle de partido requiere un club activo")

    error = crear_etiqueta_error()
    volver = ft.TextButton("Volver a partidos", icon=ft.Icons.ARROW_BACK, on_click=lambda: page.navigate("/partidos"))
    # Solo se muestran partidos del club activo: el resumen sale de sus partidos.
    resumen: PartidoResumenDTO | None = next(
        (p for p in listar_partidos_uc.ejecutar(club.idClub) if p.idPartido == id_partido), None
    )
    partido = obtener_partido_uc.ejecutar(id_partido) if resumen is not None else None
    if resumen is None or partido is None:
        contenido = crear_pagina("Partido", [volver, ft.Text(PARTIDO_NO_ENCONTRADO)])
        return crear_vista_interna(page, sesion, ruta_detalle_partido(id_partido), contenido)

    def _eliminar() -> None:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_partido_uc.ejecutar(id_partido):
                    raise RuntimeError("No se pudo eliminar el partido de la base de datos")
                page.navigate("/partidos")

            ejecutar_mostrando_errores(accion, error)
            page.update()

        pedir_confirmacion(
            page,
            "Eliminar partido",
            f"Se borra {resumen.clubLocal} {resumen.resultado} {resumen.clubVisitante} ({resumen.fecha}) con su "
            "boxscore y sus cuartos. No se puede deshacer.",
            al_confirmar,
        )

    acciones = ft.Row(
        [
            volver,
            ft.OutlinedButton(
                "Editar partido", icon=ft.Icons.EDIT, on_click=lambda: page.navigate(ruta_editar_partido(id_partido))
            ),
            ft.TextButton("Eliminar partido", icon=ft.Icons.DELETE_OUTLINE, on_click=_eliminar),
        ],
        spacing=ESPACIO,
        wrap=True,
    )

    controles: list[ft.Control] = [crear_tarjeta_marcador(resumen, club.nombre), acciones, error]
    equipos = [(partido.idClubLocal, resumen.clubLocal), (partido.idClubVisitante, resumen.clubVisitante)]
    if partido.cuartos:
        columnas, filas = filas_cuartos(partido.cuartos, equipos)
        filas_q = [resaltar(f, len(f) - 1) for f in filas]  # el total
        controles += [_titulo_seccion("Puntos por cuarto"), crear_tabla_datos(columnas, filas_q, clave=TABLA_CUARTOS)]

    controles += [
        _titulo_seccion("Totales por equipo"),
        crear_tabla_datos(
            COLUMNAS_TOTALES,
            [resaltar(fila_totales(t), 2) for t in obtener_totales_uc.ejecutar(id_partido)],
            mensaje_vacio=SIN_BOXSCORE,
            clave=TABLA_TOTALES,
        ),
    ]

    filas_bs = obtener_boxscore_uc.ejecutar(id_partido)
    if not filas_bs:
        controles += [_titulo_seccion("Boxscore"), ft.Text(SIN_BOXSCORE, key=TABLA_BOXSCORE)]
    for id_club, nombre in equipos:
        del_equipo = [resaltar(fila_boxscore(f), 2) for f in filas_bs if f.idClub == id_club]
        if del_equipo:
            controles += [
                _titulo_seccion(f"Boxscore · {nombre}"),
                crear_tabla_datos(COLUMNAS_BOXSCORE, del_equipo, clave=clave_tabla_boxscore(nombre)),
            ]

    subtitulo = " · ".join(
        parte
        for parte in (
            resumen.fecha,
            f"{resumen.competencia} {resumen.anioCompetencia}",
            resumen.categoria,
            resumen.estadio,
        )
        if parte
    )
    contenido = crear_pagina(
        f"{resumen.clubLocal} vs {resumen.clubVisitante}",
        [ft.Column(controles, spacing=ESPACIO_CHICO)],
        subtitulo=subtitulo,
    )
    return crear_vista_interna(page, sesion, ruta_detalle_partido(id_partido), contenido)
