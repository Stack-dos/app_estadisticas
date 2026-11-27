"""Tests unitarios de `PartidosScreen` (US-112) sin ventana, con mocks."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, desplegable, por_clave, textos

from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.partido_dto import BoxscoreFilaDTO, PartidoResumenDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.screens.partidos_screen import (
    AVISO_CATEGORIA_PENDIENTE,
    DETALLE_PARTIDO,
    SIN_BOXSCORE,
    SIN_PARTIDOS,
    TABLA_BOXSCORE,
    TABLA_PARTIDOS,
    crear_partidos_view,
    fila_boxscore,
    fila_partido,
    filtrar_partidos,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga Provincial", anio=2026, tipo="PROVINCIAL")
ASOCIATIVO = CompetenciaDTO(idCompetencia=11, nombre="Asociativo", anio=2026, tipo="ASOCIATIVO")
OTRA_COMP = CompetenciaDTO(idCompetencia=12, nombre="Torneo Ajeno", anio=2026, tipo="ASOCIATIVO")
U17 = CategoriaDTO(idCategoria=1, nombre="U17")
U21 = CategoriaDTO(idCategoria=2, nombre="U21")

INS_LIGA_U21 = InscripcionDTO(idInscripcion=1, idClub=7, idCategoria=2, idCompetencia=10, idListaBuenaFe=1)
INS_ASOC_U17 = InscripcionDTO(idInscripcion=2, idClub=7, idCategoria=1, idCompetencia=11, idListaBuenaFe=2)

PARTIDO_1 = PartidoResumenDTO(
    idPartido=1,
    fecha="2026-05-21",
    estadio="Cancha Atenas",
    competencia="Liga Provincial",
    anioCompetencia=2026,
    clubLocal="Atenas",
    clubVisitante="Universitario",
    categoria="U21",
)
PARTIDO_2 = PartidoResumenDTO(
    idPartido=2,
    fecha="2026-06-15",
    estadio=None,
    competencia="Asociativo",
    anioCompetencia=2026,
    clubLocal="Instituto",
    clubVisitante="Atenas",
    categoria="U17",
)

FILA_BS = BoxscoreFilaDTO(
    idPartido=1,
    idJugador=1,
    idClub=7,
    nombreJugador="Pepe Argento",
    nombreClub="Atenas",
    minutosJugados=20.0,
    puntos=10,
    t2c=2,
    t2l=5,
    t3c=2,
    t3l=5,
    t1c=0,
    t1l=4,
    rebotesDef=10,
    rebotesOf=2,
    rebotesTotales=12,
    asistencias=3,
    recuperos=2,
    perdidas=5,
    taponesRecibidos=1,
    taponesRealizados=5,
    faltasRecibidas=3,
    faltasCometidas=2,
)


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
    listar_partidos = MagicMock(spec=ListarPartidosPorClubUseCase)
    listar_partidos.ejecutar.return_value = [PARTIDO_1, PARTIDO_2]
    obtener_boxscore = MagicMock(spec=ObtenerBoxscorePartidoUseCase)
    obtener_boxscore.ejecutar.return_value = [FILA_BS]
    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.return_value = [INS_LIGA_U21, INS_ASOC_U17]
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA, ASOCIATIVO, OTRA_COMP]
    listar_cat = MagicMock(spec=ListarCategoriasUseCase)
    listar_cat.ejecutar.return_value = [U17, U21]
    return {
        "listar_partidos": listar_partidos,
        "obtener_boxscore": obtener_boxscore,
        "listar_ins": listar_ins,
        "listar_comp": listar_comp,
        "listar_cat": listar_cat,
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_partidos_view(
        page,
        mocks["listar_partidos"],
        mocks["obtener_boxscore"],
        mocks["listar_ins"],
        mocks["listar_comp"],
        mocks["listar_cat"],
        sesion,
    )


def test_fila_partido_y_fila_boxscore_formatean_sin_ids():
    assert fila_partido(PARTIDO_2) == ("2026-06-15", "Asociativo", "2026", "Instituto", "Atenas", "—")
    celdas_bs = fila_boxscore(FILA_BS)
    assert celdas_bs[:7] == ("Atenas", "Pepe Argento", "20", "10", "2/5", "2/5", "0/4")


def test_filtrar_partidos_por_competencia_y_categoria():
    assert filtrar_partidos([PARTIDO_1, PARTIDO_2], competencia_nombre="Asociativo", anio_competencia=2026) == [
        PARTIDO_2
    ]
    assert filtrar_partidos([PARTIDO_1, PARTIDO_2], categoria_nombre="U21") == [PARTIDO_1]


def test_exige_club_activo(page, mocks):
    sesion_sin_club = SessionManager(MagicMock(spec=SesionAlmacen))
    sesion_sin_club.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="Profesor", email="profe@test.com"))

    with pytest.raises(RuntimeError, match="club activo"):
        crear_partidos_view(
            page,
            mocks["listar_partidos"],
            mocks["obtener_boxscore"],
            mocks["listar_ins"],
            mocks["listar_comp"],
            mocks["listar_cat"],
            sesion_sin_club,
        )


def test_lista_partidos_y_filtra_solo_competencias_con_inscripcion(armar, mocks):
    vista = armar()

    mocks["listar_partidos"].ejecutar.assert_called_once_with(7)
    contenido = textos(por_clave(vista, TABLA_PARTIDOS))
    assert "Liga Provincial" in contenido
    assert "Asociativo" in contenido

    dd_comp = desplegable(vista, "Filtrar por competencia")
    nombres_opciones = [o.text for o in dd_comp.options]
    assert "Liga Provincial (2026)" in nombres_opciones
    assert "Asociativo (2026)" in nombres_opciones
    assert "Torneo Ajeno (2026)" not in nombres_opciones

    # Al elegir Liga Provincial, la categoria se acota solo a U21 y la tabla muestra PARTIDO_1
    dd_comp.value = "10"
    dd_comp.on_select()
    dd_cat = desplegable(vista, "Filtrar por categoría")
    assert [o.text for o in dd_cat.options] == ["Todas", "U21"]
    contenido_filtrado = textos(por_clave(vista, TABLA_PARTIDOS))
    assert "Universitario" in contenido_filtrado
    assert "Instituto" not in contenido_filtrado

    # Si no hay partidos, muestra estado vacio
    mocks["listar_partidos"].ejecutar.return_value = []
    vista_vacia = armar()
    assert SIN_PARTIDOS in textos(por_clave(vista_vacia, TABLA_PARTIDOS))


def test_muestra_aviso_si_se_filtra_por_categoria_y_los_partidos_no_tienen_categoria(armar, mocks):
    sin_cat = PartidoResumenDTO(1, "2026-05-21", "Cancha Atenas", "Liga Provincial", 2026, "Atenas", "Universitario")
    mocks["listar_partidos"].ejecutar.return_value = [sin_cat]
    vista = armar()

    dd_cat = desplegable(vista, "Filtrar por categoría")
    dd_cat.value = "2"
    dd_cat.on_select()

    assert AVISO_CATEGORIA_PENDIENTE in textos(vista)


def test_ver_boxscore_consulta_el_caso_de_uso_y_dibuja_el_detalle(armar, mocks):
    mocks["listar_partidos"].ejecutar.return_value = [PARTIDO_1]
    vista = armar()

    boton(vista, "Ver boxscore").on_click()

    mocks["obtener_boxscore"].ejecutar.assert_called_once_with(1)
    detalle = por_clave(vista, DETALLE_PARTIDO)
    assert "Boxscore: Atenas vs Universitario" in textos(detalle)
    assert "Pepe Argento" in textos(por_clave(vista, TABLA_BOXSCORE))

    # Si el partido no tiene filas cargadas, muestra el mensaje vacio
    mocks["obtener_boxscore"].ejecutar.return_value = []
    boton(vista, "Ver boxscore").on_click()
    assert SIN_BOXSCORE in textos(por_clave(vista, TABLA_BOXSCORE))


def test_boton_cargar_partido_navega_a_la_pantalla_de_carga(armar, page):
    vista = armar()

    boton(vista, "Cargar partido").on_click()

    page.navigate.assert_called_once_with("/partidos/cargar")
