"""Tests de la navegacion de la GUI (US-105 a US-107): ruta protegida, guard de club activo y router."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import textos

from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.casos_uso.vaciar_lista_buena_fe import VaciarListaBuenaFeUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.app import (
    AVISO_REQUIERE_CLUB,
    RUTAS_CON_CLUB,
    RUTAS_INTERNAS,
    RUTAS_PUBLICAS,
    Dependencias,
    _main,
    requiere_club_activo,
    resolver_ruta,
)


@pytest.mark.parametrize("ruta", ["/login", "/registro"])
def test_sin_sesion_las_rutas_publicas_se_respetan(ruta):
    assert resolver_ruta(ruta, autenticado=False) == ruta


@pytest.mark.parametrize(
    "ruta",
    ["/", "/inicio", "/clubes", "/competencias", "/inscripciones", "/listas", "/no-existe"],
)
def test_sin_sesion_cualquier_otra_ruta_va_al_login(ruta):
    assert resolver_ruta(ruta, autenticado=False) == "/login"


@pytest.mark.parametrize("ruta", ["/inicio", "/clubes", "/competencias", "/inscripciones", "/listas"])
def test_con_sesion_y_club_las_rutas_internas_se_respetan(ruta):
    assert resolver_ruta(ruta, autenticado=True, tiene_club=True) == ruta


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_CLUB))
def test_con_sesion_y_sin_club_las_rutas_operativas_van_a_clubes(ruta):
    assert requiere_club_activo(ruta, tiene_club=False) == "/clubes"
    assert resolver_ruta(ruta, autenticado=True, tiene_club=False) == "/clubes"


@pytest.mark.parametrize("ruta", ["/inicio", "/clubes"])
def test_con_sesion_y_sin_club_inicio_y_clubes_se_respetan(ruta):
    assert resolver_ruta(ruta, autenticado=True, tiene_club=False) == ruta


@pytest.mark.parametrize("ruta", ["/", "/login", "/registro", "/no-existe"])
def test_con_sesion_cualquier_otra_ruta_va_al_inicio(ruta):
    assert resolver_ruta(ruta, autenticado=True) == "/inicio"


@pytest.mark.parametrize("tiene_club", [False, True])
@pytest.mark.parametrize("autenticado", [False, True])
@pytest.mark.parametrize(
    "ruta",
    ["/", "/login", "/registro", "/inicio", "/clubes", "/competencias", "/inscripciones", "/listas", "/no-existe"],
)
def test_el_destino_es_estable_y_no_hay_redirecciones_circulares(ruta, autenticado, tiene_club):
    destino = resolver_ruta(ruta, autenticado, tiene_club=tiene_club)

    assert resolver_ruta(destino, autenticado, tiene_club=tiene_club) == destino


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
        crear_competencia_uc=MagicMock(spec=CrearCompetenciaUseCase),
        listar_competencias_uc=MagicMock(spec=ListarCompetenciasUseCase, **{"ejecutar.return_value": []}),
        crear_categoria_uc=MagicMock(spec=CrearCategoriaUseCase),
        listar_categorias_uc=MagicMock(spec=ListarCategoriasUseCase, **{"ejecutar.return_value": []}),
        habilitar_categoria_uc=MagicMock(spec=HabilitarCategoriaEnCompetenciaUseCase),
        listar_categorias_comp_uc=MagicMock(spec=ListarCategoriasDeCompetenciaUseCase, **{"ejecutar.return_value": []}),
        quitar_categoria_uc=MagicMock(spec=QuitarCategoriaDeCompetenciaUseCase),
        eliminar_competencia_uc=MagicMock(spec=EliminarCompetenciaUseCase),
        eliminar_categoria_uc=MagicMock(spec=EliminarCategoriaUseCase),
        inscribir_club_uc=MagicMock(spec=InscribirClubEnCompetenciaUseCase),
        listar_inscripciones_uc=MagicMock(spec=ListarInscripcionesClubUseCase, **{"ejecutar.return_value": []}),
        eliminar_inscripcion_uc=MagicMock(spec=EliminarInscripcionUseCase),
        agregar_jugador_lista_uc=MagicMock(spec=AgregarJugadorAListaBuenaFeUseCase),
        quitar_jugador_lista_uc=MagicMock(spec=QuitarJugadorDeListaBuenaFeUseCase),
        vaciar_lista_uc=MagicMock(spec=VaciarListaBuenaFeUseCase),
        listar_lista_uc=MagicMock(spec=ListarListaBuenaFeUseCase, **{"ejecutar.return_value": []}),
        listar_jugadores_club_uc=MagicMock(spec=ListarJugadoresClubUseCase, **{"ejecutar.return_value": []}),
    )


@pytest.fixture
def page():
    page = MagicMock(spec=ft.Page)
    page.route = "/"
    page.views = []
    page.window = MagicMock()  # aplicar_tema (US-111) fija el tamaño; spec=ft.Page no trae `window`
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


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_CLUB))
def test_sin_club_activo_redirige_a_clubes_con_aviso(page, deps, ruta):
    deps.sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    _main(page, deps)
    page.navigate.reset_mock()

    page.route = ruta
    page.on_route_change()
    page.navigate.assert_called_once_with("/clubes")

    page.route = "/clubes"
    page.on_route_change()
    assert AVISO_REQUIERE_CLUB in textos(page.views[0])

    # El aviso se muestra una sola vez: una navegacion normal posterior a /clubes no lo repite
    page.on_route_change()
    assert AVISO_REQUIERE_CLUB not in textos(page.views[0])


@pytest.mark.parametrize("ruta", sorted(RUTAS_CON_CLUB))
def test_con_club_activo_dibuja_las_pantallas_de_torneos(page, deps, ruta):
    deps.sesion.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))
    deps.sesion.set_active_club(ClubDTO(idClub=7, nombre="Atenas"))
    _main(page, deps)

    page.route = ruta
    page.on_route_change()

    assert [v.route for v in page.views] == [ruta]
