"""Tests unitarios de `ListaBuenaFeScreen` (US-107) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, controles, desplegable, por_clave, textos

from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.casos_uso.vaciar_lista_buena_fe import VaciarListaBuenaFeUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.lista_buena_fe_dto import AgregarJugadorListaDTO, JugadorEnListaDTO, QuitarJugadorListaDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import JugadorYaEnListaError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.lista_buena_fe_screen import (
    TABLA_LISTA_BUENA_FE,
    crear_lista_buena_fe_view,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga", anio=2026, tipo="PROVINCIAL")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")
INSCRIPCION = InscripcionDTO(idInscripcion=5, idClub=7, idCategoria=2, idCompetencia=10, idListaBuenaFe=8)
MANU = JugadorDTO(nombre_completo="Manu Ginobili", id=1, anioNacimiento=1977)
SCOLA = JugadorDTO(nombre_completo="Luis Scola", id=2, anioNacimiento=1980)


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
    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.return_value = [INSCRIPCION]
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA]
    listar_cat = MagicMock(spec=ListarCategoriasUseCase)
    listar_cat.ejecutar.return_value = [U21]
    listar_lista = MagicMock(spec=ListarListaBuenaFeUseCase)
    listar_lista.ejecutar.return_value = [MANU, SCOLA]
    listar_jugadores = MagicMock(spec=ListarJugadoresClubUseCase)
    listar_jugadores.ejecutar.return_value = [MANU, SCOLA]
    agregar = MagicMock(spec=AgregarJugadorAListaBuenaFeUseCase)
    agregar.ejecutar.return_value = JugadorEnListaDTO(idListaBuenaFe=8, idInscripcion=5, idJugador=2)
    quitar = MagicMock(spec=QuitarJugadorDeListaBuenaFeUseCase)
    quitar.ejecutar.return_value = JugadorEnListaDTO(idListaBuenaFe=8, idInscripcion=5, idJugador=1)
    vaciar = MagicMock(spec=VaciarListaBuenaFeUseCase)
    vaciar.ejecutar.return_value = 2
    eliminar_ins = MagicMock(spec=EliminarInscripcionUseCase)
    eliminar_ins.ejecutar.return_value = True
    return {
        "listar_ins": listar_ins,
        "listar_comp": listar_comp,
        "listar_cat": listar_cat,
        "listar_lista": listar_lista,
        "listar_jugadores": listar_jugadores,
        "agregar": agregar,
        "quitar": quitar,
        "vaciar": vaciar,
        "eliminar_ins": eliminar_ins,
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_lista_buena_fe_view(
        page,
        mocks["listar_ins"],
        mocks["listar_comp"],
        mocks["listar_cat"],
        mocks["listar_lista"],
        mocks["listar_jugadores"],
        mocks["agregar"],
        mocks["quitar"],
        mocks["vaciar"],
        mocks["eliminar_ins"],
        sesion,
    )


def _errores_visibles(vista: ft.View) -> list[str]:
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and c.value]


def _confirmar_ultimo_dialogo(page: MagicMock) -> None:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()


def test_carga_inscripcion_y_lista_de_jugadores(armar, mocks):
    vista = armar()

    mocks["listar_lista"].ejecutar.assert_called_once_with(5)
    mocks["listar_jugadores"].ejecutar.assert_called_once_with(7)
    contenido = textos(por_clave(vista, TABLA_LISTA_BUENA_FE))
    assert "Manu Ginobili" in contenido
    assert "Luis Scola" in contenido


def test_agregar_jugador_a_la_lista_limpia_seleccion_y_refresca(armar, mocks, page):
    vista = armar()
    desplegable(vista, "Jugador del club").value = "2"

    boton(vista, "Agregar a la lista").on_click()

    mocks["agregar"].ejecutar.assert_called_once_with(AgregarJugadorListaDTO(idInscripcion=5, idJugador=2))
    assert desplegable(vista, "Jugador del club").value is None
    page.update.assert_called()


def test_cada_boton_quitar_usa_su_propio_jugador(armar, mocks):
    vista = armar()
    tabla = por_clave(vista, TABLA_LISTA_BUENA_FE)
    assert isinstance(tabla, ft.DataTable)

    boton_quitar_manu = tabla.rows[0].cells[2].content
    assert isinstance(boton_quitar_manu, ft.TextButton)
    boton_quitar_manu.on_click()

    mocks["quitar"].ejecutar.assert_called_once_with(QuitarJugadorListaDTO(idInscripcion=5, idJugador=1))


def test_vaciar_lista_y_dar_de_baja_inscripcion_piden_confirmacion(armar, mocks, page):
    vista = armar()

    boton(vista, "Vaciar lista").on_click()
    _confirmar_ultimo_dialogo(page)
    mocks["vaciar"].ejecutar.assert_called_once_with(5)

    boton(vista, "Dar de baja inscripción").on_click()
    _confirmar_ultimo_dialogo(page)
    mocks["eliminar_ins"].ejecutar.assert_called_once_with(5)


def test_jugador_ya_en_lista_muestra_error_de_dominio(armar, mocks):
    mocks["agregar"].ejecutar.side_effect = JugadorYaEnListaError("El jugador ya esta en la lista")
    vista = armar()
    desplegable(vista, "Jugador del club").value = "1"

    boton(vista, "Agregar a la lista").on_click()

    assert "El jugador ya esta en la lista" in _errores_visibles(vista)


def test_error_inesperado_al_agregar_muestra_mensaje_generico(armar, mocks):
    mocks["agregar"].ejecutar.side_effect = OSError("error inesperado")
    vista = armar()
    desplegable(vista, "Jugador del club").value = "1"

    boton(vista, "Agregar a la lista").on_click()

    assert MENSAJE_ERROR_INESPERADO in _errores_visibles(vista)
