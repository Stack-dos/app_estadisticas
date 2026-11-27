"""Pantalla de partidos del club activo (US-112): listado filtrado por inscripciones y detalle de boxscore."""

import flet as ft

from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.partido_dto import BoxscoreFilaDTO, PartidoResumenDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO

TABLA_PARTIDOS = "tabla_partidos"
TABLA_BOXSCORE = "tabla_boxscore"
DETALLE_PARTIDO = "detalle_partido"
COLUMNAS_PARTIDOS = ("Fecha", "Competencia", "Año", "Local", "Visitante", "Estadio", "Acción")
COLUMNAS_BOXSCORE = (
    "Club",
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
SIN_PARTIDOS = "No hay partidos para mostrar con los filtros elegidos."
SIN_BOXSCORE = "Este partido todavía no tiene estadísticas cargadas en el boxscore."
AVISO_CATEGORIA_PENDIENTE = (
    "Los partidos cargados antes de la carga por categoría todavía no tienen categoría asignada."
)


def fila_partido(partido: PartidoResumenDTO) -> tuple[str, str, str, str, str, str]:
    """Convierte un `PartidoResumenDTO` en las columnas de texto de la tabla sin exponer IDs."""
    return (
        partido.fecha,
        partido.competencia,
        str(partido.anioCompetencia),
        partido.clubLocal,
        partido.clubVisitante,
        partido.estadio or "—",
    )


def fila_boxscore(fila: BoxscoreFilaDTO) -> tuple[str, ...]:
    """Convierte una `BoxscoreFilaDTO` en celdas legibles para la tabla de boxscore."""
    return (
        fila.nombreClub,
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
    obtener_boxscore_uc: ObtenerBoxscorePartidoUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de partidos y boxscore del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para redibujar al filtrar o abrir el detalle de un partido.
        listar_partidos_uc (ListarPartidosPorClubUseCase): Partidos del club activo desde `v_partidos_resumen`.
        obtener_boxscore_uc (ObtenerBoxscorePartidoUseCase): Boxscore desde `v_boxscore_completo`.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Inscripciones del club para poblar los filtros.
        listar_competencias_uc (ListarCompetenciasUseCase): Competencias para resolver nombres y años.
        listar_categorias_uc (ListarCategoriasUseCase): Categorias para resolver nombres.
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
    contenedor_detalle = ft.Column(key=DETALLE_PARTIDO, spacing=ESPACIO_CHICO)

    partidos_cache: list[PartidoResumenDTO] = []
    inscripciones_cache: list[InscripcionDTO] = []
    competencias_por_id: dict[int, CompetenciaDTO] = {}
    categorias_por_id: dict[int, CategoriaDTO] = {}

    def _cargar_opciones_categoria() -> None:
        comp_sel = int(dd_competencia.value) if dd_competencia.value else None
        ids_cat = {ins.idCategoria for ins in inscripciones_cache if comp_sel is None or ins.idCompetencia == comp_sel}
        cats = sorted(
            (categorias_por_id[cid] for cid in ids_cat if cid in categorias_por_id),
            key=lambda c: c.nombre,
        )
        dd_categoria.options = [
            ft.dropdown.Option(key="", text="Todas"),
            *(ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre) for c in cats),
        ]
        if dd_categoria.value and int(dd_categoria.value) not in ids_cat:
            dd_categoria.value = ""

    def _ver_boxscore(partido: PartidoResumenDTO) -> None:
        def accion() -> None:
            filas = obtener_boxscore_uc.ejecutar(partido.idPartido)
            subtitulo_partido = f"{partido.competencia} ({partido.anioCompetencia}) · {partido.fecha}"
            if partido.estadio:
                subtitulo_partido = f"{subtitulo_partido} · {partido.estadio}"
            tabla_bs = crear_tabla_datos(
                COLUMNAS_BOXSCORE,
                [fila_boxscore(f) for f in filas],
                mensaje_vacio=SIN_BOXSCORE,
                clave=TABLA_BOXSCORE,
            )
            contenedor_detalle.controls = [
                ft.Divider(),
                ft.Text(
                    f"Boxscore: {partido.clubLocal} vs {partido.clubVisitante}",
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(subtitulo_partido, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Row([tabla_bs], scroll=ft.ScrollMode.AUTO),
            ]

        ejecutar_mostrando_errores(accion, error)
        page.update()

    def _boton_boxscore(partido: PartidoResumenDTO) -> ft.TextButton:
        return ft.TextButton("Ver boxscore", on_click=lambda: _ver_boxscore(partido))

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

        filas = [(*fila_partido(p), _boton_boxscore(p)) for p in visibles]
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_PARTIDOS,
                filas,
                mensaje_vacio=SIN_PARTIDOS,
                clave=TABLA_PARTIDOS,
            )
        ]

    def al_cambiar_competencia() -> None:
        _cargar_opciones_categoria()
        _redibujar_tabla()
        page.update()

    def al_cambiar_categoria() -> None:
        _redibujar_tabla()
        page.update()

    dd_competencia.on_select = al_cambiar_competencia
    dd_categoria.on_select = al_cambiar_categoria

    def cargar_inicial() -> None:
        nonlocal partidos_cache, inscripciones_cache, competencias_por_id, categorias_por_id
        partidos_cache = listar_partidos_uc.ejecutar(club.idClub)
        inscripciones_cache = listar_inscripciones_uc.ejecutar(club.idClub)
        competencias_por_id = {c.idCompetencia: c for c in listar_competencias_uc.ejecutar()}
        categorias_por_id = {c.idCategoria: c for c in listar_categorias_uc.ejecutar()}

        ids_comp = {ins.idCompetencia for ins in inscripciones_cache}
        comps_inscriptas = sorted(
            (competencias_por_id[cid] for cid in ids_comp if cid in competencias_por_id),
            key=lambda c: (c.anio, c.nombre),
            reverse=True,
        )
        dd_competencia.options = [
            ft.dropdown.Option(key="", text="Todas"),
            *(ft.dropdown.Option(key=str(c.idCompetencia), text=f"{c.nombre} ({c.anio})") for c in comps_inscriptas),
        ]
        _cargar_opciones_categoria()
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
            contenedor_detalle,
        ],
        subtitulo=f"Club activo: {club.nombre}",
    )
    return crear_vista_interna(page, sesion, "/partidos", contenido)
