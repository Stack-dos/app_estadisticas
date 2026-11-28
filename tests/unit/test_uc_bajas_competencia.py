"""Tests unitarios de los casos de uso de baja/eliminacion y vaciado (US-107)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.vaciar_lista_buena_fe import VaciarListaBuenaFeUseCase
from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.exceptions import (
    CategoriaEnUsoError,
    CategoriaNoEncontradaError,
    CompetenciaEnUsoError,
    CompetenciaNoEncontradaError,
    InscripcionEnUsoError,
    InscripcionNoEncontradaError,
    ListaBuenaFeNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


@pytest.fixture
def repo():
    return MagicMock(spec=CompetenciaRepositorio)


# ------------------------------------------------------------------ EliminarCompetencia


def test_eliminar_competencia_sin_uso_la_elimina(repo):
    repo.buscar_competencia_por_id.return_value = Competencia("Liga", 2026, idCompetencia=1)
    repo.competencia_tiene_inscripciones.return_value = False
    repo.competencia_tiene_partidos.return_value = False
    repo.eliminar_competencia.return_value = True

    assert EliminarCompetenciaUseCase(repo).ejecutar(1) is True
    repo.eliminar_competencia.assert_called_once_with(1)


@pytest.mark.parametrize(
    "setup, excepcion, fragmento",
    [
        pytest.param(
            {"buscar": None},
            CompetenciaNoEncontradaError,
            "idCompetencia=1",
            id="competencia-inexistente",
        ),
        pytest.param(
            {"inscripciones": True},
            CompetenciaEnUsoError,
            "clubes inscriptos",
            id="competencia-con-inscripciones",
        ),
        pytest.param(
            {"partidos": True},
            CompetenciaEnUsoError,
            "partidos cargados",
            id="competencia-con-partidos",
        ),
    ],
)
def test_eliminar_competencia_rechaza_si_no_existe_o_esta_en_uso(repo, setup, excepcion, fragmento):
    repo.buscar_competencia_por_id.return_value = setup.get("buscar", Competencia("Liga", 2026, idCompetencia=1))
    repo.competencia_tiene_inscripciones.return_value = setup.get("inscripciones", False)
    repo.competencia_tiene_partidos.return_value = setup.get("partidos", False)

    with pytest.raises(excepcion, match=fragmento):
        EliminarCompetenciaUseCase(repo).ejecutar(1)

    repo.eliminar_competencia.assert_not_called()


# ------------------------------------------------------------------ EliminarCategoria


def test_eliminar_categoria_sin_uso_la_elimina(repo):
    repo.obtener_categorias.return_value = [Categoria("U17", idCategoria=2)]
    repo.categoria_en_uso.return_value = False
    repo.eliminar_categoria.return_value = True

    assert EliminarCategoriaUseCase(repo).ejecutar(2) is True
    repo.eliminar_categoria.assert_called_once_with(2)


def test_eliminar_categoria_inexistente_lanza_excepcion(repo):
    repo.obtener_categorias.return_value = []

    with pytest.raises(CategoriaNoEncontradaError, match="idCategoria=2"):
        EliminarCategoriaUseCase(repo).ejecutar(2)

    repo.eliminar_categoria.assert_not_called()


def test_eliminar_categoria_en_uso_lanza_excepcion(repo):
    repo.obtener_categorias.return_value = [Categoria("U17", idCategoria=2)]
    repo.categoria_en_uso.return_value = True

    with pytest.raises(CategoriaEnUsoError, match="esta en uso"):
        EliminarCategoriaUseCase(repo).ejecutar(2)

    repo.eliminar_categoria.assert_not_called()


# ------------------------------------------------------------------ EliminarInscripcion


def test_eliminar_inscripcion_sin_partidos_la_elimina(repo):
    repo.buscar_inscripcion_por_id.return_value = Inscripcion(1, 2, 3, idInscripcion=5)
    repo.inscripcion_tiene_partidos.return_value = False
    repo.eliminar_inscripcion.return_value = True

    assert EliminarInscripcionUseCase(repo).ejecutar(5) is True
    repo.eliminar_inscripcion.assert_called_once_with(5)


def test_eliminar_inscripcion_inexistente_lanza_excepcion(repo):
    repo.buscar_inscripcion_por_id.return_value = None

    with pytest.raises(InscripcionNoEncontradaError, match="idInscripcion=5"):
        EliminarInscripcionUseCase(repo).ejecutar(5)


def test_eliminar_inscripcion_con_partidos_lanza_excepcion(repo):
    repo.buscar_inscripcion_por_id.return_value = Inscripcion(1, 2, 3, idInscripcion=5)
    repo.inscripcion_tiene_partidos.return_value = True

    with pytest.raises(InscripcionEnUsoError, match="partidos cargados"):
        EliminarInscripcionUseCase(repo).ejecutar(5)

    repo.eliminar_inscripcion.assert_not_called()


# ------------------------------------------------------------------ VaciarListaBuenaFe


def test_vaciar_lista_buena_fe_devuelve_cantidad_quitada(repo):
    repo.buscar_inscripcion_por_id.return_value = Inscripcion(1, 2, 3, idInscripcion=5)
    repo.obtener_lista_por_inscripcion.return_value = ListaBuenaFe("2026-03-01", 5, idListaBuenaFe=8)
    repo.obtener_jugadores_lista.return_value = [JugadorListaBuenaFe(1, 8), JugadorListaBuenaFe(2, 8)]
    repo.vaciar_lista_buena_fe.return_value = True

    assert VaciarListaBuenaFeUseCase(repo).ejecutar(5) == 2
    repo.vaciar_lista_buena_fe.assert_called_once_with(8)


def test_vaciar_lista_ya_vacia_devuelve_cero_sin_llamar_al_repo(repo):
    repo.buscar_inscripcion_por_id.return_value = Inscripcion(1, 2, 3, idInscripcion=5)
    repo.obtener_lista_por_inscripcion.return_value = ListaBuenaFe("2026-03-01", 5, idListaBuenaFe=8)
    repo.obtener_jugadores_lista.return_value = []

    assert VaciarListaBuenaFeUseCase(repo).ejecutar(5) == 0
    repo.vaciar_lista_buena_fe.assert_not_called()


def test_vaciar_lista_con_inscripcion_o_lista_inexistente_lanza_excepcion(repo):
    repo.buscar_inscripcion_por_id.return_value = None
    with pytest.raises(InscripcionNoEncontradaError):
        VaciarListaBuenaFeUseCase(repo).ejecutar(5)

    repo.buscar_inscripcion_por_id.return_value = Inscripcion(1, 2, 3, idInscripcion=5)
    repo.obtener_lista_por_inscripcion.return_value = None
    with pytest.raises(ListaBuenaFeNoEncontradaError):
        VaciarListaBuenaFeUseCase(repo).ejecutar(5)
