"""Tests unitarios de `tabla_datos` y de las funciones puras de conversion DTO -> fila (US-107)."""

import flet as ft
from ayudantes_flet import controles, por_clave

from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.screens.categorias_screen import fila_categoria
from infraestructura.ui.flet.screens.competencias_screen import fila_competencia, filtrar_competencias
from infraestructura.ui.flet.screens.inscripciones_screen import fila_inscripcion, filtrar_inscripciones
from infraestructura.ui.flet.screens.lista_buena_fe_screen import etiqueta_inscripcion, fila_jugador_lista


def test_tabla_vacia_muestra_el_mensaje_sin_datos():
    tabla = crear_tabla_datos(("Col A", "Col B"), [], mensaje_vacio="Nada por aca", clave="t")

    assert tabla.key == "t"
    assert [c.value for c in controles(tabla) if isinstance(c, ft.Text)] == ["Nada por aca"]


def test_tabla_con_filas_alterna_color_en_filas_impares_y_envuelve_textos():
    contenedor = crear_tabla_datos(
        ("Nombre", "Acción"),
        [("A", ft.TextButton("Ver")), ("B", "ok"), ("C", "ok")],
        clave="tabla_test",
    )
    tabla = por_clave(contenedor, "tabla_test")

    assert isinstance(tabla, ft.DataTable)
    assert tabla.expand  # ocupa todo el ancho, no solo lo que mide su contenido
    assert tabla.key == "tabla_test"
    assert [c.label.value for c in tabla.columns] == ["Nombre", "Acción"]
    assert [r.color for r in tabla.rows] == [None, ft.Colors.SURFACE_CONTAINER_LOW, None]
    assert isinstance(tabla.rows[0].cells[0].content, ft.Text)
    assert isinstance(tabla.rows[0].cells[1].content, ft.TextButton)


# ----------------------------------------------------------------------------- funciones puras DTO -> fila


def test_fila_competencia_formatea_categorias_o_muestra_sin_categorias():
    comp = CompetenciaDTO(idCompetencia=1, nombre="Liga", anio=2026, tipo=None)
    cats = [CategoriaDTO(idCategoria=1, nombre="U17"), CategoriaDTO(idCategoria=2, nombre="U21")]

    assert fila_competencia(comp, cats) == ("Liga", "2026", "—", "U17, U21")
    assert fila_competencia(comp, []) == ("Liga", "2026", "—", "Sin categorías")


def test_fila_categoria_devuelve_el_nombre():
    assert fila_categoria(CategoriaDTO(idCategoria=3, nombre="U15")) == ("U15",)


def test_fila_inscripcion_y_etiqueta_resuelven_nombres_por_id():
    ins = InscripcionDTO(idInscripcion=5, idClub=1, idCategoria=2, idCompetencia=10, idListaBuenaFe=8)
    comps = {10: CompetenciaDTO(idCompetencia=10, nombre="Provincial", anio=2026, tipo="PROVINCIAL")}
    cats = {2: CategoriaDTO(idCategoria=2, nombre="U21")}

    assert fila_inscripcion(ins, comps, cats, 11) == ("Provincial", "2026", "U21", "11")
    assert etiqueta_inscripcion(ins, comps, cats) == "Provincial (2026) — U21"


def test_fila_jugador_lista_formatea_anio_opcional():
    assert fila_jugador_lista(JugadorDTO(nombre_completo="Manu Ginobili", id=1, anioNacimiento=1977)) == (
        "Manu Ginobili",
        "1977",
    )
    assert fila_jugador_lista(JugadorDTO(nombre_completo="Pepe Argento", id=2, anioNacimiento=None)) == (
        "Pepe Argento",
        "—",
    )


def test_filtrar_competencias_por_anio_y_categoria():
    c1 = CompetenciaDTO(idCompetencia=1, nombre="Liga", anio=2026, tipo=None)
    c2 = CompetenciaDTO(idCompetencia=2, nombre="Provincial", anio=2027, tipo=None)
    cats_por_comp = {
        1: [CategoriaDTO(idCategoria=10, nombre="U17")],
        2: [CategoriaDTO(idCategoria=20, nombre="U21")],
    }

    assert filtrar_competencias([c1, c2], cats_por_comp) == [c1, c2]
    assert filtrar_competencias([c1, c2], cats_por_comp, anio=2026) == [c1]
    assert filtrar_competencias([c1, c2], cats_por_comp, id_categoria=20) == [c2]
    assert filtrar_competencias([c1, c2], cats_por_comp, anio=2026, id_categoria=20) == []


def test_filtrar_inscripciones_por_anio_y_categoria():
    comps = {
        1: CompetenciaDTO(idCompetencia=1, nombre="Liga", anio=2026, tipo=None),
        2: CompetenciaDTO(idCompetencia=2, nombre="Provincial", anio=2027, tipo=None),
    }
    i1 = InscripcionDTO(idInscripcion=1, idClub=1, idCategoria=10, idCompetencia=1, idListaBuenaFe=1)
    i2 = InscripcionDTO(idInscripcion=2, idClub=1, idCategoria=20, idCompetencia=2, idListaBuenaFe=2)

    assert filtrar_inscripciones([i1, i2], comps) == [i1, i2]
    assert filtrar_inscripciones([i1, i2], comps, anio=2027) == [i2]
    assert filtrar_inscripciones([i1, i2], comps, id_categoria=10) == [i1]
