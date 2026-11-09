"""Tests del adaptador JSON de la sesion recordada (US-106), sobre archivos temporales (`tmp_path`).

Nunca tocan el `~/.statspro/session.json` real: la ruta se inyecta por constructor.
"""

import json

import pytest

from aplicacion.dtos.session_dto import SessionDTO
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen

SESION = SessionDTO(usuario_id=3, email="dt@club.com", club_activo_id=7)


@pytest.fixture
def ruta(tmp_path):
    return tmp_path / ".statspro" / "session.json"  # la carpeta todavia no existe, como la primera vez


@pytest.fixture
def almacen(ruta):
    return JsonSesionAlmacen(ruta)


@pytest.mark.parametrize("sesion", [SESION, SessionDTO(usuario_id=3, email="ñandú@club.com", club_activo_id=None)])
def test_guardar_y_cargar_devuelve_la_misma_sesion(almacen, sesion):
    almacen.guardar(sesion)

    assert almacen.cargar() == sesion


def test_guardar_crea_la_carpeta_y_solo_escribe_los_tres_campos(almacen, ruta):
    almacen.guardar(SESION)

    guardado = json.loads(ruta.read_text(encoding="utf-8"))
    assert guardado == {"usuario_id": 3, "email": "dt@club.com", "club_activo_id": 7}


def test_guardar_dos_veces_reemplaza_la_sesion_anterior(almacen):
    almacen.guardar(SESION)
    almacen.guardar(SessionDTO(usuario_id=4, email="otro@club.com"))

    assert almacen.cargar() == SessionDTO(usuario_id=4, email="otro@club.com", club_activo_id=None)


def test_cargar_sin_archivo_devuelve_none(almacen):
    assert almacen.cargar() is None


@pytest.mark.parametrize(
    "contenido",
    [
        pytest.param("{esto no es json", id="json roto"),
        pytest.param("", id="archivo vacio"),
        pytest.param("[]", id="no es un objeto"),
        pytest.param('{"usuario_id": 3, "email": "dt@club.com"}', id="falta un campo"),
        pytest.param('{"usuario_id": 3, "email": "dt@club.com", "club_activo_id": 7, "pass": "x"}', id="campo de mas"),
        pytest.param('{"usuario_id": "3", "email": "dt@club.com", "club_activo_id": 7}', id="id como texto"),
        pytest.param('{"usuario_id": true, "email": "dt@club.com", "club_activo_id": 7}', id="id booleano"),
        pytest.param('{"usuario_id": null, "email": "dt@club.com", "club_activo_id": 7}', id="id nulo"),
        pytest.param('{"usuario_id": 3, "email": 5, "club_activo_id": 7}', id="email no es texto"),
        pytest.param('{"usuario_id": 3, "email": "dt@club.com", "club_activo_id": "7"}', id="club como texto"),
    ],
)
def test_cargar_un_archivo_danado_devuelve_none_sin_lanzar(almacen, ruta, contenido, caplog):
    ruta.parent.mkdir(parents=True)
    ruta.write_text(contenido, encoding="utf-8")

    assert almacen.cargar() is None
    assert "se ignora" in caplog.text
    assert "dt@club.com" not in caplog.text  # el contenido (datos personales) nunca va al log


def test_cargar_bytes_que_no_son_utf8_devuelve_none(almacen, ruta):
    ruta.parent.mkdir(parents=True)
    ruta.write_bytes(b"\xff\xfe\x00basura")

    assert almacen.cargar() is None


def test_borrar_elimina_el_archivo(almacen, ruta):
    almacen.guardar(SESION)

    almacen.borrar()

    assert not ruta.exists()
    assert almacen.cargar() is None


def test_borrar_sin_archivo_no_falla(almacen):
    almacen.borrar()
    almacen.borrar()


def test_guardar_si_el_disco_falla_no_lanza(tmp_path, caplog):
    """Mejor esfuerzo: que no se pueda recordar la sesion no debe impedir iniciarla."""
    (tmp_path / "es_un_archivo").write_text("x")
    almacen = JsonSesionAlmacen(tmp_path / "es_un_archivo" / "session.json")  # la "carpeta" es un archivo

    almacen.guardar(SESION)

    assert "no se va a recordar" in caplog.text


def test_borrar_si_el_disco_falla_no_lanza(tmp_path, caplog):
    (tmp_path / "session.json").mkdir()  # una carpeta con el nombre del archivo: unlink falla
    almacen = JsonSesionAlmacen(tmp_path / "session.json")

    almacen.borrar()

    assert "se va a seguir recordando" in caplog.text
