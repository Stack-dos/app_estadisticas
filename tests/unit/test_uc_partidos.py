"""Tests unitarios del caso de uso de partidos, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.eliminar_partido import EliminarPartidoUseCase
from aplicacion.casos_uso.listar_lideres_club import ListarLideresClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.partido_dto import (
    BoxscoreDTO,
    BoxscoreFilaDTO,
    CuartoDTO,
    EstadisticaInputDTO,
    PartidoDTO,
    PartidoResumenDTO,
    TotalesEquipoDTO,
)
from dominio.entidades.club import Club
from dominio.entidades.competencia import Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.entidades.jugador import Jugador
from dominio.entidades.partido import (
    ID_CLUB_NUEVO,
    MAX_JUGADORES_PARTIDO,
    BoxscoreFila,
    EstadisticaEquipo,
    JugadorPartido,
    LiderClub,
    Partido,
    PartidoCuarto,
    PartidoResumen,
    TotalesEquipoFila,
)
from dominio.exceptions import (
    CuartosInconsistentesError,
    DatoInvalidoError,
    InscripcionNoEncontradaError,
    JugadorNoEstaEnListaError,
    JugadorNoPerteneceAlClubError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from dominio.repositorios.partido_repositorio import PartidoRepositorio


@pytest.fixture
def repo_partido():
    return MagicMock(spec=PartidoRepositorio)


def test_listar_partidos_muestra_los_nombres_de_la_competencia_y_de_los_clubes(repo_partido):
    repo_partido.resumen_por_club.return_value = [
        PartidoResumen(1, "2026-05-21", "Cancha Atenas", "PROVINCIAL U21", 2026, "Atenas", "Universitario", "U21"),
        PartidoResumen(2, "2026-06-20", None, "PROVINCIAL U21", 2026, "Universitario", "Atenas"),
    ]

    resultado = ListarPartidosPorClubUseCase(repo_partido).ejecutar(1)

    assert resultado == [
        PartidoResumenDTO(1, "2026-05-21", "Cancha Atenas", "PROVINCIAL U21", 2026, "Atenas", "Universitario", "U21"),
        PartidoResumenDTO(2, "2026-06-20", None, "PROVINCIAL U21", 2026, "Universitario", "Atenas", None),
    ]
    repo_partido.resumen_por_club.assert_called_once_with(1)


def test_listar_partidos_sin_partidos_devuelve_lista_vacia(repo_partido):
    repo_partido.resumen_por_club.return_value = []

    assert ListarPartidosPorClubUseCase(repo_partido).ejecutar(1) == []


def test_obtener_boxscore_partido_devuelve_filas_dto(repo_partido):
    repo_partido.boxscore_por_partido.return_value = [
        BoxscoreFila(
            idPartido=1,
            idJugador=10,
            idClub=1,
            nombreJugador="Pepe Argento",
            nombreClub="Atenas",
            minutosJugados=25.5,
            puntos=14,
            t2c=4,
            t2l=7,
            t3c=2,
            t3l=5,
            t1c=0,
            t1l=2,
            rebotesDef=6,
            rebotesOf=2,
            rebotesTotales=8,
            asistencias=3,
            recuperos=1,
            perdidas=2,
            taponesRecibidos=0,
            taponesRealizados=1,
            faltasRecibidas=3,
            faltasCometidas=2,
        )
    ]

    resultado = ObtenerBoxscorePartidoUseCase(repo_partido).ejecutar(1)

    assert resultado == [
        BoxscoreFilaDTO(
            idPartido=1,
            idJugador=10,
            idClub=1,
            nombreJugador="Pepe Argento",
            nombreClub="Atenas",
            minutosJugados=25.5,
            puntos=14,
            t2c=4,
            t2l=7,
            t3c=2,
            t3l=5,
            t1c=0,
            t1l=2,
            rebotesDef=6,
            rebotesOf=2,
            rebotesTotales=8,
            asistencias=3,
            recuperos=1,
            perdidas=2,
            taponesRecibidos=0,
            taponesRealizados=1,
            faltasRecibidas=3,
            faltasCometidas=2,
        )
    ]
    repo_partido.boxscore_por_partido.assert_called_once_with(1)


def test_obtener_boxscore_partido_sin_datos_devuelve_lista_vacia(repo_partido):
    repo_partido.boxscore_por_partido.return_value = []

    assert ObtenerBoxscorePartidoUseCase(repo_partido).ejecutar(999) == []


# ------------------------------------------------------------------ CargarPartido (US-108, rediseñado en US-113)


@pytest.fixture
def repo_competencia_con_listas():
    """Mock de CompetenciaRepositorio.

    - Club 1 (propio): inscripto en comp=1/cat=1 (lista 100, jugador 1) y en cat=2 (lista 101, jugador 99).
    - Club 2 (rival inscripto): comp=1/cat=1 (lista 200, jugador 6).
    - Club 3 (rival nuevo): sin inscripciones.
    """
    repo = MagicMock(spec=CompetenciaRepositorio)

    def _inscripciones(id_club: int):
        if id_club == 1:
            return [
                Inscripcion(idClub=1, idCategoria=1, idCompetencia=1, idInscripcion=10),
                Inscripcion(idClub=1, idCategoria=2, idCompetencia=1, idInscripcion=11),
            ]
        if id_club == 2:
            return [Inscripcion(idClub=2, idCategoria=1, idCompetencia=1, idInscripcion=20)]
        return []

    def _lista(id_inscripcion: int):
        return {
            10: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=10, idListaBuenaFe=100),
            11: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=11, idListaBuenaFe=101),
            20: ListaBuenaFe(fechaPresentacion="2026-03-01", idInscripcion=20, idListaBuenaFe=200),
        }.get(id_inscripcion)

    def _jugadores(id_lista: int):
        return {
            100: [JugadorListaBuenaFe(idJugador=1, idListaBuenaFe=100)],
            101: [JugadorListaBuenaFe(idJugador=99, idListaBuenaFe=101)],
            200: [JugadorListaBuenaFe(idJugador=6, idListaBuenaFe=200)],
        }.get(id_lista, [])

    repo.obtener_inscripciones_por_club.side_effect = _inscripciones
    repo.obtener_lista_por_inscripcion.side_effect = _lista
    repo.obtener_jugadores_lista.side_effect = _jugadores
    return repo


@pytest.fixture
def repo_jugador():
    """Plantel vigente: club 2 tiene a Lucas Gomez (6) y a José Pérez (7, todavia no en su lista); club 3 a nadie."""
    repo = MagicMock(spec=JugadorRepositorio)
    repo.buscar_por_club.side_effect = lambda id_club: {
        2: [Jugador("Lucas", "Gomez", idJugador=6), Jugador("José", "Pérez", idJugador=7)],
    }.get(id_club, [])
    return repo


@pytest.fixture
def uc(repo_partido, repo_competencia_con_listas, repo_jugador):
    repo_partido.save_with_boxscore.return_value = (
        Partido("2026-08-10", "Estadio Atenas", 1, 1, 1, 2, idPartido=42),
        [],
    )
    return CargarPartidoUseCase(repo_partido, repo_competencia_con_listas, repo_jugador)


def _partido(cuartos: list[CuartoDTO] | None = None, local: int = 1, visitante: int = 2) -> PartidoDTO:
    return PartidoDTO(
        fecha="2026-08-10",
        estadio="Estadio Atenas",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=local,
        idClubVisitante=visitante,
        cuartos=cuartos or [],
    )


def _box_propio() -> BoxscoreDTO:
    return BoxscoreDTO(
        idClub=1, estadisticas=[EstadisticaInputDTO(idJugador=1, minutosJugados=20.0, puntos=10, t2c=5, t2l=8)]
    )


def _totales_rival(puntos: int = 8, **tiros) -> TotalesEquipoDTO:
    return TotalesEquipoDTO(idClub=2, puntos=puntos, **tiros)


def test_cargar_partido_con_totales_del_rival_guarda_atomicamente(uc, repo_partido):
    resultado = uc.ejecutar(_partido(), _box_propio(), _totales_rival(8, t2c=4, t2l=9))

    assert resultado is not None
    assert resultado.idPartido == 42
    repo_partido.save_with_boxscore.assert_called_once_with(
        partido=Partido(
            fecha="2026-08-10",
            estadio="Estadio Atenas",
            idCompetencia=1,
            idCategoria=1,
            idClubLocal=1,
            idClubVisitante=2,
        ),
        boxscore=[JugadorPartido(idJugador=1, idPartido=0, idClub=1, minutosJugados=20.0, puntos=10, t2c=5, t2l=8)],
        cuartos=None,
        totales=[EstadisticaEquipo(idClub=2, puntos=8, t2c=4, t2l=9)],
        alta_rival=None,
        club_rival_nuevo=None,
    )


def test_del_rival_alcanza_con_el_resultado(uc, repo_partido):
    uc.ejecutar(_partido(), _box_propio(), _totales_rival(57))

    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert kwargs["totales"] == [EstadisticaEquipo(idClub=2, puntos=57)]


def test_totales_del_rival_con_tiros_que_no_cierran_se_rechazan(uc, repo_partido):
    with pytest.raises(DatoInvalidoError, match="no cierran"):
        uc.ejecutar(_partido(), _box_propio(), _totales_rival(50, t2c=4, t2l=9))
    repo_partido.save_with_boxscore.assert_not_called()


def test_el_club_propio_puede_jugar_de_visitante(uc, repo_partido):
    uc.ejecutar(_partido(local=2, visitante=1), _box_propio(), _totales_rival(8))

    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert (kwargs["partido"].idClubLocal, kwargs["partido"].idClubVisitante) == (2, 1)


def test_cargar_partido_devuelve_none_si_repositorio_revierte(uc, repo_partido):
    repo_partido.save_with_boxscore.return_value = None

    assert uc.ejecutar(_partido(), _box_propio(), _totales_rival()) is None


@pytest.mark.parametrize(
    "id_jugador, texto_esperado",
    [
        pytest.param(999, "idJugador=999", id="jugador-fuera-de-lista"),
        pytest.param(99, "idJugador=99", id="jugador-de-otra-categoria-AC6"),
    ],
)
def test_jugador_propio_no_habilitado_se_rechaza_antes_de_persistir(uc, repo_partido, id_jugador, texto_esperado):
    box = _box_propio()
    box.estadisticas.append(EstadisticaInputDTO(idJugador=id_jugador))

    with pytest.raises(JugadorNoEstaEnListaError, match=texto_esperado):
        uc.ejecutar(_partido(), box, _totales_rival())
    repo_partido.save_with_boxscore.assert_not_called()


def test_club_propio_sin_inscripcion_se_rechaza(uc, repo_partido):
    partido = _partido()
    partido.idCategoria = 3

    with pytest.raises(InscripcionNoEncontradaError, match="Tu club"):
        uc.ejecutar(partido, _box_propio(), _totales_rival())
    repo_partido.save_with_boxscore.assert_not_called()


@pytest.mark.parametrize(
    "partido, rival, mensaje",
    [
        pytest.param(_partido(local=1, visitante=1), _totales_rival(), "no pueden ser el mismo", id="mismo-club"),
        pytest.param(_partido(), TotalesEquipoDTO(idClub=1, puntos=3), "no el propio", id="rival-es-el-propio"),
        pytest.param(_partido(), TotalesEquipoDTO(idClub=9, puntos=3), "otro club del partido", id="rival-ajeno"),
    ],
)
def test_clubes_incoherentes_se_rechazan(uc, repo_partido, partido, rival, mensaje):
    with pytest.raises(DatoInvalidoError, match=mensaje):
        uc.ejecutar(partido, _box_propio(), rival)
    repo_partido.save_with_boxscore.assert_not_called()


@pytest.mark.parametrize("fecha", ["2026", "10/08/2026", ""])
def test_fecha_invalida_se_rechaza(uc, fecha):
    partido = _partido()
    partido.fecha = fecha

    with pytest.raises(DatoInvalidoError, match="AAAA-MM-DD"):
        uc.ejecutar(partido, _box_propio(), _totales_rival())


def test_boxscore_propio_vacio_se_rechaza(uc):
    with pytest.raises(DatoInvalidoError, match="al menos un jugador de tu equipo"):
        uc.ejecutar(_partido(), BoxscoreDTO(idClub=1), _totales_rival())


def test_rival_inscripto_con_jugador_de_su_lista_no_da_de_alta_nada(uc, repo_partido):
    rival = BoxscoreDTO(idClub=2, estadisticas=[EstadisticaInputDTO(idJugador=6, puntos=8, t2c=4, t2l=7)])

    uc.ejecutar(_partido(), _box_propio(), rival)

    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert kwargs["alta_rival"] is None
    assert kwargs["totales"] is None
    assert [f.idJugador for f in kwargs["boxscore"]] == [1, 6]


def test_rival_inscripto_reconoce_por_nombre_sin_tildes_y_habilita_al_que_faltaba(uc, repo_partido):
    rival = BoxscoreDTO(
        idClub=2,
        estadisticas=[
            EstadisticaInputDTO(idJugador=None, nombre="jose", apellido="PEREZ", puntos=3, t3c=1, t3l=2),
            EstadisticaInputDTO(idJugador=None, nombre="Ana", apellido="Nueva", puntos=2, t2c=1, t2l=1),
        ],
    )

    uc.ejecutar(_partido(), _box_propio(), rival)

    _, kwargs = repo_partido.save_with_boxscore.call_args
    alta = kwargs["alta_rival"]
    assert alta.idListaBuenaFe == 200  # ya estaba inscripto: no se crea otra inscripcion
    assert alta.habilitar == [7]  # José Pérez era del club pero no estaba en la lista
    assert [n.jugador.nombre_completo for n in alta.nuevos] == ["Ana Nueva"]
    assert alta.nuevos[0].estadistica.puntos == 2
    assert [f.idJugador for f in kwargs["boxscore"]] == [1, 7]


def test_rival_sin_inscripcion_se_inscribe_solo_con_su_lista(uc, repo_partido):
    partido = _partido(local=1, visitante=3)
    rival = BoxscoreDTO(
        idClub=3,
        estadisticas=[EstadisticaInputDTO(idJugador=None, nombre="Juan", apellido="Rival", puntos=2, t2c=1, t2l=3)],
    )

    uc.ejecutar(partido, _box_propio(), rival)

    _, kwargs = repo_partido.save_with_boxscore.call_args
    alta = kwargs["alta_rival"]
    assert alta.idListaBuenaFe is None  # el repositorio crea inscripcion y lista
    assert (alta.idClub, alta.idCompetencia, alta.idCategoria, alta.fecha) == (3, 1, 1, "2026-08-10")
    assert len(alta.nuevos) == 1


def test_rival_con_jugador_de_otro_club_por_id_se_rechaza(uc, repo_partido):
    rival = BoxscoreDTO(idClub=2, estadisticas=[EstadisticaInputDTO(idJugador=1, puntos=0)])

    with pytest.raises(JugadorNoPerteneceAlClubError, match="idJugador=1"):
        uc.ejecutar(_partido(), _box_propio(), rival)
    repo_partido.save_with_boxscore.assert_not_called()


def test_rival_con_el_mismo_jugador_nuevo_dos_veces_se_rechaza(uc):
    fila = EstadisticaInputDTO(idJugador=None, nombre="Ana", apellido="Nueva")
    with pytest.raises(DatoInvalidoError, match="dos veces"):
        uc.ejecutar(_partido(), _box_propio(), BoxscoreDTO(idClub=2, estadisticas=[fila, fila]))


def test_rival_con_jugador_sin_apellido_se_rechaza(uc):
    fila = EstadisticaInputDTO(idJugador=None, nombre="Ana", apellido="")
    with pytest.raises(DatoInvalidoError, match="apellido"):
        uc.ejecutar(_partido(), _box_propio(), BoxscoreDTO(idClub=2, estadisticas=[fila]))


def test_cuatro_cuartos_y_prorroga_validos_contra_los_totales_del_rival_AC7(uc, repo_partido):
    cuartos = [CuartoDTO(idClub=1, nroCuarto=n, puntos=2) for n in range(1, 6)] + [
        CuartoDTO(idClub=2, nroCuarto=n, puntos=p) for n, p in zip(range(1, 6), [2, 2, 2, 2, 0], strict=True)
    ]

    resultado = uc.ejecutar(_partido(cuartos), _box_propio(), _totales_rival(8))

    assert resultado is not None
    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert len(kwargs["cuartos"]) == 10
    assert kwargs["cuartos"][0] == PartidoCuarto(idClub=1, nroCuarto=1, puntos=2)


@pytest.mark.parametrize(
    "cuartos, mensaje_esperado",
    [
        pytest.param(
            [CuartoDTO(idClub=1, nroCuarto=1, puntos=5), CuartoDTO(idClub=1, nroCuarto=2, puntos=5)],
            "visitante",
            id="cuartos-de-un-solo-equipo",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=1, puntos=8),
            ],
            "distinta cantidad",
            id="distinta-cantidad-de-periodos",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=4),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=4),  # suma 8, faltan 2 para 10
                CuartoDTO(idClub=2, nroCuarto=1, puntos=4),
                CuartoDTO(idClub=2, nroCuarto=2, puntos=4),
            ],
            r"local.*faltan 2",
            id="suma-local-menor-al-boxscore",
        ),
        pytest.param(
            [
                CuartoDTO(idClub=1, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=1, nroCuarto=2, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=1, puntos=5),
                CuartoDTO(idClub=2, nroCuarto=2, puntos=6),  # suma 11, sobran 3 sobre los 8 del rival
            ],
            r"visitante.*sobran 3",
            id="suma-visitante-mayor-a-sus-totales",
        ),
    ],
)
def test_cuartos_inconsistentes_se_rechazan_AC7(uc, repo_partido, cuartos, mensaje_esperado):
    with pytest.raises(CuartosInconsistentesError, match=mensaje_esperado):
        uc.ejecutar(_partido(cuartos), _box_propio(), _totales_rival(8))
    repo_partido.save_with_boxscore.assert_not_called()


# ------------------------------------------------------------------ Totales y lideres (US-113)


def test_obtener_totales_partido_traduce_filas(repo_partido):
    repo_partido.totales_por_partido.return_value = [
        TotalesEquipoFila(
            idPartido=1, idClub=2, nombreClub="Pesca", origen="totales", puntos=51,
            t2c=19, t2l=52, t3c=3, t3l=19, t1c=4, t1l=10, rebotesDef=31, rebotesOf=7, asistencias=6,
            recuperos=7, perdidas=26, taponesRecibidos=0, taponesRealizados=0, faltasRecibidas=0, faltasCometidas=9,
        )
    ]  # fmt: skip

    (tot,) = ObtenerTotalesPartidoUseCase(repo_partido).ejecutar(1)

    assert (tot.nombreClub, tot.origen, tot.puntos, tot.perdidas) == ("Pesca", "totales", 51, 26)
    repo_partido.totales_por_partido.assert_called_once_with(1)


def test_listar_lideres_club_pide_el_limite_y_traduce(repo_partido):
    repo_partido.lideres_por_club.return_value = [
        LiderClub(idJugador=1, nombreJugador="Tomas Valdez", partidosJugados=16, puntosPromedio=13.8,
                  rebotesPromedio=7.9, asistenciasPromedio=2.3)
    ]  # fmt: skip

    (lider,) = ListarLideresClubUseCase(repo_partido).ejecutar(7)

    assert (lider.nombreJugador, lider.puntosPromedio) == ("Tomas Valdez", 13.8)
    repo_partido.lideres_por_club.assert_called_once_with(7, 5)


# ----------------------------------------------------------------------------- US-114: reglas nuevas de la carga


def test_empate_se_rechaza(uc, repo_partido):
    with pytest.raises(DatoInvalidoError, match="no hay empates"):
        uc.ejecutar(_partido(), _box_propio(), _totales_rival(10))
    repo_partido.save_with_boxscore.assert_not_called()


def test_mas_de_12_jugadores_en_un_equipo_se_rechaza(uc, repo_partido):
    rival = BoxscoreDTO(
        idClub=2,
        estadisticas=[
            EstadisticaInputDTO(idJugador=None, nombre=f"Jugador{n}", apellido="Rival", puntos=1, t1c=1, t1l=1)
            for n in range(MAX_JUGADORES_PARTIDO + 1)
        ],
    )

    with pytest.raises(DatoInvalidoError, match="12"):
        uc.ejecutar(_partido(), _box_propio(), rival)
    repo_partido.save_with_boxscore.assert_not_called()


def test_rival_nuevo_viaja_con_el_partido_para_crearse_en_la_misma_transaccion(uc, repo_partido):
    uc.ejecutar(
        _partido(local=1, visitante=ID_CLUB_NUEVO),
        _box_propio(),
        TotalesEquipoDTO(idClub=ID_CLUB_NUEVO, puntos=8),
        nombre_rival_nuevo="  Pesca ",
    )

    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert kwargs["club_rival_nuevo"] == Club("Pesca")
    assert kwargs["partido"].idClubVisitante == ID_CLUB_NUEVO


@pytest.mark.parametrize(
    ("id_rival", "nombre", "mensaje"),
    [(ID_CLUB_NUEVO, None, "Falta el nombre"), (2, "Pesca", "no puede venir con el id")],
)
def test_rival_nuevo_exige_id_provisorio_y_nombre_juntos(uc, repo_partido, id_rival, nombre, mensaje):
    with pytest.raises(DatoInvalidoError, match=mensaje):
        uc.ejecutar(
            _partido(local=1, visitante=id_rival),
            _box_propio(),
            TotalesEquipoDTO(idClub=id_rival, puntos=8),
            nombre_rival_nuevo=nombre,
        )
    repo_partido.save_with_boxscore.assert_not_called()


def test_editar_manda_el_id_del_partido_al_repositorio(uc, repo_partido):
    dto = _partido()
    dto.idPartido = 42

    uc.ejecutar(dto, _box_propio(), _totales_rival(8))

    _, kwargs = repo_partido.save_with_boxscore.call_args
    assert kwargs["partido"].idPartido == 42


# ----------------------------------------------------------------------------- US-114: obtener y eliminar partido


def test_obtener_partido_trae_sus_datos_y_cuartos(repo_partido):
    repo_partido.buscar_por_id.return_value = Partido("2026-08-10", "Estadio", 1, 1, 1, 2, idPartido=42)
    repo_partido.cuartos_por_partido.return_value = [PartidoCuarto(idPartido=42, idClub=1, nroCuarto=1, puntos=20)]

    dto = ObtenerPartidoUseCase(repo_partido).ejecutar(42)

    assert dto == PartidoDTO(
        fecha="2026-08-10",
        estadio="Estadio",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=1,
        idClubVisitante=2,
        cuartos=[CuartoDTO(idClub=1, nroCuarto=1, puntos=20)],
        idPartido=42,
    )


def test_obtener_partido_inexistente_devuelve_none(repo_partido):
    repo_partido.buscar_por_id.return_value = None

    assert ObtenerPartidoUseCase(repo_partido).ejecutar(99) is None
    repo_partido.cuartos_por_partido.assert_not_called()


def test_eliminar_partido_delega_en_el_repositorio(repo_partido):
    repo_partido.eliminar.return_value = True

    assert EliminarPartidoUseCase(repo_partido).ejecutar(42)
    repo_partido.eliminar.assert_called_once_with(42)
