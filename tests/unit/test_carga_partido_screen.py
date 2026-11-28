"""Tests unitarios de la carga de partido (US-108, rediseñada en US-113) sin ventana, con mocks.

Cubre la planilla tipo Excel (`PlanillaBoxscore`, `FilaTotalesEquipo`), el bloque de cuartos y la pantalla:
el club activo carga su boxscore y, del rival, sus totales (o solo el resultado) o su boxscore por jugador.
US-114: convocados (hasta 12), avisos con "Guardar igual", rival nuevo creado por el caso de uso y edicion.
Las celdas se buscan por su `key`, que arma `clave_celda`: "Pepe Argento · T2C", "Totales · PTS", "Rival 1 · Nombre".
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import flet as ft
import pytest
from ayudantes_flet import boton, campo, casilla, controles, desplegable, por_clave, textos

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.partido_dto import (
    BoxscoreDTO,
    BoxscoreFilaDTO,
    CuartoDTO,
    EstadisticaInputDTO,
    PartidoDTO,
    PartidoResumenDTO,
    TotalesEquipoDTO,
    TotalesEquipoFilaDTO,
)
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.partido import ID_CLUB_NUEVO, MAX_JUGADORES_PARTIDO
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.planilla_boxscore import FilaTotalesEquipo, PlanillaBoxscore, clave_celda
from infraestructura.ui.flet.components.puntos_por_cuarto import (
    BloquePuntosPorCuarto,
    clave_casillero_cuarto,
    etiqueta_periodo,
)
from infraestructura.ui.flet.screens.carga_partido_screen import (
    CLAVE_AVISO_LISTA,
    CLAVE_AVISOS_RESUMEN,
    CLAVE_BLOQUE_BOXSCORE_RIVAL,
    CLAVE_BLOQUE_TOTALES_RIVAL,
    CLAVE_BOTON_ATRAS,
    CLAVE_BOTON_GUARDAR,
    CLAVE_BOTON_SIGUIENTE,
    CLAVE_CONTADOR_CONVOCADOS,
    CLAVE_ERROR,
    CLAVE_INDICADOR_PASOS,
    CLAVE_MARCADOR,
    CLAVE_PASOS,
    CLAVE_PLEGABLE_CONVOCADOS,
    CLAVE_RESUMEN,
    CLAVE_SECCION_PROPIA,
    CONDICION_VISITANTE,
    FILAS_RIVAL_INICIALES,
    MODO_BOXSCORE,
    PASOS,
    SIN_CONVOCADOS,
    SIN_INSCRIPCIONES,
    crear_carga_partido_view,
)

LIGA = CompetenciaDTO(idCompetencia=10, nombre="Liga Provincial", anio=2026, tipo="PROVINCIAL")
U21 = CategoriaDTO(idCategoria=1, nombre="U21")
CLUB_ATENAS = ClubDTO(idClub=7, nombre="Atenas")
CLUB_INSTITUTO = ClubDTO(idClub=8, nombre="Instituto")
CLUB_HINDU = ClubDTO(idClub=9, nombre="Hindú")

INS_ATENAS = InscripcionDTO(idInscripcion=101, idClub=7, idCategoria=1, idCompetencia=10, idListaBuenaFe=1)
INS_INSTITUTO = InscripcionDTO(idInscripcion=102, idClub=8, idCategoria=1, idCompetencia=10, idListaBuenaFe=2)

PEPE = JugadorDTO(nombre_completo="Pepe Argento", id=1, anioNacimiento=2005)
MONI = JugadorDTO(nombre_completo="Moni Argento", id=4, anioNacimiento=2005)
JUAN = JugadorDTO(nombre_completo="Juan Perez", id=2, anioNacimiento=2005)


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
        fecha="2026-08-10", idCompetencia=10, idCategoria=1, idClubLocal=7, idClubVisitante=8, idPartido=55
    )
    listar_ins = MagicMock(spec=ListarInscripcionesClubUseCase)
    listar_ins.ejecutar.side_effect = lambda id_club: {7: [INS_ATENAS], 8: [INS_INSTITUTO]}.get(id_club, [])
    listar_lista = MagicMock(spec=ListarListaBuenaFeUseCase)
    listar_lista.ejecutar.side_effect = lambda id_ins: {101: [PEPE, MONI], 102: [JUAN]}.get(id_ins, [])
    return {
        "cargar": cargar,
        "listar_comp": MagicMock(spec=ListarCompetenciasUseCase, **{"ejecutar.return_value": [LIGA]}),
        "listar_cat": MagicMock(spec=ListarCategoriasUseCase, **{"ejecutar.return_value": [U21]}),
        "listar_clubes": MagicMock(
            spec=ListarClubesUseCase, **{"ejecutar.return_value": [CLUB_ATENAS, CLUB_INSTITUTO, CLUB_HINDU]}
        ),
        "listar_ins": listar_ins,
        "listar_lista": listar_lista,
        "listar_partidos": MagicMock(spec=ListarPartidosPorClubUseCase, **{"ejecutar.return_value": []}),
        "obtener_partido": MagicMock(spec=ObtenerPartidoUseCase, **{"ejecutar.return_value": None}),
        "obtener_boxscore": MagicMock(spec=ObtenerBoxscorePartidoUseCase, **{"ejecutar.return_value": []}),
        "obtener_totales": MagicMock(spec=ObtenerTotalesPartidoUseCase, **{"ejecutar.return_value": []}),
    }


@pytest.fixture
def armar(page, mocks, sesion):
    """`armar()` carga un partido nuevo; `armar(55)` abre la edicion del partido 55."""
    return lambda id_partido=None: crear_carga_partido_view(page, *mocks.values(), sesion, id_partido)


def _ir_a_confirmar(vista: ft.View) -> bool:
    """Toca "Siguiente" hasta el paso 3 (Confirmar). False si un paso no deja avanzar (el error queda a la vista)."""
    for _ in range(len(PASOS)):
        if por_clave(vista, CLAVE_PASOS[2]).visible:
            return True
        por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()
        if _error(vista):
            return False
    return por_clave(vista, CLAVE_PASOS[2]).visible


def _guardar(vista: ft.View, page: MagicMock) -> None:
    """Recorre el asistente hasta Confirmar y toca Guardar (los avisos ya se ven en el resumen)."""
    if _ir_a_confirmar(vista):
        por_clave(vista, CLAVE_BOTON_GUARDAR).on_click()


def _dialogo(page: MagicMock) -> ft.AlertDialog:
    dialogo = page.show_dialog.call_args.args[0]
    assert isinstance(dialogo, ft.AlertDialog)
    return dialogo


def _escribir(vista: ft.BaseControl, fila: str, valores: dict[str, str]) -> None:
    """Escribe en las celdas de una fila y dispara su `on_change`, como si el usuario tipeara."""
    for etiqueta, valor in valores.items():
        celda = por_clave(vista, clave_celda(fila, etiqueta))
        assert isinstance(celda, ft.TextField)
        celda.value = valor
        if celda.on_change is not None:  # nombre y apellido no recalculan nada
            celda.on_change()


def _segmentado(vista: ft.View, valor: str) -> ft.SegmentedButton:
    return next(
        c for c in controles(vista) if isinstance(c, ft.SegmentedButton) and any(s.value == valor for s in c.segments)
    )


def _elegir(vista: ft.View, valor: str) -> None:
    seg = _segmentado(vista, valor)
    seg.selected = [valor]
    seg.on_change()


def _elegir_rival(vista: ft.View, id_club: int) -> None:
    dd = desplegable(vista, "Rival")
    dd.value = str(id_club)
    dd.on_select()


def _escribir_rival(vista: ft.View, nombre: str) -> None:
    desplegable(vista, "Rival").on_text_change(SimpleNamespace(data=nombre))


def _error(vista: ft.View) -> str:
    etiqueta = por_clave(vista, CLAVE_ERROR)
    assert isinstance(etiqueta, ft.Text)
    return etiqueta.value or ""


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


# ------------------------------------------------------------------ PlanillaBoxscore / FilaTotalesEquipo


def test_planilla_calcula_puntos_por_fila_y_la_fila_equipo():
    planilla = PlanillaBoxscore("Atenas")
    planilla.cargar_jugadores([PEPE, MONI])

    _escribir(planilla.control, "Pepe Argento", {"T2C": "3", "T2L": "5", "T3C": "1", "T3L": "2"})
    _escribir(planilla.control, "Moni Argento", {"T1C": "2", "T1L": "2"})

    assert planilla.puntos == 11  # 3*2 + 1*3 + 2
    assert "9" in textos(planilla.control)  # PTS de Pepe


def test_planilla_ignora_filas_vacias_y_devuelve_una_estadistica_por_jugador_que_jugo():
    planilla = PlanillaBoxscore("Atenas")
    planilla.cargar_jugadores([PEPE, MONI])
    _escribir(planilla.control, "Pepe Argento", {"Min": "25,5", "T2C": "2", "T2L": "4", "AST": "3"})

    assert planilla.leer() == [
        EstadisticaInputDTO(idJugador=1, minutosJugados=25.5, puntos=4, t2c=2, t2l=4, asistencias=3)
    ]


def test_planilla_rechaza_convertidos_mayores_a_lanzados_y_marca_el_error():
    planilla = PlanillaBoxscore("Atenas")
    planilla.cargar_jugadores([PEPE])
    _escribir(planilla.control, "Pepe Argento", {"T2C": "5", "T2L": "2"})

    with pytest.raises(DatoInvalidoError, match="Pepe Argento"):
        planilla.leer()
    assert planilla.error.visible


def test_planilla_rechaza_celdas_no_numericas_o_negativas():
    planilla = PlanillaBoxscore("Atenas")
    planilla.cargar_jugadores([PEPE])
    _escribir(planilla.control, "Pepe Argento", {"AST": "tres"})
    with pytest.raises(DatoInvalidoError, match="AST"):
        planilla.leer()

    _escribir(planilla.control, "Pepe Argento", {"AST": "-1"})
    with pytest.raises(DatoInvalidoError, match="negativo"):
        planilla.leer()


def test_planilla_del_rival_con_filas_a_mano_exige_nombre_y_apellido():
    planilla = PlanillaBoxscore("Pesca", permite_agregar=True)
    planilla.agregar_fila()
    planilla.agregar_fila()
    _escribir(planilla.control, "Rival 1", {"Nombre": "Juan", "T3C": "1", "T3L": "1"})

    with pytest.raises(DatoInvalidoError, match="nombre y apellido"):
        planilla.leer()

    _escribir(planilla.control, "Rival 1", {"Apellido": "Rival"})
    assert planilla.leer() == [
        EstadisticaInputDTO(idJugador=None, nombre="Juan", apellido="Rival", puntos=3, t3c=1, t3l=1)
    ]  # la fila "Rival 2" quedo vacia: no se guarda


def test_fila_totales_con_tiros_calcula_los_puntos_y_los_bloquea():
    fila = FilaTotalesEquipo("Pesca")
    _escribir(fila.control, "Totales", {"T2C": "19", "T2L": "52", "T3C": "3", "T3L": "19", "T1C": "4", "T1L": "10"})

    assert fila.campo_puntos.value == "51"
    assert fila.campo_puntos.read_only
    assert fila.leer(20) == TotalesEquipoDTO(idClub=20, puntos=51, t2c=19, t2l=52, t3c=3, t3l=19, t1c=4, t1l=10)


def test_fila_totales_alcanza_con_el_resultado_pero_no_vacia():
    fila = FilaTotalesEquipo("Pesca")
    with pytest.raises(DatoInvalidoError, match="puntos del equipo"):
        fila.leer(20)

    _escribir(fila.control, "Totales", {"PTS": "65"})
    assert fila.leer(20) == TotalesEquipoDTO(idClub=20, puntos=65)


# ------------------------------------------------------------------ Pantalla


def test_exige_club_activo(page, mocks):
    sin_club = SessionManager(MagicMock(spec=SesionAlmacen))
    sin_club.iniciar_sesion(UsuarioDTO(idUsuario=1, nombre="DT", email="dt@test.com"))

    with pytest.raises(RuntimeError, match="club activo"):
        crear_carga_partido_view(page, *list(mocks.values()), sin_club)


def test_con_una_sola_inscripcion_ya_viene_elegida_y_muestra_la_planilla_propia(armar):
    vista = armar()

    dd_torneo = desplegable(vista, "Competencia y categoría")
    assert dd_torneo.value == "101"
    assert [o.text for o in dd_torneo.options] == ["Liga Provincial (2026) — U21"]
    assert por_clave(vista, CLAVE_SECCION_PROPIA).visible
    por_clave(vista, clave_celda("Pepe Argento", "T2C"))
    # El rival se elige entre los demas clubes: el propio no aparece
    assert [o.text for o in desplegable(vista, "Rival").options] == ["Instituto", "Hindú"]
    # Por defecto, del rival solo se cargan totales
    assert por_clave(vista, CLAVE_BLOQUE_TOTALES_RIVAL).visible
    assert not por_clave(vista, CLAVE_BLOQUE_BOXSCORE_RIVAL).visible


def test_guardar_con_rival_existente_y_sus_totales(armar, mocks, page):
    vista = armar()
    _elegir_rival(vista, 8)
    _escribir(vista, "Pepe Argento", {"Min": "30", "T2C": "6", "T2L": "10"})
    _escribir(vista, "Totales", {"PTS": "60"})

    _guardar(vista, page)

    partido, propio, rival, nombre_nuevo = mocks["cargar"].ejecutar.call_args.args
    assert (partido.idCompetencia, partido.idCategoria, partido.idClubLocal, partido.idClubVisitante) == (10, 1, 7, 8)
    assert propio == BoxscoreDTO(
        idClub=7, estadisticas=[EstadisticaInputDTO(idJugador=1, minutosJugados=30.0, puntos=12, t2c=6, t2l=10)]
    )
    assert rival == TotalesEquipoDTO(idClub=8, puntos=60)
    assert nombre_nuevo is None
    page.navigate.assert_called_once_with("/partidos")


def test_el_marcador_sigue_lo_cargado_y_la_condicion_de_local_o_visitante(armar):
    vista = armar()
    _elegir_rival(vista, 8)
    _escribir(vista, "Pepe Argento", {"T3C": "2", "T3L": "4"})
    _escribir(vista, "Totales", {"PTS": "4"})

    assert por_clave(vista, CLAVE_MARCADOR).value == "Atenas 6 - 4 Instituto"

    _elegir(vista, CONDICION_VISITANTE)
    assert por_clave(vista, CLAVE_MARCADOR).value == "Instituto 4 - 6 Atenas"


def test_de_visitante_el_club_propio_va_como_visitante(armar, mocks, page):
    vista = armar()
    _elegir_rival(vista, 8)
    _elegir(vista, CONDICION_VISITANTE)
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})
    _escribir(vista, "Totales", {"PTS": "70"})

    _guardar(vista, page)

    partido = mocks["cargar"].ejecutar.call_args.args[0]
    assert (partido.idClubLocal, partido.idClubVisitante) == (8, 7)


def test_rival_escrito_que_no_existe_lo_crea_el_caso_de_uso_junto_con_el_partido(armar, mocks, page):
    vista = armar()
    _escribir_rival(vista, "Pesca")
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})
    _escribir(vista, "Totales", {"PTS": "51"})

    _guardar(vista, page)

    # La pantalla no crea el club: manda el id provisorio y el nombre, y todo se guarda en una transaccion
    partido, _propio, rival, nombre_nuevo = mocks["cargar"].ejecutar.call_args.args
    assert partido.idClubVisitante == ID_CLUB_NUEVO
    assert rival.idClub == ID_CLUB_NUEVO
    assert nombre_nuevo == "Pesca"


def test_rival_escrito_igual_a_uno_existente_no_lo_duplica(armar, mocks, page):
    vista = armar()
    _escribir_rival(vista, "  instituto ")
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})
    _escribir(vista, "Totales", {"PTS": "51"})

    _guardar(vista, page)

    partido, _propio, _rival, nombre_nuevo = mocks["cargar"].ejecutar.call_args.args
    assert partido.idClubVisitante == 8
    assert nombre_nuevo is None


@pytest.mark.parametrize(
    ("preparar", "mensaje"),
    [
        (lambda v: _escribir(v, "Totales", {"PTS": "50"}), "al menos un jugador de tu equipo"),
        (lambda v: _escribir(v, "Pepe Argento", {"T2C": "1", "T2L": "1"}), "puntos del equipo"),
        (lambda v: _escribir(v, "Pepe Argento", {"T2C": "3", "T2L": "1"}), "Pepe Argento"),
    ],
)
def test_si_los_datos_tienen_errores_no_guarda(armar, mocks, page, preparar, mensaje):
    vista = armar()
    _escribir_rival(vista, "Pesca")
    preparar(vista)

    _guardar(vista, page)

    assert any(mensaje in t for t in textos(vista))  # en la planilla o abajo, junto a Guardar
    mocks["cargar"].ejecutar.assert_not_called()
    page.navigate.assert_not_called()


def test_sin_rival_pide_elegirlo(armar, mocks, page):
    vista = armar()
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})
    _escribir(vista, "Totales", {"PTS": "50"})

    _guardar(vista, page)

    assert "Elegí el rival" in _error(vista)
    mocks["cargar"].ejecutar.assert_not_called()


def test_boxscore_del_rival_inscripto_trae_su_lista(armar, mocks, page):
    vista = armar()
    _elegir_rival(vista, 8)

    _elegir(vista, MODO_BOXSCORE)

    assert por_clave(vista, CLAVE_BLOQUE_BOXSCORE_RIVAL).visible
    assert not por_clave(vista, CLAVE_BLOQUE_TOTALES_RIVAL).visible
    _escribir(vista, "Juan Perez", {"T2C": "2", "T2L": "3"})
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})

    _guardar(vista, page)

    rival = mocks["cargar"].ejecutar.call_args.args[2]
    assert rival == BoxscoreDTO(idClub=8, estadisticas=[EstadisticaInputDTO(idJugador=2, puntos=4, t2c=2, t2l=3)])


def test_boxscore_de_un_rival_nuevo_ofrece_filas_para_escribir_sus_jugadores(armar, mocks, page):
    vista = armar()
    _escribir_rival(vista, "Pesca")

    _elegir(vista, MODO_BOXSCORE)
    por_clave(vista, clave_celda(f"Rival {FILAS_RIVAL_INICIALES}", "Nombre"))  # las filas iniciales
    boton(vista, "Agregar jugador").on_click()
    por_clave(vista, clave_celda(f"Rival {FILAS_RIVAL_INICIALES + 1}", "Nombre"))
    _escribir(vista, "Rival 1", {"Nombre": "Juan", "Apellido": "Rival", "T1C": "1", "T1L": "2"})
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})

    _guardar(vista, page)

    rival = mocks["cargar"].ejecutar.call_args.args[2]
    assert rival == BoxscoreDTO(
        idClub=ID_CLUB_NUEVO,
        estadisticas=[EstadisticaInputDTO(idJugador=None, nombre="Juan", apellido="Rival", puntos=1, t1c=1, t1l=2)],
    )


def test_boxscore_del_rival_vacio_pide_cargar_alguno(armar, mocks, page):
    vista = armar()
    _elegir_rival(vista, 8)
    _elegir(vista, MODO_BOXSCORE)
    _escribir(vista, "Pepe Argento", {"T2C": "1", "T2L": "1"})

    _guardar(vista, page)

    assert "al menos un jugador del rival" in _error(vista)
    mocks["cargar"].ejecutar.assert_not_called()


def test_sin_inscripciones_avisa_y_lleva_a_inscribir(armar, mocks, page):
    mocks["listar_ins"].ejecutar.side_effect = lambda id_club: []
    vista = armar()

    aviso = por_clave(vista, CLAVE_AVISO_LISTA)
    assert aviso.visible
    assert SIN_INSCRIPCIONES in textos(aviso)
    boton(aviso, "Ir a inscripciones").on_click()
    page.navigate.assert_called_once_with("/inscripciones")


def test_lista_propia_vacia_avisa_y_lleva_a_listas(armar, mocks, page):
    mocks["listar_lista"].ejecutar.side_effect = lambda id_ins: []
    vista = armar()

    assert not por_clave(vista, CLAVE_SECCION_PROPIA).visible
    boton(por_clave(vista, CLAVE_AVISO_LISTA), "Ir a listas de buena fe").on_click()
    page.navigate.assert_called_once_with("/listas")


def test_si_falla_el_guardado_conserva_los_datos_cargados_AC4(armar, mocks, page):
    mocks["cargar"].ejecutar.return_value = None
    vista = armar()
    _elegir_rival(vista, 8)
    _escribir(vista, "Pepe Argento", {"T2C": "6", "T2L": "10"})
    _escribir(vista, "Totales", {"PTS": "60"})

    _guardar(vista, page)

    assert _error(vista)
    page.navigate.assert_not_called()
    assert por_clave(vista, clave_celda("Pepe Argento", "T2C")).value == "6"
    assert por_clave(vista, clave_celda("Totales", "PTS")).value == "60"


def test_cancelar_vuelve_a_partidos(armar, page):
    boton(armar(), "Cancelar").on_click()

    page.navigate.assert_called_once_with("/partidos")


# ------------------------------------------------------------------ US-114: componentes para editar


def test_bloque_cuartos_carga_lo_guardado_y_suma_las_prorrogas():
    bloque = BloquePuntosPorCuarto()
    cuartos = [CuartoDTO(idClub=7, nroCuarto=n, puntos=10) for n in range(1, 6)] + [
        CuartoDTO(idClub=8, nroCuarto=n, puntos=9) for n in range(1, 6)
    ]

    bloque.cargar_cuartos(cuartos, 7, 8)

    assert bloque.cantidad_periodos == 5  # 4 cuartos + PR1
    assert bloque.leer_cuartos(7, 8) == cuartos


def test_planilla_conserva_lo_cargado_si_se_vuelven_a_poner_los_jugadores():
    planilla = PlanillaBoxscore("Atenas")
    planilla.cargar_jugadores([PEPE, MONI])
    assert planilla.poner_valores(PEPE.id, {"t2c": 3, "t2l": 5, "minutosJugados": 20.5})

    planilla.cargar_jugadores([PEPE])  # se desmarco a Moni: Pepe sigue con lo suyo

    assert planilla.cantidad_filas == 1
    assert planilla.puntos == 6
    assert planilla.leer() == [EstadisticaInputDTO(idJugador=1, minutosJugados=20.5, puntos=6, t2c=3, t2l=5)]
    assert not planilla.poner_valores(MONI.id, {"t2c": 1})


def test_fila_totales_pone_valores_y_bloquea_los_puntos_si_hay_tiros():
    fila = FilaTotalesEquipo("Instituto")

    fila.poner_valores(10, {"t2c": 5, "t2l": 9})

    assert fila.campo_puntos.read_only
    assert fila.leer(8) == TotalesEquipoDTO(idClub=8, puntos=10, t2c=5, t2l=9)


# ------------------------------------------------------------------ US-114: convocados

PLANTEL_LARGO = [JugadorDTO(nombre_completo=f"Jugador {n}", id=100 + n, anioNacimiento=2005) for n in range(1, 14)]


def _contador(vista: ft.View) -> str:
    return por_clave(vista, CLAVE_CONTADOR_CONVOCADOS).value or ""


def test_con_12_o_menos_en_la_lista_vienen_todos_convocados(armar):
    vista = armar()

    assert casilla(vista, "Pepe Argento").value
    assert casilla(vista, "Moni Argento").value
    assert _contador(vista) == f"Convocados: 2/{MAX_JUGADORES_PARTIDO}"
    assert not por_clave(vista, CLAVE_PLEGABLE_CONVOCADOS).expanded  # ya estan todos: la seccion viene plegada


def test_desconvocar_saca_al_jugador_de_la_planilla(armar):
    vista = armar()

    casilla(vista, "Moni Argento").on_change()

    assert _contador(vista) == f"Convocados: 1/{MAX_JUGADORES_PARTIDO}"
    por_clave(vista, clave_celda("Pepe Argento", "T2C"))
    with pytest.raises(StopIteration):
        por_clave(vista, clave_celda("Moni Argento", "T2C"))


def test_con_mas_de_12_en_la_lista_no_viene_nadie_marcado_y_no_deja_pasar_de_12(armar, mocks):
    mocks["listar_lista"].ejecutar.side_effect = lambda id_ins: PLANTEL_LARGO
    vista = armar()
    assert _contador(vista) == f"Convocados: 0/{MAX_JUGADORES_PARTIDO}"
    assert por_clave(vista, CLAVE_PLEGABLE_CONVOCADOS).expanded  # hay que elegir: viene abierta

    for jugador in PLANTEL_LARGO:
        casilla(vista, jugador.nombre_completo).on_change()

    assert _contador(vista) == f"Convocados: 12/{MAX_JUGADORES_PARTIDO}"
    assert not casilla(vista, "Jugador 13").value
    assert "como máximo 12" in _error(vista)


def test_sin_convocados_no_guarda(armar, mocks, page):
    mocks["listar_lista"].ejecutar.side_effect = lambda id_ins: PLANTEL_LARGO
    vista = armar()
    _elegir_rival(vista, 8)

    _guardar(vista, page)

    assert _error(vista) == SIN_CONVOCADOS
    mocks["cargar"].ejecutar.assert_not_called()


# ------------------------------------------------------------------ US-114: avisos y un solo error


def _cargar_basico(vista: ft.View) -> None:
    _elegir_rival(vista, 8)
    _escribir(vista, "Pepe Argento", {"T2C": "6", "T2L": "10"})
    _escribir(vista, "Totales", {"PTS": "60"})


def test_con_menos_de_5_jugadores_avisa_en_el_resumen_antes_de_guardar(armar, mocks, page):
    vista = armar()
    _cargar_basico(vista)

    assert _ir_a_confirmar(vista)

    assert any("al menos 5" in t for t in textos(por_clave(vista, CLAVE_AVISOS_RESUMEN)))
    mocks["cargar"].ejecutar.assert_not_called()  # hasta que toque Guardar

    por_clave(vista, CLAVE_BOTON_GUARDAR).on_click()

    mocks["cargar"].ejecutar.assert_called_once()
    page.navigate.assert_called_once_with("/partidos")


def test_avisa_si_ya_hay_un_partido_igual(armar, mocks, page):
    mocks["listar_partidos"].ejecutar.return_value = [
        PartidoResumenDTO(
            idPartido=40,
            fecha="2026-08-10",
            estadio=None,
            competencia="Liga Provincial",
            anioCompetencia=2026,
            clubLocal="Atenas",
            clubVisitante="Instituto",
            categoria="U21",
        )
    ]
    vista = armar()
    campo(vista, "Fecha (AAAA-MM-DD)").value = "2026-08-10"
    _cargar_basico(vista)

    assert _ir_a_confirmar(vista)

    avisos = textos(por_clave(vista, CLAVE_AVISOS_RESUMEN))
    assert "Ya cargaste un partido contra Instituto el 2026-08-10 en este torneo." in avisos


def test_el_error_de_la_planilla_se_muestra_en_la_planilla_y_abajo_solo_dice_donde(armar, mocks, page):
    vista = armar()
    _elegir_rival(vista, 8)
    _escribir(vista, "Pepe Argento", {"T2C": "3", "T2L": "1"})
    _escribir(vista, "Totales", {"PTS": "60"})

    _guardar(vista, page)

    assert _error(vista) == "Revisá la planilla de Atenas: el error está marcado arriba."
    assert sum(t.startswith("Pepe Argento:") for t in textos(vista)) == 1  # el detalle, una sola vez


# ------------------------------------------------------------------ US-114: asistente de 3 pasos


def test_arranca_en_el_paso_1_con_solo_los_datos_del_partido(armar):
    vista = armar()

    assert [por_clave(vista, clave).visible for clave in CLAVE_PASOS] == [True, False, False]
    assert por_clave(vista, CLAVE_BOTON_SIGUIENTE).visible
    assert not por_clave(vista, CLAVE_BOTON_ATRAS).visible
    assert not por_clave(vista, CLAVE_BOTON_GUARDAR).visible
    assert "Datos del partido" in textos(por_clave(vista, CLAVE_INDICADOR_PASOS))


def test_no_pasa_del_paso_1_sin_rival(armar):
    vista = armar()

    por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()

    assert _error(vista) == "Elegí el rival o escribí su nombre."
    assert por_clave(vista, CLAVE_PASOS[0]).visible


def test_siguiente_y_atras_cambian_de_paso_sin_perder_lo_cargado(armar):
    vista = armar()
    _elegir_rival(vista, 8)

    por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()
    assert [por_clave(vista, clave).visible for clave in CLAVE_PASOS] == [False, True, False]
    _escribir(vista, "Pepe Argento", {"T2C": "6", "T2L": "10"})

    por_clave(vista, CLAVE_BOTON_ATRAS).on_click()
    assert por_clave(vista, CLAVE_PASOS[0]).visible
    por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()
    assert por_clave(vista, clave_celda("Pepe Argento", "T2C")).value == "6"


def test_el_resumen_muestra_marcador_equipos_y_cuartos(armar):
    vista = armar()
    _cargar_basico(vista)
    por_clave(vista, clave_casillero_cuarto("local", 1)).value = "12"
    por_clave(vista, clave_casillero_cuarto("visitante", 1)).value = "60"

    assert _ir_a_confirmar(vista)

    contenido = textos(por_clave(vista, CLAVE_RESUMEN))
    assert "Atenas 12 - 60 Instituto" in contenido
    assert "Jugadores cargados" in contenido
    assert "Puntos por cuarto" in contenido
    assert "Solo totales" in contenido


def test_un_error_del_paso_2_no_deja_llegar_al_resumen(armar, mocks):
    vista = armar()
    _elegir_rival(vista, 8)
    por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()

    por_clave(vista, CLAVE_BOTON_SIGUIENTE).on_click()  # planilla vacia

    assert _error(vista) == "Cargá las estadísticas de al menos un jugador de tu equipo."
    assert por_clave(vista, CLAVE_PASOS[1]).visible
    mocks["cargar"].ejecutar.assert_not_called()


# ------------------------------------------------------------------ US-114: editar


def _fila_bs(id_jugador: int, id_club: int, nombre: str, **valores: float) -> BoxscoreFilaDTO:
    base = dict.fromkeys(
        [
            "minutosJugados",
            "puntos",
            "t2c",
            "t2l",
            "t3c",
            "t3l",
            "t1c",
            "t1l",
            "rebotesDef",
            "rebotesOf",
            "rebotesTotales",
            "asistencias",
            "recuperos",
            "perdidas",
            "taponesRecibidos",
            "taponesRealizados",
            "faltasRecibidas",
            "faltasCometidas",
        ],
        0,
    )
    base.update(valores)
    return BoxscoreFilaDTO(
        idPartido=55, idJugador=id_jugador, idClub=id_club, nombreJugador=nombre, nombreClub="", **base
    )


def _totales(id_club: int, origen: str, puntos: int) -> TotalesEquipoFilaDTO:
    ceros = dict.fromkeys(
        [
            "t2c",
            "t2l",
            "t3c",
            "t3l",
            "t1c",
            "t1l",
            "rebotesDef",
            "rebotesOf",
            "asistencias",
            "recuperos",
            "perdidas",
            "taponesRecibidos",
            "taponesRealizados",
            "faltasRecibidas",
            "faltasCometidas",
        ],
        0,
    )
    return TotalesEquipoFilaDTO(idClub=id_club, nombreClub="", origen=origen, puntos=puntos, **ceros)


@pytest.fixture
def partido_guardado(mocks):
    """Atenas (local) 12 - 60 Instituto: Pepe metio 6 dobles; del rival solo los totales; con cuartos."""
    cuartos = [CuartoDTO(idClub=7, nroCuarto=n, puntos=3) for n in range(1, 5)] + [
        CuartoDTO(idClub=8, nroCuarto=n, puntos=15) for n in range(1, 5)
    ]
    mocks["obtener_partido"].ejecutar.return_value = PartidoDTO(
        fecha="2026-08-01",
        estadio="Cancha Atenas",
        idCompetencia=10,
        idCategoria=1,
        idClubLocal=7,
        idClubVisitante=8,
        cuartos=cuartos,
        idPartido=55,
    )
    mocks["obtener_boxscore"].ejecutar.return_value = [_fila_bs(1, 7, "Pepe Argento", puntos=12, t2c=6, t2l=10)]
    mocks["obtener_totales"].ejecutar.return_value = [_totales(7, "boxscore", 12), _totales(8, "totales", 60)]
    return cuartos


def test_editar_llega_con_lo_guardado(armar, partido_guardado):
    vista = armar(55)

    assert vista.route == "/partidos/editar/55"
    assert "Editar partido" in textos(vista)
    assert desplegable(vista, "Rival").value == "8"
    assert por_clave(vista, clave_celda("Pepe Argento", "T2C")).value == "6"
    assert por_clave(vista, clave_celda("Totales", "PTS")).value == "60"
    # Convocados: los que jugaron (Moni no tiene fila en el boxscore)
    assert casilla(vista, "Pepe Argento").value
    assert not casilla(vista, "Moni Argento").value
    assert por_clave(vista, CLAVE_MARCADOR).value == "Atenas 12 - 60 Instituto"


def test_guardar_cambios_reemplaza_el_mismo_partido(armar, mocks, page, partido_guardado):
    vista = armar(55)
    assert por_clave(vista, CLAVE_BOTON_GUARDAR).content == "Guardar cambios"
    _escribir(vista, "Pepe Argento", {"T2C": "7", "T2L": "10"})
    # Los cuartos tienen que seguir sumando el total: Q1 local pasa de 3 a 5 (5+3+3+3 = 14)
    por_clave(vista, clave_casillero_cuarto("local", 1)).value = "5"

    _guardar(vista, page)

    partido, propio, _rival, _nuevo = mocks["cargar"].ejecutar.call_args.args
    assert partido.idPartido == 55
    assert propio.estadisticas[0].puntos == 14
    assert partido.cuartos[0] == CuartoDTO(idClub=7, nroCuarto=1, puntos=5)


def test_editar_un_partido_ajeno_no_deja_guardar(armar, mocks, partido_guardado):
    mocks["obtener_partido"].ejecutar.return_value = PartidoDTO(
        fecha="2026-08-01", idCompetencia=10, idCategoria=1, idClubLocal=8, idClubVisitante=9, idPartido=55
    )

    vista = armar(55)

    assert "no es de tu club" in _error(vista)
    assert por_clave(vista, CLAVE_BOTON_GUARDAR).disabled


def test_editar_avisa_si_un_jugador_ya_no_esta_en_la_lista(armar, mocks, partido_guardado):
    mocks["obtener_boxscore"].ejecutar.return_value = [
        _fila_bs(1, 7, "Pepe Argento", puntos=2, t2c=1, t2l=1),
        _fila_bs(99, 7, "Ex Jugador", puntos=10, t2c=5, t2l=5),
    ]

    vista = armar(55)

    assert any("Ex Jugador" in t and "se pierden" in t for t in textos(vista))
