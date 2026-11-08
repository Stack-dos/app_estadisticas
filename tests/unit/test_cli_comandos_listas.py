"""Tests unitarios de los comandos de categorias, competencias, inscripciones y lista de buena fe.

Igual que en `test_cli_comandos.py`: cada comando se llama directo con un `argparse.Namespace` armado a mano
y con repositorios falsos (`unittest.mock`); lo que imprime se captura con `capsys`. No tocan SQLite.
"""

import argparse
from unittest.mock import MagicMock

import pytest

from dominio.entidades.club import Club
from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.entidades.jugador import Jugador
from dominio.exceptions import CategoriaDuplicadaError, JugadorNoEstaEnListaError, JugadorYaEnListaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from infraestructura.ui.cli.commands import (
    categoria_add,
    categoria_list,
    competencia_list,
    inscripcion_list,
    lista_add,
    lista_list,
    lista_remove,
)


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _repo(interfaz, **config):
    repo = MagicMock(spec=interfaz)
    repo.configure_mock(**config)
    return repo


def _es_una_tabla(texto: str) -> bool:
    return "+---" in texto and "|" in texto


# ----------------------------------------------------------------------------- categoria add


def test_categoria_add_informa_la_categoria_creada(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{"obtener_categorias.return_value": [], "guardar_categoria.return_value": Categoria("U21", idCategoria=1)},
    )

    categoria_add.ejecutar(_args(nombre="U21"), repo)

    assert capsys.readouterr().out == "Categoria creada: U21 (id=1)\n"


def test_categoria_add_con_nombre_repetido_deja_subir_el_error_de_dominio():
    repo = _repo(CompetenciaRepositorio, **{"obtener_categorias.return_value": [Categoria("U21", idCategoria=1)]})

    with pytest.raises(CategoriaDuplicadaError):
        categoria_add.ejecutar(_args(nombre="u21"), repo)


def test_categoria_add_aborta_si_el_repositorio_no_pudo_guardar(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{"obtener_categorias.return_value": [], "guardar_categoria.return_value": None},
    )

    with pytest.raises(SystemExit) as info:
        categoria_add.ejecutar(_args(nombre="U21"), repo)

    salida = capsys.readouterr()
    assert info.value.code == 1
    assert salida.err == "Error: no se pudo guardar la categoria\n"


# ----------------------------------------------------------------------------- categoria list


def test_categoria_list_muestra_las_categorias_en_una_tabla(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{"obtener_categorias.return_value": [Categoria("U17", idCategoria=1), Categoria("U21", idCategoria=2)]},
    )

    categoria_list.ejecutar(_args(), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "U17" in salida and "U21" in salida


def test_categoria_list_sin_categorias_avisa(capsys):
    repo = _repo(CompetenciaRepositorio, **{"obtener_categorias.return_value": []})

    categoria_list.ejecutar(_args(), repo)

    assert capsys.readouterr().out == "No hay categorias cargadas.\n"


# ----------------------------------------------------------------------------- competencia list


def test_competencia_list_muestra_las_competencias_en_una_tabla(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{
            "obtener_todas_competencias.return_value": [
                Competencia("Liga Provincial", 2026, "PROVINCIAL", idCompetencia=1),
                Competencia("Copa", 2027, idCompetencia=2),
            ]
        },
    )

    competencia_list.ejecutar(_args(), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "Liga Provincial" in salida and "PROVINCIAL" in salida
    assert "-" in salida.splitlines()[-2]  # la competencia sin tipo se muestra con un guion


def test_competencia_list_sin_competencias_avisa(capsys):
    repo = _repo(CompetenciaRepositorio, **{"obtener_todas_competencias.return_value": []})

    competencia_list.ejecutar(_args(), repo)

    assert capsys.readouterr().out == "No hay competencias cargadas.\n"


# ----------------------------------------------------------------------------- inscripcion list


def test_inscripcion_list_muestra_las_inscripciones_y_sus_listas_en_una_tabla(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{
            "obtener_inscripciones_por_club.return_value": [Inscripcion(1, 2, 3, idInscripcion=10)],
            "obtener_lista_por_inscripcion.return_value": ListaBuenaFe("2026-03-01", 10, idListaBuenaFe=20),
        },
    )

    inscripcion_list.ejecutar(_args(id_club=1), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "10" in salida and "20" in salida


def test_inscripcion_list_sin_inscripciones_avisa(capsys):
    repo = _repo(CompetenciaRepositorio, **{"obtener_inscripciones_por_club.return_value": []})

    inscripcion_list.ejecutar(_args(id_club=1), repo)

    assert capsys.readouterr().out == "El club 1 no tiene inscripciones.\n"


# ----------------------------------------------------------------------------- lista add / lista list


def _repos_de_la_lista(**overrides):
    """Repos falsos con el escenario feliz (inscripcion 5 del club 1, lista 7, jugador 3 en el club 1)."""
    competencia_config = {
        "buscar_inscripcion_por_id.return_value": Inscripcion(1, 1, 1, idInscripcion=5),
        "obtener_lista_por_inscripcion.return_value": ListaBuenaFe("2026-03-01", 5, idListaBuenaFe=7),
        "obtener_jugadores_lista.return_value": [],
        "agregar_jugador_lista.return_value": JugadorListaBuenaFe(idJugador=3, idListaBuenaFe=7),
    }
    jugador_config = {
        "buscar_por_id.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=3),
        "club_activo.return_value": Club("Atenas", idClub=1),
    }
    competencia_config.update(overrides.get("competencia", {}))
    jugador_config.update(overrides.get("jugador", {}))
    return _repo(CompetenciaRepositorio, **competencia_config), _repo(JugadorRepositorio, **jugador_config)


ARGS_LISTA_ADD = _args(id_inscripcion=5, id_jugador=3)


def test_lista_add_informa_el_jugador_habilitado(capsys):
    repo_competencia, repo_jugador = _repos_de_la_lista()

    lista_add.ejecutar(ARGS_LISTA_ADD, repo_competencia, repo_jugador)

    assert capsys.readouterr().out == "Jugador 3 habilitado en la lista de buena fe 7 (inscripcion 5)\n"


def test_lista_add_con_jugador_ya_habilitado_deja_subir_el_error_de_dominio():
    repo_competencia, repo_jugador = _repos_de_la_lista(
        competencia={"obtener_jugadores_lista.return_value": [JugadorListaBuenaFe(3, 7)]}
    )

    with pytest.raises(JugadorYaEnListaError):
        lista_add.ejecutar(ARGS_LISTA_ADD, repo_competencia, repo_jugador)


def test_lista_add_aborta_si_el_repositorio_no_pudo_guardar(capsys):
    repo_competencia, repo_jugador = _repos_de_la_lista(competencia={"agregar_jugador_lista.return_value": None})

    with pytest.raises(SystemExit) as info:
        lista_add.ejecutar(ARGS_LISTA_ADD, repo_competencia, repo_jugador)

    salida = capsys.readouterr()
    assert info.value.code == 1
    assert salida.err == "Error: no se pudo agregar el jugador a la lista de buena fe\n"


def test_lista_list_muestra_los_jugadores_habilitados_en_una_tabla(capsys):
    repo_competencia, repo_jugador = _repos_de_la_lista(
        competencia={"obtener_jugadores_lista.return_value": [JugadorListaBuenaFe(3, 7)]}
    )

    lista_list.ejecutar(_args(id_inscripcion=5), repo_competencia, repo_jugador)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "Manu Ginobili" in salida


def test_lista_list_sin_jugadores_avisa(capsys):
    repo_competencia, repo_jugador = _repos_de_la_lista()

    lista_list.ejecutar(_args(id_inscripcion=5), repo_competencia, repo_jugador)

    assert capsys.readouterr().out == "La lista de buena fe de la inscripcion 5 no tiene jugadores.\n"


def test_lista_remove_informa_el_jugador_quitado(capsys):
    repo_competencia, _ = _repos_de_la_lista(
        competencia={
            "obtener_jugadores_lista.return_value": [JugadorListaBuenaFe(3, 7)],
            "quitar_jugador_lista.return_value": True,
        }
    )

    lista_remove.ejecutar(_args(id_inscripcion=5, id_jugador=3), repo_competencia)

    assert capsys.readouterr().out == "Jugador 3 quitado de la lista de buena fe 7 (inscripcion 5)\n"


def test_lista_remove_de_un_jugador_que_no_esta_deja_subir_el_error_de_dominio():
    repo_competencia, _ = _repos_de_la_lista()  # la lista esta vacia

    with pytest.raises(JugadorNoEstaEnListaError):
        lista_remove.ejecutar(_args(id_inscripcion=5, id_jugador=3), repo_competencia)


def test_lista_remove_aborta_si_el_repositorio_no_pudo_borrar(capsys):
    repo_competencia, _ = _repos_de_la_lista(
        competencia={
            "obtener_jugadores_lista.return_value": [JugadorListaBuenaFe(3, 7)],
            "quitar_jugador_lista.return_value": False,
        }
    )

    with pytest.raises(SystemExit) as info:
        lista_remove.ejecutar(_args(id_inscripcion=5, id_jugador=3), repo_competencia)

    assert info.value.code == 1
    assert capsys.readouterr().err == "Error: no se pudo quitar al jugador de la lista de buena fe\n"
