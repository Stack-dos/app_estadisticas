"""US-107, AC5 (lado base): la tabla competenciaCategoria y la FK compuesta de inscripcion.

La base rechaza por si sola una inscripcion en una categoria que la competencia no juega, aunque alguien se
saltee el caso de uso. Usa el seed: competencia 1 juega la categoria 1 y los clubes 1 y 2 estan inscriptos ahi.
"""

import sqlite3

import pytest


def _inscribir(conexion, id_club: int, id_categoria: int, id_competencia: int) -> None:
    conexion.execute(
        "INSERT INTO inscripcion (idClub, idCategoria, idCompetencia) VALUES (?, ?, ?)",
        (id_club, id_categoria, id_competencia),
    )


def _contar(conexion, sql: str, parametros: tuple = ()) -> int:
    return conexion.execute(sql, parametros).fetchone()[0]


@pytest.fixture
def con_categoria_nueva(db_conexion):
    """Seed + una categoria U17 (id 2) que la competencia 1 todavia no juega."""
    db_conexion.execute("INSERT INTO categoria (idCategoria, nombre) VALUES (2, 'U17')")
    return db_conexion


def test_inscribir_en_categoria_no_habilitada_falla(con_categoria_nueva):
    with pytest.raises(sqlite3.IntegrityError):
        _inscribir(con_categoria_nueva, 1, 2, 1)


def test_inscribir_despues_de_habilitar_la_categoria_funciona(con_categoria_nueva):
    con_categoria_nueva.execute("INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (1, 2)")

    _inscribir(con_categoria_nueva, 1, 2, 1)

    assert _contar(con_categoria_nueva, "SELECT COUNT(*) FROM inscripcion WHERE idCategoria = 2") == 1


def test_no_se_habilita_dos_veces_la_misma_categoria(db_conexion):
    with pytest.raises(sqlite3.IntegrityError):
        db_conexion.execute("INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (1, 1)")


@pytest.mark.parametrize(
    ("id_competencia", "id_categoria"),
    [(99, 1), (1, 99)],
    ids=["competencia-inexistente", "categoria-inexistente"],
)
def test_no_se_habilita_una_competencia_o_categoria_inexistente(db_conexion, id_competencia, id_categoria):
    with pytest.raises(sqlite3.IntegrityError):
        db_conexion.execute(
            "INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (?, ?)",
            (id_competencia, id_categoria),
        )


def test_quitar_una_categoria_con_inscriptos_falla(db_conexion):
    with pytest.raises(sqlite3.IntegrityError):
        db_conexion.execute("DELETE FROM competenciaCategoria WHERE idCompetencia = 1 AND idCategoria = 1")


def test_quitar_una_categoria_sin_inscriptos_funciona(con_categoria_nueva):
    con_categoria_nueva.execute("INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (1, 2)")

    con_categoria_nueva.execute("DELETE FROM competenciaCategoria WHERE idCompetencia = 1 AND idCategoria = 2")

    assert _contar(con_categoria_nueva, "SELECT COUNT(*) FROM competenciaCategoria WHERE idCategoria = 2") == 0


def test_borrar_la_competencia_borra_en_cascada_inscripciones_y_categorias(db_conexion_sin_seed):
    """Con NO ACTION (y no RESTRICT) en la FK compuesta, la cascada no depende del orden en que SQLite la recorre.

    Sin seed: en el seed la competencia 1 tiene partidos con estadisticas, y jugadorPartido (RESTRICT) frenaria
    el borrado.
    """
    conexion = db_conexion_sin_seed
    conexion.execute("INSERT INTO club (nombre) VALUES ('Atenas')")
    conexion.execute("INSERT INTO categoria (nombre) VALUES ('U17')")
    conexion.execute("INSERT INTO competencia (nombre, anio) VALUES ('Liga 2026', 2026)")
    conexion.execute("INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (1, 1)")
    _inscribir(conexion, 1, 1, 1)

    conexion.execute("DELETE FROM competencia WHERE idCompetencia = 1")

    assert _contar(conexion, "SELECT COUNT(*) FROM inscripcion") == 0
    assert _contar(conexion, "SELECT COUNT(*) FROM competenciaCategoria") == 0
