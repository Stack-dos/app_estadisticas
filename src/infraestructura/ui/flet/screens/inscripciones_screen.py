"""Pantalla de inscripciones del club activo (US-107): inscribir, filtrar y dar de baja inscripciones."""

from datetime import date

import flet as ft

from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscribirClubDTO, InscripcionDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.subnav_torneos import crear_subnav_torneos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO

TABLA_INSCRIPCIONES = "tabla_inscripciones"
COLUMNAS_INSCRIPCIONES = ("Competencia", "Año", "Categoría", "Lista", "Acción")
SIN_INSCRIPCIONES = "No hay inscripciones para mostrar."


def fila_inscripcion(
    inscripcion: InscripcionDTO,
    competencias_por_id: dict[int, CompetenciaDTO],
    categorias_por_id: dict[int, CategoriaDTO],
) -> tuple[str, str, str, str]:
    """Convierte una inscripcion en las columnas de texto sin exponer IDs de competencia o categoria."""
    comp = competencias_por_id.get(inscripcion.idCompetencia)
    cat = categorias_por_id.get(inscripcion.idCategoria)
    nombre_comp = comp.nombre if comp is not None else f"Competencia #{inscripcion.idCompetencia}"
    anio_comp = str(comp.anio) if comp is not None else "—"
    nombre_cat = cat.nombre if cat is not None else f"Categoría #{inscripcion.idCategoria}"
    return (nombre_comp, anio_comp, nombre_cat, f"Lista #{inscripcion.idListaBuenaFe}")


def filtrar_inscripciones(
    inscripciones: list[InscripcionDTO],
    competencias_por_id: dict[int, CompetenciaDTO],
    *,
    anio: int | None = None,
    id_categoria: int | None = None,
) -> list[InscripcionDTO]:
    """Filtra inscripciones en memoria por año de la competencia y/o categoria."""
    resultado: list[InscripcionDTO] = []
    for ins in inscripciones:
        comp = competencias_por_id.get(ins.idCompetencia)
        if anio is not None and (comp is None or comp.anio != anio):
            continue
        if id_categoria is not None and ins.idCategoria != id_categoria:
            continue
        resultado.append(ins)
    return resultado


def crear_inscripciones_view(
    page: ft.Page,
    inscribir_club_uc: InscribirClubEnCompetenciaUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    listar_categorias_comp_uc: ListarCategoriasDeCompetenciaUseCase,
    eliminar_inscripcion_uc: EliminarInscripcionUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de inscripciones del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, confirmar bajas y redibujar.
        inscribir_club_uc (InscribirClubEnCompetenciaUseCase): Inscribe al club y crea su lista de buena fe.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Inscripciones del club activo.
        listar_competencias_uc (ListarCompetenciasUseCase): Competencias disponibles.
        listar_categorias_uc (ListarCategoriasUseCase): Catalogo de categorias para resolver nombres.
        listar_categorias_comp_uc (ListarCategoriasDeCompetenciaUseCase): Filtra categorias habilitadas.
        eliminar_inscripcion_uc (EliminarInscripcionUseCase): Da de baja una inscripcion sin partidos cargados.
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/inscripciones".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de inscripciones requiere un club activo")

    dd_competencia = ft.Dropdown(label="Competencia", options=[])
    dd_categoria = ft.Dropdown(label="Categoría", options=[])
    fecha_presentacion = ft.TextField(label="Fecha de presentación", value=date.today().isoformat())
    error = crear_etiqueta_error()

    dd_filtro_anio = ft.Dropdown(label="Filtrar por año", options=[ft.dropdown.Option(key="", text="Todos")], value="")
    dd_filtro_categoria = ft.Dropdown(
        label="Filtrar por categoría", options=[ft.dropdown.Option(key="", text="Todas")], value=""
    )
    error_tabla = crear_etiqueta_error()
    contenedor_tabla = ft.Column()

    inscripciones_cache: list[InscripcionDTO] = []
    competencias_por_id_cache: dict[int, CompetenciaDTO] = {}
    categorias_por_id_cache: dict[int, CategoriaDTO] = {}

    def _cargar_categorias_habilitadas() -> None:
        if not dd_competencia.value:
            dd_categoria.options = []
            dd_categoria.value = None
            return
        habilitadas = listar_categorias_comp_uc.ejecutar(int(dd_competencia.value))
        dd_categoria.options = [ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre) for c in habilitadas]
        dd_categoria.value = None

    def al_elegir_competencia() -> None:
        ejecutar_mostrando_errores(_cargar_categorias_habilitadas, error)
        page.update()

    dd_competencia.on_select = al_elegir_competencia

    def _boton_dar_de_baja(ins: InscripcionDTO) -> ft.TextButton:
        comp = competencias_por_id_cache.get(ins.idCompetencia)
        cat = categorias_por_id_cache.get(ins.idCategoria)
        etiqueta_comp = f"{comp.nombre} ({comp.anio})" if comp is not None else f"Competencia #{ins.idCompetencia}"
        etiqueta_cat = cat.nombre if cat is not None else f"Categoría #{ins.idCategoria}"

        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_inscripcion_uc.ejecutar(ins.idInscripcion):
                    raise RuntimeError("No se pudo dar de baja la inscripción en la base")
                refrescar()

            ejecutar_mostrando_errores(accion, error_tabla)
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Dar de baja inscripción",
                f"¿Querés dar de baja a {club.nombre} de '{etiqueta_comp} — {etiqueta_cat}'? "
                "Esto también eliminará su lista de buena fe asociada.",
                al_confirmar,
                texto_confirmar="Dar de baja",
            )

        return ft.TextButton("Dar de baja", on_click=abrir_confirmacion)

    def _redibujar_tabla() -> None:
        anio_sel = int(dd_filtro_anio.value) if dd_filtro_anio.value else None
        cat_sel = int(dd_filtro_categoria.value) if dd_filtro_categoria.value else None
        visibles = filtrar_inscripciones(
            inscripciones_cache,
            competencias_por_id_cache,
            anio=anio_sel,
            id_categoria=cat_sel,
        )
        filas = [
            (*fila_inscripcion(ins, competencias_por_id_cache, categorias_por_id_cache), _boton_dar_de_baja(ins))
            for ins in visibles
        ]
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_INSCRIPCIONES,
                filas,
                mensaje_vacio=SIN_INSCRIPCIONES,
                clave=TABLA_INSCRIPCIONES,
            )
        ]

    def al_cambiar_filtro() -> None:
        _redibujar_tabla()
        page.update()

    dd_filtro_anio.on_select = al_cambiar_filtro
    dd_filtro_categoria.on_select = al_cambiar_filtro

    def refrescar() -> None:
        """Recarga competencias, inscripciones del club y opciones del desplegable."""
        competencias = listar_competencias_uc.ejecutar()
        categorias = listar_categorias_uc.ejecutar()
        inscripciones = listar_inscripciones_uc.ejecutar(club.idClub)

        inscripciones_cache.clear()
        inscripciones_cache.extend(inscripciones)
        competencias_por_id_cache.clear()
        competencias_por_id_cache.update({c.idCompetencia: c for c in competencias})
        categorias_por_id_cache.clear()
        categorias_por_id_cache.update({c.idCategoria: c for c in categorias})

        anios = sorted(
            {
                competencias_por_id_cache[i.idCompetencia].anio
                for i in inscripciones
                if i.idCompetencia in competencias_por_id_cache
            },
            reverse=True,
        )
        dd_filtro_anio.options = [ft.dropdown.Option(key="", text="Todos")] + [
            ft.dropdown.Option(key=str(a), text=str(a)) for a in anios
        ]
        if dd_filtro_anio.value and int(dd_filtro_anio.value) not in anios:
            dd_filtro_anio.value = ""

        ids_cat_inscriptas = {i.idCategoria for i in inscripciones}
        dd_filtro_categoria.options = [ft.dropdown.Option(key="", text="Todas")] + [
            ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre)
            for c in categorias
            if c.idCategoria in ids_cat_inscriptas
        ]
        if dd_filtro_categoria.value and int(dd_filtro_categoria.value) not in ids_cat_inscriptas:
            dd_filtro_categoria.value = ""

        _redibujar_tabla()

        dd_competencia.options = [
            ft.dropdown.Option(key=str(c.idCompetencia), text=f"{c.nombre} ({c.anio})") for c in competencias
        ]

    def inscribir() -> None:
        def accion() -> None:
            if not dd_competencia.value:
                raise DatoInvalidoError("Elegí una competencia")
            if not dd_categoria.value:
                raise DatoInvalidoError("Elegí una categoría")
            fecha = (fecha_presentacion.value or "").strip()
            if not fecha:
                raise DatoInvalidoError("Ingresá una fecha de presentación")
            creada = inscribir_club_uc.ejecutar(
                InscribirClubDTO(
                    idClub=club.idClub,
                    idCategoria=int(dd_categoria.value),
                    idCompetencia=int(dd_competencia.value),
                    fechaPresentacion=fecha,
                )
            )
            if creada is None:
                raise RuntimeError("Inscribir al club no devolvio la inscripcion (fallo al guardar en la base)")
            dd_categoria.value = None
            refrescar()

        ejecutar_mostrando_errores(accion, error)
        page.update()

    refrescar()

    lateral = ft.Column(
        [
            ft.Text("Inscribir club", weight=ft.FontWeight.W_600),
            crear_formulario(
                [dd_competencia, dd_categoria, fecha_presentacion],
                error,
                "Inscribir club",
                inscribir,
                ancho=None,
            ),
        ],
        spacing=ESPACIO,
    )

    contenido = crear_pagina(
        "Torneos · Inscripciones",
        [
            crear_subnav_torneos(page, "/inscripciones"),
            ft.Text(f"Inscripciones de {club.nombre}", weight=ft.FontWeight.W_600),
            ft.Row([dd_filtro_anio, dd_filtro_categoria], spacing=ESPACIO, wrap=True),
            contenedor_tabla,
            error_tabla,
        ],
        subtitulo=f"Club activo: {club.nombre}",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/inscripciones", contenido)
