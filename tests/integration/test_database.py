import sqlite3

import pytest

import config.rutas as ruta
from infraestructura.persistencia.database_manager import SQLiteManager


def test_schema_sql_ejecuta_sin_errores():
    """Smoke test: schema.sql se aplica en DB vacía sin excepciones."""
    conexion = sqlite3.connect(":memory:")
    conexion.execute("PRAGMA foreign_keys = ON;")
    with open(ruta.SCHEMA_SQL, encoding="utf-8") as f:
        conexion.executescript(f.read())
    conexion.close()


def test_views_sql_ejecuta_sin_errores():
    """Smoke test: views.sql se aplica luego del schema sin excepciones."""
    conexion = sqlite3.connect(":memory:")
    with open(ruta.SCHEMA_SQL, encoding="utf-8") as f:
        conexion.executescript(f.read())
    with open(ruta.VISTA_SQL, encoding="utf-8") as f:
        conexion.executescript(f.read())
    conexion.close()


def test_seed_sql_ejecuta_sin_errores():
    """Smoke test: seed.sql se aplica luego del schema+vistas sin excepciones."""
    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL, ruta.SEED_SQL)
    manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()
    manager.close_connection()


def test_database_schema(db_conexion_sin_seed):
    """
    Test destinado a verificar que se creen las tablas especificadas en en schenma
    """

    tablas_esperadas = {
        "usuario",
        "club",
        "usuarioClub",
        "jugador",
        "jugadorClub",
        "competencia",
        "inscripcion",
        "listaBuenaFe",
        "jugadorListaBuenaFe",
        "partido",
        "jugadorPartido",
        "categoria",
    }

    cursor = db_conexion_sin_seed.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tablas_existentes = {row[0] for row in cursor.fetchall()}

    faltan = tablas_esperadas - tablas_existentes
    assert not faltan, f"Error: No se encontraron las tablas: {faltan}"


def test_database_schema_view(db_conexion_sin_seed):
    """
    Test destinado a verificar que se generen las vistas especificadas en el archivo sql
    """

    vistas_esperadas = {
        "v_jugador_totales_temporada",
        "v_listas_detalle",
        "v_boxscore_completo",
        "v_partidos_resumen",
    }

    cursor = db_conexion_sin_seed.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")

    vistas_existentes = {row[0] for row in cursor.fetchall()}

    faltan = vistas_esperadas - vistas_existentes
    assert not faltan, f"Error: No se encontraron las vistas: {faltan}"


def test_referential_integrity(db_conexion_sin_seed):
    # Intentar insertar un registro con una categoría que NO existe (id: 999)
    # Debe lanzar un sqlite3.IntegrityError
    db_cursor = db_conexion_sin_seed.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        db_cursor.execute(
            "INSERT INTO listaBuenaFe (fechaPresentacion, idInscripcion) VALUES (?, ?)",
            ("2026-03-21", 1),
        )


@pytest.mark.parametrize(
    "sentencia, parametros",
    [
        pytest.param(
            """
            INSERT INTO jugadorPartido
            (idJugador, idPartido, idClub, minutosJugados, T2C, T2L, T3C)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (1, 1, 1, 20, -20, -10, -30),
            id="estadisticas-negativas",
        ),
        pytest.param(
            """
            INSERT INTO jugadorPartido
            (idJugador, idPartido, idClub, minutosJugados)
            VALUES (?, ?, ?, ?)
            """,
            (1, 1, 1, 49),
            id="registro-incompleto-con-minutos-mayores-a-48",
        ),
    ],
)
def test_check_constraints(db_conexion_sin_seed, sentencia, parametros):
    """
    Test destinado a verificar que se cumplan los CHECK definidos en la DB
    """

    db_cursor = db_conexion_sin_seed.cursor()
    db_cursor.execute("PRAGMA foreign_keys = OFF;")

    with pytest.raises(sqlite3.IntegrityError):
        db_cursor.execute(sentencia, parametros)


def test_close_connection_cierra_la_conexion():
    """
    Test para verificar el cierre correcto de conexion
    """

    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL)
    conexion = manager.connect()

    manager.close_connection()

    with pytest.raises(sqlite3.ProgrammingError):
        conexion.execute("SELECT 1")


def test_limpieza_elimina_datos_de_seed():
    """
    Test que verifica la limpieza correcta de los datos seed
    """

    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL, ruta.SEED_SQL, ruta.CLEAR_SQL)
    conexion = manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()

    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuario WHERE nombre = ?", ("juan salvatierra",))
    assert cursor.fetchone()[0] == 1

    manager.limpieza()

    cursor.execute("SELECT COUNT(*) FROM usuario WHERE nombre = ?", ("juan salvatierra",))
    assert cursor.fetchone()[0] == 0


def test_seed_execution_devuelve_datos_en_vistas():
    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL, ruta.SEED_SQL)
    conexion = manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()

    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM v_partidos_resumen")

    assert cursor.fetchone()[0] > 0


def test_division_by_zero_devuelve_cero_en_vistas():
    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL, ruta.SEED_SQL)
    conexion = manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()

    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO jugador (nombre, apellido, dni, anioNacimiento)
        VALUES (?, ?, ?, ?)
        """,
        ("Jugador", "Cero", 99999999, 2000),
    )
    id_jugador = cursor.lastrowid

    cursor.execute("SELECT idClub FROM club WHERE nombre = ?", ("Atenas",))
    id_club = cursor.fetchone()[0]
    cursor.execute("SELECT idPartido FROM partido WHERE fecha = ?", ("2026-05-21",))
    id_partido = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO jugadorPartido (
            idJugador, idPartido, idClub, minutosJugados, puntos, T2C, T2L, T3C, T3L,
            T1C, T1L, rebotesDef, rebotesOf, asistencias, recuperos, perdidas,
            taponesRecibidos, taponesRealizados, faltasRecibidas, faltasCometidas
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_jugador,
            id_partido,
            id_club,
            10,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
    )

    cursor.execute(
        """
        SELECT porcentaje_t2, porcentaje_t3, porcentaje_t1
        FROM v_jugador_totales_temporada
        WHERE nombre_jugador = ?
        """,
        ("Jugador Cero",),
    )
    porcentaje_t2, porcentaje_t3, porcentaje_t1 = cursor.fetchone()

    assert porcentaje_t2 == 0.0
    assert porcentaje_t3 == 0.0
    assert porcentaje_t1 == 0.0


@pytest.fixture
def db_con_datos_base(db_conexion_sin_seed):
    """Datos previos que necesitan las restricciones de negocio: 2 clubes, 1 competencia, 1 jugador y 1 partido."""
    cursor = db_conexion_sin_seed.cursor()
    cursor.execute("INSERT INTO club (nombre) VALUES ('Atenas')")
    cursor.execute("INSERT INTO club (nombre) VALUES ('Instituto')")
    cursor.execute("INSERT INTO competencia (nombre, anio) VALUES ('Liga 2026', 2026)")
    cursor.execute("INSERT INTO jugador (nombre, apellido) VALUES ('Facundo', 'Campazzo')")
    cursor.execute(
        "INSERT INTO partido (fecha, idCompetencia, idClubLocal, idClubVisitante) VALUES (?, ?, ?, ?)",
        ("2026-01-01", 1, 1, 2),
    )
    return db_conexion_sin_seed


@pytest.mark.parametrize(
    "sentencia, parametros",
    [
        pytest.param(
            "INSERT INTO partido (fecha, idCompetencia, idClubLocal, idClubVisitante) VALUES (?, ?, ?, ?)",
            ("2026-01-01", 1, 1, 1),  # ID local == ID visitante
            id="club-local-igual-al-visitante",
        ),
        pytest.param(
            "INSERT INTO jugadorPartido (idJugador, idPartido, idClub, T2C, T2L) VALUES (?, ?, ?, ?, ?)",
            (1, 1, 1, 10, 5),  # 10 convertidos, 5 lanzados (IMPOSIBLE)
            id="tiros-convertidos-mayores-a-lanzados",
        ),
        pytest.param(
            "INSERT INTO competencia (nombre, anio) VALUES (?, ?)",
            ("Torneo Prehistorico", 1850),
            id="anio-de-competencia-muy-anterior-a-1900",
        ),
        pytest.param(
            "INSERT INTO competencia (nombre, anio) VALUES (?, ?)",
            ("Torneo 1900", 1900),  # el CHECK es anio > 1900: el limite mismo se rechaza (igual que la entidad)
            id="anio-de-competencia-igual-a-1900",
        ),
    ],
)
def test_business_constraints(db_con_datos_base, sentencia, parametros):
    with pytest.raises(sqlite3.IntegrityError):
        db_con_datos_base.execute(sentencia, parametros)


def test_foreign_key_behavior(db_conexion_sin_seed):
    cursor = db_conexion_sin_seed.cursor()

    # Setup datos iniciales
    cursor.execute("INSERT INTO club (nombre) VALUES ('Atenas')")
    cursor.execute("INSERT INTO categoria (nombre) VALUES ('U21')")
    cursor.execute("INSERT INTO competencia (nombre, anio) VALUES ('Liga 2026', 2026)")
    cursor.execute("INSERT INTO inscripcion (idClub, idCategoria, idCompetencia) VALUES (1, 1, 1)")

    # 1. CASCADE: Al borrar competencia, se debe borrar la inscripción automáticamente
    cursor.execute("DELETE FROM competencia WHERE idCompetencia = 1")
    cursor.execute("SELECT COUNT(*) FROM inscripcion WHERE idCompetencia = 1")
    assert cursor.fetchone()[0] == 0

    # 2. RESTRICT: No se puede borrar un club si tiene registros en jugadorPartido
    # Re-insertamos datos necesarios
    cursor.execute("INSERT INTO club (nombre) VALUES ('Instituto')")  # idClub = 2
    cursor.execute("INSERT INTO competencia (nombre, anio) VALUES ('Liga 2026 B', 2026)")  # idCompetencia = 2
    cursor.execute(
        """
        INSERT INTO partido (fecha, idCompetencia, idClubLocal, idClubVisitante)
        VALUES (?, ?, ?, ?)
        """,
        ("2026-01-01", 2, 1, 2),  # Local=1, Visitante=2
    )
    cursor.execute("INSERT INTO jugador (nombre, apellido) VALUES ('John', 'Doe')")
    cursor.execute(
        """
        INSERT INTO jugadorPartido (idJugador, idPartido, idClub, puntos)
        VALUES (1, 1, 1, 10)
        """
    )

    # Intentar borrar el club (debe fallar por el RESTRICT en jugadorPartido)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("DELETE FROM club WHERE idClub = 1")


def test_view_semantics_and_cardinality():
    # Setup: Inicializar con datos semilla
    manager = SQLiteManager(":memory:", ruta.SCHEMA_SQL, ruta.VISTA_SQL, ruta.SEED_SQL)
    conexion = manager.connect()
    manager.inicializar_schema()
    manager.cargar_seed()
    cursor = conexion.cursor()

    # 1. Validar v_partidos_resumen
    cursor.execute("SELECT * FROM v_partidos_resumen")
    columnas = [description[0] for description in cursor.description]
    datos = cursor.fetchall()
    assert set(columnas) == {
        "id_partido",
        "fecha_partido",
        "estadio",
        "competencia",
        "anio_competencia",
        "id_club_local",
        "club_local",
        "id_club_visitante",
        "club_visitante",
    }
    assert len(datos) > 0  # Hay partidos en el seed

    # 2. Validar v_boxscore_completo
    cursor.execute("SELECT * FROM v_boxscore_completo")
    columnas = [description[0] for description in cursor.description]
    datos = cursor.fetchall()
    assert "nombre_jugador" in columnas
    assert "puntos" in columnas
    assert "rebotes_totales" in columnas
    assert len(datos) > 0  # Hay registros de estadísticas en el seed

    # 3. Validar v_jugador_totales_temporada
    cursor.execute("SELECT * FROM v_jugador_totales_temporada")
    columnas = [description[0] for description in cursor.description]
    datos = cursor.fetchall()
    assert "total_puntos" in columnas
    assert "porcentaje_t3" in columnas
    assert "total_rebotes" in columnas
    assert len(datos) > 0  # Jugadores distintos con estadísticas

    # 4. Validar v_listas_detalle
    cursor.execute("SELECT * FROM v_listas_detalle")
    columnas = [description[0] for description in cursor.description]
    datos = cursor.fetchall()
    assert set(columnas) == {
        "id_inscripcion",
        "nombre_club",
        "nombre_categoria",
        "nombre_competencia",
        "nombre_jugador",
    }
    assert len(datos) > 0  # Jugadores en listas de buena fe
