import pytest

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.dtos.club_dto import CrearClubDTO
from aplicacion.dtos.partido_dto import BoxscoreDTO, CuartoDTO, EstadisticaInputDTO, PartidoDTO
from dominio.entidades.partido import PartidoCuarto
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
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


def test_cargar_partido_use_case_flujo_completo_con_clubes_sin_usuario_y_cuartos(db_conexion):
    """US-108 AC5/AC7 integracion: carga un partido completo entre dos clubes sin vinculo con ningun usuario."""
    repo_club = SqliteClubRepositorio(db_conexion)
    repo_comp = SqliteCompetenciaRepositorio(db_conexion)
    repo_partido = SqlitePartidoRepositorio(db_conexion)

    # Creamos dos clubes de terceros sin vincular a ningun usuario (idUsuario=None)
    crear_club = CrearClubUseCase(repo_club)
    club_a = crear_club.ejecutar(CrearClubDTO(nombre="Barrio Parque"))
    club_b = crear_club.ejecutar(CrearClubDTO(nombre="Hindú"))
    assert club_a is not None and club_b is not None

    # Inscribimos ambos clubes en la competencia 1 / categoria 1 del seed y habilitamos 1 jugador por club
    cursor = db_conexion.cursor()
    cursor.execute("INSERT INTO inscripcion (idClub, idCategoria, idCompetencia) VALUES (?, 1, 1)", (club_a.idClub,))
    insc_a = cursor.lastrowid
    cursor.execute("INSERT INTO listaBuenaFe (fechaPresentacion, idInscripcion) VALUES ('2026-03-01', ?)", (insc_a,))
    lista_a = cursor.lastrowid
    cursor.execute("INSERT INTO jugadorListaBuenaFe (idJugador, idListaBuenaFe) VALUES (3, ?)", (lista_a,))

    cursor.execute("INSERT INTO inscripcion (idClub, idCategoria, idCompetencia) VALUES (?, 1, 1)", (club_b.idClub,))
    insc_b = cursor.lastrowid
    cursor.execute("INSERT INTO listaBuenaFe (fechaPresentacion, idInscripcion) VALUES ('2026-03-01', ?)", (insc_b,))
    lista_b = cursor.lastrowid
    cursor.execute("INSERT INTO jugadorListaBuenaFe (idJugador, idListaBuenaFe) VALUES (8, ?)", (lista_b,))
    db_conexion.commit()

    uc = CargarPartidoUseCase(repo_partido, repo_comp)
    partido_dto = PartidoDTO(
        fecha="2026-09-01",
        estadio="El Teatro",
        idCompetencia=1,
        idCategoria=1,
        idClubLocal=club_a.idClub,
        idClubVisitante=club_b.idClub,
        cuartos=[
            CuartoDTO(idClub=club_a.idClub, nroCuarto=1, puntos=6),
            CuartoDTO(idClub=club_a.idClub, nroCuarto=2, puntos=6),
            CuartoDTO(idClub=club_b.idClub, nroCuarto=1, puntos=4),
            CuartoDTO(idClub=club_b.idClub, nroCuarto=2, puntos=5),
        ],
    )
    box_local = BoxscoreDTO(
        idClub=club_a.idClub,
        estadisticas=[EstadisticaInputDTO(idJugador=3, minutosJugados=30.0, puntos=12, t2c=6, t2l=10)],
    )
    box_visitante = BoxscoreDTO(
        idClub=club_b.idClub,
        estadisticas=[EstadisticaInputDTO(idJugador=8, minutosJugados=28.0, puntos=9, t3c=3, t3l=6)],
    )

    guardado = uc.ejecutar(partido_dto, box_local, box_visitante)

    assert guardado is not None
    assert guardado.idPartido is not None

    # Verificamos que el boxscore y los cuartos se persistieron en la base
    boxscore_leido = ObtenerBoxscorePartidoUseCase(repo_partido).ejecutar(guardado.idPartido)
    assert len(boxscore_leido) == 2
    assert {f.puntos for f in boxscore_leido} == {12, 9}

    cursor.execute("SELECT COUNT(*) FROM partidoCuarto WHERE idPartido = ?", (guardado.idPartido,))
    assert cursor.fetchone()[0] == 4

    # Ninguno de los dos clubes quedo vinculado a usuarioClub
    cursor.execute(
        "SELECT COUNT(*) FROM usuarioClub WHERE idClub IN (?, ?)",
        (club_a.idClub, club_b.idClub),
    )
    assert cursor.fetchone()[0] == 0
