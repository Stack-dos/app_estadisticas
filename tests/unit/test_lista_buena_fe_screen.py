"""Tests unitarios de `ListaBuenaFeScreen` (US-107; alta masiva de la US-113) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, casilla, controles, por_clave, textos

from aplicacion.casos_uso.agregar_jugadores_lista import AgregarJugadoresAListaBuenaFeUseCase
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
from aplicacion.dtos.lista_buena_fe_dto import (
    AgregarJugadoresListaDTO,
    JugadorEnListaDTO,
    JugadorRechazadoDTO,
    QuitarJugadorListaDTO,
    ResultadoAgregarJugadoresDTO,
)
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.lista_buena_fe_screen import (
    CASILLAS_PLANTEL,
    PLANTEL_COMPLETO,
    PLANTEL_VACIO,
    TABLA_LISTA_BUENA_FE,
    crear_lista_buena_fe_view,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga", anio=2026, tipo="PROVINCIAL")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")
INSCRIPCION = InscripcionDTO(idInscripcion=5, idClub=7, idCategoria=2, idCompetencia=10, idListaBuenaFe=8)
MANU = JugadorDTO(nombre_completo="Manu Ginobili", id=1, anioNacimiento=1977)
SCOLA = JugadorDTO(nombre_completo="Luis Scola", id=2, anioNacimiento=1980)
FACU = JugadorDTO(nombre_completo="Facundo Campazzo", id=3, anioNacimiento=None)


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
    listar_jugadores.ejecutar.return_value = [MANU, SCOLA, FACU]
    agregar = MagicMock(spec=AgregarJugadoresAListaBuenaFeUseCase)
    agregar.ejecutar.return_value = ResultadoAgregarJugadoresDTO(agregados=[3])
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


def _casillas(vista: ft.View) -> list[ft.Checkbox]:
    return [c for c in controles(por_clave(vista, CASILLAS_PLANTEL)) if isinstance(c, ft.Checkbox)]


def test_solo_ofrece_los_jugadores_del_plantel_que_no_estan_en_la_lista(armar):
    vista = armar()

    assert [c.label for c in _casillas(vista)] == ["Facundo Campazzo"]


def test_agregar_varios_seleccionados_de_una_vez(armar, mocks, page):
    mocks["listar_lista"].ejecutar.return_value = [MANU]
    mocks["agregar"].ejecutar.return_value = ResultadoAgregarJugadoresDTO(agregados=[2, 3])
    vista = armar()
    scola, facu = _casillas(vista)
    assert [scola.label, facu.label] == ["Luis Scola (1980)", "Facundo Campazzo"]

    scola.value = True
    facu.value = True
    facu.on_change()
    assert boton(vista, "Agregar seleccionados (2)")  # el boton cuenta cuantos van

    boton(vista, "Agregar seleccionados (2)").on_click()

    mocks["agregar"].ejecutar.assert_called_once_with(AgregarJugadoresListaDTO(idInscripcion=5, idJugadores=[2, 3]))
    assert "Se agregaron 2 jugadores a la lista." in textos(vista)
    assert mocks["listar_lista"].ejecutar.call_count == 2  # refresca la lista
    page.update.assert_called()


def test_seleccionar_todos_marca_cada_casilla(armar, mocks):
    mocks["listar_lista"].ejecutar.return_value = []
    vista = armar()

    todos = casilla(vista, "Seleccionar todos")
    todos.value = True
    todos.on_change()

    assert all(c.value for c in _casillas(vista))
    assert boton(vista, "Agregar seleccionados (3)")


def test_informa_los_rechazados_con_su_motivo_sin_frenar_al_resto(armar, mocks):
    mocks["listar_lista"].ejecutar.return_value = []
    mocks["agregar"].ejecutar.return_value = ResultadoAgregarJugadoresDTO(
        agregados=[1], rechazados=[JugadorRechazadoDTO(idJugador=2, motivo="El jugador ya esta en la lista")]
    )
    vista = armar()
    for c in _casillas(vista)[:2]:
        c.value = True

    boton(vista, "Agregar seleccionados").on_click()

    assert "Se agregó 1 jugador a la lista." in textos(vista)
    assert "Luis Scola: El jugador ya esta en la lista" in _errores_visibles(vista)


def test_sin_seleccion_muestra_el_error_del_caso_de_uso(armar, mocks):
    mocks["agregar"].ejecutar.side_effect = DatoInvalidoError("Elegí al menos un jugador para agregar a la lista.")
    vista = armar()

    boton(vista, "Agregar seleccionados").on_click()

    assert "Elegí al menos un jugador para agregar a la lista." in _errores_visibles(vista)


def test_plantel_completo_o_vacio_lo_avisa_y_deshabilita_agregar(armar, mocks):
    mocks["listar_lista"].ejecutar.return_value = [MANU, SCOLA, FACU]
    vista = armar()
    assert PLANTEL_COMPLETO in textos(por_clave(vista, CASILLAS_PLANTEL))
    assert boton(vista, "Agregar seleccionados").disabled

    mocks["listar_jugadores"].ejecutar.return_value = []
    mocks["listar_lista"].ejecutar.return_value = []
    assert PLANTEL_VACIO in textos(por_clave(armar(), CASILLAS_PLANTEL))


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


def test_error_inesperado_al_agregar_muestra_mensaje_generico(armar, mocks):
    mocks["agregar"].ejecutar.side_effect = OSError("error inesperado")
    vista = armar()
    _casillas(vista)[0].value = True

    boton(vista, "Agregar seleccionados").on_click()

    assert MENSAJE_ERROR_INESPERADO in _errores_visibles(vista)
