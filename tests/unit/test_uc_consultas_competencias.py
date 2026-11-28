"""Tests unitarios de los casos de uso de consulta de competencias e inscripciones (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from dominio.entidades.competencia import Competencia, Inscripcion, ListaBuenaFe
from dominio.exceptions import ListaBuenaFeNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


@pytest.fixture
def repo_competencia():
    return MagicMock(spec=CompetenciaRepositorio)


# ------------------------------------------------------------------ ListarCompetencias


def test_listar_competencias_convierte_cada_competencia_en_dto(repo_competencia):
    repo_competencia.obtener_todas_competencias.return_value = [
        Competencia("Liga Provincial", 2026, "PROVINCIAL", idCompetencia=1),
        Competencia("Copa", 2027, idCompetencia=2),
    ]

    resultado = ListarCompetenciasUseCase(repo_competencia).ejecutar()

    assert resultado == [
        CompetenciaDTO(idCompetencia=1, nombre="Liga Provincial", anio=2026, tipo="PROVINCIAL"),
        CompetenciaDTO(idCompetencia=2, nombre="Copa", anio=2027, tipo=None),
    ]


def test_listar_competencias_sin_competencias_devuelve_lista_vacia(repo_competencia):
    repo_competencia.obtener_todas_competencias.return_value = []

    assert ListarCompetenciasUseCase(repo_competencia).ejecutar() == []


def test_listar_competencias_con_una_competencia_sin_id_es_un_error_del_repositorio(repo_competencia):
    repo_competencia.obtener_todas_competencias.return_value = [Competencia("Liga", 2026)]

    with pytest.raises(RuntimeError, match="Competencia"):
        ListarCompetenciasUseCase(repo_competencia).ejecutar()


# ------------------------------------------------------------------ ListarInscripcionesClub


def test_listar_inscripciones_incluye_el_id_de_la_lista_de_cada_una(repo_competencia):
    repo_competencia.obtener_inscripciones_por_club.return_value = [
        Inscripcion(1, 2, 3, idInscripcion=10),
        Inscripcion(1, 4, 3, idInscripcion=11),
    ]
    listas = {
        10: ListaBuenaFe("2026-03-01", 10, idListaBuenaFe=20),
        11: ListaBuenaFe("2026-03-02", 11, idListaBuenaFe=21),
    }
    repo_competencia.obtener_lista_por_inscripcion.side_effect = lambda id_inscripcion: listas[id_inscripcion]

    resultado = ListarInscripcionesClubUseCase(repo_competencia).ejecutar(1)

    assert resultado == [
        InscripcionDTO(idInscripcion=10, idClub=1, idCategoria=2, idCompetencia=3, idListaBuenaFe=20),
        InscripcionDTO(idInscripcion=11, idClub=1, idCategoria=4, idCompetencia=3, idListaBuenaFe=21),
    ]
    repo_competencia.obtener_inscripciones_por_club.assert_called_once_with(1)


def test_listar_inscripciones_sin_inscripciones_devuelve_lista_vacia(repo_competencia):
    repo_competencia.obtener_inscripciones_por_club.return_value = []

    assert ListarInscripcionesClubUseCase(repo_competencia).ejecutar(1) == []


def test_listar_inscripciones_con_una_inscripcion_sin_lista_lanza_excepcion(repo_competencia):
    repo_competencia.obtener_inscripciones_por_club.return_value = [Inscripcion(1, 2, 3, idInscripcion=10)]
    repo_competencia.obtener_lista_por_inscripcion.return_value = None

    with pytest.raises(ListaBuenaFeNoEncontradaError, match="idInscripcion=10"):
        ListarInscripcionesClubUseCase(repo_competencia).ejecutar(1)
