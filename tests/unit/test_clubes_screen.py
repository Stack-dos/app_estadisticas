"""Tests de la pantalla de clubes (US-106, AC2 y AC3) sin ventana, con `page` y casos de uso mockeados."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, botones_icono, campo, etiqueta_error, por_clave, textos

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.eliminar_club import EliminarClubUseCase
from aplicacion.casos_uso.listar_clubes_rivales import ListarClubesRivalesUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.renombrar_club import RenombrarClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO, RenombrarClubDTO
from aplicacion.dtos.competencia_dto import InscripcionDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import ClubEnUsoError, ClubNoEncontradoError, ClubYaExisteError, DatoInvalidoError
from infraestructura.ui.flet.errores import MENSAJE_ERROR_INESPERADO
from infraestructura.ui.flet.screens.clubes_screen import (
    EN_USO,
    LISTA_CLUBES,
    LISTA_RIVALES,
    SIN_CLUBES,
    SIN_RIVALES,
    crear_clubes_view,
    iniciales,
    resumen_club,
)

ATENAS = ClubDTO(idClub=7, nombre="Atenas")
INSTITUTO = ClubDTO(idClub=8, nombre="Instituto")


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    sesion = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    return sesion


@pytest.fixture
def crear_club_uc():
    uc = MagicMock(spec=CrearClubUseCase)
    uc.ejecutar.return_value = INSTITUTO
    return uc


@pytest.fixture
def listar_clubes_uc():
    uc = MagicMock(spec=ListarClubesUsuarioUseCase)
    uc.ejecutar.return_value = [ATENAS]
    return uc


@pytest.fixture
def cambiar_club_uc():
    uc = MagicMock(spec=CambiarClubActivoUseCase)
    uc.ejecutar.side_effect = lambda _id_usuario, id_club: {7: ATENAS, 8: INSTITUTO}[id_club]
    return uc


@pytest.fixture
def rivales():
    """Casos de uso de "Clubes rivales" (US-114) y los que cuentan categorias y jugadores de cada club."""
    inscripciones = [
        InscripcionDTO(idInscripcion=1, idClub=7, idCategoria=1, idCompetencia=10, idListaBuenaFe=1),
        InscripcionDTO(idInscripcion=2, idClub=7, idCategoria=1, idCompetencia=11, idListaBuenaFe=2),
        InscripcionDTO(idInscripcion=3, idClub=7, idCategoria=2, idCompetencia=11, idListaBuenaFe=3),
    ]
    return (
        MagicMock(spec=ListarClubesRivalesUseCase, **{"ejecutar.return_value": []}),
        MagicMock(spec=RenombrarClubUseCase),
        MagicMock(spec=EliminarClubUseCase),
        MagicMock(spec=ListarInscripcionesClubUseCase, **{"ejecutar.return_value": inscripciones}),
        MagicMock(spec=ListarJugadoresClubUseCase, **{"ejecutar.return_value": [object()] * 41}),
    )


@pytest.fixture
def armar(page, crear_club_uc, listar_clubes_uc, cambiar_club_uc, rivales, sesion):
    return lambda: crear_clubes_view(page, crear_club_uc, listar_clubes_uc, cambiar_club_uc, *rivales, sesion)


def renglones(vista: ft.View) -> list[ft.Control]:
    lista = por_clave(vista, LISTA_CLUBES)
    assert isinstance(lista, ft.Column)
    return list(lista.controls)


def renglon(vista: ft.View, nombre: str) -> ft.ListTile:
    return next(r for r in renglones(vista) if isinstance(r, ft.ListTile) and r.title.value == nombre)


# ----------------------------------------------------------------------------- listado


def test_lista_los_clubes_del_usuario_de_la_sesion(armar, listar_clubes_uc):
    vista = armar()

    listar_clubes_uc.ejecutar.assert_called_once_with(1)
    assert renglon(vista, "Atenas").trailing.content == "Usar este club"


def test_sin_clubes_muestra_un_mensaje(armar, listar_clubes_uc):
    listar_clubes_uc.ejecutar.return_value = []

    vista = armar()

    [unico] = renglones(vista)
    assert unico.value == SIN_CLUBES


def test_el_club_activo_se_marca_en_uso_y_los_demas_tienen_boton(armar, listar_clubes_uc, sesion):
    listar_clubes_uc.ejecutar.return_value = [ATENAS, INSTITUTO]
    sesion.set_active_club(ATENAS)

    vista = armar()

    assert renglon(vista, "Atenas").trailing.content.value == EN_USO
    assert renglon(vista, "Instituto").trailing.content == "Usar este club"


def test_cada_club_tiene_iniciales_y_resumen_de_categorias_y_jugadores(armar, listar_clubes_uc):
    listar_clubes_uc.ejecutar.return_value = [ATENAS]

    fila = renglon(armar(), "Atenas")

    assert fila.leading.content.value == "AT"
    assert fila.subtitle.value == "2 categorías · 41 jugadores"  # U17 en dos torneos cuenta una vez


def test_iniciales_y_resumen_club():
    assert iniciales("Hindú Club") == "HC"
    assert iniciales("atenas") == "AT"
    assert resumen_club(1, 1) == "1 categoría · 1 jugador"
    assert resumen_club(0, 12) == "0 categorías · 12 jugadores"


# ----------------------------------------------------------------------------- crear


def test_crear_club_usa_el_usuario_de_la_sesion_y_refresca_la_lista(armar, crear_club_uc, listar_clubes_uc, page):
    vista = armar()
    campo(vista, "Nombre del club").value = "Instituto"
    listar_clubes_uc.ejecutar.return_value = [ATENAS, INSTITUTO]  # lo que devuelve la base despues de crear

    boton(vista, "Crear club").on_click()

    crear_club_uc.ejecutar.assert_called_once_with(CrearClubDTO(nombre="Instituto"), 1)
    assert [r.title.value for r in renglones(vista)] == ["Atenas", "Instituto"]
    assert campo(vista, "Nombre del club").value == ""
    assert etiqueta_error(vista).value == ""
    page.update.assert_called()
    page.navigate.assert_not_called()  # se queda en la pantalla


def test_enter_en_el_nombre_crea_igual_que_el_boton(armar, crear_club_uc):
    vista = armar()
    campo(vista, "Nombre del club").value = "Instituto"

    campo(vista, "Nombre del club").on_submit()

    crear_club_uc.ejecutar.assert_called_once()


@pytest.mark.parametrize(
    "excepcion",
    [
        ClubYaExisteError("Ya existe un club llamado 'Atenas'"),
        DatoInvalidoError("El nombre del club no puede estar vacio"),
    ],
)
def test_error_de_negocio_al_crear_muestra_el_mensaje_y_conserva_lo_escrito(armar, crear_club_uc, excepcion):
    crear_club_uc.ejecutar.side_effect = excepcion
    vista = armar()
    campo(vista, "Nombre del club").value = "Atenas"

    boton(vista, "Crear club").on_click()

    assert etiqueta_error(vista).value == str(excepcion)
    assert campo(vista, "Nombre del club").value == "Atenas"


def test_si_la_base_no_guarda_el_club_muestra_el_mensaje_generico(armar, crear_club_uc):
    crear_club_uc.ejecutar.return_value = None
    vista = armar()
    campo(vista, "Nombre del club").value = "Instituto"

    boton(vista, "Crear club").on_click()

    assert etiqueta_error(vista).value == MENSAJE_ERROR_INESPERADO


# ----------------------------------------------------------------------------- usar este club


def test_usar_este_club_lo_deja_activo_y_va_al_inicio(armar, cambiar_club_uc, sesion, page):
    vista = armar()

    renglon(vista, "Atenas").trailing.on_click()

    cambiar_club_uc.ejecutar.assert_called_once_with(1, 7)
    assert sesion.club_activo() == ATENAS
    page.navigate.assert_called_once_with("/inicio")


def test_cada_boton_usa_su_propio_club(armar, listar_clubes_uc, sesion):
    """Regresion del error clasico de las lambdas en un bucle: todas terminarian usando el ultimo club."""
    listar_clubes_uc.ejecutar.return_value = [ATENAS, INSTITUTO]
    vista = armar()

    renglon(vista, "Atenas").trailing.on_click()

    assert sesion.club_activo() == ATENAS


def test_club_sin_acceso_muestra_el_error_y_no_navega(armar, cambiar_club_uc, sesion, page):
    cambiar_club_uc.ejecutar.side_effect = ClubNoEncontradoError("El usuario no tiene acceso al club")
    vista = armar()

    renglon(vista, "Atenas").trailing.on_click()

    assert etiqueta_error(vista).value == "El usuario no tiene acceso al club"
    assert sesion.club_activo() is None
    page.navigate.assert_not_called()


def test_sin_sesion_no_se_puede_construir(page, crear_club_uc, listar_clubes_uc, cambiar_club_uc, rivales):
    with pytest.raises(RuntimeError):
        crear_clubes_view(
            page,
            crear_club_uc,
            listar_clubes_uc,
            cambiar_club_uc,
            *rivales,
            SessionManager(MagicMock(spec=SesionAlmacen)),
        )


def test_muestra_el_aviso_cuando_se_pasa_por_guard_de_club_activo(
    page, crear_club_uc, listar_clubes_uc, cambiar_club_uc, rivales, sesion
):
    vista = crear_clubes_view(
        page, crear_club_uc, listar_clubes_uc, cambiar_club_uc, *rivales, sesion, aviso="Elegí un club para seguir."
    )

    assert "Elegí un club para seguir." in textos(vista)


# ----------------------------------------------------------------------------- clubes rivales (US-114)

PEZCA = ClubDTO(idClub=20, nombre="Pezca")


def _dialogo(page: MagicMock) -> ft.AlertDialog:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    return dialogo


def test_sin_rivales_explica_de_donde_salen(armar):
    assert SIN_RIVALES in textos(por_clave(armar(), LISTA_RIVALES))


def test_renombrar_un_rival_abre_el_dialogo_y_rehace_la_lista(armar, rivales, page):
    listar, renombrar, _eliminar, *_ = rivales
    listar.ejecutar.side_effect = [[PEZCA], [ClubDTO(idClub=20, nombre="Pesca")]]
    renombrar.ejecutar.return_value = ClubDTO(idClub=20, nombre="Pesca")
    vista = armar()

    botones_icono(por_clave(vista, LISTA_RIVALES), "Renombrar")[0].on_click()
    dialogo = _dialogo(page)
    campo_nombre = dialogo.content.controls[0]
    assert campo_nombre.value == "Pezca"
    campo_nombre.value = "Pesca"
    dialogo.actions[1].on_click()

    renombrar.ejecutar.assert_called_once_with(RenombrarClubDTO(idClub=20, nombre="Pesca"))
    page.pop_dialog.assert_called_once()
    assert "Pesca" in textos(por_clave(vista, LISTA_RIVALES))


def test_renombrar_a_un_nombre_que_ya_existe_muestra_el_error_en_el_dialogo(armar, rivales, page):
    listar, renombrar, _eliminar, *_ = rivales
    listar.ejecutar.return_value = [PEZCA]
    renombrar.ejecutar.side_effect = ClubYaExisteError("Ya existe un club llamado 'Atenas'.")
    vista = armar()

    botones_icono(por_clave(vista, LISTA_RIVALES), "Renombrar")[0].on_click()
    dialogo = _dialogo(page)
    dialogo.actions[1].on_click()

    assert dialogo.content.controls[1].value == "Ya existe un club llamado 'Atenas'."
    page.pop_dialog.assert_not_called()


def test_eliminar_un_rival_con_partidos_pide_confirmar_y_muestra_por_que_no(armar, rivales, page):
    listar, _renombrar, eliminar, *_ = rivales
    listar.ejecutar.return_value = [PEZCA]
    eliminar.ejecutar.side_effect = ClubEnUsoError(
        "El club tiene partidos cargados. Si el nombre está mal, renombralo."
    )
    vista = armar()

    botones_icono(por_clave(vista, LISTA_RIVALES), "Eliminar")[0].on_click()
    _dialogo(page).actions[1].on_click()

    eliminar.ejecutar.assert_called_once_with(20)
    assert "renombralo" in etiqueta_error(vista).value
