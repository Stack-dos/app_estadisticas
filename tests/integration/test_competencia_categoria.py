"""US-107, AC5 (lado base): la tabla competenciaCategoria y la FK compuesta de inscripcion.

La base rechaza por si sola una inscripcion en una categoria que la competencia no juega, aunque alguien se
saltee el caso de uso. Usa el seed: competencia 1 juega la categoria 1 y los clubes 1 y 2 estan inscriptos ahi.
"""

import sqlite3

import pytest

from dominio.entidades.competencia import Competencia
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio


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


# --- Repositorio (US-107, paso 2) ---


def _nombres(categorias) -> list[str]:
    return [c.nombre for c in categorias]


def test_repo_habilitar_listar_y_quitar(con_categoria_nueva):
    repo = SqliteCompetenciaRepositorio(con_categoria_nueva)

    assert repo.habilitar_categoria(1, 2) is True
    assert _nombres(repo.obtener_categorias_de_competencia(1)) == ["U17", "U21"]

    assert repo.quitar_categoria(1, 2) is True
    assert _nombres(repo.obtener_categorias_de_competencia(1)) == ["U21"]


def test_repo_habilitar_dos_veces_devuelve_false(db_conexion):
    assert SqliteCompetenciaRepositorio(db_conexion).habilitar_categoria(1, 1) is False


def test_repo_quitar_categoria_no_habilitada_devuelve_false(con_categoria_nueva):
    assert SqliteCompetenciaRepositorio(con_categoria_nueva).quitar_categoria(1, 2) is False


def test_repo_quitar_categoria_con_inscriptos_devuelve_false_y_no_la_quita(db_conexion):
    repo = SqliteCompetenciaRepositorio(db_conexion)

    assert repo.quitar_categoria(1, 1) is False
    assert _nombres(repo.obtener_categorias_de_competencia(1)) == ["U21"]


def test_repo_obtener_categorias_de_competencia_sin_categorias(db_conexion):
    assert SqliteCompetenciaRepositorio(db_conexion).obtener_categorias_de_competencia(99) == []


def test_repo_tiene_inscripciones(con_categoria_nueva):
    repo = SqliteCompetenciaRepositorio(con_categoria_nueva)
    repo.habilitar_categoria(1, 2)

    assert repo.tiene_inscripciones(1, 1) is True
    assert repo.tiene_inscripciones(1, 2) is False


@pytest.mark.parametrize("id_categorias", [[1, 2], []], ids=["con-categorias", "sin-categorias"])
def test_repo_guardar_competencia_con_categorias(con_categoria_nueva, id_categorias):
    repo = SqliteCompetenciaRepositorio(con_categoria_nueva)

    guardada = repo.guardar_competencia_con_categorias(
        Competencia(nombre="Asociativo 2027", anio=2027, tipo="ASOCIATIVO"), id_categorias
    )

    assert guardada is not None and guardada.idCompetencia is not None
    habilitadas = [c.idCategoria for c in repo.obtener_categorias_de_competencia(guardada.idCompetencia)]
    assert sorted(habilitadas) == sorted(id_categorias)


@pytest.mark.parametrize("id_categorias", [[1, 99], [1, 1]], ids=["categoria-inexistente", "categoria-repetida"])
def test_repo_guardar_competencia_con_categorias_es_atomica(db_conexion, id_categorias):
    """Si falla una categoria, no queda ni la competencia ni las categorias que si se habian insertado."""
    repo = SqliteCompetenciaRepositorio(db_conexion)
    competencias_antes = _contar(db_conexion, "SELECT COUNT(*) FROM competencia")
    habilitadas_antes = _contar(db_conexion, "SELECT COUNT(*) FROM competenciaCategoria")

    resultado = repo.guardar_competencia_con_categorias(
        Competencia(nombre="Torneo Rollback", anio=2027, tipo="ASOCIATIVO"), id_categorias
    )

    assert resultado is None
    assert _contar(db_conexion, "SELECT COUNT(*) FROM competencia") == competencias_antes
    assert _contar(db_conexion, "SELECT COUNT(*) FROM competenciaCategoria") == habilitadas_antes
