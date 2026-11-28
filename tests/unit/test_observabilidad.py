"""Tests de la US-110: contexto por accion, filtros, formato JSON y eleccion del sink."""

import json
import logging
import sys
import uuid
from logging.handlers import RotatingFileHandler

import pytest

import config.rutas as r
from dominio.exceptions import ClubYaExisteError
from infraestructura.logger import crear_handler
from infraestructura.observabilidad import (
    TAPADO,
    FiltroContexto,
    FiltroSecretos,
    FormateadorJson,
    contexto_actual,
    nueva_accion,
    redactar,
)
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores

logger = logging.getLogger("tests.observabilidad")


def _registro(mensaje: str = "hola", *args: object, **extras: object) -> logging.LogRecord:
    registro = logging.LogRecord("tests", logging.INFO, __file__, 1, mensaje, args or None, None)
    registro.__dict__.update(extras)
    return registro


def _json(registro: logging.LogRecord) -> dict:
    for filtro in (FiltroContexto(), FiltroSecretos()):
        filtro.filter(registro)
    return json.loads(FormateadorJson().format(registro))


# ------------------------------------------------------------------ contexto


def test_fuera_de_una_accion_no_hay_contexto():
    assert contexto_actual() is None


def test_una_accion_tiene_un_uuid4_y_se_cierra_al_salir():
    with nueva_accion("clubes.crear") as ctx:
        assert contexto_actual() == ctx
        assert ctx.accion == "clubes.crear"
        assert uuid.UUID(ctx.correlation_id).version == 4

    assert contexto_actual() is None


def test_dos_acciones_tienen_ids_distintos():
    with nueva_accion("a") as primera:
        pass
    with nueva_accion("b") as segunda:
        pass

    assert primera.correlation_id != segunda.correlation_id


def test_una_accion_adentro_de_otra_sigue_la_de_afuera():
    with nueva_accion("carga_partido.guardar") as afuera, nueva_accion("navegar") as adentro:
        assert adentro == afuera

    assert contexto_actual() is None


def test_la_accion_se_cierra_aunque_haya_excepcion():
    with pytest.raises(RuntimeError), nueva_accion("x"):
        raise RuntimeError("bug")

    assert contexto_actual() is None


def test_el_filtro_copia_el_contexto_al_registro():
    with nueva_accion("clubes.crear") as ctx:
        datos = _json(_registro())

    assert datos["correlation_id"] == ctx.correlation_id
    assert datos["accion"] == "clubes.crear"


# ------------------------------------------------------------------ JSON


def test_el_json_trae_los_campos_fijos_y_los_extras():
    datos = _json(_registro("Club %s", "creado", evento="club_creado", id_club=7))

    assert datos["nivel"] == "INFO"
    assert datos["logger"] == "tests"
    assert datos["mensaje"] == "Club creado"
    assert datos["evento"] == "club_creado"
    assert datos["id_club"] == 7
    assert datos["correlation_id"] is None
    assert datos["ts"].endswith("+00:00")


def test_el_json_trae_el_traceback():
    try:
        raise ValueError("bug")
    except ValueError:
        registro = logging.LogRecord("tests", logging.ERROR, __file__, 1, "fallo", None, sys.exc_info())

    assert "ValueError: bug" in _json(registro)["exc"]


# ------------------------------------------------------------------ secretos


@pytest.mark.parametrize(
    "texto",
    [
        "password=secreta123",
        "password: secreta123",
        "{'password': 'secreta123'}",
        'password_hash="secreta123"',
        "token=secreta123 y algo mas",
        "contraseña = secreta123",
    ],
)
def test_redactar_tapa_los_valores_secretos(texto):
    tapado = redactar(texto)

    assert "secreta123" not in tapado
    assert TAPADO in tapado


def test_redactar_tapa_emails():
    assert redactar("El email 'nico@ejemplo.com' ya esta registrado") == "El email '***' ya esta registrado"


def test_redactar_no_toca_mensajes_comunes():
    assert redactar("Email o contraseña incorrectos") == "Email o contraseña incorrectos"


def test_el_filtro_tapa_mensaje_extras_y_traceback():
    try:
        raise ValueError("password=secreta123")
    except ValueError:
        registro = logging.LogRecord("tests", logging.ERROR, __file__, 1, "login %s", ("token=abc",), sys.exc_info())
    registro.__dict__.update(password="secreta123", detalle="mail nico@ejemplo.com")

    datos = _json(registro)

    assert datos["mensaje"] == f"login token={TAPADO}"
    assert datos["password"] == TAPADO
    assert datos["detalle"] == f"mail {TAPADO}"
    assert "secreta123" not in datos["exc"]


# ------------------------------------------------------------------ sink y nivel


def test_sink_consola_escribe_en_stderr():
    handler = crear_handler("consola", "DEBUG")

    assert type(handler) is logging.StreamHandler
    assert handler.level == logging.DEBUG
    assert isinstance(handler.formatter, FormateadorJson)
    assert {type(f) for f in handler.filters} == {FiltroContexto, FiltroSecretos}


def test_sink_archivo_rota_en_la_carpeta_de_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(r, "APP_LOG_FILE", str(tmp_path / "logs" / "app.log"))

    handler = crear_handler("archivo", "warning")
    handler.close()

    assert isinstance(handler, RotatingFileHandler)
    assert handler.level == logging.WARNING
    assert (tmp_path / "logs").is_dir()


def test_sink_o_nivel_desconocido_usan_el_default(tmp_path, monkeypatch):
    monkeypatch.setattr(r, "LOG_DIR", str(tmp_path))
    monkeypatch.setattr(r, "APP_LOG_FILE", str(tmp_path / "app.log"))

    handler = crear_handler("seq", "MUCHO")
    handler.close()

    assert isinstance(handler, RotatingFileHandler)
    assert handler.level == logging.INFO


# ------------------------------------------------------------------ inicio y fin de cada accion de la GUI


def _eventos(registros: list[logging.LogRecord]) -> list[tuple[str, str | None]]:
    return [(r.evento, getattr(r, "resultado", None)) for r in registros if hasattr(r, "evento")]


def test_una_accion_ok_loguea_inicio_y_fin_con_duracion(registros_log):
    ejecutar_mostrando_errores(lambda: logger.info("adentro"), crear_etiqueta_error(), nombre="clubes.crear")

    assert _eventos(registros_log) == [("accion_inicio", None), ("accion_fin", "ok")]
    fin = registros_log[-1]
    assert fin.pantalla == "clubes"
    assert fin.duracion_ms >= 0
    assert len({r.correlation_id for r in registros_log}) == 1  # el log de adentro tambien
    assert {r.accion for r in registros_log} == {"clubes.crear"}


def test_un_error_de_dominio_es_warning_y_termina_en_error_dominio(registros_log):
    def accion() -> None:
        raise ClubYaExisteError("Ya existe un club llamado 'Atenas'")

    ejecutar_mostrando_errores(accion, crear_etiqueta_error(), nombre="clubes.crear")

    assert _eventos(registros_log) == [
        ("accion_inicio", None),
        ("error_dominio", None),
        ("accion_fin", "error_dominio"),
    ]
    assert registros_log[1].levelno == logging.WARNING


def test_un_error_inesperado_es_error_y_termina_en_error(registros_log):
    def accion() -> None:
        raise RuntimeError("bug")

    ejecutar_mostrando_errores(accion, crear_etiqueta_error(), nombre="clubes.crear")

    assert _eventos(registros_log)[-1] == ("accion_fin", "error")
    assert registros_log[1].levelno == logging.ERROR
