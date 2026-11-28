"""Tests de la pantalla principal (US-105, AC3; club activo de la US-106; tablero de la US-113) sin ventana."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, por_clave, textos

from aplicacion.casos_uso.listar_lideres_club import ListarLideresClubUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.partido_dto import LiderClubDTO, PartidoResumenDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.screens.inicio_screen import (
    SIN_LIDERES,
    SIN_PARTIDOS,
    TABLA_LIDERES,
    TARJETA_ULTIMO_PARTIDO,
    crear_inicio_view,
    fila_lider,
)

PARTIDO_VIEJO = PartidoResumenDTO(1, "2026-05-01", None, "Liga", 2026, "Atenas", "Pesca", "U21", 60, 50)
PARTIDO_NUEVO = PartidoResumenDTO(2, "2026-06-01", None, "Liga", 2026, "Instituto", "Atenas", "U21", 70, 72)
LIDER = LiderClubDTO(
    nombreJugador="Pepe Argento",
    partidosJugados=2,
    puntosPromedio=15.5,
    rebotesPromedio=7.0,
    asistenciasPromedio=3.25,
)


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


@pytest.fixture
def listar_partidos():
    return MagicMock(spec=ListarPartidosPorClubUseCase, **{"ejecutar.return_value": [PARTIDO_VIEJO, PARTIDO_NUEVO]})


@pytest.fixture
def listar_lideres():
    return MagicMock(spec=ListarLideresClubUseCase, **{"ejecutar.return_value": [LIDER]})


@pytest.fixture
def armar(page, sesion, listar_partidos, listar_lideres):
    return lambda: crear_inicio_view(page, sesion, listar_partidos, listar_lideres)


def test_saluda_al_usuario_de_la_sesion(armar):
    assert "Hola, Profesor" in textos(armar())


def test_usa_la_barra_superior_compartida(armar):
    """El detalle de la barra (club activo, cerrar sesion) se prueba en test_barra_superior.py."""
    vista = armar()

    assert vista.appbar.title.value == "StatsPro · Sin club elegido"
    boton(vista, "Cerrar sesión")  # esta en las acciones de la barra


def test_sin_club_activo_invita_a_elegir_uno_y_no_consulta_partidos(armar, page, listar_partidos):
    vista = armar()

    assert "Elegí un club para empezar." in textos(vista)
    boton(vista, "Elegir club").on_click()
    page.navigate.assert_called_once_with("/clubes")
    listar_partidos.ejecutar.assert_not_called()


def test_con_club_activo_muestra_el_ultimo_partido_y_los_lideres(armar, sesion, listar_lideres):
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))

    vista = armar()

    assert "Elegí un club para empezar." not in textos(vista)
    assert vista.appbar.title.value == "StatsPro · Atenas"
    tarjeta = textos(por_clave(vista, TARJETA_ULTIMO_PARTIDO))
    assert "Instituto 70 - 72 Atenas" in tarjeta  # el mas reciente es el ultimo de la lista
    assert any("vs Instituto, de visitante" in t for t in tarjeta)
    listar_lideres.ejecutar.assert_called_once_with(7)
    assert "Pepe Argento" in textos(por_clave(vista, TABLA_LIDERES))


def test_sin_partidos_muestra_estados_vacios(armar, sesion, listar_partidos, listar_lideres):
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))
    listar_partidos.ejecutar.return_value = []
    listar_lideres.ejecutar.return_value = []

    vista = armar()

    assert SIN_PARTIDOS in textos(por_clave(vista, TARJETA_ULTIMO_PARTIDO))
    assert SIN_LIDERES in textos(por_clave(vista, TABLA_LIDERES))


@pytest.mark.parametrize(
    ("texto", "ruta"),
    [("Cargar partido", "/partidos/cargar"), ("Ver partidos", "/partidos"), ("Jugadores", "/jugadores")],
)
def test_accesos_rapidos_navegan(armar, sesion, page, texto, ruta):
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))

    boton(armar(), texto).on_click()

    page.navigate.assert_called_once_with(ruta)


def test_fila_lider_redondea_promedios_a_un_decimal():
    assert fila_lider(LIDER) == ("Pepe Argento", "2", "15.5", "7.0", "3.2")


def test_sin_sesion_no_se_puede_construir(page, listar_partidos, listar_lideres):
    # La ruta protegida nunca deberia llegar aca sin sesion: si llega, es un bug y falla fuerte.
    with pytest.raises(RuntimeError):
        crear_inicio_view(page, SessionManager(MagicMock(spec=SesionAlmacen)), listar_partidos, listar_lideres)
