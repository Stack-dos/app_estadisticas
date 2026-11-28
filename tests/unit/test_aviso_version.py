"""Tests del aviso de version nueva en la GUI (spike, paso 7), sin ventana y sin red.

`page.run_thread` se reemplaza por una llamada directa: el hilo de verdad lo maneja Flet.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest
from ayudantes_flet import controles, textos

from aplicacion.casos_uso.buscar_actualizacion import BuscarActualizacionUseCase
from aplicacion.casos_uso.omitir_version import OmitirVersionUseCase
from aplicacion.dtos.version_dto import VersionPublicadaDTO
from infraestructura.ui.flet import app
from infraestructura.ui.flet.components.aviso_version import buscar_version_en_segundo_plano

V101 = VersionPublicadaDTO(tag="v1.0.1", url="https://github.com/Stack-dos/app_estadisticas/releases/tag/v1.0.1")


@pytest.fixture
def page():
    page = MagicMock(spec=ft.Page)
    page.run_thread.side_effect = lambda handler, *args: handler(*args)
    return page


@pytest.fixture
def buscar_uc():
    return MagicMock(spec=BuscarActualizacionUseCase, **{"ejecutar.return_value": V101})


@pytest.fixture
def omitir_uc():
    return MagicMock(spec=OmitirVersionUseCase)


def _aviso(page, buscar_uc, omitir_uc) -> ft.Banner:
    buscar_version_en_segundo_plano(page, buscar_uc, omitir_uc)
    page.show_dialog.assert_called_once()
    return page.show_dialog.call_args.args[0]


def _boton(aviso: ft.Banner, texto: str):
    return next(c for c in controles(aviso) if isinstance(c, ft.TextButton | ft.FilledButton) and c.content == texto)


def test_la_busqueda_corre_en_otro_hilo(page, buscar_uc, omitir_uc):
    buscar_version_en_segundo_plano(page, buscar_uc, omitir_uc)

    page.run_thread.assert_called_once()


def test_con_version_nueva_muestra_un_banner_con_la_version(page, buscar_uc, omitir_uc):
    aviso = _aviso(page, buscar_uc, omitir_uc)

    assert isinstance(aviso, ft.Banner)
    assert "Hay una versión nueva de StatsPro: 1.0.1." in textos(aviso)


def test_sin_version_nueva_no_muestra_nada(page, buscar_uc, omitir_uc):
    buscar_uc.ejecutar.return_value = None

    buscar_version_en_segundo_plano(page, buscar_uc, omitir_uc)

    page.show_dialog.assert_not_called()


def test_un_error_inesperado_se_loguea_y_no_se_propaga(page, buscar_uc, omitir_uc, caplog):
    buscar_uc.ejecutar.side_effect = RuntimeError("bug")

    buscar_version_en_segundo_plano(page, buscar_uc, omitir_uc)

    page.show_dialog.assert_not_called()
    assert "Fallo la busqueda de version nueva" in caplog.text


def test_descargar_cierra_el_aviso_y_abre_la_pagina_del_release(page, buscar_uc, omitir_uc):
    aviso = _aviso(page, buscar_uc, omitir_uc)
    lanzador = MagicMock(**{"launch_url": AsyncMock()})

    with patch.object(ft, "UrlLauncher", return_value=lanzador):
        asyncio.run(_boton(aviso, "Descargar").on_click())

    page.pop_dialog.assert_called_once()
    lanzador.launch_url.assert_awaited_once_with(V101.url)


def test_omitir_cierra_el_aviso_y_recuerda_el_tag(page, buscar_uc, omitir_uc):
    aviso = _aviso(page, buscar_uc, omitir_uc)

    _boton(aviso, "Omitir esta versión").on_click()

    page.pop_dialog.assert_called_once()
    omitir_uc.ejecutar.assert_called_once_with("v1.0.1")


def test_ahora_no_solo_cierra_el_aviso(page, buscar_uc, omitir_uc):
    aviso = _aviso(page, buscar_uc, omitir_uc)

    _boton(aviso, "Ahora no").on_click()

    page.pop_dialog.assert_called_once()
    omitir_uc.ejecutar.assert_not_called()


def test_armar_aviso_por_defecto_esta_activo(monkeypatch, tmp_path):
    monkeypatch.delenv(app.VAR_SIN_AVISO_VERSION, raising=False)

    assert app.armar_aviso_version(tmp_path / "aviso_version.json") is not None


def test_armar_aviso_con_la_variable_de_entorno_queda_desactivado(monkeypatch, tmp_path):
    monkeypatch.setenv(app.VAR_SIN_AVISO_VERSION, "1")

    assert app.armar_aviso_version(tmp_path / "aviso_version.json") is None
