"""Pantalla principal, solo con sesion (US-105, AC3; club activo de la US-106; tablero de la US-113).

Saluda al usuario y, si no eligio un club, lo invita a hacerlo. Con club activo muestra un tablero
chico: el ultimo partido con su resultado, accesos rapidos a lo que mas se usa y los lideres del club
en puntos (con rebotes y asistencias). Cerrar sesion esta en la barra superior compartida.
"""

import flet as ft

from aplicacion.casos_uso.listar_lideres_club import ListarLideresClubUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.partido_dto import LiderClubDTO, PartidoResumenDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO

TARJETA_ULTIMO_PARTIDO = "tarjeta_ultimo_partido"
TABLA_LIDERES = "tabla_lideres"
COLUMNAS_LIDERES = ("Jugador", "PJ", "PTS", "REB", "AST")
SIN_PARTIDOS = "Todavía no cargaste partidos de este club."
SIN_LIDERES = "Los líderes aparecen cuando cargues el primer partido."


def fila_lider(lider: LiderClubDTO) -> tuple[str, str, str, str, str]:
    """Convierte un lider en celdas: nombre, partidos jugados y promedios por partido."""
    return (
        lider.nombreJugador,
        str(lider.partidosJugados),
        f"{lider.puntosPromedio:.1f}",
        f"{lider.rebotesPromedio:.1f}",
        f"{lider.asistenciasPromedio:.1f}",
    )


def _tarjeta(titulo: str, contenido: list[ft.Control], clave: str | None = None) -> ft.Container:
    return ft.Container(
        key=clave,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border_radius=RADIO,
        padding=ESPACIO,
        content=ft.Column([ft.Text(titulo, weight=ft.FontWeight.W_600), *contenido], spacing=ESPACIO_CHICO),
    )


def _tarjeta_ultimo_partido(partidos: list[PartidoResumenDTO], club: ClubDTO) -> ft.Container:
    if not partidos:
        return _tarjeta(
            "Último partido", [ft.Text(SIN_PARTIDOS, color=ft.Colors.ON_SURFACE_VARIANT)], TARJETA_ULTIMO_PARTIDO
        )
    ultimo = partidos[-1]  # vienen del mas antiguo al mas reciente
    rival = ultimo.clubVisitante if ultimo.clubLocal == club.nombre else ultimo.clubLocal
    condicion = "de local" if ultimo.clubLocal == club.nombre else "de visitante"
    return _tarjeta(
        "Último partido",
        [
            ft.Text(
                f"{ultimo.clubLocal} {ultimo.resultado} {ultimo.clubVisitante}", size=20, weight=ft.FontWeight.W_600
            ),
            ft.Text(
                f"{ultimo.fecha} · {ultimo.competencia} ({ultimo.anioCompetencia}) · vs {rival}, {condicion}",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
        ],
        TARJETA_ULTIMO_PARTIDO,
    )


def crear_inicio_view(
    page: ft.Page,
    sesion: SessionManager,
    listar_partidos_uc: ListarPartidosPorClubUseCase,
    listar_lideres_uc: ListarLideresClubUseCase,
) -> ft.View:
    """
    Arma la pantalla principal. Solo se construye con sesion iniciada (lo garantiza la ruta protegida).

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        sesion (SessionManager): Sesion en memoria: de ahi salen el nombre y el club activo.
        listar_partidos_uc (ListarPartidosPorClubUseCase): Partidos del club, para el ultimo resultado.
        listar_lideres_uc (ListarLideresClubUseCase): Lideres del club en puntos.

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
    else:
        partidos = listar_partidos_uc.ejecutar(club.idClub)
        lideres = listar_lideres_uc.ejecutar(club.idClub)
        accesos = ft.Row(
            [
                ft.FilledButton(
                    "Cargar partido", icon=ft.Icons.ADD_CHART, on_click=lambda: page.navigate("/partidos/cargar")
                ),
                ft.OutlinedButton("Ver partidos", icon=ft.Icons.LIST, on_click=lambda: page.navigate("/partidos")),
                ft.OutlinedButton("Jugadores", icon=ft.Icons.GROUPS, on_click=lambda: page.navigate("/jugadores")),
                ft.OutlinedButton(
                    "Listas de buena fe", icon=ft.Icons.FACT_CHECK, on_click=lambda: page.navigate("/listas")
                ),
            ],
            spacing=ESPACIO_CHICO,
            wrap=True,
        )
        tabla_lideres = crear_tabla_datos(
            COLUMNAS_LIDERES, [fila_lider(lider) for lider in lideres], mensaje_vacio=SIN_LIDERES, clave=TABLA_LIDERES
        )
        controles += [
            accesos,
            ft.ResponsiveRow(
                spacing=ESPACIO,
                run_spacing=ESPACIO,
                controls=[
                    ft.Container(_tarjeta_ultimo_partido(partidos, club), col={"md": 12, "lg": 5}),
                    ft.Container(
                        _tarjeta("Líderes del club (promedio por partido)", [tabla_lideres]), col={"md": 12, "lg": 7}
                    ),
                ],
            ),
        ]
    subtitulo = f"Club activo: {club.nombre}." if club is not None else None
    contenido = crear_pagina(f"Hola, {usuario.nombre}", controles, subtitulo=subtitulo)
    return crear_vista_interna(page, sesion, "/inicio", contenido)
