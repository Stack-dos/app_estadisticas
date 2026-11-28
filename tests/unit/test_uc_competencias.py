"""Tests unitarios de los casos de uso de competencias, con repositorios falsos (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.dtos.competencia_dto import CompetenciaDTO, CrearCompetenciaDTO, InscribirClubDTO, InscripcionDTO
from dominio.entidades.club import Club
from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, ListaBuenaFe
from dominio.exceptions import (
    CategoriaNoEncontradaError,
    CategoriaNoHabilitadaError,
    ClubNoEncontradoError,
    CompetenciaNoEncontradaError,
    InscripcionDuplicadaError,
)
from dominio.repositorios.club_repositorio import ClubRepositorio
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


@pytest.fixture
def repo_competencia():
    return MagicMock(spec=CompetenciaRepositorio)


@pytest.fixture
def repo_club():
    return MagicMock(spec=ClubRepositorio)


# ------------------------------------------------------------------ CrearCompetencia


def test_crear_competencia_devuelve_el_dto_con_el_id_asignado(repo_competencia):
    repo_competencia.guardar_competencia_con_categorias.return_value = Competencia(
        "Liga", 2026, "PROVINCIAL", idCompetencia=4
    )

    resultado = CrearCompetenciaUseCase(repo_competencia).ejecutar(
        CrearCompetenciaDTO(nombre="Liga", anio=2026, tipo="PROVINCIAL")
    )

    assert resultado == CompetenciaDTO(idCompetencia=4, nombre="Liga", anio=2026, tipo="PROVINCIAL")
    repo_competencia.guardar_competencia_con_categorias.assert_called_once_with(
        compe=Competencia("Liga", 2026, "PROVINCIAL"), idCategorias=[]
    )


def test_crear_competencia_con_categorias_las_valida_y_deduplica(repo_competencia):
    repo_competencia.obtener_categorias.return_value = [
        Categoria("U17", idCategoria=1),
        Categoria("U21", idCategoria=2),
    ]
    repo_competencia.guardar_competencia_con_categorias.return_value = Competencia("Liga", 2026, idCompetencia=4)

    resultado = CrearCompetenciaUseCase(repo_competencia).ejecutar(
        CrearCompetenciaDTO(nombre="Liga", anio=2026, idCategorias=[1, 2, 1])
    )

    assert resultado is not None
    repo_competencia.guardar_competencia_con_categorias.assert_called_once_with(
        compe=Competencia("Liga", 2026), idCategorias=[1, 2]
    )


def test_crear_competencia_con_categoria_inexistente_lanza_excepcion(repo_competencia):
    repo_competencia.obtener_categorias.return_value = [Categoria("U17", idCategoria=1)]

    with pytest.raises(CategoriaNoEncontradaError, match="idCategoria=99"):
        CrearCompetenciaUseCase(repo_competencia).ejecutar(
            CrearCompetenciaDTO(nombre="Liga", anio=2026, idCategorias=[1, 99])
        )

    repo_competencia.guardar_competencia_con_categorias.assert_not_called()


def test_crear_competencia_sin_tipo_es_valido(repo_competencia):
    repo_competencia.guardar_competencia_con_categorias.return_value = Competencia("Liga", 2026, idCompetencia=4)

    resultado = CrearCompetenciaUseCase(repo_competencia).ejecutar(CrearCompetenciaDTO(nombre="Liga", anio=2026))

    assert resultado is not None
    assert resultado.tipo is None


def test_crear_competencia_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_competencia):
    repo_competencia.guardar_competencia_con_categorias.return_value = None

    assert CrearCompetenciaUseCase(repo_competencia).ejecutar(CrearCompetenciaDTO("Liga", 2026)) is None


@pytest.mark.parametrize("anio", [1900, 1850, 0])
def test_crear_competencia_con_anio_invalido_lanza_value_error_y_no_guarda(repo_competencia, anio):
    with pytest.raises(ValueError, match="1900"):
        CrearCompetenciaUseCase(repo_competencia).ejecutar(CrearCompetenciaDTO("Liga", anio))

    repo_competencia.guardar_competencia_con_categorias.assert_not_called()


# ------------------------------------------------------------------ InscribirClubEnCompetencia


def _dto_inscripcion(**overrides) -> InscribirClubDTO:
    datos = {"idClub": 1, "idCategoria": 2, "idCompetencia": 3, "fechaPresentacion": "2026-03-01"}
    return InscribirClubDTO(**{**datos, **overrides})


def _preparar_inscripcion(repo_competencia, repo_club, **overrides):
    """Configura los mocks para el camino feliz; cada test pisa (override) lo que quiere romper."""
    categorias_catalogo = [Categoria("U17", idCategoria=1), Categoria("U21", idCategoria=2)]
    config = {
        "club": Club("Atenas", idClub=1),
        "competencia": Competencia("Liga", 2026, idCompetencia=3),
        "categorias": categorias_catalogo,
        "categorias_habilitadas": categorias_catalogo,
        "inscripciones_del_club": [],
        **overrides,
    }
    repo_club.buscar_por_id.return_value = config["club"]
    repo_competencia.buscar_competencia_por_id.return_value = config["competencia"]
    repo_competencia.obtener_categorias.return_value = config["categorias"]
    repo_competencia.obtener_categorias_de_competencia.return_value = config["categorias_habilitadas"]
    repo_competencia.obtener_inscripciones_por_club.return_value = config["inscripciones_del_club"]


def test_inscribir_club_devuelve_la_inscripcion_con_el_id_de_su_lista(repo_competencia, repo_club):
    _preparar_inscripcion(repo_competencia, repo_club)
    repo_competencia.inscribir_con_lista.return_value = (
        Inscripcion(1, 2, 3, idInscripcion=10),
        ListaBuenaFe("2026-03-01", 10, idListaBuenaFe=20),
    )

    resultado = InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club).ejecutar(_dto_inscripcion())

    assert resultado == InscripcionDTO(idInscripcion=10, idClub=1, idCategoria=2, idCompetencia=3, idListaBuenaFe=20)
    # Un unico metodo del repositorio guarda la inscripcion y la lista juntas (atomicidad, AC5)
    repo_competencia.inscribir_con_lista.assert_called_once_with(
        Inscripcion(idClub=1, idCategoria=2, idCompetencia=3), "2026-03-01"
    )
    repo_competencia.guardar_inscripcion.assert_not_called()
    repo_competencia.guardar_lista_buena_fe.assert_not_called()


@pytest.mark.parametrize(
    "overrides, excepcion, fragmento",
    [
        pytest.param({"club": None}, ClubNoEncontradoError, "idClub=1", id="club-inexistente"),
        pytest.param(
            {"competencia": None}, CompetenciaNoEncontradaError, "idCompetencia=3", id="competencia-inexistente"
        ),
        pytest.param(
            {"categorias": [Categoria("U17", idCategoria=1)]},
            CategoriaNoEncontradaError,
            "idCategoria=2",
            id="categoria-inexistente",
        ),
        pytest.param(
            {"categorias_habilitadas": [Categoria("U17", idCategoria=1)]},
            CategoriaNoHabilitadaError,
            "no esta habilitada",
            id="categoria-no-habilitada-en-competencia",
        ),
        pytest.param(
            {"inscripciones_del_club": [Inscripcion(1, 2, 3, idInscripcion=99)]},
            InscripcionDuplicadaError,
            "ya esta inscripto",
            id="mismo-club-competencia-y-categoria",
        ),
    ],
)
def test_inscribir_club_que_rompe_una_regla_lanza_excepcion_y_no_guarda(
    repo_competencia, repo_club, overrides, excepcion, fragmento
):
    _preparar_inscripcion(repo_competencia, repo_club, **overrides)

    with pytest.raises(excepcion, match=fragmento):
        InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club).ejecutar(_dto_inscripcion())

    repo_competencia.inscribir_con_lista.assert_not_called()


@pytest.mark.parametrize(
    "inscripcion_previa",
    [
        pytest.param(Inscripcion(1, 1, 3, idInscripcion=99), id="misma-competencia-otra-categoria"),
        pytest.param(Inscripcion(1, 2, 8, idInscripcion=99), id="misma-categoria-otra-competencia"),
    ],
)
def test_inscribir_club_en_otra_categoria_o_competencia_no_es_duplicado(
    repo_competencia, repo_club, inscripcion_previa
):
    _preparar_inscripcion(repo_competencia, repo_club, inscripciones_del_club=[inscripcion_previa])
    repo_competencia.inscribir_con_lista.return_value = (
        Inscripcion(1, 2, 3, idInscripcion=10),
        ListaBuenaFe("2026-03-01", 10, idListaBuenaFe=20),
    )

    resultado = InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club).ejecutar(_dto_inscripcion())

    assert resultado is not None


def test_inscribir_club_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_competencia, repo_club):
    _preparar_inscripcion(repo_competencia, repo_club)
    repo_competencia.inscribir_con_lista.return_value = None

    assert InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club).ejecutar(_dto_inscripcion()) is None
