"""La version embebida tiene que tener la forma X.Y.Z: si no, el aviso de version nueva nunca avisaria."""

from config.version import VERSION
from dominio.versiones import parsear_version


def test_la_version_embebida_es_x_y_z():
    assert parsear_version(VERSION) is not None
