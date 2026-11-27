"""Tests unitarios de `CargaPartidoScreen` y `BloquePuntosPorCuarto` (US-108) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, desplegable, por_clave, textos

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.partido_dto import CuartoDTO, PartidoDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import CuartosInconsistentesError, DatoInvalidoError
from infraestructura.ui.flet.components.puntos_por_cuarto import BloquePuntosPorCuarto, etiqueta_periodo
from infraestructura.ui.flet.screens.carga_partido_screen import (
    CLAVE_AVISO_LISTA,
    CLAVE_ERROR,
    CLAVE_PASO_BOXSCORE,
    CLAVE_PASO_DATOS,
    CLAVE_PASO_RESUMEN,
    CLAVE_RESUMEN_TEXTO,
    crear_carga_partido_view,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga Provincial", anio=2026, tipo="PROVINCIAL")
U21 = CategoriaDTO(idCategoria=1, nombre="U21")
CLUB_ATENAS = ClubDTO(idClub=7, nombre="Atenas")
CLUB_INSTITUTO = ClubDTO(idClub=8, nombre="Instituto")
CLUB_HINDU = ClubDTO(idClub=9, nombre="Hindú")

INS_ATENAS = InscripcionDTO(idInscripcion=101, idClub=7, idCategoria=1, idCompetencia=10, idListaBuenaFe=1)
INS_INSTITUTO = InscripcionDTO(idInscripcion=102, idClub=8, idCategoria=1, idCompetencia=10, idListaBuenaFe=2)
INS_HINDU = InscripcionDTO(idInscripcion=103, idClub=9, idCategoria=1, idCompetencia=10, idListaBuenaFe=3)

JUG_ATENAS = [JugadorDTO(nombre_completo="Pepe Argento", id=1, anioNacimiento=2005)]
JUG_INSTITUTO = [JugadorDTO(nombre_completo="Juan Perez", id=2, anioNacimiento=2005)]
JUG_HINDU = [JugadorDTO(nombre_completo="Lucas Gomez", id=3, anioNacimiento=2005)]


@pytest.fixture
def page():
    return MagicMock(spec=ft.Page)


@pytest.fixture
def sesion():
    s = SessionManager(MagicMock(spec=SesionAlmacen))
    s.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="DT", email="dt@test.com"))
    s.set_active_club(CLUB_ATENAS)
    return s


@pytest.fixture
def mocks():
    cargar = MagicMock(spec=CargarPartidoUseCase)
    cargar.ejecutar.return_value = PartidoDTO(
        fecha="2026-08-10",
        estadio="Polideportivo",
        idCompetencia=10,
        idCategoria=1,
        idClubLocal=7,
        idClubVisitante=8,
        idPartido=55,
    )
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA]
    listar_cats_comp = MagicMock(spec=ListarCategoriasDeCompetenciaUseCase)
    listar_cats_comp.ejecutar.return_value = [U21]
    listar_clubes = MagicMock(spec=ListarClubesUseCase)
    listar_clubes.ejecutar.return_value = [CLUB_ATENAS, CLUB_INSTITUTO, CLUB_HINDU]

    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.side_effect = lambda id_club: {
        7: [INS_ATENAS],
        8: [INS_INSTITUTO],
        9: [INS_HINDU],
    }.get(id_club, [])

    listar_lista = MagicMock(spec=ListarListaBuenaFeUseCase)
    listar_lista.ejecutar.side_effect = lambda id_ins: {
        101: JUG_ATENAS,
        102: JUG_INSTITUTO,
        103: JUG_HINDU,
    }.get(id_ins, [])

    return {
        "cargar": cargar,
        "listar_comp": listar_comp,
        "listar_cats_comp": listar_cats_comp,
        "listar_clubes": listar_clubes,
        "listar_ins": listar_ins,
        "listar_lista": listar_lista,
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_carga_partido_view(
        page,
        mocks["cargar"],
        mocks["listar_comp"],
        mocks["listar_cats_comp"],
        mocks["listar_clubes"],
        mocks["listar_ins"],
        mocks["listar_lista"],
        sesion,
    )


# ------------------------------------------------------------------ BloquePuntosPorCuarto


def test_bloque_cuartos_vacio_devuelve_lista_vacia_y_permite_agregar_prorroga():
    assert etiqueta_periodo(1) == "Q1"
    assert etiqueta_periodo(4) == "Q4"
    assert etiqueta_periodo(5) == "PR1"

    bloque = BloquePuntosPorCuarto("Atenas", "Instituto")
    assert bloque.cantidad_periodos == 4
    assert bloque.leer_cuartos(7, 8) == []

    bloque.agregar_prorroga()
    assert bloque.cantidad_periodos == 5


def test_bloque_cuartos_lee_valores_validos_y_rechaza_no_numericos():
    bloque = BloquePuntosPorCuarto("Atenas", "Instituto")
    bloque._campos_local[0].value = "10"
    bloque._campos_visitante[0].value = "8"

    assert bloque.leer_cuartos(7, 8) == [
        CuartoDTO(idClub=7, nroCuarto=1, puntos=10),
        CuartoDTO(idClub=8, nroCuarto=1, puntos=8),
    ]

    bloque._campos_local[1].value = "abc"
    with pytest.raises(DatoInvalidoError, match=r"Local Q2|local Q2"):
        bloque.leer_cuartos(7, 8)
    assert bloque._campos_local[1].error is not None


# ------------------------------------------------------------------ CargaPartidoScreen


def test_preselecciona_club_activo_como_local_y_permite_cargar_partido_de_terceros_AC5(armar, mocks, page):
    vista = armar()

    dd_local = desplegable(vista, "Club local")
    assert dd_local.value == "7"  # Atenas preseleccionado

    # Cambiamos ambos equipos para cargar un partido entre Instituto (8) y Hindu (9) — AC5
    dd_comp = desplegable(vista, "Competencia")
    dd_comp.value = "10"
    dd_comp.on_select()
    desplegable(vista, "Categoría").value = "1"
    campo(vista, "Fecha (AAAA-MM-DD)").value = "2026-08-10"
    campo(vista, "Estadio (opcional)").value = "Cancha Neutral"
    dd_local.value = "8"
    desplegable(vista, "Club visitante").value = "9"

    boton(vista, "Continuar a boxscores").on_click()
    assert por_clave(vista, CLAVE_PASO_BOXSCORE).visible is True
    assert por_clave(vista, CLAVE_PASO_DATOS).visible is False

    # Cargamos estadisticas a ambos jugadores
    campo(vista, "Juan Perez · Min").value = "20"
    campo(vista, "Juan Perez · T2C").value = "3"
    campo(vista, "Juan Perez · T2L").value = "5"
    campo(vista, "Lucas Gomez · Min").value = "18"
    campo(vista, "Lucas Gomez · T3C").value = "2"
    campo(vista, "Lucas Gomez · T3L").value = "4"

    boton(vista, "Continuar a resumen").on_click()
    assert por_clave(vista, CLAVE_PASO_RESUMEN).visible is True
    resumen = por_clave(vista, CLAVE_RESUMEN_TEXTO).value
    assert "Instituto 6 - 6 Hindú" in resumen

    boton(vista, "Guardar partido").on_click()
    mocks["cargar"].ejecutar.assert_called_once()
    partido_enviado, box_local, box_visitante = mocks["cargar"].ejecutar.call_args.args
    assert (partido_enviado.idClubLocal, partido_enviado.idClubVisitante) == (8, 9)
    assert partido_enviado.idCategoria == 1
    assert partido_enviado.cuartos == []
    assert box_local.estadisticas[0].puntos == 6
    assert box_visitante.estadisticas[0].puntos == 6
    page.navigate.assert_called_with("/partidos")


def test_avisa_y_lleva_a_listas_si_un_equipo_no_tiene_inscripcion_o_lista(armar, mocks, page):
    mocks["listar_lista"].ejecutar.side_effect = lambda id_ins: [] if id_ins == 102 else JUG_ATENAS
    vista = armar()

    dd_comp = desplegable(vista, "Competencia")
    dd_comp.value = "10"
    dd_comp.on_select()
    desplegable(vista, "Categoría").value = "1"
    campo(vista, "Fecha (AAAA-MM-DD)").value = "2026-08-10"
    desplegable(vista, "Club visitante").value = "8"

    boton(vista, "Continuar a boxscores").on_click()

    assert por_clave(vista, CLAVE_PASO_DATOS).visible is True
    assert por_clave(vista, CLAVE_AVISO_LISTA).visible is True
    assert "lista de buena fe" in por_clave(vista, CLAVE_ERROR).value

    boton(vista, "Ir a listas de buena fe").on_click()
    page.navigate.assert_called_with("/listas")


def test_si_falla_el_guardado_conserva_los_datos_cargados_AC4(armar, mocks, page):
    mocks["cargar"].ejecutar.side_effect = CuartosInconsistentesError(
        "La suma de cuartos del equipo local no coincide (faltan 2 puntos)."
    )
    vista = armar()

    dd_comp = desplegable(vista, "Competencia")
    dd_comp.value = "10"
    dd_comp.on_select()
    desplegable(vista, "Categoría").value = "1"
    campo(vista, "Fecha (AAAA-MM-DD)").value = "2026-08-10"
    desplegable(vista, "Club visitante").value = "8"
    boton(vista, "Continuar a boxscores").on_click()

    campo(vista, "Pepe Argento · T2C").value = "4"
    campo(vista, "Pepe Argento · T2L").value = "6"
    campo(vista, "Juan Perez · T2C").value = "2"
    campo(vista, "Juan Perez · T2L").value = "5"
    boton(vista, "Continuar a resumen").on_click()

    campo(vista, "Local Q1").value = "6"  # faltan 2 respecto a los 8 del boxscore
    campo(vista, "Visitante Q1").value = "4"

    boton(vista, "Guardar partido").on_click()

    # Muestra el error, NO navega, y conserva todos los datos cargados (AC4)
    assert "faltan 2 puntos" in por_clave(vista, CLAVE_ERROR).value
    page.navigate.assert_not_called()
    assert campo(vista, "Local Q1").value == "6"
    assert campo(vista, "Pepe Argento · T2C").value == "4"
    assert campo(vista, "Juan Perez · T2C").value == "2"


def test_error_en_boxscore_se_marca_en_la_fila_y_conserva_los_demas_jugadores(armar):
    vista = armar()

    dd_comp = desplegable(vista, "Competencia")
    dd_comp.value = "10"
    dd_comp.on_select()
    desplegable(vista, "Categoría").value = "1"
    campo(vista, "Fecha (AAAA-MM-DD)").value = "2026-08-10"
    desplegable(vista, "Club visitante").value = "8"
    boton(vista, "Continuar a boxscores").on_click()

    # T2C > T2L en Pepe Argento, dato valido en Juan Perez
    campo(vista, "Pepe Argento · T2C").value = "5"
    campo(vista, "Pepe Argento · T2L").value = "2"
    campo(vista, "Juan Perez · T2C").value = "3"
    campo(vista, "Juan Perez · T2L").value = "5"

    boton(vista, "Continuar a resumen").on_click()

    assert por_clave(vista, CLAVE_PASO_BOXSCORE).visible is True
    assert "Pepe Argento" in por_clave(vista, CLAVE_ERROR).value
    assert any("Pepe Argento" in t and "T2C" in t for t in textos(vista))
    assert campo(vista, "Juan Perez · T2C").value == "3"
