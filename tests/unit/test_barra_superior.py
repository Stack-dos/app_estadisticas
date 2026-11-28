"""Tests de la barra superior compartida (US-106) sin ventana. La navegacion esta en test_componentes_base.py."""

from unittest.mock import MagicMock

import flet as ft
import pytest

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.barra_superior import crear_barra_superior


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


def accion(barra: ft.AppBar, texto: str) -> ft.TextButton:
    return next(c for c in barra.actions or [] if isinstance(c, ft.TextButton) and c.content == texto)


def test_sin_club_activo_lo_indica_en_el_titulo(page, sesion):
    barra = crear_barra_superior(page, sesion)

    assert barra.title.value == "StatsPro · Sin club elegido"


def test_muestra_el_club_activo_en_el_titulo(page, sesion):
    sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))

    barra = crear_barra_superior(page, sesion)

    assert barra.title.value == "StatsPro · Atenas"


def test_la_navegacion_ya_no_esta_en_la_barra(page, sesion):
    """Desde la US-111, Inicio y Clubes estan en el menu lateral: en la barra solo queda cerrar sesion."""
    barra = crear_barra_superior(page, sesion)

    assert [c.content for c in barra.actions or []] == ["Cerrar sesión"]


def test_cerrar_sesion_cierra_la_sesion_y_vuelve_al_login(page, sesion):
    accion(crear_barra_superior(page, sesion), "Cerrar sesión").on_click()

    assert sesion.is_authenticated() is False
    page.navigate.assert_called_once_with("/login")


def test_cerrar_sesion_cierra_antes_de_navegar(page, sesion):
    """Al reves, el router recibiria "/login" con la sesion abierta y devolveria a "/inicio"."""
    autenticado_al_navegar = []
    page.navigate.side_effect = lambda _ruta: autenticado_al_navegar.append(sesion.is_authenticated())

    accion(crear_barra_superior(page, sesion), "Cerrar sesión").on_click()

    assert autenticado_al_navegar == [False]
