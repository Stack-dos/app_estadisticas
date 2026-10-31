"""Tests unitarios del punto de entrada de la CLI (`src/main.py`): el parser y el manejo de errores.

Ningun test toca la base real: `main()` se prueba con `inicializar_db` reemplazada por una funcion vacia.
"""

import sys
from unittest.mock import MagicMock

import pytest

import main
from dominio.exceptions import DNIDuplicadoError
from infraestructura.ui.cli.commands import (
    auth_login,
    auth_logout,
    auth_register,
    categoria_add,
    categoria_list,
    club_add,
    club_list,
    competencia_add,
    competencia_inscribir,
    competencia_list,
    game_list,
    inscripcion_list,
    jugador_add,
    jugador_link,
    jugador_list,
    jugador_unlink,
    lista_add,
    lista_list,
    lista_remove,
)


@pytest.mark.parametrize(
    "argv, funcion, esperado",
    [
        pytest.param(
            ["auth", "register", "--nombre", "Entrenador", "--email", "coach@test.com", "--password", "secreta123"],
            auth_register.ejecutar,
            {"nombre": "Entrenador", "email": "coach@test.com", "password": "secreta123"},
            id="auth register",
        ),
        pytest.param(
            ["auth", "login", "--email", "coach@test.com", "--password", "secreta123"],
            auth_login.ejecutar,
            {"email": "coach@test.com", "password": "secreta123"},
            id="auth login",
        ),
        pytest.param(
            ["auth", "logout"],
            auth_logout.ejecutar,
            {},
            id="auth logout",
        ),
        pytest.param(["club", "add", "--nombre", "Atenas"], club_add.ejecutar, {"nombre": "Atenas"}, id="club add"),
        pytest.param(["club", "list", "--id-usuario", "10"], club_list.ejecutar, {"id_usuario": 10}, id="club list"),
        pytest.param(
            ["jugador", "add", "--nombre", "Manu", "--apellido", "Ginobili", "--dni", "20111222", "--anio", "1977"],
            jugador_add.ejecutar,
            {"nombre": "Manu", "apellido": "Ginobili", "dni": 20111222, "anio": 1977},
            id="jugador add",
        ),
        pytest.param(
            ["jugador", "link", "--id-jugador", "1", "--id-club", "2", "--fecha-desde", "2026-1-5"],
            jugador_link.ejecutar,
            {"id_jugador": 1, "id_club": 2, "fecha_desde": "2026-01-05"},  # la fecha se normaliza
            id="jugador link",
        ),
        pytest.param(["jugador", "list", "--id-club", "2"], jugador_list.ejecutar, {"id_club": 2}, id="jugador list"),
        pytest.param(
            ["competencia", "add", "--nombre", "Liga", "--anio", "2026", "--tipo", "PROVINCIAL"],
            competencia_add.ejecutar,
            {"nombre": "Liga", "anio": 2026, "tipo": "PROVINCIAL"},
            id="competencia add",
        ),
        pytest.param(
            ["competencia", "add", "--nombre", "Liga", "--anio", "2026"],
            competencia_add.ejecutar,
            {"nombre": "Liga", "anio": 2026, "tipo": None},  # --tipo es opcional
            id="competencia add sin tipo",
        ),
        pytest.param(
            [
                "competencia",
                "inscribir",
                "--id-club",
                "1",
                "--id-categoria",
                "2",
                "--id-competencia",
                "3",
                "--fecha-presentacion",
                "2026-03-01",
            ],
            competencia_inscribir.ejecutar,
            {"id_club": 1, "id_categoria": 2, "id_competencia": 3, "fecha_presentacion": "2026-03-01"},
            id="competencia inscribir",
        ),
        pytest.param(["partido", "list", "--id-club", "1"], game_list.ejecutar, {"id_club": 1}, id="partido list"),
        pytest.param(["competencia", "list"], competencia_list.ejecutar, {}, id="competencia list"),
        pytest.param(
            ["categoria", "add", "--nombre", "U21"], categoria_add.ejecutar, {"nombre": "U21"}, id="categoria add"
        ),
        pytest.param(["categoria", "list"], categoria_list.ejecutar, {}, id="categoria list"),
        pytest.param(
            ["inscripcion", "list", "--id-club", "1"], inscripcion_list.ejecutar, {"id_club": 1}, id="inscripcion list"
        ),
        pytest.param(
            ["lista", "add", "--id-inscripcion", "5", "--id-jugador", "3"],
            lista_add.ejecutar,
            {"id_inscripcion": 5, "id_jugador": 3},
            id="lista add",
        ),
        pytest.param(
            ["lista", "list", "--id-inscripcion", "5"], lista_list.ejecutar, {"id_inscripcion": 5}, id="lista list"
        ),
        pytest.param(
            ["lista", "remove", "--id-inscripcion", "5", "--id-jugador", "3"],
            lista_remove.ejecutar,
            {"id_inscripcion": 5, "id_jugador": 3},
            id="lista remove",
        ),
        pytest.param(
            ["jugador", "unlink", "--id-jugador", "1", "--fecha-hasta", "2026-6-30"],
            jugador_unlink.ejecutar,
            {"id_jugador": 1, "fecha_hasta": "2026-06-30"},  # la fecha se normaliza
            id="jugador unlink",
        ),
    ],
)
def test_parser_asocia_cada_comando_con_su_funcion_y_sus_argumentos(argv, funcion, esperado):
    args = main.construir_parser().parse_args(argv)

    assert args.func is funcion
    for nombre, valor in esperado.items():
        assert getattr(args, nombre) == valor


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["auth"], id="auth sin subcomando"),
        pytest.param(["auth", "register", "--nombre", "Profe"], id="auth register sin email ni password"),
        pytest.param(["auth", "login", "--email", "profe@test.com"], id="auth login sin password"),
        pytest.param(["club"], id="grupo sin subcomando"),
        pytest.param(["club", "add"], id="falta --nombre"),
        pytest.param(["jugador", "add", "--nombre", "Manu"], id="faltan apellido, dni y anio"),
        pytest.param(["jugador", "link", "--id-jugador", "1", "--id-club", "2"], id="falta --fecha-desde"),
        pytest.param(["jugador", "list", "--id-club", "no-es-un-numero"], id="id que no es numero"),
        pytest.param(["competencia", "add", "--nombre", "Liga", "--anio", "dos-mil"], id="anio que no es numero"),
        pytest.param(["categoria", "add"], id="categoria add sin nombre"),
        pytest.param(["lista", "add", "--id-inscripcion", "5"], id="lista add sin jugador"),
        pytest.param(["lista", "list"], id="lista list sin inscripcion"),
        pytest.param(["inscripcion", "list"], id="inscripcion list sin club"),
        pytest.param(["lista", "remove", "--id-inscripcion", "5"], id="lista remove sin jugador"),
        pytest.param(["jugador", "unlink", "--id-jugador", "1"], id="jugador unlink sin fecha"),
    ],
)
def test_parser_rechaza_argumentos_incorrectos_con_codigo_2(argv, capsys):
    with pytest.raises(SystemExit) as info:
        main.construir_parser().parse_args(argv)

    assert info.value.code == 2  # codigo de salida estandar de argparse para "uso incorrecto"
    assert "usage:" in capsys.readouterr().err


def test_parser_rechaza_una_fecha_con_formato_incorrecto(capsys):
    argv = ["jugador", "link", "--id-jugador", "1", "--id-club", "2", "--fecha-desde", "31-12-2026"]

    with pytest.raises(SystemExit) as info:
        main.construir_parser().parse_args(argv)

    assert info.value.code == 2
    assert "AAAA-MM-DD" in capsys.readouterr().err


# ------------------------------------------------------------------ main()


@pytest.fixture
def cli_sin_base(monkeypatch):
    """Evita que main() abra o modifique la base de datos real, y deja elegir los argumentos de la CLI."""
    monkeypatch.setattr(main, "inicializar_db", lambda: None)

    def con_argumentos(*argv):
        monkeypatch.setattr(sys, "argv", ["stats", *argv])

    return con_argumentos


def test_main_ejecuta_el_comando_elegido_con_los_argumentos_parseados(monkeypatch, cli_sin_base):
    comando = MagicMock()
    monkeypatch.setattr(club_add, "ejecutar", comando)
    cli_sin_base("club", "add", "--nombre", "Atenas")

    main.main()

    comando.assert_called_once()
    assert comando.call_args.args[0].nombre == "Atenas"


def test_main_muestra_un_error_de_dominio_sin_traceback_y_sale_con_codigo_1(monkeypatch, cli_sin_base, capsys):
    monkeypatch.setattr(club_add, "ejecutar", MagicMock(side_effect=DNIDuplicadoError("Ya existe ese DNI")))
    cli_sin_base("club", "add", "--nombre", "Atenas")

    with pytest.raises(SystemExit) as info:
        main.main()

    salida = capsys.readouterr()
    assert info.value.code == 1
    assert salida.err == "Error: Ya existe ese DNI\n"
    assert "Traceback" not in salida.err


def test_main_no_esconde_los_errores_que_no_son_de_dominio(monkeypatch, cli_sin_base):
    # Un bug real (RuntimeError) tiene que verse con su traceback: solo ErrorDeDominio se traduce a mensaje.
    monkeypatch.setattr(club_add, "ejecutar", MagicMock(side_effect=RuntimeError("bug")))
    cli_sin_base("club", "add", "--nombre", "Atenas")

    with pytest.raises(RuntimeError, match="bug"):
        main.main()


def test_main_sin_argumentos_muestra_la_ayuda(cli_sin_base, capsys):
    cli_sin_base()

    main.main()

    assert "usage: stats" in capsys.readouterr().out
