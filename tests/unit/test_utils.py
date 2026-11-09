"""Tests unitarios de src/utils.py (helpers puros compartidos por todas las capas)."""

import pytest

from utils import id_persistido


def test_id_persistido_devuelve_el_id():
    assert id_persistido(7, "Club") == 7


def test_id_persistido_none_lanza_runtime_error_con_nombre_de_entidad():
    with pytest.raises(RuntimeError, match="Club"):
        id_persistido(None, "Club")
