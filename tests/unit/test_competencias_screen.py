"""Tests unitarios de `CompetenciasScreen` (US-107; categorias por fila de la US-113) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, casilla, controles, desplegable, por_clave, textos

from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CategoriaCompetenciaDTO, CompetenciaDTO, CrearCompetenciaDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import CategoriaConInscripcionesError, CompetenciaEnUsoError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.competencias_screen import (
    SIN_CATEGORIAS_CATALOGO,
    TABLA_COMPETENCIAS,
    crear_competencias_view,
)

U17 = CategoriaDTO(idCategoria=1, nombre="U17")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")
LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga", anio=2026, tipo="PROVINCIAL")
PROVINCIAL = CompetenciaDTO(idCompetencia=11, nombre="Provincial", anio=2027, tipo="PROVINCIAL")


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))
    return sesion


@pytest.fixture
def mocks():
    crear_comp = MagicMock(spec=CrearCompetenciaUseCase)
    crear_comp.ejecutar.return_value = LIGA
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA]
    listar_cat = MagicMock(spec=ListarCategoriasUseCase)
    listar_cat.ejecutar.return_value = [U17, U21]
    habilitar_cat = MagicMock(spec=HabilitarCategoriaEnCompetenciaUseCase)
    habilitar_cat.ejecutar.return_value = CategoriaCompetenciaDTO(idCompetencia=10, idCategoria=2)
    listar_cat_comp = MagicMock(spec=ListarCategoriasDeCompetenciaUseCase)
    listar_cat_comp.ejecutar.return_value = [U17]
    quitar_cat = MagicMock(spec=QuitarCategoriaDeCompetenciaUseCase)
    quitar_cat.ejecutar.return_value = CategoriaCompetenciaDTO(idCompetencia=10, idCategoria=1)
    eliminar_comp = MagicMock(spec=EliminarCompetenciaUseCase)
    eliminar_comp.ejecutar.return_value = True
    return {
        "crear_comp": crear_comp,
        "listar_comp": listar_comp,
        "listar_cat": listar_cat,
        "habilitar_cat": habilitar_cat,
        "listar_cat_comp": listar_cat_comp,
        "quitar_cat": quitar_cat,
        "eliminar_comp": eliminar_comp,
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_competencias_view(
        page,
        mocks["crear_comp"],
        mocks["listar_comp"],
        mocks["listar_cat"],
        mocks["habilitar_cat"],
        mocks["listar_cat_comp"],
        mocks["quitar_cat"],
        mocks["eliminar_comp"],
        sesion,
    )


def _errores_visibles(vista: ft.View) -> list[str]:
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and c.value]


def _confirmar_ultimo_dialogo(page: MagicMock) -> None:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()


def test_sin_club_activo_falla_al_construir(page, mocks):
    sesion_sin_club = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion_sin_club.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))

    with pytest.raises(RuntimeError, match="club activo"):
        crear_competencias_view(
            page,
            mocks["crear_comp"],
            mocks["listar_comp"],
            mocks["listar_cat"],
            mocks["habilitar_cat"],
            mocks["listar_cat_comp"],
            mocks["quitar_cat"],
            mocks["eliminar_comp"],
            sesion_sin_club,
        )


def _acciones_fila(vista: ft.View, fila: int = 0) -> ft.Row:
    tabla = por_clave(vista, TABLA_COMPETENCIAS)
    assert isinstance(tabla, ft.DataTable)
    acciones = tabla.rows[fila].cells[4].content
    assert isinstance(acciones, ft.Row)
    return acciones


def _abrir_categorias(vista: ft.View, page: MagicMock) -> ft.AlertDialog:
    boton(_acciones_fila(vista), "Categorías").on_click()
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    return dialogo


def test_lista_competencias_con_sus_categorias_habilitadas(armar):
    contenido = textos(por_clave(armar(), TABLA_COMPETENCIAS))

    assert "Liga" in contenido
    assert "U17" in contenido  # la habilitada
    assert "U21" not in contenido


def test_filtrar_competencias_por_anio_y_categoria(armar, mocks):
    mocks["listar_comp"].ejecutar.return_value = [LIGA, PROVINCIAL]
    mocks["listar_cat_comp"].ejecutar.side_effect = lambda id_comp: [U17] if id_comp == 10 else [U21]
    vista = armar()

    desplegable(vista, "Filtrar por año").value = "2027"
    desplegable(vista, "Filtrar por año").on_select()
    tabla_txt = textos(por_clave(vista, TABLA_COMPETENCIAS))
    assert "Provincial" in tabla_txt
    assert "Liga" not in tabla_txt

    desplegable(vista, "Filtrar por año").value = ""
    desplegable(vista, "Filtrar por categoría").value = "1"
    desplegable(vista, "Filtrar por categoría").on_select()
    tabla_txt = textos(por_clave(vista, TABLA_COMPETENCIAS))
    assert "Liga" in tabla_txt
    assert "Provincial" not in tabla_txt


def test_crear_competencia_toma_casillas_y_limpia_campos(armar, mocks, page):
    vista = armar()
    campo(vista, "Nombre de la competencia").value = "Asociativo"
    campo(vista, "Año").value = "2026"
    campo(vista, "Tipo (opcional)").value = "ASOCIATIVO"
    casilla(vista, "U17").value = True
    casilla(vista, "U21").value = True

    boton(vista, "Crear competencia").on_click()

    mocks["crear_comp"].ejecutar.assert_called_once_with(
        CrearCompetenciaDTO(nombre="Asociativo", anio=2026, tipo="ASOCIATIVO", idCategorias=[1, 2])
    )
    assert campo(vista, "Nombre de la competencia").value == ""
    assert campo(vista, "Año").value == ""
    page.update.assert_called()


def test_crear_competencia_con_anio_no_numerico_muestra_error(armar, mocks):
    vista = armar()
    campo(vista, "Nombre de la competencia").value = "Asociativo"
    campo(vista, "Año").value = "dos mil"

    boton(vista, "Crear competencia").on_click()

    mocks["crear_comp"].ejecutar.assert_not_called()
    assert "El año debe ser un número entero" in _errores_visibles(vista)


def test_dialogo_de_categorias_marca_las_habilitadas_y_guarda_solo_los_cambios(armar, mocks, page):
    vista = armar()
    dialogo = _abrir_categorias(vista, page)
    assert casilla(dialogo, "U17").value is True
    assert casilla(dialogo, "U21").value is False

    casilla(dialogo, "U17").value = False
    casilla(dialogo, "U21").value = True
    boton(dialogo, "Guardar").on_click()

    mocks["habilitar_cat"].ejecutar.assert_called_once_with(CategoriaCompetenciaDTO(idCompetencia=10, idCategoria=2))
    mocks["quitar_cat"].ejecutar.assert_called_once_with(CategoriaCompetenciaDTO(idCompetencia=10, idCategoria=1))
    page.pop_dialog.assert_called_once()


def test_dialogo_de_categorias_sin_cambios_no_llama_a_nada(armar, mocks, page):
    boton(_abrir_categorias(armar(), page), "Guardar").on_click()

    mocks["habilitar_cat"].ejecutar.assert_not_called()
    mocks["quitar_cat"].ejecutar.assert_not_called()


def test_quitar_categoria_con_inscriptos_muestra_error_en_el_dialogo_sin_cerrar(armar, mocks, page):
    mocks["quitar_cat"].ejecutar.side_effect = CategoriaConInscripcionesError("Ya tiene clubes inscriptos")
    dialogo = _abrir_categorias(armar(), page)

    casilla(dialogo, "U17").value = False
    boton(dialogo, "Guardar").on_click()

    page.pop_dialog.assert_not_called()
    assert "Ya tiene clubes inscriptos" in _errores_visibles(dialogo)


def test_sin_catalogo_el_alta_ofrece_ir_a_categorias(armar, mocks, page):
    mocks["listar_cat"].ejecutar.return_value = []
    vista = armar()

    assert SIN_CATEGORIAS_CATALOGO in textos(vista)
    boton(vista, "Ir a Categorías").on_click()
    page.navigate.assert_called_once_with("/categorias")


def test_eliminar_competencia_pide_confirmacion_y_muestra_error_si_esta_en_uso(armar, mocks, page):
    vista = armar()
    btn_eliminar = boton(_acciones_fila(vista), "Eliminar")

    btn_eliminar.on_click()
    _confirmar_ultimo_dialogo(page)
    mocks["eliminar_comp"].ejecutar.assert_called_once_with(10)

    mocks["eliminar_comp"].ejecutar.side_effect = CompetenciaEnUsoError("Tiene clubes inscriptos")
    btn_eliminar.on_click()
    _confirmar_ultimo_dialogo(page)
    assert "Tiene clubes inscriptos" in _errores_visibles(vista)


def test_error_inesperado_al_crear_competencia_muestra_mensaje_generico(armar, mocks):
    mocks["crear_comp"].ejecutar.side_effect = OSError("disco lleno")
    vista = armar()
    campo(vista, "Nombre de la competencia").value = "Liga"
    campo(vista, "Año").value = "2026"

    boton(vista, "Crear competencia").on_click()

    assert MENSAJE_ERROR_INESPERADO in _errores_visibles(vista)
