"""Tests de BuscarActualizacionUseCase y OmitirVersionUseCase (spike de aviso de version nueva), sin red.

La fuente es un mock; el almacen es uno en memoria, asi se verifica el estado que queda guardado.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.buscar_actualizacion import BuscarActualizacionUseCase
from aplicacion.casos_uso.omitir_version import OmitirVersionUseCase
from aplicacion.dtos.version_dto import EstadoAvisoDTO, VersionPublicadaDTO
from aplicacion.servicios.estado_aviso_almacen import EstadoAvisoAlmacen
from aplicacion.servicios.fuente_de_versiones import FuenteDeVersiones

HOY = date(2026, 11, 28)
AYER = date(2026, 11, 27)
V101 = VersionPublicadaDTO(tag="v1.0.1", url="https://github.com/Stack-dos/app_estadisticas/releases/tag/v1.0.1")


class AlmacenEnMemoria(EstadoAvisoAlmacen):
    def __init__(self, estado: EstadoAvisoDTO | None = None):
        self.estado = estado or EstadoAvisoDTO()

    def cargar(self) -> EstadoAvisoDTO:
        return self.estado

    def guardar(self, estado: EstadoAvisoDTO) -> None:
        self.estado = estado


@pytest.fixture
def fuente():
    fuente = MagicMock(spec=FuenteDeVersiones)
    fuente.ultima_version_publicada.return_value = V101
    return fuente


def _buscar(fuente, almacen, instalada="1.0.0"):
    return BuscarActualizacionUseCase(fuente, almacen, version_instalada=instalada, hoy=lambda: HOY).ejecutar()


def test_primera_vez_con_version_nueva_avisa_y_guarda_el_chequeo(fuente):
    almacen = AlmacenEnMemoria()

    assert _buscar(fuente, almacen) == V101
    assert almacen.estado == EstadoAvisoDTO(ultimo_chequeo=HOY)


def test_ya_se_chequeo_hoy_no_consulta(fuente):
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=HOY))

    assert _buscar(fuente, almacen) is None
    fuente.ultima_version_publicada.assert_not_called()


def test_se_chequeo_ayer_vuelve_a_consultar(fuente):
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=AYER))

    assert _buscar(fuente, almacen) == V101
    assert almacen.estado.ultimo_chequeo == HOY


def test_ultimo_chequeo_en_el_futuro_por_reloj_atrasado_igual_consulta(fuente):
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=date(2027, 1, 1)))

    assert _buscar(fuente, almacen) == V101
    assert almacen.estado.ultimo_chequeo == HOY


@pytest.mark.parametrize("instalada", ["1.0.1", "1.0.2", "2.0.0"])
def test_misma_version_o_mas_nueva_instalada_no_avisa(fuente, instalada):
    assert _buscar(fuente, AlmacenEnMemoria(), instalada=instalada) is None


def test_fuente_sin_respuesta_no_avisa_pero_guarda_el_chequeo(fuente):
    fuente.ultima_version_publicada.return_value = None
    almacen = AlmacenEnMemoria()

    assert _buscar(fuente, almacen) is None
    assert almacen.estado.ultimo_chequeo == HOY  # sin internet tampoco se reintenta en cada arranque


def test_tag_raro_no_avisa(fuente):
    fuente.ultima_version_publicada.return_value = VersionPublicadaDTO(tag="latest", url=V101.url)

    assert _buscar(fuente, AlmacenEnMemoria()) is None


def test_version_omitida_no_avisa_y_conserva_la_omitida(fuente):
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=AYER, tag_omitido="v1.0.1"))

    assert _buscar(fuente, almacen) is None
    assert almacen.estado == EstadoAvisoDTO(ultimo_chequeo=HOY, tag_omitido="v1.0.1")


def test_otra_version_despues_de_la_omitida_si_avisa(fuente):
    v102 = VersionPublicadaDTO(tag="v1.0.2", url=V101.url.replace("1.0.1", "1.0.2"))
    fuente.ultima_version_publicada.return_value = v102
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=AYER, tag_omitido="v1.0.1"))

    assert _buscar(fuente, almacen) == v102


def test_omitir_guarda_el_tag_y_conserva_el_chequeo():
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(ultimo_chequeo=HOY))

    OmitirVersionUseCase(almacen).ejecutar("v1.0.1")

    assert almacen.estado == EstadoAvisoDTO(ultimo_chequeo=HOY, tag_omitido="v1.0.1")


def test_omitir_otra_version_reemplaza_la_anterior():
    almacen = AlmacenEnMemoria(EstadoAvisoDTO(tag_omitido="v1.0.1"))

    OmitirVersionUseCase(almacen).ejecutar("v1.0.2")

    assert almacen.estado.tag_omitido == "v1.0.2"


def test_omitir_y_al_otro_dia_no_avisa_la_omitida(fuente):
    almacen = AlmacenEnMemoria()
    assert _buscar(fuente, almacen) == V101  # primer arranque: aparece el aviso
    OmitirVersionUseCase(almacen).ejecutar(V101.tag)  # el usuario toca "Omitir"
    almacen.estado = EstadoAvisoDTO(ultimo_chequeo=AYER, tag_omitido=almacen.estado.tag_omitido)  # pasa un dia

    assert _buscar(fuente, almacen) is None
