"""Tests unitarios de `PartidosScreen` (US-112, listado) y `DetallePartidoScreen` (US-114) sin ventana."""

from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, desplegable, por_clave, textos

from aplicacion.casos_uso.eliminar_partido import EliminarPartidoUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.partido_dto import (
    BoxscoreFilaDTO,
    CuartoDTO,
    PartidoDTO,
    PartidoResumenDTO,
    TotalesEquipoFilaDTO,
)
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.puntos_por_cuarto import filas_cuartos
from infraestructura.ui.flet.screens.detalle_partido_screen import (
    PARTIDO_NO_ENCONTRADO,
    SIN_BOXSCORE,
    TABLA_BOXSCORE,
    TABLA_CUARTOS,
    TABLA_TOTALES,
    TARJETA_MARCADOR,
    clave_tabla_boxscore,
    crear_detalle_partido_view,
    fila_boxscore,
    fila_totales,
)
from infraestructura.ui.flet.screens.partidos_screen import (
    AVISO_CATEGORIA_PENDIENTE,
    SIN_PARTIDOS,
    TABLA_PARTIDOS,
    crear_partidos_view,
    fila_partido,
    filtrar_partidos,
    resultado_del_club,
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
    puntosLocal=72,
    puntosVisitante=65,
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
TOTALES_RIVAL = TotalesEquipoFilaDTO(
    idClub=8,
    nombreClub="Universitario",
    origen="totales",
    puntos=65,
    t2c=20,
    t2l=40,
    t3c=5,
    t3l=15,
    t1c=10,
    t1l=12,
    rebotesDef=0,
    rebotesOf=0,
    asistencias=0,
    recuperos=0,
    perdidas=14,
    taponesRecibidos=0,
    taponesRealizados=0,
    faltasRecibidas=0,
    faltasCometidas=0,
)
PARTIDO_1_DTO = PartidoDTO(
    fecha="2026-05-21",
    idCompetencia=10,
    idCategoria=2,
    idClubLocal=7,
    idClubVisitante=8,
    estadio="Cancha Atenas",
    cuartos=[
        CuartoDTO(idClub=7, nroCuarto=1, puntos=20),
        CuartoDTO(idClub=7, nroCuarto=2, puntos=52),
        CuartoDTO(idClub=8, nroCuarto=1, puntos=30),
        CuartoDTO(idClub=8, nroCuarto=2, puntos=35),
    ],
    idPartido=1,
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
    obtener_totales = MagicMock(spec=ObtenerTotalesPartidoUseCase)
    obtener_totales.ejecutar.return_value = [TOTALES_RIVAL]
    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.return_value = [INS_LIGA_U21, INS_ASOC_U17]
    listar_comp = MagicMock(spec=ListarCompetenciasUseCase)
    listar_comp.ejecutar.return_value = [LIGA, ASOCIATIVO, OTRA_COMP]
    listar_cat = MagicMock(spec=ListarCategoriasUseCase)
    listar_cat.ejecutar.return_value = [U17, U21]
    obtener_partido = MagicMock(spec=ObtenerPartidoUseCase)
    obtener_partido.ejecutar.return_value = PARTIDO_1_DTO
    return {
        "obtener_partido": obtener_partido,
        "listar_partidos": listar_partidos,
        "obtener_boxscore": obtener_boxscore,
        "obtener_totales": obtener_totales,
        "listar_ins": listar_ins,
        "listar_comp": listar_comp,
        "listar_cat": listar_cat,
        "eliminar": MagicMock(spec=EliminarPartidoUseCase, **{"ejecutar.return_value": True}),
    }


@pytest.fixture
def armar(page, mocks, sesion):
    return lambda: crear_partidos_view(
        page,
        mocks["listar_partidos"],
        mocks["listar_ins"],
        mocks["listar_comp"],
        mocks["listar_cat"],
        sesion,
    )


@pytest.fixture
def armar_detalle(page, mocks, sesion):
    return lambda id_partido=1: crear_detalle_partido_view(
        page,
        mocks["listar_partidos"],
        mocks["obtener_partido"],
        mocks["obtener_boxscore"],
        mocks["obtener_totales"],
        mocks["eliminar"],
        sesion,
        id_partido,
    )


def test_fila_partido_y_fila_boxscore_formatean_sin_ids():
    assert fila_partido(PARTIDO_2) == ("2026-06-15", "Asociativo 2026", "U17", "Instituto", "—", "Atenas")
    assert fila_partido(PARTIDO_1)[3:6] == ("Atenas", "72 - 65", "Universitario")
    assert fila_totales(TOTALES_RIVAL)[:6] == ("Universitario", "Totales cargados", "65", "20/40", "5/15", "10/12")
    celdas_bs = fila_boxscore(FILA_BS)
    assert celdas_bs[:6] == ("Pepe Argento", "20", "10", "2/5", "2/5", "0/4")


def test_resultado_del_club_dice_ganado_o_perdido_desde_su_lado():
    assert resultado_del_club(PARTIDO_1, "Atenas") == "G"  # local, 72 - 65
    assert resultado_del_club(PARTIDO_1, "Universitario") == "P"
    visitante_gana = PartidoResumenDTO(3, "2026-07-01", None, "Liga", 2026, "Instituto", "Atenas", None, 60, 70)
    assert resultado_del_club(visitante_gana, "Atenas") == "G"
    assert resultado_del_club(PARTIDO_2, "Atenas") is None  # sin puntos


def test_filas_cuartos_arma_una_columna_por_periodo_y_el_total():
    columnas, filas = filas_cuartos(PARTIDO_1_DTO.cuartos, [(7, "Atenas"), (8, "Universitario")])

    assert columnas == ("Equipo", "Q1", "Q2", "Total")
    assert filas == [("Atenas", "20", "52", "72"), ("Universitario", "30", "35", "65")]


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
            mocks["listar_ins"],
            mocks["listar_comp"],
            mocks["listar_cat"],
            sesion_sin_club,
        )


def test_lista_partidos_y_filtra_solo_competencias_con_inscripcion(armar, mocks):
    vista = armar()

    mocks["listar_partidos"].ejecutar.assert_called_once_with(7)
    contenido = textos(por_clave(vista, TABLA_PARTIDOS))
    assert "Liga Provincial 2026" in contenido
    assert "Asociativo 2026" in contenido

    dd_comp = desplegable(vista, "Filtrar por competencia")
    nombres_opciones = [o.text for o in dd_comp.options]
    assert "Liga Provincial (2026)" in nombres_opciones
    assert "Asociativo (2026)" in nombres_opciones
    assert "Torneo Ajeno (2026)" not in nombres_opciones

    # El filtro de categoria ofrece todo el catalogo, no solo las inscriptas
    dd_cat = desplegable(vista, "Filtrar por categoría")
    assert [o.text for o in dd_cat.options] == ["Todas", "U17", "U21"]

    dd_comp.value = "10"
    dd_comp.on_select()
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


def test_la_tabla_muestra_categoria_y_ganado_perdido(armar):
    vista = armar()
    tabla = por_clave(vista, TABLA_PARTIDOS)

    contenido = textos(tabla)
    assert "U21" in contenido
    assert "G" in contenido  # PARTIDO_1: Atenas gano 72 - 65; PARTIDO_2 no tiene puntos
    assert "P" not in contenido


def test_ver_abre_el_detalle_en_otra_pantalla(armar, page):
    vista = armar()

    boton(vista, "Ver").on_click()

    page.navigate.assert_called_once_with("/partidos/ver/1")


def test_boton_cargar_partido_navega_a_la_pantalla_de_carga(armar, page):
    vista = armar()

    boton(vista, "Cargar partido").on_click()

    page.navigate.assert_called_once_with("/partidos/cargar")


# ----------------------------------------------------------------------------- detalle del partido (US-114)


def test_detalle_muestra_resultado_cuartos_totales_y_un_boxscore_por_equipo(armar_detalle, mocks):
    vista = armar_detalle()

    mocks["obtener_boxscore"].ejecutar.assert_called_once_with(1)
    mocks["obtener_totales"].ejecutar.assert_called_once_with(1)
    marcador = textos(por_clave(vista, TARJETA_MARCADOR))
    assert marcador == ["Atenas", "Local", "72", "-", "65", "Universitario", "Visitante", "Victoria"]
    assert "Total" in textos(por_clave(vista, TABLA_CUARTOS))
    assert "Totales cargados" in textos(por_clave(vista, TABLA_TOTALES))
    assert "Pepe Argento" in textos(por_clave(vista, clave_tabla_boxscore("Atenas")))
    # El rival solo tiene totales: no hay tabla de boxscore suya
    with pytest.raises(StopIteration):
        por_clave(vista, clave_tabla_boxscore("Universitario"))


def test_detalle_sin_cuartos_ni_boxscore(armar_detalle, mocks):
    mocks["obtener_partido"].ejecutar.return_value = PartidoDTO("2026-05-21", 10, 2, 7, 8, idPartido=1)
    mocks["obtener_boxscore"].ejecutar.return_value = []

    vista = armar_detalle()

    with pytest.raises(StopIteration):
        por_clave(vista, TABLA_CUARTOS)
    assert SIN_BOXSCORE in textos(por_clave(vista, TABLA_BOXSCORE))


def test_detalle_de_un_partido_ajeno_o_inexistente(armar_detalle, mocks):
    vista = armar_detalle(99)

    assert PARTIDO_NO_ENCONTRADO in textos(vista)
    mocks["obtener_partido"].ejecutar.assert_not_called()


def test_detalle_volver_vuelve_al_listado(armar_detalle, page):
    boton(armar_detalle(), "Volver a partidos").on_click()

    page.navigate.assert_called_once_with("/partidos")


def test_editar_partido_abre_la_carga_con_ese_partido(armar_detalle, page):
    boton(armar_detalle(), "Editar partido").on_click()

    page.navigate.assert_called_once_with("/partidos/editar/1")


def test_eliminar_partido_pide_confirmar_borra_y_vuelve_al_listado(armar_detalle, mocks, page):
    vista = armar_detalle()

    boton(vista, "Eliminar partido").on_click()
    mocks["eliminar"].ejecutar.assert_not_called()  # primero pregunta
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    dialogo.actions[1].on_click()

    mocks["eliminar"].ejecutar.assert_called_once_with(1)
    page.navigate.assert_called_once_with("/partidos")
