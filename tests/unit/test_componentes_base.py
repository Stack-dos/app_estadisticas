"""Tests de la base visual (US-111) sin ventana: tema, pagina, formulario y menu lateral."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import controles

from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.menu_lateral import CLAVE_BOTON_GUIA, DESTINOS, crear_menu_lateral
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_acceso, crear_vista_interna
from infraestructura.ui.flet.errores import crear_etiqueta_error
from infraestructura.ui.flet.estilo import (
    ANCHO_FORMULARIO,
    COLOR_SEMILLA,
    FUENTE,
    LOGO,
    LOGO_BLANCO,
    aplicar_tema,
)
from infraestructura.ui.flet.screens.guia_screen import GUIA_NO_ENCONTRADA, leer_guia


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


def textos(raiz: ft.BaseControl) -> list[str]:
    return [c.value for c in controles(raiz) if isinstance(c, ft.Text) and isinstance(c.value, str)]


# ----------------------------------------------------------------------------- tema


def test_aplicar_tema_usa_la_misma_semilla_y_letra_en_claro_y_en_oscuro():
    page = MagicMock()

    aplicar_tema(page)

    for tema in (page.theme, page.dark_theme):
        assert tema.color_scheme_seed == COLOR_SEMILLA
        assert tema.font_family == FUENTE
    assert FUENTE in page.fonts
    assert page.window.min_width <= page.window.width


# ----------------------------------------------------------------------------- pagina


def test_crear_pagina_incluye_titulo_subtitulo_y_contenido():
    pagina = crear_pagina("Mis clubes", [ft.Text("contenido")], subtitulo="Atenas")

    assert textos(pagina)[:3] == ["Mis clubes", "Atenas", "contenido"]


def test_crear_pagina_usa_todo_el_ancho():
    assert crear_pagina("Titulo", []).max_width is None  # US-113: usa todo el ancho


def test_crear_pagina_pone_el_panel_lateral_a_la_derecha_del_contenido():
    pagina = crear_pagina("Titulo", [ft.Text("listado")], lateral=ft.Text("alta"))

    assert textos(pagina).index("listado") < textos(pagina).index("alta")


def test_la_vista_interna_tiene_barra_menu_y_contenido(page, sesion):
    vista = crear_vista_interna(page, sesion, "/clubes", crear_pagina("Mis clubes", []))

    assert vista.route == "/clubes"
    assert isinstance(vista.appbar, ft.AppBar)
    [menu] = [c for c in controles(vista) if isinstance(c, ft.NavigationRail)]
    assert DESTINOS[menu.selected_index].ruta == "/clubes"
    assert "Mis clubes" in textos(vista)


def test_la_vista_de_acceso_muestra_la_marca_y_el_formulario():
    formulario = crear_formulario([ft.TextField(label="Email")], crear_etiqueta_error(), "Ingresar", lambda: None)

    vista = crear_vista_acceso("/login", "Iniciar sesión", "Entrá a tu club.", formulario)

    assert vista.route == "/login"
    assert {"StatsPro", "Iniciar sesión", "Entrá a tu club."} <= set(textos(vista))
    assert any(isinstance(c, ft.Image) and c.src == LOGO_BLANCO for c in controles(vista))


# ----------------------------------------------------------------------------- formulario


def test_crear_formulario_ubica_error_debajo_de_los_campos_y_despues_el_boton_principal():
    email, password = ft.TextField(label="Email"), ft.TextField(label="Contraseña")
    error = crear_etiqueta_error()
    secundario = ft.TextButton("Crear cuenta")

    formulario = crear_formulario([email, password], error, "Ingresar", lambda: None, secundarios=[secundario])

    email_, password_, error_, principal, secundario_ = formulario.controls
    assert (email_, password_, error_, secundario_) == (email, password, error, secundario)
    assert isinstance(principal, ft.FilledButton)
    assert principal.content == "Ingresar"
    assert formulario.width == ANCHO_FORMULARIO


def test_el_boton_principal_y_el_enter_del_ultimo_campo_llaman_a_la_misma_accion():
    al_enviar = MagicMock()
    email, password = ft.TextField(label="Email"), ft.TextField(label="Contraseña")

    formulario = crear_formulario([email, password, ft.Checkbox(label="Recordarme")], ft.Text(), "Ingresar", al_enviar)
    password.on_submit()
    next(c for c in formulario.controls if isinstance(c, ft.FilledButton)).on_click()

    assert al_enviar.call_count == 2
    assert email.on_submit is None  # Enter en un campo que no es el ultimo no envia a medio completar


def test_crear_formulario_sin_ancho_ocupa_el_de_su_contenedor():
    assert crear_formulario([], ft.Text(), "Crear", lambda: None, ancho=None).width is None


# ----------------------------------------------------------------------------- menu lateral


def test_el_menu_lleva_el_logo_y_marca_la_pantalla_actual(page):
    menu = crear_menu_lateral(page, "/inicio")

    assert isinstance(menu.leading, ft.Image)
    assert menu.leading.src == LOGO
    assert menu.selected_index == 0


def test_una_ruta_que_no_esta_en_el_menu_no_marca_ninguna(page):
    assert crear_menu_lateral(page, "/otra").selected_index is None


@pytest.mark.parametrize("destino", DESTINOS)
def test_elegir_un_destino_navega_a_su_ruta(page, destino):
    menu = crear_menu_lateral(page, "/inicio")
    menu.selected_index = DESTINOS.index(destino)  # lo que hace Flet al hacer clic, antes de llamar a on_change

    menu.on_change()

    page.navigate.assert_called_once_with(destino.ruta)


@pytest.mark.parametrize("ruta", ["/competencias", "/inscripciones", "/listas"])
def test_las_subrutas_de_torneos_marcan_el_destino_torneos(page, ruta):
    menu = crear_menu_lateral(page, ruta)

    assert menu.selected_index is not None
    assert DESTINOS[menu.selected_index].texto == "Torneos"


# ----------------------------------------------------------------------------- guia y rutas con id (US-114)


@pytest.mark.parametrize("ruta", ["/partidos/cargar", "/partidos/editar/5"])
def test_cargar_y_editar_un_partido_marcan_el_destino_partidos(page, ruta):
    menu = crear_menu_lateral(page, ruta)

    assert DESTINOS[menu.selected_index].texto == "Partidos"


def test_la_vista_interna_tiene_el_boton_guia_abajo_del_menu(page, sesion):
    vista = crear_vista_interna(page, sesion, "/clubes", crear_pagina("Clubes", []))

    [boton_guia] = [c for c in controles(vista) if c.key == CLAVE_BOTON_GUIA]
    boton_guia.on_click()
    page.navigate.assert_called_once_with("/guia")


def test_leer_guia_sin_archivo_avisa_en_vez_de_romper(tmp_path):
    assert leer_guia(str(tmp_path / "no_existe.md")) == GUIA_NO_ENCONTRADA
    (tmp_path / "guia.md").write_text("# Hola", encoding="utf-8")
    assert leer_guia(str(tmp_path / "guia.md")) == "# Hola"
