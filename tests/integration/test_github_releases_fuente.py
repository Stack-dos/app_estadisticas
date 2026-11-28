"""Spike de aviso de version nueva, paso 4: el adaptador de GitHub nunca lanza y ante cualquier problema da None.

Se prueba contra un servidor HTTP local (sin internet): cada test elige que responde.
"""

import json
import socket
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

import pytest

from aplicacion.dtos.version_dto import VersionPublicadaDTO
from infraestructura.github_releases_fuente import GithubReleasesFuente

RELEASE = {
    "tag_name": "v1.0.1",
    "html_url": "https://github.com/Stack-dos/app_estadisticas/releases/tag/v1.0.1",
    "prerelease": False,
}


class _Handler(BaseHTTPRequestHandler):
    # Lo que responde el servidor; cada test lo cambia con el fixture `servidor`
    status = 200
    cuerpo = b""
    demora = 0.0
    headers_recibidos: ClassVar[dict[str, str]] = {}

    def do_GET(self):
        type(self).headers_recibidos = dict(self.headers)
        time.sleep(self.demora)
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.cuerpo)

    def log_message(self, *args):  # sin ruido en la salida de pytest
        pass


@pytest.fixture
def servidor() -> Iterator[type[_Handler]]:
    "Levanta el servidor en un puerto libre; el test configura la respuesta en la clase que devuelve"
    handler = type("Handler", (_Handler,), {})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    hilo = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    hilo.start()
    handler.url = f"http://127.0.0.1:{httpd.server_port}/releases/latest"  # type: ignore[attr-defined]
    yield handler
    httpd.shutdown()
    httpd.server_close()


def _fuente(servidor, timeout=2.0):
    return GithubReleasesFuente(url=servidor.url, timeout=timeout)


def test_release_valido_devuelve_tag_y_url(servidor):
    servidor.cuerpo = json.dumps(RELEASE).encode()

    assert _fuente(servidor).ultima_version_publicada() == VersionPublicadaDTO(
        tag="v1.0.1", url="https://github.com/Stack-dos/app_estadisticas/releases/tag/v1.0.1"
    )


def test_manda_user_agent_y_accept_de_github(servidor):
    servidor.cuerpo = json.dumps(RELEASE).encode()

    _fuente(servidor).ultima_version_publicada()

    assert servidor.headers_recibidos["User-Agent"] == "statspro-basketball"
    assert servidor.headers_recibidos["Accept"] == "application/vnd.github+json"


def test_404_sin_releases_estables_devuelve_none(servidor, caplog):
    servidor.status = 404
    servidor.cuerpo = b'{"message": "Not Found", "status": "404"}'

    assert _fuente(servidor).ultima_version_publicada() is None
    assert "404" in caplog.text


@pytest.mark.parametrize("status", [403, 500, 503])  # 403: se paso el limite de 60 pedidos por hora
def test_otro_error_http_devuelve_none(servidor, status, caplog):
    servidor.status = status

    assert _fuente(servidor).ultima_version_publicada() is None
    assert str(status) in caplog.text


@pytest.mark.parametrize(
    "cuerpo",
    [
        b"no es json",
        b"\xff\xfe",  # bytes que no son UTF-8
        b"[]",
        b"{}",
        json.dumps({"tag_name": 1, "html_url": RELEASE["html_url"]}).encode(),
        json.dumps({"tag_name": "v1.0.1"}).encode(),
        # La URL no es de GitHub: no se abre en el navegador
        json.dumps({"tag_name": "v1.0.1", "html_url": "https://malicioso.example/descarga"}).encode(),
        json.dumps({"tag_name": "v1.0.1", "html_url": "https://github.com.malicioso.example/"}).encode(),
    ],
)
def test_respuesta_rara_devuelve_none(servidor, cuerpo):
    servidor.cuerpo = cuerpo

    assert _fuente(servidor).ultima_version_publicada() is None


def test_timeout_devuelve_none_sin_esperar_de_mas(servidor, caplog):
    servidor.demora = 1.0
    servidor.cuerpo = json.dumps(RELEASE).encode()

    inicio = time.monotonic()
    assert _fuente(servidor, timeout=0.2).ultima_version_publicada() is None
    assert time.monotonic() - inicio < 0.9
    assert "TimeoutError" in caplog.text


def test_sin_conexion_devuelve_none(caplog):
    # Un puerto que nadie escucha: el sistema rechaza la conexion, igual que sin servidor del otro lado
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]

    assert GithubReleasesFuente(url=f"http://127.0.0.1:{puerto}/", timeout=1).ultima_version_publicada() is None
    assert "URLError" in caplog.text
