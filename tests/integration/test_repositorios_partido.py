import pytest

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.dtos.club_dto import CrearClubDTO
from aplicacion.dtos.partido_dto import BoxscoreDTO, CuartoDTO, EstadisticaInputDTO, PartidoDTO, TotalesEquipoDTO
from dominio.entidades.club import Club
from dominio.entidades.jugador import Jugador
from dominio.entidades.partido import (
    ID_CLUB_NUEVO,
    AltaPlantelRival,
    JugadorPartido,
    JugadorRivalNuevo,
    Partido,
    PartidoCuarto,
)
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio
from infraestructura.repositorios.sqlite_partido_repositorio import SqlitePartidoRepositorio

# `crear_partido` y `crear_boxscore` son fabricas de datos validos (ver tests/conftest.py):
# cada test pisa solo el campo que quiere romper, por ejemplo crear_boxscore(idJugador=40000).


def test_buscar_por_club(db_conexion):
    """Funcion que Busca partidos por club

    Args:
        db_conexion (): conexion a la base de datos
    """
    juego_rep = SqlitePartidoRepositorio(db_conexion)
    juego_encontrado = juego_rep.buscar_por_club(1)
    assert juego_encontrado is not None
    assert len(juego_encontrado) > 0


def test_buscar_por_id(db_conexion):
    """Funcion que Busca partidos por id

    Args:
        db_conexion (_type_): conexion a la base de datos
    """
    juego_rep = SqlitePartidoRepositorio(db_conexion)
    juego_encontrado = juego_rep.buscar_por_id(1)
    assert juego_encontrado is not None
    assert juego_encontrado.idPartido == 1


def test_guardar_partido(db_conexion, crear_partido):
    """Funcion que guarda partido en la Base de Datos

    Args:
        db_conexion (_type_): Conexion a la base de datos
    """
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    nuevo_juego = juego_rep.guardar_partido(partido=crear_partido())

    assert nuevo_juego is not None
    assert nuevo_juego.idPartido is not None
    assert nuevo_juego.fecha == "2023-01-01"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"idClubLocal": 12}, id="club-local-inexistente"),
        pytest.param({"idClubVisitante": 304}, id="club-visitante-inexistente"),
        pytest.param({"idCompetencia": 205}, id="competencia-inexistente"),
        pytest.param({"idCategoria": 999}, id="categoria-inexistente"),
    ],
)
def test_guardar_partido_con_referencia_inexistente_devuelve_none(db_conexion, crear_partido, overrides):
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    assert juego_rep.guardar_partido(partido=crear_partido(**overrides)) is None


def test_guardar_boxscore(db_conexion, crear_boxscore):
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    nuevo_boxscore = juego_rep.guardar_boxscore(boxscore=crear_boxscore())

    assert nuevo_boxscore is not None


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"idJugador": 40000, "idPartido": 1}, id="jugador-inexistente"),
        pytest.param({"idPartido": 300}, id="partido-inexistente"),
        pytest.param({"idPartido": 1, "idClub": 400}, id="club-inexistente"),
    ],
)
def test_guardar_boxscore_con_referencia_inexistente_devuelve_none(db_conexion, crear_boxscore, overrides):
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    assert juego_rep.guardar_boxscore(boxscore=crear_boxscore(**overrides)) is None


def test_save_with_boxscore_rollback_no_deja_partido_huerfano(db_conexion, crear_partido, crear_boxscore):
    """US-102 AC4: ante un boxscore con FK inválida, la transacción entera se revierte."""
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    partido = crear_partido(estadio="Estadio Test Rollback", fecha="2026-01-01")
    # idPartido=0: save_with_boxscore lo reemplaza por el id real del partido que inserta
    fila_ok = crear_boxscore(idPartido=0)
    # Fila con idJugador inexistente → viola FK → provoca rollback
    fila_invalida = crear_boxscore(idPartido=0, idJugador=999999)

    resultado = juego_rep.save_with_boxscore(partido, [fila_ok, fila_invalida])

    # La transacción debe haber fallado → retorna None
    assert resultado is None

    # El partido NO debe haber quedado guardado (sin partido huérfano)
    cursor = db_conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM partido WHERE fecha = '2026-01-01' AND estadio = 'Estadio Test Rollback'")
    count = cursor.fetchone()[0]
    assert count == 0


def test_resumen_por_club_trae_los_nombres_desde_la_vista(db_conexion):
    """El seed tiene 2 partidos entre los clubes 1 (Atenas) y 2 (Universitario)."""
    juego_rep = SqlitePartidoRepositorio(db_conexion)

    resumen = juego_rep.resumen_por_club(1)

    assert [p.idPartido for p in resumen] == [1, 2]  # del mas antiguo al mas reciente
    assert resumen[0].clubLocal == "Atenas"
    assert resumen[0].clubVisitante == "Universitario"
    assert resumen[0].competencia == "PROVINCIAL U21"
    assert resumen[0].anioCompetencia == 2026
    assert resumen[0].categoria == "U21"
    # el club aparece igual si jugo de visitante
    assert resumen[1].clubLocal == "Universitario"
    assert resumen[1].clubVisitante == "Atenas"


def test_resumen_por_club_de_un_club_sin_partidos_es_una_lista_vacia(db_conexion):
    assert SqlitePartidoRepositorio(db_conexion).resumen_por_club(999) == []


def test_obtener_boxscore_partido_lee_vista_con_datos_del_seed(db_conexion):
    """El partido 1 del seed tiene 2 filas en jugadorPartido (club 1 y club 2)."""
    uc = ObtenerBoxscorePartidoUseCase(SqlitePartidoRepositorio(db_conexion))

    filas = uc.ejecutar(1)

    assert len(filas) == 2
    assert filas[0].nombreJugador == "pepe argento"
    assert filas[0].nombreClub == "Atenas"
    assert filas[0].puntos == 10
    assert filas[0].rebotesTotales == 12
    assert filas[1].nombreJugador == "Sergio aguero"
    assert filas[1].nombreClub == "Universitario"
    assert filas[1].minutosJugados == 12.4
    assert filas[1].rebotesTotales == 5


def test_obtener_boxscore_partido_inexistente_devuelve_lista_vacia(db_conexion):
    assert ObtenerBoxscorePartidoUseCase(SqlitePartidoRepositorio(db_conexion)).ejecutar(999) == []


def test_save_with_boxscore_guarda_cuartos_en_la_misma_transaccion(db_conexion, crear_partido, crear_boxscore):
    """US-108: save_with_boxscore persiste partido, boxscore y cuartos atomicamente."""
    juego_rep = SqlitePartidoRepositorio(db_conexion)
    partido = crear_partido(fecha="2026-08-10", estadio="Polideportivo")
    fila_local = crear_boxscore(idPartido=0, idJugador=1, idClub=1)
    fila_visitante = crear_boxscore(idPartido=0, idJugador=6, idClub=2)
    cuartos = [
        PartidoCuarto(idClub=1, nroCuarto=1, puntos=5),
        PartidoCuarto(idClub=1, nroCuarto=2, puntos=4),
        PartidoCuarto(idClub=2, nroCuarto=1, puntos=3),
        PartidoCuarto(idClub=2, nroCuarto=2, puntos=6),
    ]

    resultado = juego_rep.save_with_boxscore(partido, [fila_local, fila_visitante], cuartos=cuartos)

    assert resultado is not None
    partido_guardado, filas = resultado
    assert partido_guardado.idPartido is not None
    assert partido_guardado.idCategoria == 1
    assert len(filas) == 2

    cursor = db_conexion.cursor()
    cursor.execute(
        "SELECT idClub, nroCuarto, puntos FROM partidoCuarto WHERE idPartido = ? ORDER BY idClub, nroCuarto",
        (partido_guardado.idPartido,),
    )
    assert [(r["idClub"], r["nroCuarto"], r["puntos"]) for r in cursor.fetchall()] == [
        (1, 1, 5),
        (1, 2, 4),
        (2, 1, 3),
        (2, 2, 6),
    ]


def _uc_cargar(db_conexion) -> CargarPartidoUseCase:
    return CargarPartidoUseCase(
        SqlitePartidoRepositorio(db_conexion),
        SqliteCompetenciaRepositorio(db_conexion),
        SqliteJugadorRepositorio(db_conexion),
    )


def _contar(db_conexion, sql: str, *params) -> int:
    return db_conexion.execute(sql, params).fetchone()[0]


def test_rival_nuevo_con_boxscore_se_da_de_alta_entero_en_la_misma_transaccion(db_conexion):
    """US-113: club rival sin usuario, sin inscripcion y con un jugador que no existe: todo se crea al guardar."""
    pesca = CrearClubUseCase(SqliteClubRepositorio(db_conexion)).ejecutar(CrearClubDTO(nombre="Pesca"))
    assert pesca is not None

    partido_dto = PartidoDTO(
        fecha="2026-09-01",
        estadio="El Teatro",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=1,  # Atenas (seed), con el jugador 1 en su lista
        idClubVisitante=pesca.idClub,
        cuartos=[
            CuartoDTO(idClub=1, nroCuarto=1, puntos=6),
            CuartoDTO(idClub=1, nroCuarto=2, puntos=6),
            CuartoDTO(idClub=pesca.idClub, nroCuarto=1, puntos=4),
            CuartoDTO(idClub=pesca.idClub, nroCuarto=2, puntos=5),
        ],
    )
    propio = BoxscoreDTO(
        idClub=1, estadisticas=[EstadisticaInputDTO(idJugador=1, minutosJugados=30.0, puntos=12, t2c=6, t2l=10)]
    )
    rival = BoxscoreDTO(
        idClub=pesca.idClub,
        estadisticas=[
            EstadisticaInputDTO(
                idJugador=None, nombre="Juan", apellido="Rival", minutosJugados=28.0, puntos=9, t3c=3, t3l=6
            )
        ],
    )

    guardado = _uc_cargar(db_conexion).ejecutar(partido_dto, propio, rival)

    assert guardado is not None and guardado.idPartido is not None
    # El rival quedo inscripto, con su lista, y el jugador nuevo vinculado al club y habilitado
    fila = db_conexion.execute(
        """
        SELECT j.idJugador, jc.fechaDesde
        FROM jugador j
            JOIN jugadorClub jc ON jc.idJugador = j.idJugador AND jc.fechaHasta IS NULL
            JOIN jugadorListaBuenaFe jl ON jl.idJugador = j.idJugador
            JOIN listaBuenaFe l ON l.idListaBuenaFe = jl.idListaBuenaFe
            JOIN inscripcion i ON i.idInscripcion = l.idInscripcion
        WHERE j.nombre = 'Juan' AND j.apellido = 'Rival' AND jc.idClub = ? AND i.idClub = ?
        """,
        (pesca.idClub, pesca.idClub),
    ).fetchone()
    assert fila is not None
    assert fila["fechaDesde"] == "2026-09-01"
    # Sigue sin vinculo con ningun usuario: no aparece en "Mis clubes"
    assert _contar(db_conexion, "SELECT COUNT(*) FROM usuarioClub WHERE idClub = ?", pesca.idClub) == 0

    boxscore = ObtenerBoxscorePartidoUseCase(SqlitePartidoRepositorio(db_conexion)).ejecutar(guardado.idPartido)
    assert {(f.nombreClub, f.puntos) for f in boxscore} == {("Atenas", 12), ("Pesca", 9)}
    assert _contar(db_conexion, "SELECT COUNT(*) FROM partidoCuarto WHERE idPartido = ?", guardado.idPartido) == 4

    # El segundo partido contra Pesca reconoce al jugador por nombre: no lo duplica
    partido_dto.fecha = "2026-10-01"
    partido_dto.cuartos = []
    rival.estadisticas[0].nombre = "JUAN"
    assert _uc_cargar(db_conexion).ejecutar(partido_dto, propio, rival) is not None
    assert (
        _contar(db_conexion, "SELECT COUNT(*) FROM jugador WHERE nombre IN ('Juan', 'JUAN') AND apellido = 'Rival'")
        == 1
    )
    assert _contar(db_conexion, "SELECT COUNT(*) FROM inscripcion WHERE idClub = ?", pesca.idClub) == 1


def test_rival_con_totales_se_guarda_en_estadistica_equipo_y_la_vista_unifica(db_conexion):
    pesca = CrearClubUseCase(SqliteClubRepositorio(db_conexion)).ejecutar(CrearClubDTO(nombre="Pesca"))
    assert pesca is not None
    repo = SqlitePartidoRepositorio(db_conexion)
    partido_dto = PartidoDTO(
        fecha="2026-09-01", idCompetencia=1, idCategoria=1, idClubLocal=pesca.idClub, idClubVisitante=1
    )
    propio = BoxscoreDTO(
        idClub=1, estadisticas=[EstadisticaInputDTO(idJugador=1, minutosJugados=30.0, puntos=12, t2c=6, t2l=10)]
    )
    rival = TotalesEquipoDTO(idClub=pesca.idClub, puntos=51, t2c=19, t2l=52, t3c=3, t3l=19, t1c=4, t1l=10, perdidas=26)

    guardado = _uc_cargar(db_conexion).ejecutar(partido_dto, propio, rival)

    assert guardado is not None and guardado.idPartido is not None
    # El rival con totales no se inscribe ni crea jugadores
    assert _contar(db_conexion, "SELECT COUNT(*) FROM inscripcion WHERE idClub = ?", pesca.idClub) == 0
    totales = repo.totales_por_partido(guardado.idPartido)
    assert [(t.nombreClub, t.origen, t.puntos) for t in totales] == [
        ("Pesca", "totales", 51),
        ("Atenas", "boxscore", 12),
    ]
    assert totales[0].perdidas == 26

    (resumen,) = [p for p in repo.resumen_por_club(pesca.idClub) if p.idPartido == guardado.idPartido]
    assert (resumen.puntosLocal, resumen.puntosVisitante) == (51, 12)


def test_si_falla_el_boxscore_no_queda_nada_del_alta_del_rival(db_conexion):
    """Atomicidad US-113: el alta del rival (inscripcion, lista, jugadores) se revierte junto con el partido."""
    pesca = CrearClubUseCase(SqliteClubRepositorio(db_conexion)).ejecutar(CrearClubDTO(nombre="Pesca"))
    assert pesca is not None
    repo = SqlitePartidoRepositorio(db_conexion)
    jugadores_antes = _contar(db_conexion, "SELECT COUNT(*) FROM jugador")
    alta = AltaPlantelRival(
        idClub=pesca.idClub,
        idCompetencia=1,
        idCategoria=1,
        fecha="2026-09-01",
        nuevos=[
            JugadorRivalNuevo(
                jugador=Jugador("Juan", "Rival"), estadistica=JugadorPartido(idJugador=0, idPartido=0, idClub=0)
            )
        ],
    )
    partido = Partido("2026-09-01", None, 1, 1, 1, pesca.idClub)
    fila_rota = JugadorPartido(idJugador=999999, idPartido=0, idClub=1)  # jugador inexistente

    assert repo.save_with_boxscore(partido, [fila_rota], alta_rival=alta) is None

    assert _contar(db_conexion, "SELECT COUNT(*) FROM jugador") == jugadores_antes
    assert _contar(db_conexion, "SELECT COUNT(*) FROM inscripcion WHERE idClub = ?", pesca.idClub) == 0


def test_lideres_por_club_promedia_desde_la_vista(db_conexion):
    lideres = SqlitePartidoRepositorio(db_conexion).lideres_por_club(1, 3)

    assert 0 < len(lideres) <= 3
    promedios = [lider.puntosPromedio for lider in lideres]
    assert promedios == sorted(promedios, reverse=True)
    assert all(lider.partidosJugados >= 1 for lider in lideres)


# ----------------------------------------------------------------------------- US-114: rival nuevo, editar y eliminar


def _propio(puntos_dobles: int = 6) -> BoxscoreDTO:
    return BoxscoreDTO(
        idClub=1,
        estadisticas=[
            EstadisticaInputDTO(idJugador=1, minutosJugados=30.0, puntos=puntos_dobles * 2, t2c=puntos_dobles, t2l=10)
        ],
    )


def test_rival_nuevo_se_crea_en_la_misma_transaccion_que_el_partido(db_conexion):
    partido_dto = PartidoDTO(
        fecha="2026-09-01", idCompetencia=1, idCategoria=1, idClubLocal=1, idClubVisitante=ID_CLUB_NUEVO
    )

    guardado = _uc_cargar(db_conexion).ejecutar(
        partido_dto, _propio(), TotalesEquipoDTO(idClub=ID_CLUB_NUEVO, puntos=40), nombre_rival_nuevo="Pesca"
    )

    assert guardado is not None
    id_pesca = db_conexion.execute("SELECT idClub FROM club WHERE nombre = 'Pesca'").fetchone()["idClub"]
    assert guardado.idClubVisitante == id_pesca
    totales = SqlitePartidoRepositorio(db_conexion).totales_por_partido(guardado.idPartido)
    assert ("Pesca", "totales", 40) in [(t.nombreClub, t.origen, t.puntos) for t in totales]
    assert _contar(db_conexion, "SELECT COUNT(*) FROM usuarioClub WHERE idClub = ?", id_pesca) == 0


def test_si_falla_el_partido_no_queda_el_rival_nuevo(db_conexion):
    """El rival mal escrito no queda suelto en la base si el partido no se guardo (US-114)."""
    repo = SqlitePartidoRepositorio(db_conexion)
    partido = Partido("2026-09-01", None, 1, 1, 1, ID_CLUB_NUEVO)
    fila_rota = JugadorPartido(idJugador=999999, idPartido=0, idClub=1)  # jugador inexistente

    assert repo.save_with_boxscore(partido, [fila_rota], club_rival_nuevo=Club("Pezca")) is None

    assert _contar(db_conexion, "SELECT COUNT(*) FROM club WHERE nombre = 'Pezca'") == 0


def test_editar_reemplaza_las_filas_y_conserva_el_id(db_conexion):
    uc = _uc_cargar(db_conexion)
    partido_dto = PartidoDTO(
        fecha="2026-09-01",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=1,
        idClubVisitante=2,
        cuartos=[CuartoDTO(idClub=1, nroCuarto=1, puntos=12), CuartoDTO(idClub=2, nroCuarto=1, puntos=40)],
    )
    guardado = uc.ejecutar(partido_dto, _propio(6), TotalesEquipoDTO(idClub=2, puntos=40))
    assert guardado is not None
    partidos_antes = _contar(db_conexion, "SELECT COUNT(*) FROM partido")

    partido_dto.idPartido = guardado.idPartido
    partido_dto.estadio = "Cancha nueva"
    partido_dto.cuartos = []  # se sacan los cuartos
    editado = uc.ejecutar(partido_dto, _propio(8), TotalesEquipoDTO(idClub=2, puntos=41))

    assert editado is not None and editado.idPartido == guardado.idPartido
    assert _contar(db_conexion, "SELECT COUNT(*) FROM partido") == partidos_antes
    repo = SqlitePartidoRepositorio(db_conexion)
    assert repo.buscar_por_id(guardado.idPartido).estadio == "Cancha nueva"
    assert [f.puntos for f in repo.boxscore_por_partido(guardado.idPartido)] == [16]
    assert {(t.idClub, t.puntos) for t in repo.totales_por_partido(guardado.idPartido)} == {(1, 16), (2, 41)}
    assert repo.cuartos_por_partido(guardado.idPartido) == []


def test_editar_un_partido_que_no_existe_no_crea_otro(db_conexion):
    partidos_antes = _contar(db_conexion, "SELECT COUNT(*) FROM partido")
    partido = Partido("2026-09-01", None, 1, 1, 1, 2, idPartido=999999)

    assert SqlitePartidoRepositorio(db_conexion).save_with_boxscore(partido, []) is None
    assert _contar(db_conexion, "SELECT COUNT(*) FROM partido") == partidos_antes


def test_eliminar_borra_el_partido_con_sus_filas(db_conexion):
    guardado = _uc_cargar(db_conexion).ejecutar(
        PartidoDTO(
            fecha="2026-09-01",
            idCompetencia=1,
            idCategoria=1,
            idClubLocal=1,
            idClubVisitante=2,
            cuartos=[CuartoDTO(idClub=1, nroCuarto=1, puntos=12), CuartoDTO(idClub=2, nroCuarto=1, puntos=40)],
        ),
        _propio(),
        TotalesEquipoDTO(idClub=2, puntos=40),
    )
    assert guardado is not None
    repo = SqlitePartidoRepositorio(db_conexion)
    assert [(c.idClub, c.nroCuarto, c.puntos) for c in repo.cuartos_por_partido(guardado.idPartido)] == [
        (1, 1, 12),
        (2, 1, 40),
    ]

    assert repo.eliminar(guardado.idPartido)

    assert repo.buscar_por_id(guardado.idPartido) is None
    for consulta in (
        "SELECT COUNT(*) FROM jugadorPartido WHERE idPartido = ?",
        "SELECT COUNT(*) FROM partidoCuarto WHERE idPartido = ?",
        "SELECT COUNT(*) FROM estadisticaEquipoPartido WHERE idPartido = ?",
    ):
        assert _contar(db_conexion, consulta, guardado.idPartido) == 0
    assert not repo.eliminar(guardado.idPartido)  # ya no existe
