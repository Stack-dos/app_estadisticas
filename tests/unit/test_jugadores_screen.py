"""Tests unitarios de `JugadoresScreen` (US-112) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, controles, por_clave, textos

from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO, DesvincularJugadorDTO, VincularJugadorClubDTO, VinculoDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, EditarJugadorDTO, JugadorDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError, JugadorEnUsoError, VinculoActivoExistenteError
from infraestructura.ui.flet.screens.jugadores_screen import (
    COINCIDENCIAS_ALTA,
    RESULTADOS_BUSQUEDA,
    SIN_COINCIDENCIAS,
    SIN_JUGADORES,
    TABLA_JUGADORES,
    crear_jugadores_view,
    fila_jugador,
)

PEPE = JugadorDTO(id=1, nombre_completo="Pepe Argento", anioNacimiento=1980, nombre="Pepe", apellido="Argento")
MANU = JugadorDTO(id=7, nombre_completo="Manu Ginobili", anioNacimiento=1977, nombre="Manu", apellido="Ginobili")
FACU = JugadorDTO(id=10, nombre_completo="Facundo Campazzo", anioNacimiento=None, nombre="Facundo", apellido="Campazzo")


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
    return {
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
        sesion,
    )


def _errores_visibles(vista: ft.View) -> list[str]:
    return [c.value for c in controles(vista) if isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and c.value]


def _confirmar_ultimo_dialogo(page: MagicMock) -> None:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()


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


def test_alta_sin_coincidencias_registra_y_vincula_al_club_activo(armar, mocks):
    vista = armar()
    campo(vista, "Nombre").value = "Manu"
    campo(vista, "Apellido").value = "Ginobili"
    campo(vista, "Año de nacimiento (opcional)").value = "1977"
    campo(vista, "Fecha de ingreso").value = "2026-03-01"

    boton(vista, "Registrar jugador").on_click()

    mocks["buscar"].ejecutar.assert_called_once_with("Manu Ginobili")
    mocks["registrar"].ejecutar.assert_called_once_with(
        CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=1977)
    )
    mocks["vincular"].ejecutar.assert_called_once_with(
        VincularJugadorClubDTO(idJugador=7, idClub=7, fechaDesde="2026-03-01")
    )
    assert campo(vista, "Nombre").value == ""
    assert campo(vista, "Apellido").value == ""


def test_alta_con_coincidencias_avisa_y_permite_vincular_en_vez_de_duplicar(armar, mocks):
    mocks["buscar"].ejecutar.return_value = [MANU]
    vista = armar()
    campo(vista, "Nombre").value = "Manu"
    campo(vista, "Apellido").value = "Ginobili"
    campo(vista, "Fecha de ingreso").value = "2026-03-01"

    boton(vista, "Registrar jugador").on_click()

    # No crea un duplicado todavia: muestra las coincidencias y ofrece vincular
    mocks["registrar"].ejecutar.assert_not_called()
    panel = por_clave(vista, COINCIDENCIAS_ALTA)
    assert any("Manu Ginobili" in t for t in textos(panel))

    boton(panel, "Vincular al club").on_click()

    mocks["registrar"].ejecutar.assert_not_called()
    mocks["vincular"].ejecutar.assert_called_once_with(
        VincularJugadorClubDTO(idJugador=7, idClub=7, fechaDesde="2026-03-01")
    )


def test_alta_con_coincidencias_permite_confirmar_si_es_otra_persona(armar, mocks):
    mocks["buscar"].ejecutar.return_value = [MANU]
    vista = armar()
    campo(vista, "Nombre").value = "Manu"
    campo(vista, "Apellido").value = "Ginobili"
    campo(vista, "Fecha de ingreso").value = "2026-03-01"

    boton(vista, "Registrar jugador").on_click()
    panel = por_clave(vista, COINCIDENCIAS_ALTA)
    boton(panel, "Crear nuevo jugador de todas formas").on_click()

    mocks["registrar"].ejecutar.assert_called_once_with(
        CrearJugadorDTO(nombre="Manu", apellido="Ginobili", anioNacimiento=None)
    )
    mocks["vincular"].ejecutar.assert_called_once()


def test_buscar_jugador_existente_y_vincular_o_mostrar_error_de_dominio(armar, mocks):
    mocks["buscar"].ejecutar.return_value = [PEPE, FACU]
    vista = armar()

    campo(vista, "Buscar jugador existente (nombre o apellido)").value = "a"
    boton(vista, "Buscar").on_click()

    resultados = por_clave(vista, RESULTADOS_BUSQUEDA)
    assert "Ya está en el club" in textos(resultados)
    assert any("Facundo Campazzo" in t for t in textos(resultados))

    # Al intentar vincular a Facundo, si ya tiene otro club activo, se muestra el error de dominio
    mocks["vincular"].ejecutar.side_effect = VinculoActivoExistenteError("El jugador ya tiene un club activo")
    boton(resultados, "Vincular al club").on_click()
    assert "El jugador ya tiene un club activo" in _errores_visibles(vista)


def test_buscar_sin_resultados_muestra_mensaje(armar, mocks):
    mocks["buscar"].ejecutar.return_value = []
    vista = armar()

    campo(vista, "Buscar jugador existente (nombre o apellido)").value = "Nadie"
    boton(vista, "Buscar").on_click()

    assert SIN_COINCIDENCIAS in textos(por_clave(vista, RESULTADOS_BUSQUEDA))


def test_dar_de_baja_jugador_pide_confirmacion_y_desvincula(page, armar, mocks):
    vista = armar()
    campo(vista, "Fecha de baja").value = "2026-06-30"

    boton(vista, "Dar de baja").on_click()
    page.show_dialog.assert_called_once()
    mocks["desvincular"].ejecutar.assert_not_called()

    _confirmar_ultimo_dialogo(page)
    mocks["desvincular"].ejecutar.assert_called_once_with(DesvincularJugadorDTO(idJugador=1, fechaHasta="2026-06-30"))


def test_editar_jugador_abre_dialogo_y_guarda_cambios(page, armar, mocks):
    vista = armar()

    boton(vista, "Editar").on_click()
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

    boton(vista, "Editar").on_click()
    dialogo = page.show_dialog.call_args.args[0]
    campo(dialogo, "Nombre").value = ""
    boton(dialogo, "Guardar").on_click()

    page.pop_dialog.assert_not_called()
    assert any(
        isinstance(c, ft.Text) and c.color == ft.Colors.ERROR and "vacio" in (c.value or "") for c in controles(dialogo)
    )


def test_eliminar_jugador_pide_confirmacion_y_elimina_o_muestra_error_en_uso(page, armar, mocks):
    vista = armar()

    boton(vista, "Eliminar").on_click()
    page.show_dialog.assert_called_once()
    mocks["eliminar"].ejecutar.assert_not_called()

    _confirmar_ultimo_dialogo(page)
    mocks["eliminar"].ejecutar.assert_called_once_with(1)

    mocks["eliminar"].ejecutar.side_effect = JugadorEnUsoError("El jugador tiene partidos cargados")
    boton(vista, "Eliminar").on_click()
    _confirmar_ultimo_dialogo(page)
    assert "El jugador tiene partidos cargados" in _errores_visibles(vista)


def test_eliminar_jugador_dado_de_baja_desde_resultados_de_busqueda(page, armar, mocks):
    mocks["listar"].ejecutar.return_value = []
    mocks["buscar"].ejecutar.return_value = [FACU]
    vista = armar()

    campo(vista, "Buscar jugador existente (nombre o apellido)").value = "Campazzo"
    boton(vista, "Buscar").on_click()
    resultados = por_clave(vista, RESULTADOS_BUSQUEDA)

    boton(resultados, "Eliminar").on_click()
    _confirmar_ultimo_dialogo(page)

    mocks["eliminar"].ejecutar.assert_called_once_with(10)
