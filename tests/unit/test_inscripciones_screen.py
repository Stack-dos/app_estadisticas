"""Tests unitarios de `InscripcionesScreen` (US-107) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, casilla, controles, desplegable, por_clave, textos

from aplicacion.casos_uso.agregar_jugadores_lista import AgregarJugadoresAListaBuenaFeUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscribirClubDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.lista_buena_fe_dto import (
    AgregarJugadoresListaDTO,
    JugadorRechazadoDTO,
    ResultadoAgregarJugadoresDTO,
)
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import InscripcionDuplicadaError, InscripcionEnUsoError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.inscripciones_screen import (
    CLAVE_RESULTADO_INSCRIPCION,
    TABLA_INSCRIPCIONES,
    crear_inscripciones_view,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga Provincial", anio=2026, tipo="PROVINCIAL")
ASOCIATIVO = CompetenciaDTO(idCompetencia=11, nombre="Asociativo", anio=2027, tipo="ASOCIATIVO")
U17 = CategoriaDTO(idCategoria=1, nombre="U17")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")
INSCRIPCION = InscripcionDTO(idInscripcion=5, idClub=7, idCategoria=2, idCompetencia=10, idListaBuenaFe=8)
INSCRIPCION_2 = InscripcionDTO(idInscripcion=6, idClub=7, idCategoria=1, idCompetencia=11, idListaBuenaFe=9)


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
    inscribir = MagicMock(spec=InscribirClubEnCompetenciaUseCase)
    inscribir.ejecutar.return_value = INSCRIPCION
    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.return_value = [INSCRIPCION]
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA]
    listar_cat = MagicMock(spec=ListarCategoriasUseCase)
    listar_cat.ejecutar.return_value = [U17, U21]
    listar_cat_comp = MagicMock(spec=ListarCategoriasDeCompetenciaUseCase)
    listar_cat_comp.ejecutar.return_value = [U21]
    eliminar_ins = MagicMock(spec=EliminarInscripcionUseCase)
    eliminar_ins.ejecutar.return_value = True
    return {
        "inscribir": inscribir,
        "listar_ins": listar_ins,
        "listar_comp": listar_comp,
        "listar_cat": listar_cat,
        "listar_cat_comp": listar_cat_comp,
        "eliminar_ins": eliminar_ins,
        "listar_plantel": MagicMock(
            spec=ListarJugadoresClubUseCase,
            **{"ejecutar.return_value": [JugadorDTO(nombre_completo="Pepe Argento", id=1, anioNacimiento=2005)]},
        ),
        "agregar_lista": MagicMock(
            spec=AgregarJugadoresAListaBuenaFeUseCase,
            **{"ejecutar.return_value": ResultadoAgregarJugadoresDTO(agregados=[1])},
        ),
        "listar_lista": MagicMock(spec=ListarListaBuenaFeUseCase, **{"ejecutar.return_value": [object()] * 3}),
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_inscripciones_view(
        page,
        mocks["inscribir"],
        mocks["listar_ins"],
        mocks["listar_comp"],
        mocks["listar_cat"],
        mocks["listar_cat_comp"],
        mocks["eliminar_ins"],
        mocks["listar_plantel"],
        mocks["agregar_lista"],
        mocks["listar_lista"],
        sesion,
    )


def _errores_visibles(vista: ft.View) -> list[str]:
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and c.value]


def _confirmar_ultimo_dialogo(page: MagicMock) -> None:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()


def test_lista_inscripciones_con_nombres_de_competencia_y_categoria(armar, mocks):
    vista = armar()

    mocks["listar_ins"].ejecutar.assert_called_once_with(7)
    contenido_tabla = textos(por_clave(vista, TABLA_INSCRIPCIONES))
    assert "Liga Provincial" in contenido_tabla
    assert "U21" in contenido_tabla


def test_filtrar_inscripciones_por_anio_y_categoria(armar, mocks):
    mocks["listar_comp"].ejecutar.return_value = [LIGA, ASOCIATIVO]
    mocks["listar_ins"].ejecutar.return_value = [INSCRIPCION, INSCRIPCION_2]
    vista = armar()

    desplegable(vista, "Filtrar por año").value = "2027"
    desplegable(vista, "Filtrar por año").on_select()
    contenido = textos(por_clave(vista, TABLA_INSCRIPCIONES))
    assert "Asociativo" in contenido
    assert "Liga Provincial" not in contenido

    desplegable(vista, "Filtrar por año").value = ""
    desplegable(vista, "Filtrar por categoría").value = "2"
    desplegable(vista, "Filtrar por categoría").on_select()
    contenido = textos(por_clave(vista, TABLA_INSCRIPCIONES))
    assert "Liga Provincial" in contenido
    assert "Asociativo" not in contenido


def test_elegir_competencia_filtra_las_categorias_a_las_habilitadas(armar, mocks, page):
    vista = armar()
    dd_comp = desplegable(vista, "Competencia")
    dd_cat = desplegable(vista, "Categoría")

    dd_comp.value = "10"
    dd_comp.on_select()

    mocks["listar_cat_comp"].ejecutar.assert_called_once_with(10)
    assert [(o.key, o.text) for o in dd_cat.options] == [("2", "U21")]
    page.update.assert_called()


def test_inscribir_club_usa_el_club_activo_y_refresca(armar, mocks):
    vista = armar()
    desplegable(vista, "Competencia").value = "10"
    desplegable(vista, "Competencia").on_select()
    desplegable(vista, "Categoría").value = "2"
    campo(vista, "Fecha de presentación").value = "2026-04-01"

    boton(vista, "Inscribir club").on_click()

    mocks["inscribir"].ejecutar.assert_called_once_with(
        InscribirClubDTO(idClub=7, idCategoria=2, idCompetencia=10, fechaPresentacion="2026-04-01")
    )
    assert _errores_visibles(vista) == []


def test_dar_de_baja_inscripcion_pide_confirmacion_y_muestra_error_si_tiene_partidos(armar, mocks, page):
    vista = armar()
    tabla = por_clave(vista, TABLA_INSCRIPCIONES)
    assert isinstance(tabla, ft.DataTable)
    btn_baja = tabla.rows[0].cells[4].content
    assert isinstance(btn_baja, ft.TextButton)

    btn_baja.on_click()
    _confirmar_ultimo_dialogo(page)
    mocks["eliminar_ins"].ejecutar.assert_called_once_with(5)

    mocks["eliminar_ins"].ejecutar.side_effect = InscripcionEnUsoError("Tiene partidos cargados")
    btn_baja.on_click()
    _confirmar_ultimo_dialogo(page)
    assert "Tiene partidos cargados" in _errores_visibles(vista)


def test_inscripcion_duplicada_muestra_el_error_de_dominio(armar, mocks):
    mocks["inscribir"].ejecutar.side_effect = InscripcionDuplicadaError("El club ya esta inscripto")
    vista = armar()
    desplegable(vista, "Competencia").value = "10"
    desplegable(vista, "Categoría").value = "2"

    boton(vista, "Inscribir club").on_click()

    assert "El club ya esta inscripto" in _errores_visibles(vista)


def test_error_inesperado_al_inscribir_muestra_mensaje_generico(armar, mocks):
    mocks["inscribir"].ejecutar.side_effect = RuntimeError("fallo db")
    vista = armar()
    desplegable(vista, "Competencia").value = "10"
    desplegable(vista, "Categoría").value = "2"

    boton(vista, "Inscribir club").on_click()

    assert MENSAJE_ERROR_INESPERADO in _errores_visibles(vista)


# ----------------------------------------------------------------------------- agregar plantel (US-114)


def _inscribir(vista: ft.View) -> None:
    desplegable(vista, "Competencia").value = "10"
    desplegable(vista, "Competencia").on_select()
    desplegable(vista, "Categoría").value = "2"
    boton(vista, "Inscribir club").on_click()


def _resultado(vista: ft.View) -> str:
    return por_clave(vista, CLAVE_RESULTADO_INSCRIPCION).value or ""


def test_al_inscribir_pasa_todo_el_plantel_a_la_lista_por_defecto(armar, mocks):
    vista = armar()
    assert casilla(vista, "Agregar todo el plantel a la lista").value

    _inscribir(vista)

    mocks["agregar_lista"].ejecutar.assert_called_once_with(AgregarJugadoresListaDTO(idInscripcion=5, idJugadores=[1]))
    assert _resultado(vista) == "Club inscripto. Se agregaron 1 jugador(es) a la lista."


def test_si_se_desmarca_no_toca_la_lista(armar, mocks):
    vista = armar()
    casilla(vista, "Agregar todo el plantel a la lista").value = False

    _inscribir(vista)

    mocks["agregar_lista"].ejecutar.assert_not_called()
    assert _resultado(vista) == "Club inscripto."


def test_avisa_los_jugadores_que_no_entraron_y_si_no_hay_plantel(armar, mocks):
    mocks["agregar_lista"].ejecutar.return_value = ResultadoAgregarJugadoresDTO(
        rechazados=[JugadorRechazadoDTO(idJugador=1, motivo="Ya está en otra lista")]
    )
    vista = armar()
    _inscribir(vista)
    assert "1 no entraron" in _resultado(vista)

    mocks["listar_plantel"].ejecutar.return_value = []
    _inscribir(vista)
    assert "Todavía no tenés jugadores" in _resultado(vista)


def test_la_tabla_muestra_cuantos_jugadores_tiene_cada_lista_y_no_el_numero_de_lista(armar, mocks):
    vista = armar()

    contenido = textos(por_clave(vista, TABLA_INSCRIPCIONES))
    assert "Jugadores en la lista" in contenido
    assert "3" in contenido
    assert not any(t.startswith("Lista #") for t in contenido)
    mocks["listar_lista"].ejecutar.assert_called_with(INSCRIPCION.idInscripcion)
