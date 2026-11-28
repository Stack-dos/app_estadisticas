"""Tests unitarios de los casos de uso de categorias por competencia (US-107)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CategoriaCompetenciaDTO
from dominio.entidades.competencia import Categoria, Competencia
from dominio.exceptions import (
    CategoriaConInscripcionesError,
    CategoriaNoEncontradaError,
    CategoriaNoHabilitadaError,
    CategoriaYaHabilitadaError,
    CompetenciaNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


@pytest.fixture
def repo():
    return MagicMock(spec=CompetenciaRepositorio)


def _preparar(repo, **overrides):
    config = {
        "competencia": Competencia("Liga", 2026, idCompetencia=1),
        "categorias": [Categoria("U17", idCategoria=2), Categoria("U21", idCategoria=3)],
        "habilitadas": [Categoria("U21", idCategoria=3)],
        "tiene_inscripciones": False,
        **overrides,
    }
    repo.buscar_competencia_por_id.return_value = config["competencia"]
    repo.obtener_categorias.return_value = config["categorias"]
    repo.obtener_categorias_de_competencia.return_value = config["habilitadas"]
    repo.tiene_inscripciones.return_value = config["tiene_inscripciones"]


# ------------------------------------------------------------------ HabilitarCategoriaEnCompetencia


def test_habilitar_categoria_en_competencia_devuelve_confirmacion(repo):
    _preparar(repo)
    repo.habilitar_categoria.return_value = True

    resultado = HabilitarCategoriaEnCompetenciaUseCase(repo).ejecutar(
        CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=2)
    )

    assert resultado == CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=2)
    repo.habilitar_categoria.assert_called_once_with(1, 2)


def test_habilitar_categoria_devuelve_none_si_falla_el_repositorio(repo):
    _preparar(repo)
    repo.habilitar_categoria.return_value = False

    assert (
        HabilitarCategoriaEnCompetenciaUseCase(repo).ejecutar(CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=2))
        is None
    )


@pytest.mark.parametrize(
    "overrides, dto, excepcion, fragmento",
    [
        pytest.param(
            {"competencia": None},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=2),
            CompetenciaNoEncontradaError,
            "idCompetencia=1",
            id="competencia-inexistente",
        ),
        pytest.param(
            {},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=99),
            CategoriaNoEncontradaError,
            "idCategoria=99",
            id="categoria-inexistente",
        ),
        pytest.param(
            {},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3),
            CategoriaYaHabilitadaError,
            "ya esta habilitada",
            id="categoria-ya-habilitada",
        ),
    ],
)
def test_habilitar_categoria_que_rompe_una_regla_lanza_excepcion(repo, overrides, dto, excepcion, fragmento):
    _preparar(repo, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        HabilitarCategoriaEnCompetenciaUseCase(repo).ejecutar(dto)

    repo.habilitar_categoria.assert_not_called()


# ------------------------------------------------------------------ ListarCategoriasDeCompetencia


def test_listar_categorias_de_competencia_convierte_a_dtos(repo):
    _preparar(repo, habilitadas=[Categoria("U17", idCategoria=2), Categoria("U21", idCategoria=3)])

    resultado = ListarCategoriasDeCompetenciaUseCase(repo).ejecutar(1)

    assert resultado == [
        CategoriaDTO(idCategoria=2, nombre="U17"),
        CategoriaDTO(idCategoria=3, nombre="U21"),
    ]


def test_listar_categorias_de_competencia_sin_categorias_devuelve_vacio(repo):
    _preparar(repo, habilitadas=[])

    assert ListarCategoriasDeCompetenciaUseCase(repo).ejecutar(1) == []


def test_listar_categorias_de_competencia_inexistente_lanza_excepcion(repo):
    _preparar(repo, competencia=None)

    with pytest.raises(CompetenciaNoEncontradaError, match="idCompetencia=1"):
        ListarCategoriasDeCompetenciaUseCase(repo).ejecutar(1)


# ------------------------------------------------------------------ QuitarCategoriaDeCompetencia


def test_quitar_categoria_sin_inscripciones_devuelve_confirmacion(repo):
    _preparar(repo, tiene_inscripciones=False)
    repo.quitar_categoria.return_value = True

    resultado = QuitarCategoriaDeCompetenciaUseCase(repo).ejecutar(
        CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3)
    )

    assert resultado == CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3)
    repo.quitar_categoria.assert_called_once_with(1, 3)


def test_quitar_categoria_devuelve_none_si_falla_el_repositorio(repo):
    _preparar(repo, tiene_inscripciones=False)
    repo.quitar_categoria.return_value = False

    assert (
        QuitarCategoriaDeCompetenciaUseCase(repo).ejecutar(CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3))
        is None
    )


@pytest.mark.parametrize(
    "overrides, dto, excepcion, fragmento",
    [
        pytest.param(
            {"competencia": None},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3),
            CompetenciaNoEncontradaError,
            "idCompetencia=1",
            id="competencia-inexistente",
        ),
        pytest.param(
            {},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=99),
            CategoriaNoEncontradaError,
            "idCategoria=99",
            id="categoria-inexistente",
        ),
        pytest.param(
            {},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=2),
            CategoriaNoHabilitadaError,
            "no esta habilitada",
            id="categoria-no-habilitada",
        ),
        pytest.param(
            {"tiene_inscripciones": True},
            CategoriaCompetenciaDTO(idCompetencia=1, idCategoria=3),
            CategoriaConInscripcionesError,
            "tiene clubes inscriptos",
            id="categoria-con-inscripciones",
        ),
    ],
)
def test_quitar_categoria_que_rompe_una_regla_lanza_excepcion(repo, overrides, dto, excepcion, fragmento):
    _preparar(repo, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        QuitarCategoriaDeCompetenciaUseCase(repo).ejecutar(dto)

    repo.quitar_categoria.assert_not_called()
