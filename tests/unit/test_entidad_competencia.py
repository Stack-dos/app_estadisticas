import pytest

from dominio.entidades.competencia import Competencia


@pytest.mark.parametrize("anio", [1900, 1899, 1000, 0, -5])
def test_competencia_anio_menor_o_igual_a_1900_lanza_value_error(anio):
    """Mismo criterio que el CHECK(anio > 1900) del schema."""
    with pytest.raises(ValueError):
        Competencia(nombre="Liga Vieja", anio=anio)


@pytest.mark.parametrize("anio", [1901, 1990, 2000, 2026])
def test_competencia_anio_mayor_a_1900_es_valido(anio):
    """Antes se rechazaba el 2000 y todo lo anterior: el limite real es 1900."""
    assert Competencia(nombre="Liga", anio=anio).anio == anio
