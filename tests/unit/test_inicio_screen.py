"""Tests de la pantalla principal (US-105, AC3; club activo de la US-106) sin ventana."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, textos

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.screens.inicio_screen import crear_inicio_view


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


def test_saluda_al_usuario_de_la_sesion(page, sesion):
    vista = crear_inicio_view(page, sesion)

    assert "Hola, Profesor" in textos(vista)


def test_usa_la_barra_superior_compartida(page, sesion):
    """El detalle de la barra (club activo, cerrar sesion) se prueba en test_barra_superior.py."""
    vista = crear_inicio_view(page, sesion)

    assert vista.appbar.title.value == "StatsPro · Sin club elegido"
    boton(vista, "Cerrar sesión")  # esta en las acciones de la barra


def test_sin_club_activo_invita_a_elegir_uno(page, sesion):
    vista = crear_inicio_view(page, sesion)

    assert "Elegí un club para empezar." in textos(vista)
    boton(vista, "Elegir club").on_click()
    page.navigate.assert_called_once_with("/clubes")


def test_con_club_activo_no_invita_a_elegir(page, sesion):
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))

    vista = crear_inicio_view(page, sesion)

    assert "Elegí un club para empezar." not in textos(vista)
    assert vista.appbar.title.value == "StatsPro · Atenas"


def test_sin_sesion_no_se_puede_construir(page):
    # La ruta protegida nunca deberia llegar aca sin sesion: si llega, es un bug y falla fuerte.
    with pytest.raises(RuntimeError):
        crear_inicio_view(page, SessionManager(MagicMock(spec=SesionAlmacen)))
