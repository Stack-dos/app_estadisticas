"""Aviso de version nueva al abrir la app (spike: docs/spike/spike_aviso_actualizaciones.md).

La consulta a GitHub corre en otro hilo (`page.run_thread`): la ventana se dibuja enseguida y el aviso
aparece cuando llega la respuesta, o nunca si no hay internet.
"""

import flet as ft

from aplicacion.casos_uso.buscar_actualizacion import BuscarActualizacionUseCase
from aplicacion.casos_uso.omitir_version import OmitirVersionUseCase
from aplicacion.dtos.version_dto import VersionPublicadaDTO
from infraestructura.logger import get_logger
from infraestructura.observabilidad import nueva_accion

logger = get_logger(__name__)


def buscar_version_en_segundo_plano(
    page: ft.Page, buscar_uc: BuscarActualizacionUseCase, omitir_uc: OmitirVersionUseCase
) -> None:
    """
    Lanza la busqueda de version nueva en otro hilo y, si hay una, muestra el aviso.

    Args:
        page (ft.Page): La ventana donde se muestra el aviso.
        buscar_uc (BuscarActualizacionUseCase): Decide si hay que avisar.
        omitir_uc (OmitirVersionUseCase): Lo usa el boton "Omitir esta versión".
    """

    def buscar() -> None:
        with nueva_accion("aviso_version.buscar"):
            # Un error en este hilo no lo ve nadie (el executor se lo guarda): se loguea y la app sigue
            try:
                version = buscar_uc.ejecutar()
                if version is not None:
                    page.show_dialog(crear_aviso_version(page, version, omitir_uc))
            except Exception:
                logger.exception("Fallo la busqueda de version nueva: se sigue sin avisar")

    page.run_thread(buscar)


def crear_aviso_version(page: ft.Page, version: VersionPublicadaDTO, omitir_uc: OmitirVersionUseCase) -> ft.Banner:
    """
    Arma el aviso: un Banner arriba de la pantalla con "Descargar", "Omitir esta versión" y "Ahora no".

    Banner y no SnackBar: el SnackBar admite un solo boton y se va solo a los 4 segundos.

    Args:
        page (ft.Page): La ventana (para cerrar el aviso con `pop_dialog`).
        version (VersionPublicadaDTO): La version a avisar.
        omitir_uc (OmitirVersionUseCase): Para recordar "Omitir esta versión".

    Returns:
        ft.Banner: El aviso, listo para `page.show_dialog`.
    """

    async def descargar() -> None:
        page.pop_dialog()
        logger.info(f"Abriendo la pagina de descarga de {version.tag}")
        # En Flet 1.x ya no existe page.launch_url: es un servicio, y es asincrono
        await ft.UrlLauncher().launch_url(version.url)

    def omitir() -> None:
        page.pop_dialog()
        omitir_uc.ejecutar(version.tag)

    return ft.Banner(
        leading=ft.Icon(ft.Icons.SYSTEM_UPDATE_ALT),
        content=ft.Text(f"Hay una versión nueva de StatsPro: {version.tag.removeprefix('v')}."),
        actions=[
            ft.TextButton("Omitir esta versión", on_click=omitir),
            ft.TextButton("Ahora no", on_click=lambda: page.pop_dialog()),
            ft.FilledButton("Descargar", on_click=descargar),
        ],
    )
