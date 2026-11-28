"""Tests unitarios de los casos de uso de categorias, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO, CrearCategoriaDTO
from dominio.entidades.competencia import Categoria
from dominio.exceptions import CategoriaDuplicadaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


@pytest.fixture
def repo_competencia():
    return MagicMock(spec=CompetenciaRepositorio)


# ------------------------------------------------------------------ CrearCategoria


def test_crear_categoria_devuelve_el_dto_con_el_id_asignado(repo_competencia):
    repo_competencia.obtener_categorias.return_value = [Categoria("U17", idCategoria=1)]
    repo_competencia.guardar_categoria.return_value = Categoria("U21", idCategoria=2)

    resultado = CrearCategoriaUseCase(repo_competencia).ejecutar(CrearCategoriaDTO(nombre="U21"))

    assert resultado == CategoriaDTO(idCategoria=2, nombre="U21")
    repo_competencia.guardar_categoria.assert_called_once_with(cat=Categoria("U21"))


@pytest.mark.parametrize(
    "nombre_ingresado",
    [
        pytest.param("U21", id="mismo-nombre"),
        pytest.param("u21", id="distinta-capitalizacion"),
        pytest.param("  U21 ", id="con-espacios-en-los-extremos"),
    ],
)
def test_crear_categoria_con_nombre_repetido_lanza_excepcion_y_no_guarda(repo_competencia, nombre_ingresado):
    repo_competencia.obtener_categorias.return_value = [Categoria("U21", idCategoria=1)]

    with pytest.raises(CategoriaDuplicadaError, match=r"(?i)u21"):
        CrearCategoriaUseCase(repo_competencia).ejecutar(CrearCategoriaDTO(nombre=nombre_ingresado))

    repo_competencia.guardar_categoria.assert_not_called()


def test_crear_categoria_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_competencia):
    repo_competencia.obtener_categorias.return_value = []
    repo_competencia.guardar_categoria.return_value = None

    assert CrearCategoriaUseCase(repo_competencia).ejecutar(CrearCategoriaDTO(nombre="U21")) is None


def test_crear_categoria_con_nombre_de_tipo_invalido_no_llega_al_repositorio(repo_competencia):
    with pytest.raises(TypeError):
        CrearCategoriaUseCase(repo_competencia).ejecutar(CrearCategoriaDTO(nombre=None))

    repo_competencia.guardar_categoria.assert_not_called()


# ------------------------------------------------------------------ ListarCategorias


def test_listar_categorias_convierte_cada_categoria_en_dto(repo_competencia):
    repo_competencia.obtener_categorias.return_value = [
        Categoria("U17", idCategoria=1),
        Categoria("U21", idCategoria=2),
    ]

    resultado = ListarCategoriasUseCase(repo_competencia).ejecutar()

    assert resultado == [CategoriaDTO(1, "U17"), CategoriaDTO(2, "U21")]


def test_listar_categorias_sin_categorias_devuelve_lista_vacia(repo_competencia):
    repo_competencia.obtener_categorias.return_value = []

    assert ListarCategoriasUseCase(repo_competencia).ejecutar() == []


def test_listar_categorias_con_una_categoria_sin_id_es_un_error_del_repositorio(repo_competencia):
    repo_competencia.obtener_categorias.return_value = [Categoria("U21")]

    with pytest.raises(RuntimeError, match="Categoria"):
        ListarCategoriasUseCase(repo_competencia).ejecutar()
