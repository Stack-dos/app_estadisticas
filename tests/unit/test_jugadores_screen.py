"""Tests unitarios de `JugadoresScreen` (US-112; dialogos de la US-113; buscador y alcance de la US-114)."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, botones_icono, campo, controles, por_clave, textos

from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_jugadores_todos import ListarJugadoresTodosUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO, DesvincularJugadorDTO, VincularJugadorClubDTO, VinculoDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, EditarJugadorDTO, JugadorConClubDTO, JugadorDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError, JugadorEnUsoError
from infraestructura.ui.flet.screens.jugadores_screen import (
    COINCIDENCIAS_ALTA,
    SELECTOR_ALCANCE,
    SIN_CLUB,
    SIN_COINCIDENCIAS,
    SIN_JUGADORES,
    TABLA_JUGADORES,
    TODOS_LOS_CLUBES,
    coincide,
    crear_jugadores_view,
    fila_jugador,
)

PEPE = JugadorDTO(id=1, nombre_completo="Pepe Argento", anioNacimiento=1980, nombre="Pepe", apellido="Argento")
MANU = JugadorDTO(id=7, nombre_completo="Manu Ginobili", anioNacimiento=1977, nombre="Manu", apellido="Ginobili")
FACU = JugadorDTO(id=10, nombre_completo="Facundo Campazzo", anioNacimiento=None, nombre="Facundo", apellido="Campazzo")
TODOS = [
    JugadorConClubDTO("Pepe Argento", 1, 1980, "Atenas"),
    JugadorConClubDTO("Manu Ginobili", 7, 1977, "Instituto"),
    JugadorConClubDTO("Facundo Campazzo", 10, None, None),
]


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
    listar = MagicMock(spec=ListarJugadoresClubUseCase)
    listar.ejecutar.return_value = [PEPE]
    registrar = MagicMock(spec=RegistrarJugadorUseCase)
    registrar.ejecutar.return_value = MANU
    vincular = MagicMock(spec=VincularJugadorAClubUseCase)
    vincular.ejecutar.return_value = VinculoDTO(idJugador=7, idClub=7, fechaDesde="2026-03-01", fechaHasta=None)
    desvincular = MagicMock(spec=DesvincularJugadorDeClubUseCase)
    desvincular.ejecutar.return_value = VinculoDTO(
        idJugador=1, idClub=7, fechaDesde="2025-01-01", fechaHasta="2026-03-01"
    )
    buscar = MagicMock(spec=BuscarJugadoresPorNombreUseCase)
    buscar.ejecutar.return_value = []
    editar = MagicMock(spec=EditarJugadorUseCase)
    editar.ejecutar.return_value = PEPE
    eliminar = MagicMock(spec=EliminarJugadorUseCase)
    eliminar.ejecutar.return_value = True
    todos = MagicMock(spec=ListarJugadoresTodosUseCase, **{"ejecutar.return_value": TODOS})
    return {
        "todos": todos,
        "listar": listar,
        "registrar": registrar,
        "vincular": vincular,
        "desvincular": desvincular,
        "buscar": buscar,
        "editar": editar,
        "eliminar": eliminar,
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_jugadores_view(
        page,
        mocks["listar"],
        mocks["registrar"],
        mocks["vincular"],
        mocks["desvincular"],
        mocks["buscar"],
        mocks["editar"],
        mocks["eliminar"],
        mocks["todos"],
        sesion,
    )


def _ver_todos(vista: ft.View) -> None:
    selector = por_clave(vista, SELECTOR_ALCANCE)
    selector.selected = [TODOS_LOS_CLUBES]
    selector.on_change()


def _errores_visibles(vista: ft.View) -> list[str]:
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and c.value]


def _confirmar_ultimo_dialogo(page: MagicMock) -> None:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()


def _abrir_alta(page: MagicMock, vista: ft.View) -> ft.AlertDialog:
    """El alta vive en un dialogo que abre "Nuevo jugador" (US-113)."""
    boton(vista, "Nuevo jugador").on_click()
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    return dialogo


def test_fila_jugador_formatea_anio_o_guion():
    assert fila_jugador(PEPE) == ("Pepe Argento", "1980")
    assert fila_jugador(FACU) == ("Facundo Campazzo", "—")


def test_exige_club_activo(page, mocks):
    sesion_sin_club = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion_sin_club.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))

    with pytest.raises(RuntimeError, match="club activo"):
        crear_jugadores_view(
            page,
            mocks["listar"],
            mocks["registrar"],
            mocks["vincular"],
            mocks["desvincular"],
            mocks["buscar"],
            mocks["editar"],
            mocks["eliminar"],
            mocks["todos"],
            sesion_sin_club,
        )


def test_muestra_el_plantel_del_club_activo_y_estado_vacio(armar, mocks):
    vista = armar()
    mocks["listar"].ejecutar.assert_called_once_with(7)
    contenido = textos(por_clave(vista, TABLA_JUGADORES))
    assert "Pepe Argento" in contenido
    assert "1980" in contenido

    mocks["listar"].ejecutar.return_value = []
    vista_vacia = armar()
    assert SIN_JUGADORES in textos(por_clave(vista_vacia, TABLA_JUGADORES))


def test_alta_sin_coincidencias_registra_y_vincula_al_club_activo(page, armar, mocks):
    vista = armar()
    alta = _abrir_alta(page, vista)
    campo(alta, "Nombre").value = "Manu"
    campo(alta, "Apellido").value = "Ginobili"
    campo(alta, "Año de nacimiento (opcional)").value = "1977"
    campo(alta, "Fecha de ingreso").value = "2026-03-01"

    boton(alta, "Registrar jugador").on_click()

    mocks["buscar"].ejecutar.assert_called_once_with("Manu Ginobili")
    mocks["registrar"].ejecutar.assert_called_once_with(
        CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=1977)
    )
    mocks["vincular"].ejecutar.assert_called_once_with(
        VincularJugadorClubDTO(idJugador=7, idClub=7, fechaDesde="2026-03-01")
    )
    assert campo(alta, "Nombre").value == ""
    assert campo(alta, "Apellido").value == ""
    page.pop_dialog.assert_called_once()  # el dialogo se cierra al terminar bien


def test_alta_con_homonimo_en_otro_club_avisa_donde_esta_y_no_ofrece_vincular(page, armar, mocks):
    mocks["buscar"].ejecutar.return_value = [MANU]
    vista = armar()
    alta = _abrir_alta(page, vista)
    campo(alta, "Nombre").value = "Manu"
    campo(alta, "Apellido").value = "Ginobili"

    boton(alta, "Registrar jugador").on_click()

    mocks["registrar"].ejecutar.assert_not_called()  # no duplica sin preguntar
    panel = por_clave(alta, COINCIDENCIAS_ALTA)
    assert "Manu Ginobili (1977)" in textos(panel)
    assert "en Instituto" in textos(panel)
    with pytest.raises(StopIteration):
        boton(panel, "Sin club: sumarlo a Atenas")


def test_alta_con_homonimo_sin_club_permite_sumarlo_en_vez_de_duplicar(page, armar, mocks):
    mocks["buscar"].ejecutar.return_value = [FACU]
    vista = armar()
    alta = _abrir_alta(page, vista)
    campo(alta, "Nombre").value = "Facundo"
    campo(alta, "Apellido").value = "Campazzo"
    campo(alta, "Fecha de ingreso").value = "2026-03-01"

    boton(alta, "Registrar jugador").on_click()
    boton(por_clave(alta, COINCIDENCIAS_ALTA), "Sin club: sumarlo a Atenas").on_click()

    mocks["registrar"].ejecutar.assert_not_called()
    mocks["vincular"].ejecutar.assert_called_once_with(
        VincularJugadorClubDTO(idJugador=10, idClub=7, fechaDesde="2026-03-01")
    )
    page.pop_dialog.assert_called_once()


def test_alta_con_coincidencias_permite_confirmar_si_es_otra_persona(page, armar, mocks):
    mocks["buscar"].ejecutar.return_value = [MANU]
    vista = armar()
    alta = _abrir_alta(page, vista)
    campo(alta, "Nombre").value = "Manu"
    campo(alta, "Apellido").value = "Ginobili"
    campo(alta, "Fecha de ingreso").value = "2026-03-01"

    boton(alta, "Registrar jugador").on_click()
    panel = por_clave(alta, COINCIDENCIAS_ALTA)
    boton(panel, "Crear nuevo jugador de todas formas").on_click()

    mocks["registrar"].ejecutar.assert_called_once_with(
        CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=None)
    )
    mocks["vincular"].ejecutar.assert_called_once()


def test_coincide_ignora_mayusculas_y_tildes_y_exige_todas_las_palabras():
    assert coincide("Manu Ginóbili", "ginobili")
    assert coincide("Manu Ginobili", "manu gin")
    assert not coincide("Manu Ginobili", "manu argento")
    assert coincide("Manu Ginobili", "")


def test_el_buscador_filtra_el_plantel_mientras_se_escribe(armar, mocks):
    mocks["listar"].ejecutar.return_value = [PEPE, FACU]
    vista = armar()

    buscador = campo(vista, "Buscar")
    buscador.value = "campa"
    buscador.on_change()

    contenido = textos(por_clave(vista, TABLA_JUGADORES))
    assert "Facundo Campazzo" in contenido
    assert "Pepe Argento" not in contenido

    buscador.value = "nadie"
    buscador.on_change()
    assert SIN_COINCIDENCIAS in textos(por_clave(vista, TABLA_JUGADORES))


def test_en_todos_los_clubes_muestra_el_club_actual_de_cada_jugador(armar, mocks):
    vista = armar()

    _ver_todos(vista)

    contenido = textos(por_clave(vista, TABLA_JUGADORES))
    assert "Club actual" in contenido
    assert "Instituto" in contenido
    assert SIN_CLUB in contenido
    # Solo el que no tiene club se puede borrar desde aca; los demas no tienen acciones
    tabla = por_clave(vista, TABLA_JUGADORES)
    assert len(botones_icono(tabla, "Eliminar")) == 1
    assert botones_icono(tabla, "Editar") == []


def test_dar_de_baja_pide_la_fecha_en_el_dialogo_y_desvincula(page, armar, mocks):
    vista = armar()

    botones_icono(vista, "Dar de baja")[0].on_click()
    dialogo = page.show_dialog.call_args.args[0]
    mocks["desvincular"].ejecutar.assert_not_called()
    campo(dialogo, "Fecha de baja").value = "2026-06-30"

    _confirmar_ultimo_dialogo(page)
    mocks["desvincular"].ejecutar.assert_called_once_with(DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30"))
    page.pop_dialog.assert_called_once()


def test_dar_de_baja_sin_fecha_muestra_error_en_el_dialogo(page, armar, mocks):
    vista = armar()

    botones_icono(vista, "Dar de baja")[0].on_click()
    dialogo = page.show_dialog.call_args.args[0]
    campo(dialogo, "Fecha de baja").value = "  "
    _confirmar_ultimo_dialogo(page)

    mocks["desvincular"].ejecutar.assert_not_called()
    page.pop_dialog.assert_not_called()
    assert "Indicá la fecha de baja" in _errores_visibles(dialogo)


def test_editar_jugador_abre_dialogo_y_guarda_cambios(page, armar, mocks):
    vista = armar()

    botones_icono(vista, "Editar")[0].on_click()
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    campo(dialogo, "Nombre").value = "José"
    campo(dialogo, "Apellido").value = "Argento"
    campo(dialogo, "Año de nacimiento (opcional)").value = "1981"

    boton(dialogo, "Guardar").on_click()

    mocks["editar"].ejecutar.assert_called_once_with(
        EditarJugadorDTO(idJugador=1, nombre="José", apellido="Argento", anioNacimiento=1981)
    )
    page.pop_dialog.assert_called_once()


def test_editar_jugador_con_error_muestra_aviso_en_el_dialogo_sin_cerrar(page, armar, mocks):
    mocks["editar"].ejecutar.side_effect = DatoInvalidoError("El nombre del jugador no puede estar vacio")
    vista = armar()

    botones_icono(vista, "Editar")[0].on_click()
    dialogo = page.show_dialog.call_args.args[0]
    campo(dialogo, "Nombre").value = ""
    boton(dialogo, "Guardar").on_click()

    page.pop_dialog.assert_not_called()
    assert any(
        isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and "vacio" in (c.value or "") for c in controles(dialogo)
    )


def test_eliminar_jugador_pide_confirmacion_y_elimina_o_muestra_error_en_uso(page, armar, mocks):
    vista = armar()

    botones_icono(vista, "Eliminar")[0].on_click()
    page.show_dialog.assert_called_once()
    mocks["eliminar"].ejecutar.assert_not_called()

    _confirmar_ultimo_dialogo(page)
    mocks["eliminar"].ejecutar.assert_called_once_with(1)

    mocks["eliminar"].ejecutar.side_effect = JugadorEnUsoError("El jugador tiene partidos cargados")
    botones_icono(vista, "Eliminar")[0].on_click()
    _confirmar_ultimo_dialogo(page)
    assert "El jugador tiene partidos cargados" in _errores_visibles(vista)


def test_eliminar_jugador_sin_club_desde_todos_los_clubes(page, armar, mocks):
    mocks["listar"].ejecutar.return_value = []
    vista = armar()
    _ver_todos(vista)

    botones_icono(por_clave(vista, TABLA_JUGADORES), "Eliminar")[0].on_click()
    _confirmar_ultimo_dialogo(page)

    mocks["eliminar"].ejecutar.assert_called_once_with(10)
