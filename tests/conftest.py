import sqlite3

import pytest

import config.rutas as ruta
from dominio.entidades.jugador import Jugador
from dominio.entidades.partido import JugadorPartido, Partido
from infraestructura.persistencia.database_manager import SQLiteManager


@pytest.fixture
def db_conexion():
    conexion = sqlite3.connect(":memory:")
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open(ruta.SCHEMA_SQL) as schema:
        cursor.executescript(schema.read())

    with open(ruta.VISTA_SQL) as schema:
        cursor.executescript(schema.read())

    with open(ruta.SEED_SQL) as seed:
        cursor.executescript(seed.read())
    conexion.row_factory = sqlite3.Row

    yield conexion
    conexion.close()


@pytest.fixture
def db_conexion_sin_seed():
    conexion = sqlite3.connect(":memory:")
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    with open(ruta.SCHEMA_SQL) as schema:
        cursor.executescript(schema.read())

    with open(ruta.VISTA_SQL) as schema:
        cursor.executescript(schema.read())

    conexion.row_factory = sqlite3.Row

    yield conexion
    conexion.close()


@pytest.fixture
def db_conexion_sandbox():
    manager = SQLiteManager(
        db_path=":memory:",
        schema_path=ruta.SCHEMA_SQL,
        views_path=ruta.VISTA_SQL,
        seed_path=ruta.SEED_SQL,
    )

    conexion = manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()

    yield conexion
    conexion.close()


# --------------------------------------------------------------------------------------
# Fabricas de datos de prueba (patron **overrides)
#
# Cada fabrica devuelve una funcion que arma una entidad VALIDA con valores por defecto;
# el test solo pisa (override) el campo que le importa:
#     crear_boxscore(idJugador=999999)   # igual que el default, pero con un jugador inexistente
# --------------------------------------------------------------------------------------


@pytest.fixture
def crear_jugador():
    """Fabrica de `Jugador` validos. Uso: crear_jugador(dni=123, nombre="Otro")."""

    def _crear(**overrides) -> Jugador:
        datos = {"nombre": "Manu", "apellido": "Ginobili", "dni": 20111222, "anioNacimiento": 1977}
        return Jugador(**{**datos, **overrides})

    return _crear


@pytest.fixture
def crear_partido():
    """Fabrica de `Partido` validos (clubes 1 y 2 y competencia 1 existen en el seed)."""

    def _crear(**overrides) -> Partido:
        datos = {
            "fecha": "2023-01-01",
            "estadio": "Estadio Principal",
            "idCompetencia": 1,
            "idClubLocal": 1,
            "idClubVisitante": 2,
        }
        return Partido(**{**datos, **overrides})

    return _crear


@pytest.fixture
def crear_boxscore():
    """Fabrica de `JugadorPartido` validos. Los puntos por defecto (9) cumplen T2C*2 + T3C*3 + T1C.

    Ojo: si el test cambia t2c, t3c o t1c tiene que pisar tambien `puntos` para que siga siendo valido.
    """

    def _crear(**overrides) -> JugadorPartido:
        datos = {
            "idJugador": 1,
            "idPartido": 2,
            "idClub": 1,
            "minutosJugados": 20.0,
            "puntos": 9,
            "t2c": 2,
            "t2l": 5,
            "t3c": 1,
            "t3l": 5,
            "t1c": 2,
            "t1l": 5,
            "rebotesDef": 4,
            "rebotesOf": 2,
            "asistencias": 5,
            "recuperos": 3,
            "perdidas": 2,
            "taponesRecibidos": 1,
            "taponesRealizados": 2,
            "faltasRecibidas": 4,
            "faltasCometidas": 3,
        }
        return JugadorPartido(**{**datos, **overrides})

    return _crear
