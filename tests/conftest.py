import logging
import sqlite3

import pytest

import config.rutas as ruta
from dominio.entidades.jugador import Jugador
from dominio.entidades.partido import JugadorPartido, Partido
from infraestructura.observabilidad import FiltroContexto, FiltroSecretos
from infraestructura.persistencia.database_manager import SQLiteManager


@pytest.fixture(autouse=True)
def prohibir_abrir_la_ventana(monkeypatch):
    """Ningun test abre la GUI: `ft.run` bloquea hasta que se cierra la ventana y colgaria la suite (y el CI)."""

    def _falla(*args, **kwargs):
        raise RuntimeError("Un test intento abrir la ventana de Flet (ft.run): testear sin ventana")

    monkeypatch.setattr("flet.run", _falla)


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
    """Fabrica de `Jugador` validos. Uso: crear_jugador(nombre="Otro")."""

    def _crear(**overrides) -> Jugador:
        datos = {"nombre": "Manu", "apellido": "Ginobili", "anioNacimiento": 1977}
        return Jugador(**{**datos, **overrides})

    return _crear


@pytest.fixture
def crear_partido():
    """Fabrica de `Partido` validos (clubes 1 y 2, competencia 1 y categoria 1 existen en el seed)."""

    def _crear(**overrides) -> Partido:
        datos = {
            "fecha": "2023-01-01",
            "estadio": "Estadio Principal",
            "idCompetencia": 1,
            "idCategoria": 1,
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


class _HandlerLista(logging.Handler):
    """Guarda los registros en una lista, con los mismos filtros que el handler real de la app (US-110)."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.registros: list[logging.LogRecord] = []
        self.addFilter(FiltroContexto())
        self.addFilter(FiltroSecretos())

    def emit(self, record: logging.LogRecord) -> None:
        self.registros.append(record)


@pytest.fixture
def registros_log():
    """Los registros que se loguean durante el test, ya con correlation_id, accion y secretos tapados.

    `caplog` no sirve para esto: su handler no tiene los filtros de `logger.py`.
    """
    handler = _HandlerLista()
    raiz = logging.getLogger()
    nivel = raiz.level
    raiz.addHandler(handler)
    raiz.setLevel(logging.DEBUG)
    yield handler.registros
    raiz.removeHandler(handler)
    raiz.setLevel(nivel)
