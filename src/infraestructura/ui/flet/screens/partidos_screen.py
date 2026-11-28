"""Pantalla de partidos del club activo (US-112): listado filtrado por competencia y categoria.

US-113: el listado muestra el resultado. US-114 (ajuste con la maqueta): suma la categoria y el
cuadradito G/P, el filtro de categoria ofrece todo el catalogo y "Ver" abre el detalle en su propia
pantalla (`detalle_partido_screen.py`), donde estan editar y eliminar.
"""

import flet as ft

from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO
from aplicacion.dtos.partido_dto import PartidoResumenDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error
from infraestructura.ui.flet.estilo import ESPACIO
from infraestructura.ui.flet.screens.detalle_partido_screen import ruta_detalle_partido

TABLA_PARTIDOS = "tabla_partidos"
COLUMNAS_PARTIDOS = ("Fecha", "Competencia", "Cat.", "Local", "Resultado", "Visitante", "", "")
SIN_PARTIDOS = "No hay partidos para mostrar con los filtros elegidos."
AVISO_CATEGORIA_PENDIENTE = (
    "Los partidos cargados antes de la carga por categoría todavía no tienen categoría asignada."
)
GANADO, PERDIDO = "G", "P"


def fila_partido(partido: PartidoResumenDTO) -> tuple[str, str, str, str, str, str]:
    """Convierte un `PartidoResumenDTO` en las columnas de texto de la tabla sin exponer IDs."""
    return (
        partido.fecha,
        f"{partido.competencia} {partido.anioCompetencia}",
        partido.categoria or "—",
        partido.clubLocal,
        partido.resultado,
        partido.clubVisitante,
    )


def resultado_del_club(partido: PartidoResumenDTO, nombre_club: str) -> str | None:
    """Devuelve "G" si el club gano, "P" si perdio y None sin puntos cargados (no hay empates, US-114).

    Compara por nombre: los nombres de club son unicos (`ClubYaExisteError`).
    """
    if partido.puntosLocal is None or partido.puntosVisitante is None:
        return None
    gano_local = partido.puntosLocal > partido.puntosVisitante
    return GANADO if gano_local == (partido.clubLocal == nombre_club) else PERDIDO


def crear_marca_resultado(resultado: str | None) -> ft.Control:
    """Cuadradito "G" (color primario) o "P" (color de error) como en la maqueta; vacio sin resultado."""
    if resultado is None:
        return ft.Text("")
    ganado = resultado == GANADO
    return ft.Container(
        content=ft.Text(
            resultado,
            size=12,
            weight=ft.FontWeight.W_600,
            color=ft.Colors.ON_PRIMARY_CONTAINER if ganado else ft.Colors.ON_ERROR_CONTAINER,
        ),
        width=24,
        height=24,
        border_radius=6,
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.PRIMARY_CONTAINER if ganado else ft.Colors.ERROR_CONTAINER,
        tooltip="Ganado" if ganado else "Perdido",
    )


def filtrar_partidos(
    partidos: list[PartidoResumenDTO],
    *,
    competencia_nombre: str | None = None,
    anio_competencia: int | None = None,
    categoria_nombre: str | None = None,
) -> list[PartidoResumenDTO]:
    """Filtra partidos en memoria por competencia (nombre + año) y/o categoría."""
    resultado: list[PartidoResumenDTO] = []
    for partido in partidos:
        if competencia_nombre is not None and (
            partido.competencia != competencia_nombre or partido.anioCompetencia != anio_competencia
        ):
            continue
        if categoria_nombre is not None and partido.categoria != categoria_nombre:
            continue
        resultado.append(partido)
    return resultado


def crear_partidos_view(
    page: ft.Page,
    listar_partidos_uc: ListarPartidosPorClubUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma el listado de partidos del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para redibujar al filtrar y navegar al detalle o a la carga.
        listar_partidos_uc (ListarPartidosPorClubUseCase): Partidos del club activo desde `v_partidos_resumen`.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Inscripciones: las competencias del filtro.
        listar_competencias_uc (ListarCompetenciasUseCase): Competencias para resolver nombres y años.
        listar_categorias_uc (ListarCategoriasUseCase): Todas las categorias, para el filtro.
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/partidos".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de partidos requiere un club activo")

    dd_competencia = ft.Dropdown(
        label="Filtrar por competencia",
        options=[ft.dropdown.Option(key="", text="Todas")],
        value="",
    )
    dd_categoria = ft.Dropdown(
        label="Filtrar por categoría",
        options=[ft.dropdown.Option(key="", text="Todas")],
        value="",
    )
    error = crear_etiqueta_error()
    aviso_filtro = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT, visible=False)
    contenedor_tabla = ft.Column()

    partidos_cache: list[PartidoResumenDTO] = []
    competencias_por_id: dict[int, CompetenciaDTO] = {}
    categorias_por_id: dict[int, CategoriaDTO] = {}

    def _boton_ver(partido: PartidoResumenDTO) -> ft.TextButton:
        return ft.TextButton("Ver", on_click=lambda: page.navigate(ruta_detalle_partido(partido.idPartido)))

    def _redibujar_tabla() -> None:
        comp_sel = competencias_por_id.get(int(dd_competencia.value)) if dd_competencia.value else None
        cat_sel = categorias_por_id.get(int(dd_categoria.value)) if dd_categoria.value else None

        visibles = filtrar_partidos(
            partidos_cache,
            competencia_nombre=comp_sel.nombre if comp_sel is not None else None,
            anio_competencia=comp_sel.anio if comp_sel is not None else None,
            categoria_nombre=cat_sel.nombre if cat_sel is not None else None,
        )
        sin_categorias_cargadas = bool(partidos_cache) and all(p.categoria is None for p in partidos_cache)
        if cat_sel is not None and sin_categorias_cargadas:
            aviso_filtro.value = AVISO_CATEGORIA_PENDIENTE
            aviso_filtro.visible = True
        else:
            aviso_filtro.value = ""
            aviso_filtro.visible = False

        filas = [
            (*fila_partido(p), crear_marca_resultado(resultado_del_club(p, club.nombre)), _boton_ver(p))
            for p in visibles
        ]
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_PARTIDOS,
                filas,
                mensaje_vacio=SIN_PARTIDOS,
                clave=TABLA_PARTIDOS,
            )
        ]

    def al_cambiar_filtro() -> None:
        _redibujar_tabla()
        page.update()

    dd_competencia.on_select = al_cambiar_filtro
    dd_categoria.on_select = al_cambiar_filtro

    def cargar_inicial() -> None:
        nonlocal partidos_cache, competencias_por_id, categorias_por_id
        partidos_cache = listar_partidos_uc.ejecutar(club.idClub)
        inscripciones = listar_inscripciones_uc.ejecutar(club.idClub)
        competencias_por_id = {c.idCompetencia: c for c in listar_competencias_uc.ejecutar()}
        categorias_por_id = {c.idCategoria: c for c in listar_categorias_uc.ejecutar()}

        ids_comp = {ins.idCompetencia for ins in inscripciones}
        comps_inscriptas = sorted(
            (competencias_por_id[cid] for cid in ids_comp if cid in competencias_por_id),
            key=lambda c: (c.anio, c.nombre),
            reverse=True,
        )
        dd_competencia.options = [
            ft.dropdown.Option(key="", text="Todas"),
            *(ft.dropdown.Option(key=str(c.idCompetencia), text=f"{c.nombre} ({c.anio})") for c in comps_inscriptas),
        ]
        # Todo el catalogo de categorias, no solo las inscriptas en la competencia elegida.
        dd_categoria.options = [
            ft.dropdown.Option(key="", text="Todas"),
            *(
                ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre)
                for c in sorted(categorias_por_id.values(), key=lambda c: c.nombre)
            ),
        ]
        _redibujar_tabla()

    cargar_inicial()

    contenido = crear_pagina(
        "Partidos",
        [
            ft.Row(
                [
                    dd_competencia,
                    dd_categoria,
                    ft.FilledButton("Cargar partido", on_click=lambda: page.navigate("/partidos/cargar")),
                ],
                spacing=ESPACIO,
                wrap=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            aviso_filtro,
            error,
            contenedor_tabla,
        ],
        subtitulo=f"Club activo: {club.nombre}",
    )
    return crear_vista_interna(page, sesion, "/partidos", contenido)
