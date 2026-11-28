"""Pantalla "Mis clubes" (US-106): crear un club, ver los del usuario y elegir el club activo.

Es la primera pantalla que cambia sin navegar: al crear un club, la lista se rehace en el lugar
(`refrescar()` reemplaza `lista.controls` y el handler llama a `page.update()`). Navegar a "/clubes"
estando en "/clubes" no serviria: la ruta no cambia, asi que Flet no dispara `on_route_change`.

US-114: abajo, "Clubes rivales" lista los clubes sin usuario (los que se crearon al cargar partidos) para
corregirles el nombre o borrar los que no tienen partidos (por ejemplo uno mal escrito). Como en la
maqueta, cada club se ve con un circulo con sus iniciales y un resumen ("3 categorías · 41 jugadores").
"""

import flet as ft

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.eliminar_club import EliminarClubUseCase
from aplicacion.casos_uso.listar_clubes_rivales import ListarClubesRivalesUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.renombrar_club import RenombrarClubUseCase
from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO, RenombrarClubDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO

SIN_CLUBES = "Todavía no tenés clubes. Creá el primero."
EN_USO = "✓ En uso"
LISTA_CLUBES = "lista_clubes"  # key de la lista: los tests la buscan por aca
LISTA_RIVALES = "lista_clubes_rivales"
SIN_RIVALES = "Todavía no hay rivales: se agregan solos cuando cargás un partido contra un club nuevo."


def iniciales(nombre: str) -> str:
    """Dos letras para el circulo del club: "Hindú Club" -> "HC", "Atenas" -> "AT"."""
    palabras = nombre.split()
    if len(palabras) >= 2:
        return (palabras[0][0] + palabras[1][0]).upper()
    return nombre[:2].upper()


def resumen_club(categorias: int, jugadores: int) -> str:
    """Linea debajo del nombre: "3 categorías · 41 jugadores" (con singular para 1)."""
    texto_cat = "1 categoría" if categorias == 1 else f"{categorias} categorías"
    texto_jug = "1 jugador" if jugadores == 1 else f"{jugadores} jugadores"
    return f"{texto_cat} · {texto_jug}"


def _tarjeta(contenido: ft.Control) -> ft.Container:
    """Lista dentro de un recuadro, como las tarjetas de la maqueta."""
    return ft.Container(
        content=contenido,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=RADIO,
        padding=ft.Padding.symmetric(vertical=ESPACIO_CHICO),
    )


def crear_clubes_view(
    page: ft.Page,
    crear_club_uc: CrearClubUseCase,
    listar_clubes_uc: ListarClubesUsuarioUseCase,
    cambiar_club_uc: CambiarClubActivoUseCase,
    listar_rivales_uc: ListarClubesRivalesUseCase,
    renombrar_club_uc: RenombrarClubUseCase,
    eliminar_club_uc: EliminarClubUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_jugadores_club_uc: ListarJugadoresClubUseCase,
    sesion: SessionManager,
    *,
    aviso: str | None = None,
) -> ft.View:
    """
    Arma la pantalla de clubes. Solo se construye con sesion iniciada (lo garantiza la ruta protegida).

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        crear_club_uc (CrearClubUseCase): Crea el club y vincula al usuario como entrenador.
        listar_clubes_uc (ListarClubesUsuarioUseCase): Los clubes del usuario ("mis clubes").
        cambiar_club_uc (CambiarClubActivoUseCase): Valida que el club elegido sea del usuario.
        listar_rivales_uc (ListarClubesRivalesUseCase): Clubes sin usuario (los rivales).
        renombrar_club_uc (RenombrarClubUseCase): Corrige el nombre de un rival.
        eliminar_club_uc (EliminarClubUseCase): Borra un rival sin partidos.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Para contar las categorias de cada club.
        listar_jugadores_club_uc (ListarJugadoresClubUseCase): Para contar los jugadores de cada club.
        sesion (SessionManager): De ahi sale el usuario; guarda el club activo elegido.
        aviso (str | None): Aviso opcional mostrado cuando otra pantalla redirigio por falta de club activo.

    Returns:
        ft.View: La pantalla, para la ruta "/clubes".
    """
    usuario = sesion.usuario_actual()
    nombre = ft.TextField(label="Nombre del club", autofocus=True)
    error = crear_etiqueta_error()
    lista = ft.Column(key=LISTA_CLUBES, spacing=0)
    lista_rivales = ft.Column(key=LISTA_RIVALES, spacing=0)

    def _avatar(club: ClubDTO) -> ft.CircleAvatar:
        return ft.CircleAvatar(
            content=ft.Text(iniciales(club.nombre), weight=ft.FontWeight.W_600),
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            color=ft.Colors.ON_PRIMARY_CONTAINER,
        )

    def _resumen(club: ClubDTO) -> ft.Text:
        # shortcut: dos consultas por club; alcanza para los pocos clubes de la pantalla. Si crece, un COUNT agrupado.
        categorias = {ins.idCategoria for ins in listar_inscripciones_uc.ejecutar(club.idClub)}
        jugadores = listar_jugadores_club_uc.ejecutar(club.idClub)
        return ft.Text(resumen_club(len(categorias), len(jugadores)), color=ft.Colors.ON_SURFACE_VARIANT)

    def usar(club: ClubDTO) -> None:
        """Handler de "Usar este club": valida, lo deja activo y va al inicio (la barra se redibuja con el club)."""

        def accion() -> None:
            elegido = cambiar_club_uc.ejecutar(usuario.idUsuario, club.idClub)
            sesion.set_active_club(elegido)
            page.navigate("/inicio")

        ejecutar_mostrando_errores(accion, error, nombre="clubes.usar")
        page.update()

    def renglon(club: ClubDTO) -> ft.ListTile:
        # `club` es parametro de esta funcion: cada lambda recuerda su propio club. Con la lambda escrita
        # directo en un `for`, todas recordarian la variable del bucle y usarian el ultimo club.
        activo = sesion.club_activo()
        en_uso = activo is not None and activo.idClub == club.idClub
        chip_en_uso = ft.Container(
            content=ft.Text(EN_USO, color=ft.Colors.ON_SECONDARY_CONTAINER, weight=ft.FontWeight.W_500),
            bgcolor=ft.Colors.SECONDARY_CONTAINER,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        )
        return ft.ListTile(
            leading=_avatar(club),
            title=ft.Text(club.nombre),
            subtitle=_resumen(club),
            trailing=chip_en_uso if en_uso else ft.TextButton("Usar este club", on_click=lambda: usar(club)),
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

        ejecutar_mostrando_errores(accion, error, nombre="clubes.crear")
        page.update()

    def refrescar_rivales() -> None:
        rivales = listar_rivales_uc.ejecutar()
        lista_rivales.controls = [renglon_rival(c) for c in rivales] or [
            ft.Text(SIN_RIVALES, color=ft.Colors.ON_SURFACE_VARIANT)
        ]

    def renombrar(club: ClubDTO) -> None:
        """Abre un dialogo con el nombre actual; Guardar lo cambia y rehace la lista."""
        campo = ft.TextField(label="Nombre del club", value=club.nombre, autofocus=True)
        error_dialogo = crear_etiqueta_error()

        def guardar() -> None:
            def accion() -> None:
                if renombrar_club_uc.ejecutar(RenombrarClubDTO(idClub=club.idClub, nombre=campo.value or "")) is None:
                    raise RuntimeError("Renombrar el club no devolvio el club (fallo al guardar en la base)")
                page.pop_dialog()
                refrescar_rivales()

            ejecutar_mostrando_errores(accion, error_dialogo, nombre="clubes.renombrar")
            page.update()

        campo.on_submit = guardar
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Renombrar club rival"),
                content=ft.Column([campo, error_dialogo], tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda: page.pop_dialog()),
                    ft.FilledButton("Guardar", on_click=guardar),
                ],
            )
        )

    def eliminar(club: ClubDTO) -> None:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_club_uc.ejecutar(club.idClub):
                    raise RuntimeError("No se pudo eliminar el club de la base")
                refrescar_rivales()

            ejecutar_mostrando_errores(
                accion, error, nombre="clubes.eliminar"
            )  # el mismo aviso de errores de la pantalla
            page.update()

        pedir_confirmacion(
            page,
            "Eliminar club rival",
            f"Se borra '{club.nombre}' con sus inscripciones y listas. Sus jugadores quedan cargados.",
            al_confirmar,
        )

    def renglon_rival(club: ClubDTO) -> ft.ListTile:
        return ft.ListTile(
            leading=_avatar(club),
            title=ft.Text(club.nombre),
            subtitle=_resumen(club),
            trailing=ft.Row(
                [
                    ft.IconButton(ft.Icons.EDIT, tooltip="Renombrar", on_click=lambda: renombrar(club)),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Eliminar", on_click=lambda: eliminar(club)),
                ],
                tight=True,
            ),
        )

    refrescar_rivales()
    refrescar()  # la primera vez no hace falta update(): la pantalla todavia no se dibujo

    # Alta en un panel al costado del listado; Enter en el nombre crea igual que el boton (crear_formulario)
    alta = ft.Column(
        [
            ft.Text("Nuevo club", weight=ft.FontWeight.W_600),
            crear_formulario([nombre], error, "Crear club", crear, ancho=None),
        ],
        spacing=ESPACIO,
    )
    controles_principales: list[ft.Control] = []
    if aviso:
        controles_principales.append(
            ft.Container(
                content=ft.Text(aviso, color=ft.Colors.ON_SECONDARY_CONTAINER),
                bgcolor=ft.Colors.SECONDARY_CONTAINER,
                padding=ESPACIO,
                border_radius=RADIO,
            )
        )
    controles_principales += [
        ft.Text("Tus clubes", weight=ft.FontWeight.W_600),
        _tarjeta(lista),
        ft.Text("Clubes rivales", weight=ft.FontWeight.W_600),
        ft.Text(
            "Se crean solos al cargar un partido contra un club nuevo. Si escribiste mal un nombre, corregilo acá.",
            color=ft.Colors.ON_SURFACE_VARIANT,
        ),
        _tarjeta(lista_rivales),
    ]
    contenido = crear_pagina("Mis clubes", controles_principales, lateral=alta)
    return crear_vista_interna(page, sesion, "/clubes", contenido)
