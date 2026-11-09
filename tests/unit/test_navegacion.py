"""Tests de la navegacion de la GUI (US-105): la ruta protegida (`resolver_ruta`, pura) y el router de `_main`."""

from unittest.mock import MagicMock

import flet as ft
import pytest

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.app import RUTAS_INTERNAS, RUTAS_PUBLICAS, Dependencias, _main, resolver_ruta


@pytest.mark.parametrize("ruta", ["/login", "/registro"])
def test_sin_sesion_las_rutas_publicas_se_respetan(ruta):
    assert resolver_ruta(ruta, autenticado=False) == ruta


@pytest.mark.parametrize("ruta", ["/", "/inicio", "/clubes", "/no-existe"])
def test_sin_sesion_cualquier_otra_ruta_va_al_login(ruta):
    assert resolver_ruta(ruta, autenticado=False) == "/login"


@pytest.mark.parametrize("ruta", ["/inicio", "/clubes"])
def test_con_sesion_las_rutas_internas_se_respetan(ruta):
    assert resolver_ruta(ruta, autenticado=True) == ruta


@pytest.mark.parametrize("ruta", ["/", "/login", "/registro", "/no-existe"])
def test_con_sesion_cualquier_otra_ruta_va_al_inicio(ruta):
    assert resolver_ruta(ruta, autenticado=True) == "/inicio"


@pytest.mark.parametrize("autenticado", [False, True])
@pytest.mark.parametrize("ruta", ["/", "/login", "/registro", "/inicio", "/clubes", "/no-existe"])
def test_el_destino_es_estable_y_no_hay_redirecciones_circulares(ruta, autenticado):
    destino = resolver_ruta(ruta, autenticado)

    assert resolver_ruta(destino, autenticado) == destino


def test_ninguna_ruta_es_publica_e_interna_a_la_vez():
    assert RUTAS_PUBLICAS.isdisjoint(RUTAS_INTERNAS)


# ----------------------------------------------------------------------------- router (_main) con una page falsa
# Flet no esta: se simula a mano lo que haria. `page.navigate` solo se registra; para "llegar" a la ruta
# el test cambia `page.route` y llama a `page.on_route_change()`, como haria Flet.


@pytest.fixture
def deps():
    return Dependencias(
        sesion=SessionManager(MagicMock(spec=SesionAlmacen)),
        registrar_uc=MagicMock(spec=RegistrarEntrenadorUseCase),
        login_uc=MagicMock(spec=LoginLocalUseCase),
        crear_club_uc=MagicMock(spec=CrearClubUseCase),
        listar_clubes_uc=MagicMock(spec=ListarClubesUsuarioUseCase, **{"ejecutar.return_value": []}),
        cambiar_club_uc=MagicMock(spec=CambiarClubActivoUseCase),
    )


@pytest.fixture
def page():
    page = MagicMock(spec=ft.Page)
    page.route = "/"
    page.views = []
    return page


def test_al_arrancar_en_la_raiz_redirige_al_login(page, deps):
    _main(page, deps)

    page.navigate.assert_called_once_with("/login")
    assert page.views == []  # todavia no dibujo nada: espera a que Flet confirme la ruta nueva


def test_al_llegar_a_una_ruta_permitida_dibuja_su_pantalla(page, deps):
    _main(page, deps)
    page.route = "/login"

    page.on_route_change()

    assert [v.route for v in page.views] == ["/login"]
    page.update.assert_called()


def test_sin_sesion_inicio_redirige_al_login_sin_dibujar(page, deps):
    _main(page, deps)
    page.navigate.reset_mock()
    page.route = "/inicio"

    page.on_route_change()

    page.navigate.assert_called_once_with("/login")
    assert page.views == []


def test_con_sesion_inicio_dibuja_la_pantalla_principal(page, deps):
    deps.sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    _main(page, deps)
    page.route = "/inicio"

    page.on_route_change()

    assert [v.route for v in page.views] == ["/inicio"]


def test_cada_navegacion_reemplaza_la_pantalla_anterior(page, deps):
    _main(page, deps)
    page.route = "/login"
    page.on_route_change()
    page.route = "/registro"

    page.on_route_change()

    assert [v.route for v in page.views] == ["/registro"]


def test_con_sesion_clubes_dibuja_la_pantalla_de_clubes(page, deps):
    deps.sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    _main(page, deps)
    page.route = "/clubes"

    page.on_route_change()

    assert [v.route for v in page.views] == ["/clubes"]
