"""Tests end-to-end de la CLI: `main()` completo contra una base SQLite real en un archivo temporal.

Cada llamada a `cli(...)` simula una ejecucion separada del programa (`stats club add ...`): abre la base,
inicializa el esquema, corre el comando y termina. Que los datos de una ejecucion aparezcan en la
siguiente es justamente lo que estos tests protegen.
"""

import sqlite3
import sys

import pytest

import config.rutas as rutas
import main


@pytest.fixture
def cli(tmp_path, monkeypatch, capsys):
    """Devuelve `cli(*argv) -> (codigo_de_salida, stdout, stderr)` sobre una base temporal (no toca estadisticas.db)."""
    db_temporal = tmp_path / "e2e.db"
    monkeypatch.setattr(rutas, "DB_FILE", str(db_temporal))

    def ejecutar(*argv):
        monkeypatch.setattr(sys, "argv", ["stats", *argv])
        capsys.readouterr()  # descarta lo que haya quedado de la llamada anterior
        codigo = 0
        try:
            main.main()
        except SystemExit as salida:
            codigo = salida.code
        capturado = capsys.readouterr()
        return codigo, capturado.out, capturado.err

    ejecutar.db = db_temporal
    return ejecutar


def test_los_datos_persisten_entre_ejecuciones(cli):
    """Regresion: schema.sql empezaba con DROP TABLE y cada arranque de la CLI borraba todos los datos."""
    assert cli("club", "add", "--nombre", "Atenas") == (0, "Club creado: Atenas (id=1)\n", "")

    codigo, salida, _ = cli("club", "add", "--nombre", "Instituto")

    assert codigo == 0
    assert "id=2" in salida  # si la base se hubiera borrado, el id volveria a ser 1


def test_flujo_completo_de_punta_a_punta(cli):
    assert cli("club", "add", "--nombre", "Atenas")[0] == 0
    assert (
        cli("jugador", "add", "--nombre", "Manu", "--apellido", "Ginobili", "--anio", "1977")[1]
        == "Jugador creado: Manu Ginobili (id=1)\n"
    )

    codigo, salida, _ = cli("jugador", "link", "--id-jugador", "1", "--id-club", "1", "--fecha-desde", "2026-01-05")
    assert (codigo, salida) == (0, "Jugador 1 vinculado al club 1 desde 2026-01-05\n")

    codigo, salida, _ = cli("jugador", "list", "--id-club", "1")
    assert codigo == 0
    assert "Manu Ginobili" in salida
    assert "+---" in salida  # se muestra como tabla

    codigo, salida, _ = cli("competencia", "add", "--nombre", "Liga", "--anio", "2026", "--tipo", "PROVINCIAL")
    assert (codigo, salida) == (0, "Competencia creada: Liga 2026 (id=1)\n")

    assert cli("categoria", "add", "--nombre", "U21") == (0, "Categoria creada: U21 (id=1)\n", "")
    assert "U21" in cli("categoria", "list")[1]
    assert "Liga" in cli("competencia", "list")[1]

    codigo, salida, _ = cli(
        "competencia",
        "inscribir",
        "--id-club",
        "1",
        "--id-categoria",
        "1",
        "--id-competencia",
        "1",
        "--fecha-presentacion",
        "2026-03-01",
    )
    assert codigo == 0
    assert "lista de buena fe id=1" in salida

    # el id de la inscripcion y de su lista se pueden volver a consultar
    codigo, salida, _ = cli("inscripcion", "list", "--id-club", "1")
    assert codigo == 0
    assert "+---" in salida

    # la lista de buena fe arranca vacia, se habilita al jugador (que juega en el club) y aparece en la lista
    assert cli("lista", "list", "--id-inscripcion", "1") == (
        0,
        "La lista de buena fe de la inscripcion 1 no tiene jugadores.\n",
        "",
    )
    assert cli("lista", "add", "--id-inscripcion", "1", "--id-jugador", "1") == (
        0,
        "Jugador 1 habilitado en la lista de buena fe 1 (inscripcion 1)\n",
        "",
    )
    codigo, salida, _ = cli("lista", "list", "--id-inscripcion", "1")
    assert codigo == 0
    assert "Manu Ginobili" in salida

    # se deshace la habilitacion y la lista vuelve a quedar vacia
    assert cli("lista", "remove", "--id-inscripcion", "1", "--id-jugador", "1") == (
        0,
        "Jugador 1 quitado de la lista de buena fe 1 (inscripcion 1)\n",
        "",
    )
    assert "no tiene jugadores" in cli("lista", "list", "--id-inscripcion", "1")[1]

    assert cli("partido", "list", "--id-club", "1") == (0, "El club 1 no tiene partidos.\n", "")


def test_un_jugador_puede_cambiar_de_club_sin_pisar_el_periodo_anterior(cli):
    for paso in [
        ("club", "add", "--nombre", "Atenas"),
        ("club", "add", "--nombre", "Instituto"),
        ("jugador", "add", "--nombre", "Manu", "--apellido", "Ginobili", "--anio", "1977"),
        ("jugador", "link", "--id-jugador", "1", "--id-club", "1", "--fecha-desde", "2026-01-01"),
    ]:
        assert cli(*paso)[0] == 0

    # se lo da de baja: deja de figurar en el club 1
    assert cli("jugador", "unlink", "--id-jugador", "1", "--fecha-hasta", "2026-06-30") == (
        0,
        "Jugador 1 desvinculado del club 1 (desde 2026-01-01 hasta 2026-06-30)\n",
        "",
    )
    assert "no tiene jugadores" in cli("jugador", "list", "--id-club", "1")[1]

    # el vinculo nuevo no puede empezar antes de que termine el anterior...
    codigo, _, error = cli("jugador", "link", "--id-jugador", "1", "--id-club", "2", "--fecha-desde", "2026-06-01")
    assert codigo == 1
    assert "antes de que termine el anterior" in error

    # ...pero si despues, y entonces pasa a figurar en el club 2
    assert cli("jugador", "link", "--id-jugador", "1", "--id-club", "2", "--fecha-desde", "2026-07-01")[0] == 0
    assert "Manu Ginobili" in cli("jugador", "list", "--id-club", "2")[1]


def test_partido_list_muestra_los_nombres_de_los_clubes_y_de_la_competencia(cli):
    for paso in [
        ("club", "add", "--nombre", "Atenas"),
        ("club", "add", "--nombre", "Instituto"),
        ("competencia", "add", "--nombre", "Liga Provincial", "--anio", "2026"),
    ]:
        assert cli(*paso)[0] == 0
    # todavia no hay un comando para cargar partidos (US-105): se inserta directo en la base
    conexion = sqlite3.connect(cli.db)
    conexion.execute(
        "INSERT INTO partido (fecha, estadio, idCompetencia, idClubLocal, idClubVisitante) VALUES (?, ?, ?, ?, ?)",
        ("2026-05-21", "Cancha Atenas", 1, 1, 2),
    )
    conexion.commit()
    conexion.close()

    codigo, salida, _ = cli("partido", "list", "--id-club", "2")  # el club 2 jugo de visitante

    assert codigo == 0
    for texto in ("Atenas", "Instituto", "Liga Provincial 2026", "Cancha Atenas", "2026-05-21"):
        assert texto in salida


INSCRIPCION_DEL_CLUB_1 = [
    ("club", "add", "--nombre", "Atenas"),
    ("jugador", "add", "--nombre", "A", "--apellido", "B", "--anio", "1990"),
    ("competencia", "add", "--nombre", "Liga", "--anio", "2026"),
    ("categoria", "add", "--nombre", "U21"),
    (
        "competencia",
        "inscribir",
        "--id-club",
        "1",
        "--id-categoria",
        "1",
        "--id-competencia",
        "1",
        "--fecha-presentacion",
        "2026-03-01",
    ),
]


@pytest.mark.parametrize(
    "preparacion, comando, mensaje",
    [
        pytest.param(
            [],
            ("jugador", "link", "--id-jugador", "99", "--id-club", "1", "--fecha-desde", "2026-01-01"),
            "No existe un jugador con idJugador=99",
            id="jugador inexistente",
        ),
        pytest.param(
            [
                ("club", "add", "--nombre", "Atenas"),
                ("club", "add", "--nombre", "Instituto"),
                ("jugador", "add", "--nombre", "A", "--apellido", "B", "--anio", "1990"),
                ("jugador", "link", "--id-jugador", "1", "--id-club", "1", "--fecha-desde", "2026-01-01"),
            ],
            ("jugador", "link", "--id-jugador", "1", "--id-club", "2", "--fecha-desde", "2026-02-01"),
            "tiene un club activo",
            id="jugador que ya tiene club activo",
        ),
        pytest.param(
            [("categoria", "add", "--nombre", "U21")],
            ("categoria", "add", "--nombre", " u21"),
            "Ya existe una categoria",
            id="categoria repetida",
        ),
        pytest.param(
            [],
            ("lista", "add", "--id-inscripcion", "7", "--id-jugador", "1"),
            "No existe una inscripcion con idInscripcion=7",
            id="lista de una inscripcion inexistente",
        ),
        pytest.param(
            [
                ("club", "add", "--nombre", "Atenas"),
                ("jugador", "add", "--nombre", "A", "--apellido", "B", "--anio", "1990"),
                ("competencia", "add", "--nombre", "Liga", "--anio", "2026"),
                ("categoria", "add", "--nombre", "U21"),
                (
                    "competencia",
                    "inscribir",
                    "--id-club",
                    "1",
                    "--id-categoria",
                    "1",
                    "--id-competencia",
                    "1",
                    "--fecha-presentacion",
                    "2026-03-01",
                ),
            ],
            ("lista", "add", "--id-inscripcion", "1", "--id-jugador", "1"),
            "no tiene un vinculo vigente con el club",
            id="jugador que no juega en el club de la inscripcion",
        ),
        pytest.param(
            [],
            ("competencia", "add", "--nombre", "Vieja", "--anio", "1900"),
            "Año debe ser mayor que 1900",
            id="anio de competencia invalido",
        ),
        pytest.param(
            [], ("club", "add", "--nombre", ""), "El nombre del club no puede estar vacio", id="club sin nombre"
        ),
        pytest.param(
            [],
            ("jugador", "add", "--nombre", "A", "--apellido", "B", "--anio", "3000"),
            "El año de nacimiento debe estar entre",
            id="anio de nacimiento imposible",
        ),
        pytest.param(
            [("jugador", "add", "--nombre", "A", "--apellido", "B", "--anio", "1990")],
            ("jugador", "unlink", "--id-jugador", "1", "--fecha-hasta", "2026-06-30"),
            "no tiene un club activo",
            id="desvincular a un jugador sin club",
        ),
        pytest.param(
            INSCRIPCION_DEL_CLUB_1,
            ("lista", "remove", "--id-inscripcion", "1", "--id-jugador", "1"),
            "no esta en la lista de buena fe",
            id="quitar de la lista a quien no esta",
        ),
    ],
)
def test_los_errores_de_negocio_salen_como_mensaje_con_codigo_1_y_sin_traceback(cli, preparacion, comando, mensaje):
    for paso in preparacion:
        assert cli(*paso)[0] == 0

    codigo, salida, error = cli(*comando)

    assert codigo == 1
    assert salida == ""
    assert error.startswith("Error:")
    assert mensaje in error
    assert "Traceback" not in error
