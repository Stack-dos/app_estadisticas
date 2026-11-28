"""Tests unitarios de las reglas de negocio de `JugadorPartido` (el boxscore de un jugador en un partido).

Usan la fabrica `crear_boxscore` (ver tests/conftest.py): arma un boxscore valido y cada test pisa
solo el campo que quiere romper con `**overrides`.
"""

import pytest

from dominio.entidades.partido import JugadorPartido


def test_boxscore_valido_por_defecto(crear_boxscore):
    boxscore = crear_boxscore()

    assert boxscore.puntos == boxscore.t2c * 2 + boxscore.t3c * 3 + boxscore.t1c


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"minutosJugados": 0.0}, id="minutos-minimo"),
        pytest.param({"minutosJugados": 48.0}, id="minutos-maximo"),
        pytest.param(
            {"puntos": 0, "t2c": 0, "t2l": 0, "t3c": 0, "t3l": 0, "t1c": 0, "t1l": 0}, id="sin-tiros-ni-puntos"
        ),
        pytest.param({"t2c": 5, "t2l": 5, "puntos": 15}, id="convertidos-igual-a-lanzados"),
    ],
)
def test_boxscore_en_el_limite_es_valido(crear_boxscore, overrides):
    assert crear_boxscore(**overrides) is not None


@pytest.mark.parametrize(
    "overrides, fragmento_del_mensaje",
    [
        # minutos: entre 0 y 48
        pytest.param({"minutosJugados": -0.1}, "Minutos", id="minutos-negativos"),
        pytest.param({"minutosJugados": 48.1}, "Minutos", id="minutos-mayor-a-48"),
        # puntos = T2C*2 + T3C*3 + T1C
        pytest.param({"puntos": 10}, "Puntos", id="puntos-no-coinciden-con-los-tiros"),
        pytest.param({"puntos": -1, "t2c": 0, "t3c": 0, "t1c": 0}, "Puntos", id="puntos-negativos"),
        # convertidos <= lanzados (se pisan tambien los puntos para que esa no sea la regla que falle)
        pytest.param({"t2c": 6, "t2l": 5, "puntos": 17}, "T2C", id="t2-convertidos-mayor-a-lanzados"),
        pytest.param({"t3c": 6, "t3l": 5, "puntos": 24}, "T3C", id="t3-convertidos-mayor-a-lanzados"),
        pytest.param({"t1c": 6, "t1l": 5, "puntos": 13}, "T1C", id="t1-convertidos-mayor-a-lanzados"),
        # el resto de las estadisticas no puede ser negativo
        pytest.param({"rebotesDef": -1}, "Rebotes defensivos", id="rebotes-defensivos-negativos"),
        pytest.param({"rebotesOf": -1}, "Rebotes ofensivos", id="rebotes-ofensivos-negativos"),
        pytest.param({"asistencias": -1}, "Asistencias", id="asistencias-negativas"),
        pytest.param({"recuperos": -1}, "Recuperos", id="recuperos-negativos"),
        pytest.param({"perdidas": -1}, "Perdidas", id="perdidas-negativas"),
        pytest.param({"taponesRecibidos": -1}, "Tapones Recibidos", id="tapones-recibidos-negativos"),
        pytest.param({"taponesRealizados": -1}, "Tapones Realizados", id="tapones-realizados-negativos"),
        pytest.param({"faltasRecibidas": -1}, "Faltas Recibidas", id="faltas-recibidas-negativas"),
        pytest.param({"faltasCometidas": -1}, "Faltas Cometidas", id="faltas-cometidas-negativas"),
    ],
)
def test_boxscore_que_rompe_una_regla_lanza_value_error(crear_boxscore, overrides, fragmento_del_mensaje):
    with pytest.raises(ValueError, match=fragmento_del_mensaje):
        crear_boxscore(**overrides)


@pytest.mark.parametrize("campo", ["idJugador", "idPartido", "idClub"])
def test_boxscore_con_id_que_no_es_entero_lanza_type_error(campo):
    ids = {"idJugador": 1, "idPartido": 1, "idClub": 1}

    with pytest.raises(TypeError, match="recibido str"):
        JugadorPartido(**{**ids, campo: "1"})
