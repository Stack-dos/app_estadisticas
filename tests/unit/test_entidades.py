"""Tests unitarios de la validacion de tipos (`__post_init__`) de las entidades de dominio.

No usan SQLite: una entidad se valida al construirse, sin necesidad de un repositorio.
"""

import pytest

from dominio.entidades.club import Club, UsuarioClub
from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.entidades.jugador import Jugador, JugadorClub
from dominio.entidades.partido import Partido
from dominio.entidades.usuario import Usuario

# Para cada entidad: (datos validos, {campo: valor con tipo incorrecto}).
# Cada par campo/valor genera un test: la entidad valida + ese unico campo roto.
ENTIDADES = [
    (Club, {"nombre": "Atenas"}, {"nombre": None, "idClub": "1"}),
    (UsuarioClub, {"rol": "DT"}, {"rol": 5, "idUsuario": "1", "idClub": "1"}),
    (
        Jugador,
        {"nombre": "Manu", "apellido": "Ginobili", "dni": 20111222, "anioNacimiento": 1977},
        {"nombre": 10, "apellido": None, "dni": "20111222", "anioNacimiento": "1977", "idJugador": "1"},
    ),
    (
        JugadorClub,
        {"fechaDesde": "2026-01-01", "fechaHasta": None},
        {"fechaDesde": 20260101, "fechaHasta": 20261231, "idJugador": "1", "idClub": "1"},
    ),
    (
        Competencia,
        {"nombre": "Liga", "anio": 2026},
        {"nombre": 1, "anio": "2026", "tipo": 5, "idCompetencia": "1"},
    ),
    (Categoria, {"nombre": "U21"}, {"nombre": 21, "idCategoria": "1"}),
    (
        Inscripcion,
        {"idClub": 1, "idCategoria": 1, "idCompetencia": 1},
        {"idClub": "1", "idCategoria": "1", "idCompetencia": "1", "idInscripcion": "1"},
    ),
    (
        ListaBuenaFe,
        {"fechaPresentacion": "2026-03-01", "idInscripcion": 1},
        {"fechaPresentacion": 20260301, "idInscripcion": "1", "idListaBuenaFe": "1"},
    ),
    (JugadorListaBuenaFe, {"idJugador": 1, "idListaBuenaFe": 1}, {"idJugador": "1", "idListaBuenaFe": "1"}),
    (
        Partido,
        {"fecha": "2026-05-21", "estadio": None, "idCompetencia": 1, "idClubLocal": 1, "idClubVisitante": 2},
        {
            "fecha": 20260521,
            "estadio": 5,
            "idCompetencia": "1",
            "idClubLocal": "1",
            "idClubVisitante": "2",
            "idPartido": "1",
        },
    ),
    (
        Usuario,
        {"nombre": "Claudio", "email": "claudio@gmail.com", "password_hash": "hash-de-prueba"},
        {"nombre": 10, "email": True, "password_hash": 123456, "idUsuario": "1"},
    ),
]

CASOS_VALIDOS = [pytest.param(clase, validos, id=clase.__name__) for clase, validos, _ in ENTIDADES]

CASOS_INVALIDOS = [
    pytest.param(clase, validos, campo, valor, id=f"{clase.__name__}.{campo}={valor!r}")
    for clase, validos, invalidos in ENTIDADES
    for campo, valor in invalidos.items()
]


@pytest.mark.parametrize("clase, validos", CASOS_VALIDOS)
def test_entidad_con_datos_validos_se_construye(clase, validos):
    entidad = clase(**validos)

    for campo, valor in validos.items():
        assert getattr(entidad, campo) == valor


@pytest.mark.parametrize("clase, validos, campo, valor", CASOS_INVALIDOS)
def test_entidad_con_tipo_invalido_lanza_type_error(clase, validos, campo, valor):
    # Todos los mensajes informan el tipo recibido: "<campo> debe ser <tipo>, recibido <tipo real>"
    with pytest.raises(TypeError, match=f"recibido {type(valor).__name__}"):
        clase(**{**validos, campo: valor})
