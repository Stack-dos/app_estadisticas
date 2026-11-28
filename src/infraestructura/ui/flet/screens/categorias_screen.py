"""Pantalla del catalogo de categorias (US-113): se separo de Competencias, donde mezclaba tres cosas.

Lista las categorias (U13, U15, Primera...), permite crear nuevas y eliminar las que no se usan. Que
categorias juega cada competencia se elige en la pantalla de Competencias, desde la fila de cada una.
"""

import flet as ft

from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO, CrearCategoriaDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.subnav_torneos import crear_subnav_torneos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO

TABLA_CATEGORIAS = "tabla_categorias"
COLUMNAS_CATEGORIAS = ("Nombre", "Acción")
SIN_CATEGORIAS = "Todavía no hay categorías cargadas."


def fila_categoria(categoria: CategoriaDTO) -> tuple[str]:
    """Convierte una categoria en la columna de texto de `tabla_datos`."""
    return (categoria.nombre,)


def crear_categorias_view(
    page: ft.Page,
    crear_categoria_uc: CrearCategoriaUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    eliminar_categoria_uc: EliminarCategoriaUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla del catalogo de categorias. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, confirmar bajas y redibujar.
        crear_categoria_uc (CrearCategoriaUseCase): Alta de categoria en el catalogo.
        listar_categorias_uc (ListarCategoriasUseCase): Listado del catalogo.
        eliminar_categoria_uc (EliminarCategoriaUseCase): Elimina una categoria sin uso.
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/categorias".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de categorías requiere un club activo")

    nombre_cat = ft.TextField(label="Nombre de la categoría")
    error_cat = crear_etiqueta_error()
    error_tabla = crear_etiqueta_error()
    contenedor_tabla = ft.Column()

    def _boton_eliminar(cat: CategoriaDTO) -> ft.TextButton:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_categoria_uc.ejecutar(cat.idCategoria):
                    raise RuntimeError("No se pudo eliminar la categoría de la base")
                refrescar()

            ejecutar_mostrando_errores(accion, error_tabla)
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Eliminar categoría",
                f"¿Querés eliminar la categoría '{cat.nombre}' del catálogo?",
                al_confirmar,
            )

        return ft.TextButton("Eliminar", on_click=abrir_confirmacion)

    def refrescar() -> None:
        categorias = listar_categorias_uc.ejecutar()
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_CATEGORIAS,
                [(*fila_categoria(c), _boton_eliminar(c)) for c in categorias],
                mensaje_vacio=SIN_CATEGORIAS,
                clave=TABLA_CATEGORIAS,
            )
        ]

    def crear_categoria() -> None:
        def accion() -> None:
            creada = crear_categoria_uc.ejecutar(CrearCategoriaDTO(nombre=nombre_cat.value or ""))
            if creada is None:
                raise RuntimeError("Crear la categoria no devolvio el registro (fallo al guardar en la base)")
            nombre_cat.value = ""
            refrescar()

        ejecutar_mostrando_errores(accion, error_cat)
        page.update()

    refrescar()

    lateral = ft.Column(
        [
            ft.Text("Nueva categoría", weight=ft.FontWeight.W_600),
            crear_formulario([nombre_cat], error_cat, "Crear categoría", crear_categoria, ancho=None),
        ],
        spacing=ESPACIO,
    )
    contenido = crear_pagina(
        "Torneos · Categorías",
        [crear_subnav_torneos(page, "/categorias"), contenedor_tabla, error_tabla],
        subtitulo="Catálogo común a todas las competencias. Qué categorías juega cada una se elige en Competencias.",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/categorias", contenido)
