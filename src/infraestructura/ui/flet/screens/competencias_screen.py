"""Pantalla de competencias y categorias (US-107): catalogo de categorias, competencias, filtros y bajas."""

import flet as ft

from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO, CrearCategoriaDTO
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
TABLA_CATEGORIAS = "tabla_categorias"
CASILLAS_CATEGORIAS = "casillas_categorias_competencia"
COLUMNAS_COMPETENCIAS = ("Nombre", "Año", "Tipo", "Categorías habilitadas", "Acción")
COLUMNAS_CATEGORIAS = ("Nombre", "Acción")
SIN_COMPETENCIAS = "Todavía no hay competencias para mostrar."
SIN_CATEGORIAS = "Todavía no hay categorías cargadas."


def fila_competencia(competencia: CompetenciaDTO, categorias: list[CategoriaDTO]) -> tuple[str, str, str, str]:
    """Convierte una competencia y sus categorias habilitadas en las columnas de texto de `tabla_datos`."""
    nombres_cat = ", ".join(c.nombre for c in categorias) if categorias else "Sin categorías"
    return (competencia.nombre, str(competencia.anio), competencia.tipo or "—", nombres_cat)


def fila_categoria(categoria: CategoriaDTO) -> tuple[str]:
    """Convierte una categoria en la columna de texto de `tabla_datos`."""
    return (categoria.nombre,)


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
    crear_categoria_uc: CrearCategoriaUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    habilitar_categoria_uc: HabilitarCategoriaEnCompetenciaUseCase,
    listar_categorias_comp_uc: ListarCategoriasDeCompetenciaUseCase,
    quitar_categoria_uc: QuitarCategoriaDeCompetenciaUseCase,
    eliminar_competencia_uc: EliminarCompetenciaUseCase,
    eliminar_categoria_uc: EliminarCategoriaUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de competencias y categorias. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, abrir confirmaciones y redibujar.
        crear_competencia_uc (CrearCompetenciaUseCase): Alta atomica de competencia con categorias.
        listar_competencias_uc (ListarCompetenciasUseCase): Listado de competencias.
        crear_categoria_uc (CrearCategoriaUseCase): Alta de categoria en el catalogo.
        listar_categorias_uc (ListarCategoriasUseCase): Listado del catalogo de categorias.
        habilitar_categoria_uc (HabilitarCategoriaEnCompetenciaUseCase): Habilita una categoria en una competencia.
        listar_categorias_comp_uc (ListarCategoriasDeCompetenciaUseCase): Categorias habilitadas por competencia.
        quitar_categoria_uc (QuitarCategoriaDeCompetenciaUseCase): Quita una categoria sin inscriptos.
        eliminar_competencia_uc (EliminarCompetenciaUseCase): Elimina una competencia sin inscripciones ni partidos.
        eliminar_categoria_uc (EliminarCategoriaUseCase): Elimina una categoria sin uso.
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

    nombre_cat = ft.TextField(label="Nombre de la categoría")
    error_cat = crear_etiqueta_error()

    dd_competencia = ft.Dropdown(label="Competencia", options=[])
    dd_categoria = ft.Dropdown(label="Categoría", options=[])
    error_gestion = crear_etiqueta_error()

    dd_filtro_anio = ft.Dropdown(label="Filtrar por año", options=[ft.dropdown.Option(key="", text="Todos")], value="")
    dd_filtro_categoria = ft.Dropdown(
        label="Filtrar por categoría", options=[ft.dropdown.Option(key="", text="Todas")], value=""
    )
    error_tabla_comp = crear_etiqueta_error()
    error_tabla_cat = crear_etiqueta_error()

    contenedor_tabla_comp = ft.Column()
    contenedor_tabla_cat = ft.Column()

    competencias_cache: list[CompetenciaDTO] = []
    categorias_por_comp_cache: dict[int, list[CategoriaDTO]] = {}

    def _casillas_seleccionadas() -> list[int]:
        seleccionadas: list[int] = []
        for ctrl in casillas_categorias.controls:
            if isinstance(ctrl, ft.Checkbox) and bool(ctrl.value) and ctrl.data is not None:
                seleccionadas.append(int(ctrl.data))
        return seleccionadas

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

    def _boton_eliminar_categoria(cat: CategoriaDTO) -> ft.TextButton:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_categoria_uc.ejecutar(cat.idCategoria):
                    raise RuntimeError("No se pudo eliminar la categoría de la base")
                refrescar()

            ejecutar_mostrando_errores(accion, error_tabla_cat)
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Eliminar categoría",
                f"¿Querés eliminar la categoría '{cat.nombre}' del catálogo?",
                al_confirmar,
            )

        return ft.TextButton("Eliminar", on_click=abrir_confirmacion)

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
            (*fila_competencia(comp, categorias_por_comp_cache[comp.idCompetencia]), _boton_eliminar_competencia(comp))
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

        competencias_cache.clear()
        competencias_cache.extend(competencias)
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

        filas_cat = [(*fila_categoria(cat), _boton_eliminar_categoria(cat)) for cat in categorias]
        contenedor_tabla_cat.controls = [
            crear_tabla_datos(
                COLUMNAS_CATEGORIAS,
                filas_cat,
                mensaje_vacio=SIN_CATEGORIAS,
                clave=TABLA_CATEGORIAS,
            )
        ]

        prev_sel = set(_casillas_seleccionadas())
        casillas_categorias.controls = [
            ft.Checkbox(label=cat.nombre, value=cat.idCategoria in prev_sel, data=cat.idCategoria) for cat in categorias
        ]

        ids_comp = {c.idCompetencia for c in competencias}
        dd_competencia.options = [
            ft.dropdown.Option(key=str(c.idCompetencia), text=f"{c.nombre} ({c.anio})") for c in competencias
        ]
        if dd_competencia.value and int(dd_competencia.value) not in ids_comp:
            dd_competencia.value = None

        dd_categoria.options = [ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre) for c in categorias]
        if dd_categoria.value and int(dd_categoria.value) not in ids_cat:
            dd_categoria.value = None

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
                idCategorias=_casillas_seleccionadas(),
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

    def crear_categoria() -> None:
        def accion() -> None:
            creada = crear_categoria_uc.ejecutar(CrearCategoriaDTO(nombre=nombre_cat.value or ""))
            if creada is None:
                raise RuntimeError("Crear la categoria no devolvio el registro (fallo al guardar en la base)")
            nombre_cat.value = ""
            refrescar()

        ejecutar_mostrando_errores(accion, error_cat)
        page.update()

    def _leer_competencia_y_categoria() -> CategoriaCompetenciaDTO:
        if not dd_competencia.value:
            raise DatoInvalidoError("Elegí una competencia")
        if not dd_categoria.value:
            raise DatoInvalidoError("Elegí una categoría")
        return CategoriaCompetenciaDTO(
            idCompetencia=int(dd_competencia.value),
            idCategoria=int(dd_categoria.value),
        )

    def habilitar_categoria() -> None:
        def accion() -> None:
            dto = _leer_competencia_y_categoria()
            if habilitar_categoria_uc.ejecutar(dto) is None:
                raise RuntimeError("Habilitar la categoria no devolvio confirmacion (fallo al guardar en la base)")
            refrescar()

        ejecutar_mostrando_errores(accion, error_gestion)
        page.update()

    def quitar_categoria() -> None:
        def accion() -> None:
            dto = _leer_competencia_y_categoria()
            if quitar_categoria_uc.ejecutar(dto) is None:
                raise RuntimeError("Quitar la categoria no devolvio confirmacion (fallo al borrar en la base)")
            refrescar()

        ejecutar_mostrando_errores(accion, error_gestion)
        page.update()

    refrescar()

    gestion_categorias_comp = ft.Column(
        [
            ft.Text("Categorías por competencia", weight=ft.FontWeight.W_600),
            ft.Row([dd_competencia, dd_categoria], spacing=ESPACIO, wrap=True),
            error_gestion,
            ft.Row(
                [
                    ft.FilledButton("Habilitar categoría", on_click=habilitar_categoria),
                    ft.TextButton("Quitar categoría", on_click=quitar_categoria),
                ],
                spacing=ESPACIO_CHICO,
            ),
        ],
        spacing=ESPACIO_CHICO,
    )

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
            ft.Divider(),
            ft.Text("Nueva categoría", weight=ft.FontWeight.W_600),
            crear_formulario([nombre_cat], error_cat, "Crear categoría", crear_categoria, ancho=None),
        ],
        spacing=ESPACIO,
    )

    contenido = crear_pagina(
        "Torneos · Competencias",
        [
            crear_subnav_torneos(page, "/competencias"),
            ft.Text("Competencias", weight=ft.FontWeight.W_600),
            ft.Row([dd_filtro_anio, dd_filtro_categoria], spacing=ESPACIO, wrap=True),
            contenedor_tabla_comp,
            error_tabla_comp,
            gestion_categorias_comp,
            ft.Text("Catálogo de categorías", weight=ft.FontWeight.W_600),
            contenedor_tabla_cat,
            error_tabla_cat,
        ],
        subtitulo=f"Club activo: {club.nombre}",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/competencias", contenido)
