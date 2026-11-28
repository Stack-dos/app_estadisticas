"""Tests unitarios de `CategoriasScreen` (US-113: catalogo separado de Competencias) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, controles, por_clave, textos

from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO, CrearCategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import CategoriaDuplicadaError, CategoriaEnUsoError
from infraestructura.ui.flet.screens.categorias_screen import SIN_CATEGORIAS, TABLA_CATEGORIAS, crear_categorias_view

U17 = CategoriaDTO(idCategoria=1, nombre="U17")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")


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
    return {
        "crear": MagicMock(spec=CrearCategoriaUseCase, **{"ejecutar.return_value": U21}),
        "listar": MagicMock(spec=ListarCategoriasUseCase, **{"ejecutar.return_value": [U17, U21]}),
        "eliminar": MagicMock(spec=EliminarCategoriaUseCase, **{"ejecutar.return_value": True}),
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_categorias_view(page, mocks["crear"], mocks["listar"], mocks["eliminar"], sesion)


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
        crear_categorias_view(page, mocks["crear"], mocks["listar"], mocks["eliminar"], sesion_sin_club)


def test_lista_el_catalogo_o_el_estado_vacio(armar, mocks):
    contenido = textos(por_clave(armar(), TABLA_CATEGORIAS))
    assert "U17" in contenido
    assert "U21" in contenido

    mocks["listar"].ejecutar.return_value = []
    assert SIN_CATEGORIAS in textos(por_clave(armar(), TABLA_CATEGORIAS))


def test_crear_categoria_limpia_el_campo_y_refresca(armar, mocks):
    vista = armar()
    campo(vista, "Nombre de la categoría").value = "U13"

    boton(vista, "Crear categoría").on_click()

    mocks["crear"].ejecutar.assert_called_once_with(CrearCategoriaDTO(nombre="U13"))
    assert campo(vista, "Nombre de la categoría").value == ""
    assert mocks["listar"].ejecutar.call_count == 2


def test_crear_categoria_duplicada_muestra_error_de_dominio(armar, mocks):
    mocks["crear"].ejecutar.side_effect = CategoriaDuplicadaError("Ya existe una categoria")
    vista = armar()
    campo(vista, "Nombre de la categoría").value = "U17"

    boton(vista, "Crear categoría").on_click()

    assert "Ya existe una categoria" in _errores_visibles(vista)


def test_eliminar_categoria_pide_confirmacion_y_muestra_error_si_esta_en_uso(armar, mocks, page):
    vista = armar()
    tabla = por_clave(vista, TABLA_CATEGORIAS)
    assert isinstance(tabla, ft.DataTable)
    btn_eliminar = tabla.rows[0].cells[1].content
    assert isinstance(btn_eliminar, ft.TextButton)

    btn_eliminar.on_click()
    _confirmar_ultimo_dialogo(page)
    mocks["eliminar"].ejecutar.assert_called_once_with(1)

    mocks["eliminar"].ejecutar.side_effect = CategoriaEnUsoError("Categoria en uso")
    btn_eliminar.on_click()
    _confirmar_ultimo_dialogo(page)
    assert "Categoria en uso" in _errores_visibles(vista)
