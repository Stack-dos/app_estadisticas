"""Pantalla de competencias (US-107, reordenada en US-113): listado con filtros, alta y categorias por fila.

Desde la US-113 la pantalla hace una sola cosa: competencias. Las categorias que juega cada competencia
se eligen desde su fila (boton "Categorías", un dialogo con casillas) y el catalogo de categorias se
mudo a su propia pestaña (`categorias_screen.py`, ruta "/categorias").
"""

import flet as ft

from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CategoriaCompetenciaDTO, CompetenciaDTO, CrearCompetenciaDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.subnav_torneos import crear_subnav_torneos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO

TABLA_COMPETENCIAS = "tabla_competencias"
CASILLAS_CATEGORIAS = "casillas_categorias_competencia"
COLUMNAS_COMPETENCIAS = ("Nombre", "Año", "Tipo", "Categorías habilitadas", "Acciones")
SIN_COMPETENCIAS = "Todavía no hay competencias para mostrar."
SIN_CATEGORIAS_CATALOGO = "Todavía no hay categorías: creá alguna en la pestaña Categorías."


def fila_competencia(competencia: CompetenciaDTO, categorias: list[CategoriaDTO]) -> tuple[str, str, str, str]:
    """Convierte una competencia y sus categorias habilitadas en las columnas de texto de `tabla_datos`."""
    nombres_cat = ", ".join(c.nombre for c in categorias) if categorias else "Sin categorías"
    return (competencia.nombre, str(competencia.anio), competencia.tipo or "—", nombres_cat)


def filtrar_competencias(
    competencias: list[CompetenciaDTO],
    categorias_por_comp: dict[int, list[CategoriaDTO]],
    *,
    anio: int | None = None,
    id_categoria: int | None = None,
) -> list[CompetenciaDTO]:
    """Filtra competencias en memoria por año y/o por categoria habilitada."""
    resultado: list[CompetenciaDTO] = []
    for comp in competencias:
        if anio is not None and comp.anio != anio:
            continue
        if id_categoria is not None and not any(
            cat.idCategoria == id_categoria for cat in categorias_por_comp.get(comp.idCompetencia, [])
        ):
            continue
        resultado.append(comp)
    return resultado


def crear_competencias_view(
    page: ft.Page,
    crear_competencia_uc: CrearCompetenciaUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    habilitar_categoria_uc: HabilitarCategoriaEnCompetenciaUseCase,
    listar_categorias_comp_uc: ListarCategoriasDeCompetenciaUseCase,
    quitar_categoria_uc: QuitarCategoriaDeCompetenciaUseCase,
    eliminar_competencia_uc: EliminarCompetenciaUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de competencias. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, abrir dialogos y redibujar.
        crear_competencia_uc (CrearCompetenciaUseCase): Alta atomica de competencia con categorias.
        listar_competencias_uc (ListarCompetenciasUseCase): Listado de competencias.
        listar_categorias_uc (ListarCategoriasUseCase): Catalogo de categorias (para las casillas).
        habilitar_categoria_uc (HabilitarCategoriaEnCompetenciaUseCase): Habilita una categoria en una competencia.
        listar_categorias_comp_uc (ListarCategoriasDeCompetenciaUseCase): Categorias habilitadas por competencia.
        quitar_categoria_uc (QuitarCategoriaDeCompetenciaUseCase): Quita una categoria sin inscriptos.
        eliminar_competencia_uc (EliminarCompetenciaUseCase): Elimina una competencia sin inscripciones ni partidos.
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/competencias".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de competencias requiere un club activo")

    nombre_comp = ft.TextField(label="Nombre de la competencia")
    anio_comp = ft.TextField(label="Año")
    tipo_comp = ft.TextField(label="Tipo (opcional)")
    error_comp = crear_etiqueta_error()
    casillas_categorias = ft.Column(key=CASILLAS_CATEGORIAS, spacing=ESPACIO_CHICO)

    dd_filtro_anio = ft.Dropdown(label="Filtrar por año", options=[ft.dropdown.Option(key="", text="Todos")], value="")
    dd_filtro_categoria = ft.Dropdown(
        label="Filtrar por categoría", options=[ft.dropdown.Option(key="", text="Todas")], value=""
    )
    error_tabla_comp = crear_etiqueta_error()
    contenedor_tabla_comp = ft.Column()

    competencias_cache: list[CompetenciaDTO] = []
    categorias_cache: list[CategoriaDTO] = []
    categorias_por_comp_cache: dict[int, list[CategoriaDTO]] = {}

    def _casillas_seleccionadas(columna: ft.Column) -> list[int]:
        return [
            int(c.data) for c in columna.controls if isinstance(c, ft.Checkbox) and bool(c.value) and c.data is not None
        ]

    def _boton_eliminar_competencia(comp: CompetenciaDTO) -> ft.TextButton:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_competencia_uc.ejecutar(comp.idCompetencia):
                    raise RuntimeError("No se pudo eliminar la competencia de la base")
                refrescar()

            ejecutar_mostrando_errores(accion, error_tabla_comp)
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Eliminar competencia",
                f"¿Querés eliminar la competencia '{comp.nombre} ({comp.anio})'?",
                al_confirmar,
            )

        return ft.TextButton("Eliminar", on_click=abrir_confirmacion)

    def _boton_categorias(comp: CompetenciaDTO) -> ft.TextButton:
        """Abre un dialogo con una casilla por categoria del catalogo: marcadas = las que juega."""

        def abrir() -> None:
            habilitadas = {c.idCategoria for c in categorias_por_comp_cache.get(comp.idCompetencia, [])}
            casillas = ft.Column(
                [
                    ft.Checkbox(label=c.nombre, value=c.idCategoria in habilitadas, data=c.idCategoria)
                    for c in categorias_cache
                ]
                or [ft.Text(SIN_CATEGORIAS_CATALOGO, color=ft.Colors.ON_SURFACE_VARIANT)],
                tight=True,
            )
            error_dialogo = crear_etiqueta_error()

            def guardar() -> None:
                def accion() -> None:
                    elegidas = set(_casillas_seleccionadas(casillas))
                    # Primero se habilitan las nuevas; si una que se quita tiene inscriptos, el error lo dice
                    for id_cat in sorted(elegidas - habilitadas):
                        dto = CategoriaCompetenciaDTO(idCompetencia=comp.idCompetencia, idCategoria=id_cat)
                        if habilitar_categoria_uc.ejecutar(dto) is None:
                            raise RuntimeError("Habilitar la categoria no devolvio confirmacion")
                    for id_cat in sorted(habilitadas - elegidas):
                        dto = CategoriaCompetenciaDTO(idCompetencia=comp.idCompetencia, idCategoria=id_cat)
                        if quitar_categoria_uc.ejecutar(dto) is None:
                            raise RuntimeError("Quitar la categoria no devolvio confirmacion")
                    page.pop_dialog()

                ejecutar_mostrando_errores(accion, error_dialogo)
                refrescar()  # aunque falle a mitad, la tabla muestra lo que quedo guardado
                page.update()

            page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text(f"Categorías de {comp.nombre} ({comp.anio})"),
                    content=ft.Column([casillas, error_dialogo], tight=True),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda: page.pop_dialog()),
                        ft.FilledButton("Guardar", on_click=guardar),
                    ],
                )
            )

        return ft.TextButton("Categorías", on_click=abrir)

    def _redibujar_tabla_competencias() -> None:
        anio_sel = int(dd_filtro_anio.value) if dd_filtro_anio.value else None
        cat_sel = int(dd_filtro_categoria.value) if dd_filtro_categoria.value else None
        visibles = filtrar_competencias(
            competencias_cache,
            categorias_por_comp_cache,
            anio=anio_sel,
            id_categoria=cat_sel,
        )
        filas_comp = [
            (
                *fila_competencia(comp, categorias_por_comp_cache[comp.idCompetencia]),
                ft.Row([_boton_categorias(comp), _boton_eliminar_competencia(comp)], spacing=0),
            )
            for comp in visibles
        ]
        contenedor_tabla_comp.controls = [
            crear_tabla_datos(
                COLUMNAS_COMPETENCIAS,
                filas_comp,
                mensaje_vacio=SIN_COMPETENCIAS,
                clave=TABLA_COMPETENCIAS,
            )
        ]

    def al_cambiar_filtro() -> None:
        _redibujar_tabla_competencias()
        page.update()

    dd_filtro_anio.on_select = al_cambiar_filtro
    dd_filtro_categoria.on_select = al_cambiar_filtro

    def refrescar() -> None:
        """Recarga competencias, categorias y controles dependientes."""
        competencias = listar_competencias_uc.ejecutar()
        categorias = listar_categorias_uc.ejecutar()

        competencias_cache[:] = competencias
        categorias_cache[:] = categorias
        categorias_por_comp_cache.clear()
        for comp in competencias:
            categorias_por_comp_cache[comp.idCompetencia] = listar_categorias_comp_uc.ejecutar(comp.idCompetencia)

        anios = sorted({c.anio for c in competencias}, reverse=True)
        dd_filtro_anio.options = [ft.dropdown.Option(key="", text="Todos")] + [
            ft.dropdown.Option(key=str(a), text=str(a)) for a in anios
        ]
        if dd_filtro_anio.value and int(dd_filtro_anio.value) not in anios:
            dd_filtro_anio.value = ""

        ids_cat = {c.idCategoria for c in categorias}
        dd_filtro_categoria.options = [ft.dropdown.Option(key="", text="Todas")] + [
            ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre) for c in categorias
        ]
        if dd_filtro_categoria.value and int(dd_filtro_categoria.value) not in ids_cat:
            dd_filtro_categoria.value = ""

        _redibujar_tabla_competencias()

        prev_sel = set(_casillas_seleccionadas(casillas_categorias))
        casillas_categorias.controls = [
            ft.Checkbox(label=cat.nombre, value=cat.idCategoria in prev_sel, data=cat.idCategoria) for cat in categorias
        ] or [
            ft.Text(SIN_CATEGORIAS_CATALOGO, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.TextButton("Ir a Categorías", on_click=lambda: page.navigate("/categorias")),
        ]

    def crear_competencia() -> None:
        def accion() -> None:
            texto_anio = (anio_comp.value or "").strip()
            try:
                anio_num = int(texto_anio)
            except ValueError as exc:
                raise DatoInvalidoError("El año debe ser un número entero") from exc
            tipo_limpio = (tipo_comp.value or "").strip() or None
            dto = CrearCompetenciaDTO(
                nombre=nombre_comp.value or "",
                anio=anio_num,
                tipo=tipo_limpio,
                idCategorias=_casillas_seleccionadas(casillas_categorias),
            )
            creada = crear_competencia_uc.ejecutar(dto)
            if creada is None:
                raise RuntimeError("Crear la competencia no devolvio el registro (fallo al guardar en la base)")
            nombre_comp.value = ""
            anio_comp.value = ""
            tipo_comp.value = ""
            for ctrl in casillas_categorias.controls:
                if isinstance(ctrl, ft.Checkbox):
                    ctrl.value = False
            refrescar()

        ejecutar_mostrando_errores(accion, error_comp)
        page.update()

    refrescar()

    lateral = ft.Column(
        [
            ft.Text("Nueva competencia", weight=ft.FontWeight.W_600),
            crear_formulario(
                [
                    nombre_comp,
                    anio_comp,
                    tipo_comp,
                    ft.Text("Categorías que juega:", color=ft.Colors.ON_SURFACE_VARIANT),
                    casillas_categorias,
                ],
                error_comp,
                "Crear competencia",
                crear_competencia,
                ancho=None,
            ),
        ],
        spacing=ESPACIO,
    )

    contenido = crear_pagina(
        "Torneos · Competencias",
        [
            crear_subnav_torneos(page, "/competencias"),
            ft.Row([dd_filtro_anio, dd_filtro_categoria], spacing=ESPACIO, wrap=True),
            contenedor_tabla_comp,
            error_tabla_comp,
        ],
        subtitulo=f"Club activo: {club.nombre}",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/competencias", contenido)
