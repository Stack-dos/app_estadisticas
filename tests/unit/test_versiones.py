"""Tests de la comparacion de versiones del aviso de version nueva (spike, paso 3)."""

import pytest

from dominio.versiones import hay_version_nueva, parsear_version


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1.0.0", (1, 0, 0)),
        ("v1.0.0", (1, 0, 0)),
        ("v1.10.0", (1, 10, 0)),
        (" v2.3.4 ", (2, 3, 4)),
    ],
)
def test_parsear_version_valida(texto, esperado):
    assert parsear_version(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    ["", "latest", "v1.0", "1", "v1.0.0-rc.1", "v1.0.0.0", "V1.0.0", "vv1.0.0", "v1.a.0", "v\u0661.0.0"],
)
def test_parsear_version_invalida_devuelve_none(texto):
    assert parsear_version(texto) is None


@pytest.mark.parametrize(
    ("instalada", "tag", "esperado"),
    [
        ("1.0.0", "v1.0.0", False),  # la misma
        ("1.0.0", "v1.0.1", True),  # parche nuevo
        ("1.0.0", "v1.1.0", True),
        ("1.0.0", "v2.0.0", True),
        ("1.0.0", "v0.9.9", False),  # mas vieja
        ("1.2.0", "v1.1.9", False),
        ("1.9.0", "v1.10.0", True),  # como texto daria False
        ("1.10.0", "v1.9.0", False),
        ("1.0.0", "1.0.1", True),  # tag sin "v"
    ],
)
def test_hay_version_nueva(instalada, tag, esperado):
    assert hay_version_nueva(instalada, tag) is esperado


@pytest.mark.parametrize("tag", ["v1.1", "latest", "", "v2.0.0-rc.1"])
def test_tag_raro_no_avisa(tag):
    assert hay_version_nueva("1.0.0", tag) is False


def test_version_instalada_invalida_no_avisa():
    assert hay_version_nueva("desconocida", "v9.9.9") is False
