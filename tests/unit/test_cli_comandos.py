"""Tests unitarios de los comandos de la CLI (`infraestructura/ui/cli/commands/`).

Cada comando se llama directo con un `argparse.Namespace` armado a mano (sin `sys.argv`) y con
repositorios falsos (`unittest.mock`). Lo que imprime se captura con `capsys`. No tocan SQLite.
"""

import argparse
from unittest.mock import MagicMock

import pytest

from dominio.entidades.club import Club
from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, ListaBuenaFe
from dominio.entidades.jugador import Jugador, JugadorClub
from dominio.entidades.partido import PartidoResumen
from dominio.exceptions import (
    DatoInvalidoError,
    JugadorSinVinculoActivoError,
    VinculoActivoExistenteError,
)
from dominio.repositorios.club_repositorio import ClubRepositorio
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from dominio.repositorios.partido_repositorio import PartidoRepositorio
from infraestructura.ui.cli.commands import (
    club_add,
    club_list,
    competencia_add,
    competencia_inscribir,
    game_list,
    jugador_add,
    jugador_link,
    jugador_list,
    jugador_unlink,
)


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _repo(interfaz, **config):
    """Repositorio falso con la forma de `interfaz`. Ej: _repo(ClubRepositorio, **{"guardar.return_value": x})."""
    repo = MagicMock(spec=interfaz)
    repo.configure_mock(**config)
    return repo


def _es_una_tabla(texto: str) -> bool:
    return "+---" in texto and "|" in texto


# ----------------------------------------------------------------------------- club add


def test_club_add_informa_el_club_creado(capsys):
    repo = _repo(ClubRepositorio, **{"guardar.return_value": Club("Atenas", idClub=3)})

    club_add.ejecutar(_args(nombre="Atenas"), repo)

    assert capsys.readouterr().out == "Club creado: Atenas (id=3)\n"


# ----------------------------------------------------------------------------- club list


def test_club_list_muestra_los_clubes_en_una_tabla(capsys):
    repo = _repo(ClubRepositorio, **{"buscar_por_id_usuario.return_value": [Club("Atenas", idClub=1)]})

    club_list.ejecutar(_args(id_usuario=10), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "Atenas" in salida
    repo.buscar_por_id_usuario.assert_called_once_with(10)


def test_club_list_sin_clubes_avisa_en_vez_de_mostrar_una_tabla_vacia(capsys):
    repo = _repo(ClubRepositorio, **{"buscar_por_id_usuario.return_value": None})

    club_list.ejecutar(_args(id_usuario=10), repo)

    assert capsys.readouterr().out == "El usuario 10 no pertenece a ningun club.\n"


# ----------------------------------------------------------------------------- jugador add


def test_jugador_add_informa_el_jugador_creado(capsys):
    repo = _repo(JugadorRepositorio, **{"guardar.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=7)})

    jugador_add.ejecutar(_args(nombre="Manu", apellido="Ginobili", anio=1977), repo)

    assert capsys.readouterr().out == "Jugador creado: Manu Ginobili (id=7)\n"


# ----------------------------------------------------------------------------- jugador link


def _repos_para_vincular(**overrides):
    """Repos falsos con todo lo necesario para que el vinculo se pueda guardar; se pisa lo que el test rompe."""
    jugador_config = {
        "buscar_por_id.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=1),
        "club_activo.return_value": None,
        "historial_vinculos.return_value": [],
        "link_to_club.return_value": JugadorClub("2026-01-05", None, idJugador=1, idClub=2),
    }
    club_config = {"buscar_por_id.return_value": Club("Atenas", idClub=2)}
    jugador_config.update(overrides.get("jugador", {}))
    club_config.update(overrides.get("club", {}))
    return _repo(JugadorRepositorio, **jugador_config), _repo(ClubRepositorio, **club_config)


ARGS_LINK = _args(id_jugador=1, id_club=2, fecha_desde="2026-01-05")


def test_jugador_link_informa_el_vinculo_creado(capsys):
    repo_jugador, repo_club = _repos_para_vincular()

    jugador_link.ejecutar(ARGS_LINK, repo_jugador, repo_club)

    assert capsys.readouterr().out == "Jugador 1 vinculado al club 2 desde 2026-01-05\n"


def test_jugador_link_con_club_activo_deja_subir_el_error_de_dominio():
    repo_jugador, repo_club = _repos_para_vincular(jugador={"club_activo.return_value": Club("Otro", idClub=9)})

    with pytest.raises(VinculoActivoExistenteError):
        jugador_link.ejecutar(ARGS_LINK, repo_jugador, repo_club)


# ----------------------------------------------------------------------------- jugador list


def test_jugador_list_muestra_los_jugadores_en_una_tabla(capsys):
    repo = _repo(
        JugadorRepositorio,
        **{"buscar_por_club.return_value": [Jugador("Manu", "Ginobili", 1977, idJugador=1)]},
    )

    jugador_list.ejecutar(_args(id_club=2), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "Manu Ginobili" in salida
    assert "1977" in salida


def test_jugador_list_sin_jugadores_avisa(capsys):
    repo = _repo(JugadorRepositorio, **{"buscar_por_club.return_value": []})

    jugador_list.ejecutar(_args(id_club=2), repo)

    assert capsys.readouterr().out == "El club 2 no tiene jugadores.\n"


# ----------------------------------------------------------------------------- competencia add


def test_competencia_add_informa_la_competencia_creada(capsys):
    repo = _repo(
        CompetenciaRepositorio,
        **{"guardar_competencia.return_value": Competencia("Liga", 2026, "PROVINCIAL", idCompetencia=4)},
    )

    competencia_add.ejecutar(_args(nombre="Liga", anio=2026, tipo="PROVINCIAL"), repo)

    assert capsys.readouterr().out == "Competencia creada: Liga 2026 (id=4)\n"


def test_competencia_add_con_anio_invalido_deja_subir_el_error_de_dominio():
    repo = _repo(CompetenciaRepositorio)

    with pytest.raises(DatoInvalidoError, match="1900"):
        competencia_add.ejecutar(_args(nombre="Vieja", anio=1900, tipo=None), repo)

    repo.guardar_competencia.assert_not_called()


# ----------------------------------------------------------------------------- competencia inscribir


def _repos_para_inscribir(**overrides):
    competencia_config = {
        "buscar_competencia_por_id.return_value": Competencia("Liga", 2026, idCompetencia=3),
        "obtener_categorias.return_value": [Categoria("U21", idCategoria=2)],
        "obtener_inscripciones_por_club.return_value": [],
        "inscribir_con_lista.return_value": (
            Inscripcion(1, 2, 3, idInscripcion=10),
            ListaBuenaFe("2026-03-01", 10, idListaBuenaFe=20),
        ),
    }
    competencia_config.update(overrides)
    return (
        _repo(CompetenciaRepositorio, **competencia_config),
        _repo(ClubRepositorio, **{"buscar_por_id.return_value": Club("Atenas", idClub=1)}),
    )


ARGS_INSCRIBIR = _args(id_club=1, id_categoria=2, id_competencia=3, fecha_presentacion="2026-03-01")


def test_competencia_inscribir_informa_la_inscripcion_y_su_lista(capsys):
    repo_competencia, repo_club = _repos_para_inscribir()

    competencia_inscribir.ejecutar(ARGS_INSCRIBIR, repo_competencia, repo_club)

    assert capsys.readouterr().out == (
        "Club 1 inscripto en la competencia 3 (categoria 2). Inscripcion id=10, lista de buena fe id=20\n"
    )


# ----------------------------------------------------------------------------- partido list


def test_partido_list_muestra_los_nombres_de_los_clubes_en_una_tabla(capsys):
    repo = _repo(
        PartidoRepositorio,
        **{
            "resumen_por_club.return_value": [
                PartidoResumen(1, "2026-05-21", "Cancha Atenas", "Liga", 2026, "Atenas", "Universitario"),
                PartidoResumen(2, "2026-06-20", None, "Liga", 2026, "Universitario", "Atenas"),
            ]
        },
    )

    game_list.ejecutar(_args(id_club=1), repo)

    salida = capsys.readouterr().out
    assert _es_una_tabla(salida)
    assert "Cancha Atenas" in salida
    assert "Atenas" in salida and "Universitario" in salida and "Liga 2026" in salida
    assert "-" in salida.splitlines()[-2]  # el partido sin estadio se muestra con un guion


def test_partido_list_sin_partidos_avisa(capsys):
    repo = _repo(PartidoRepositorio, **{"resumen_por_club.return_value": []})

    game_list.ejecutar(_args(id_club=1), repo)

    assert capsys.readouterr().out == "El club 1 no tiene partidos.\n"


# --------------------------------------------- comandos que guardan: si el repositorio falla, abortan


def _kwargs_club_add():
    return {"repo": _repo(ClubRepositorio, **{"guardar.return_value": None})}


def _kwargs_jugador_add():
    return {"repo": _repo(JugadorRepositorio, **{"guardar.return_value": None})}


def _kwargs_jugador_link():
    repo_jugador, repo_club = _repos_para_vincular(jugador={"link_to_club.return_value": None})
    return {"repo_jugador": repo_jugador, "repo_club": repo_club}


def _kwargs_competencia_add():
    return {"repo": _repo(CompetenciaRepositorio, **{"guardar_competencia.return_value": None})}


def _kwargs_competencia_inscribir():
    repo_competencia, repo_club = _repos_para_inscribir(**{"inscribir_con_lista.return_value": None})
    return {"repo_competencia": repo_competencia, "repo_club": repo_club}


@pytest.mark.parametrize(
    "comando, args, armar_repos, mensaje",
    [
        pytest.param(club_add, _args(nombre="Atenas"), _kwargs_club_add, "no se pudo guardar el club", id="club add"),
        pytest.param(
            jugador_add,
            _args(nombre="Manu", apellido="Ginobili", anio=1977),
            _kwargs_jugador_add,
            "no se pudo guardar el jugador",
            id="jugador add",
        ),
        pytest.param(
            jugador_link,
            ARGS_LINK,
            _kwargs_jugador_link,
            "no se pudo vincular el jugador al club",
            id="jugador link",
        ),
        pytest.param(
            competencia_add,
            _args(nombre="Liga", anio=2026, tipo=None),
            _kwargs_competencia_add,
            "no se pudo guardar la competencia",
            id="competencia add",
        ),
        pytest.param(
            competencia_inscribir,
            ARGS_INSCRIBIR,
            _kwargs_competencia_inscribir,
            "no se pudo guardar la inscripcion",
            id="competencia inscribir",
        ),
    ],
)
def test_comando_que_guarda_aborta_con_error_si_el_repositorio_no_pudo_guardar(
    capsys, comando, args, armar_repos, mensaje
):
    with pytest.raises(SystemExit) as info:
        comando.ejecutar(args, **armar_repos())

    salida = capsys.readouterr()
    assert info.value.code == 1
    assert salida.err == f"Error: {mensaje}\n"
    assert salida.out == ""


# ----------------------------------------------------------------------------- jugador unlink


def test_jugador_unlink_informa_el_vinculo_cerrado(capsys):
    repo = _repo(
        JugadorRepositorio,
        **{
            "buscar_por_id.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=1),
            "historial_vinculos.return_value": [JugadorClub("2026-01-05", None, idJugador=1, idClub=2)],
            "cerrar_vinculo.return_value": JugadorClub("2026-01-05", "2026-06-30", idJugador=1, idClub=2),
        },
    )

    jugador_unlink.ejecutar(_args(id_jugador=1, fecha_hasta="2026-06-30"), repo)

    assert capsys.readouterr().out == "Jugador 1 desvinculado del club 2 (desde 2026-01-05 hasta 2026-06-30)\n"


def test_jugador_unlink_sin_club_activo_deja_subir_el_error_de_dominio():
    repo = _repo(
        JugadorRepositorio,
        **{
            "buscar_por_id.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=1),
            "historial_vinculos.return_value": [],
        },
    )

    with pytest.raises(JugadorSinVinculoActivoError):
        jugador_unlink.ejecutar(_args(id_jugador=1, fecha_hasta="2026-06-30"), repo)


def test_jugador_unlink_aborta_si_el_repositorio_no_pudo_guardar(capsys):
    repo = _repo(
        JugadorRepositorio,
        **{
            "buscar_por_id.return_value": Jugador("Manu", "Ginobili", 1977, idJugador=1),
            "historial_vinculos.return_value": [JugadorClub("2026-01-05", None, idJugador=1, idClub=2)],
            "cerrar_vinculo.return_value": None,
        },
    )

    with pytest.raises(SystemExit) as info:
        jugador_unlink.ejecutar(_args(id_jugador=1, fecha_hasta="2026-06-30"), repo)

    assert info.value.code == 1
    assert capsys.readouterr().err == "Error: no se pudo desvincular al jugador del club\n"
