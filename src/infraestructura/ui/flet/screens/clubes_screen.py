"""Pantalla "Mis clubes" (US-106): crear un club, ver los del usuario y elegir el club activo.

Es la primera pantalla que cambia sin navegar: al crear un club, la lista se rehace en el lugar
(`refrescar()` reemplaza `lista.controls` y el handler llama a `page.update()`). Navegar a "/clubes"
estando en "/clubes" no serviria: la ruta no cambia, asi que Flet no dispara `on_route_change`.
"""

import flet as ft

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.barra_superior import crear_barra_superior
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores

SIN_CLUBES = "Todavía no tenés clubes. Creá el primero."
EN_USO = "✓ En uso"


def crear_clubes_view(
    page: ft.Page,
    crear_club_uc: CrearClubUseCase,
    listar_clubes_uc: ListarClubesUsuarioUseCase,
    cambiar_club_uc: CambiarClubActivoUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de clubes. Solo se construye con sesion iniciada (lo garantiza la ruta protegida).

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        crear_club_uc (CrearClubUseCase): Crea el club y vincula al usuario como entrenador.
        listar_clubes_uc (ListarClubesUsuarioUseCase): Los clubes del usuario ("mis clubes").
        cambiar_club_uc (CambiarClubActivoUseCase): Valida que el club elegido sea del usuario.
        sesion (SessionManager): De ahi sale el usuario; guarda el club activo elegido.

    Returns:
        ft.View: La pantalla, para la ruta "/clubes".
    """
    usuario = sesion.usuario_actual()
    nombre = ft.TextField(label="Nombre del club", autofocus=True)
    error = crear_etiqueta_error()
    lista = ft.Column()

    def usar(club: ClubDTO) -> None:
        """Handler de "Usar este club": valida, lo deja activo y va al inicio (la barra se redibuja con el club)."""

        def accion() -> None:
            elegido = cambiar_club_uc.ejecutar(usuario.idUsuario, club.idClub)
            sesion.set_active_club(elegido)
            page.navigate("/inicio")

        ejecutar_mostrando_errores(accion, error)
        page.update()

    def renglon(club: ClubDTO) -> ft.ListTile:
        # `club` es parametro de esta funcion: cada lambda recuerda su propio club. Con la lambda escrita
        # directo en un `for`, todas recordarian la variable del bucle y usarian el ultimo club.
        activo = sesion.club_activo()
        en_uso = activo is not None and activo.idClub == club.idClub
        return ft.ListTile(
            title=ft.Text(club.nombre),
            trailing=ft.Text(EN_USO) if en_uso else ft.TextButton("Usar este club", on_click=lambda: usar(club)),
        )

    def refrescar() -> None:
        """Rehace la lista con los clubes del usuario. No llama a `update()`: lo hace el handler."""
        clubes = listar_clubes_uc.ejecutar(usuario.idUsuario)
        lista.controls = [renglon(c) for c in clubes] or [ft.Text(SIN_CLUBES)]

    def crear() -> None:
        """Handler de "Crear club" y del Enter en el nombre."""

        def accion() -> None:
            club = crear_club_uc.ejecutar(CrearClubDTO(nombre=nombre.value), usuario.idUsuario)
            if club is None:
                # El repositorio devuelve None si SQLite fallo al guardar: no es culpa del usuario.
                raise RuntimeError("Crear el club no devolvio el club (fallo al guardar en la base)")
            nombre.value = ""  # solo si salio bien: ante un error, el usuario corrige lo que escribio
            refrescar()

        ejecutar_mostrando_errores(accion, error)
        page.update()

    nombre.on_submit = crear
    refrescar()  # la primera vez no hace falta update(): la pantalla todavia no se dibujo

    return ft.View(
        route="/clubes",
        appbar=crear_barra_superior(page, sesion),
        controls=[
            ft.Text("Mis clubes", size=24),
            nombre,
            ft.Button("Crear club", on_click=crear),
            error,
            lista,
        ],
    )
