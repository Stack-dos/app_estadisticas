"""Tests del adaptador JSON del estado del aviso de version nueva, sobre archivos temporales (`tmp_path`).

Nunca tocan el `~/.statspro/aviso_version.json` real: la ruta se inyecta por constructor.
"""

import json
from datetime import date

import pytest

from aplicacion.dtos.version_dto import EstadoAvisoDTO
from infraestructura.persistencia.json_estado_aviso_almacen import JsonEstadoAvisoAlmacen

VACIO = EstadoAvisoDTO()


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / ".statspro" / "aviso_version.json"  # la carpeta todavia no existe, como la primera vez


@pytest.fixture
def almacen(ruta):
    return JsonEstadoAvisoAlmacen(ruta)


def test_sin_archivo_devuelve_estado_vacio(almacen):
    assert almacen.cargar() == VACIO


@pytest.mark.parametrize(
    "estado",
    [
        EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 28), tag_omitido="v1.0.1"),
        EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 28)),
        EstadoAvisoDTO(tag_omitido="v1.0.1"),
        VACIO,
    ],
)
def test_guardar_y_cargar_devuelve_el_mismo_estado(almacen, estado):
    almacen.guardar(estado)

    assert almacen.cargar() == estado


def test_guardar_crea_la_carpeta_y_escribe_la_fecha_en_iso(almacen, ruta):
    almacen.guardar(EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 28), tag_omitido="v1.0.1"))

    assert json.loads(ruta.read_text(encoding="utf-8")) == {"ultimo_chequeo": "2026-11-28", "tag_omitido": "v1.0.1"}


def test_guardar_dos_veces_reemplaza_el_estado_anterior(almacen):
    almacen.guardar(EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 27)))
    almacen.guardar(EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 28), tag_omitido="v1.0.1"))

    assert almacen.cargar() == EstadoAvisoDTO(ultimo_chequeo=date(2026, 11, 28), tag_omitido="v1.0.1")


@pytest.mark.parametrize(
    "contenido",
    [
        b"no es json",
        b"\xff\xfe",  # bytes que no son UTF-8
        b"[]",
        b"{}",
        b'{"ultimo_chequeo": "2026-11-28"}',  # falta un campo
        b'{"ultimo_chequeo": "2026-11-28", "tag_omitido": null, "otro": 1}',  # sobra un campo
        b'{"ultimo_chequeo": "ayer", "tag_omitido": null}',
        b'{"ultimo_chequeo": "2026-13-01", "tag_omitido": null}',
        b'{"ultimo_chequeo": 20261128, "tag_omitido": null}',
        b'{"ultimo_chequeo": null, "tag_omitido": 101}',
    ],
)
def test_archivo_danado_devuelve_estado_vacio_sin_lanzar(almacen, ruta, contenido, caplog):
    ruta.parent.mkdir(parents=True)
    ruta.write_bytes(contenido)

    assert almacen.cargar() == VACIO
    assert "se ignora" in caplog.text


def test_guardar_si_el_disco_falla_no_lanza(tmp_path, caplog):
    # La "carpeta" es un archivo: mkdir falla con un OSError
    (tmp_path / "ocupado").write_text("x")
    almacen = JsonEstadoAvisoAlmacen(tmp_path / "ocupado" / "aviso_version.json")

    almacen.guardar(EstadoAvisoDTO(tag_omitido="v1.0.1"))

    assert "No se pudo guardar" in caplog.text
