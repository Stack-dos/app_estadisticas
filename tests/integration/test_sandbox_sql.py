import sqlite3


def test_conexion(db_conexion_sandbox):
    assert isinstance(db_conexion_sandbox, sqlite3.Connection)


def test_select(db_conexion_sandbox):
    db_conexion_sandbox.row_factory = sqlite3.Row
    cursor = db_conexion_sandbox.cursor()
    cursor.execute("SELECT * FROM v_partidos_resumen")
    partidos = cursor.fetchall()
    assert partidos is not None


def test_insert(db_conexion_sandbox):
    db_conexion_sandbox.row_factory = sqlite3.Row
    cursor = db_conexion_sandbox.cursor()

    cursor.execute(
        """
        INSERT INTO jugador (nombre, apellido, dni, anioNacimiento)
        VALUES ('Facundo', 'Campazzo', 36123456, 1991)
    """
    )
    db_conexion_sandbox.commit()  # Guardamos los cambios

    # Comprobamos que se guardó
    cursor.execute("SELECT * FROM jugador WHERE apellido = 'Campazzo'")
    facu = cursor.fetchone()
    assert facu["nombre"] == "Facundo"
    assert facu["apellido"] == "Campazzo"
    assert facu["dni"] == 36123456
    assert facu["anioNacimiento"] == 1991
