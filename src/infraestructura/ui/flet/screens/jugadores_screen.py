"""Pantalla de plantel de jugadores del club activo (US-112): listar, alta sin duplicados, buscar y baja.

US-113: la tabla ocupa todo el ancho; el alta se abre en un dialogo ("Nuevo jugador"), las acciones de
cada fila son iconos con descripcion al pasar el mouse, y la fecha de baja se pide dentro del dialogo de
baja (antes era un campo suelto arriba de la tabla que no se entendia para que estaba).

US-114 (ajuste con la maqueta): un buscador y un selector "Del club" / "En todos los clubes". "En todos
los clubes" es solo para consultar (cada jugador con su club actual). Se quito "Vincular jugador existente":
un jugador siempre se crea con club y no se puede traer de otro club (tiene un vinculo abierto). Solo si
al dar de alta aparece el mismo jugador **sin club** (lo dieron de baja), se ofrece sumarlo en vez de duplicarlo.
"""

from datetime import date

import flet as ft

from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_jugadores_todos import ListarJugadoresTodosUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.club_dto import DesvincularJugadorDTO, VincularJugadorClubDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, EditarJugadorDTO, JugadorConClubDTO, JugadorDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.jugador import Jugador
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO
from utils import normalizar_texto

TABLA_JUGADORES = "tabla_jugadores"
SELECTOR_ALCANCE = "selector_alcance_jugadores"
COINCIDENCIAS_ALTA = "coincidencias_alta_jugador"
DEL_CLUB, TODOS_LOS_CLUBES = "club", "todos"
COLUMNAS_JUGADORES = ("Jugador", "Año nac.", "Acciones")
COLUMNAS_TODOS = ("Jugador", "Año nac.", "Club actual", "Acciones")
SIN_JUGADORES = "Este club todavía no tiene jugadores."
SIN_COINCIDENCIAS = "No se encontraron jugadores con ese nombre."
SIN_CLUB = "Sin club"


def coincide(nombre_completo: str, consulta: str) -> bool:
    """Igual que la busqueda del repositorio: todas las palabras, sin mayusculas ni tildes."""
    nombre = normalizar_texto(nombre_completo)
    return all(termino in nombre for termino in normalizar_texto(consulta).split())


def fila_jugador_todos(jugador: JugadorConClubDTO) -> tuple[str, str, str]:
    """Fila de "En todos los clubes": nombre, año y club actual."""
    anio = str(jugador.anioNacimiento) if jugador.anioNacimiento is not None else "—"
    return (jugador.nombre_completo, anio, jugador.club or SIN_CLUB)


def fila_jugador(jugador: JugadorDTO) -> tuple[str, str]:
    """Convierte un `JugadorDTO` en las columnas de texto de la tabla sin exponer su ID."""
    anio = str(jugador.anioNacimiento) if jugador.anioNacimiento is not None else "—"
    return (jugador.nombre_completo, anio)


def _etiqueta_jugador(jugador: JugadorDTO) -> str:
    if jugador.anioNacimiento is None:
        return jugador.nombre_completo
    return f"{jugador.nombre_completo} ({jugador.anioNacimiento})"


def _parsear_anio_opcional(texto: str) -> int | None:
    limpio = texto.strip()
    if not limpio:
        return None
    try:
        return int(limpio)
    except ValueError as err:
        raise DatoInvalidoError("El año de nacimiento debe ser un número entero") from err


def _nombre_y_apellido(jugador: JugadorDTO) -> tuple[str, str]:
    if jugador.nombre or jugador.apellido:
        return jugador.nombre, jugador.apellido
    partes = jugador.nombre_completo.split(" ", 1)
    return (partes[0], partes[1] if len(partes) > 1 else "")


def crear_jugadores_view(
    page: ft.Page,
    listar_jugadores_club_uc: ListarJugadoresClubUseCase,
    registrar_jugador_uc: RegistrarJugadorUseCase,
    vincular_jugador_uc: VincularJugadorAClubUseCase,
    desvincular_jugador_uc: DesvincularJugadorDeClubUseCase,
    buscar_jugadores_uc: BuscarJugadoresPorNombreUseCase,
    editar_jugador_uc: EditarJugadorUseCase,
    eliminar_jugador_uc: EliminarJugadorUseCase,
    listar_jugadores_todos_uc: ListarJugadoresTodosUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de jugadores del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para confirmar bajas, editar y redibujar.
        listar_jugadores_club_uc (ListarJugadoresClubUseCase): Plantel actual del club activo.
        registrar_jugador_uc (RegistrarJugadorUseCase): Alta de un jugador nuevo.
        vincular_jugador_uc (VincularJugadorAClubUseCase): Vincula al club el jugador recien creado (o uno sin club).
        desvincular_jugador_uc (DesvincularJugadorDeClubUseCase): Cierra el vinculo vigente con el club.
        buscar_jugadores_uc (BuscarJugadoresPorNombreUseCase): Busca homonimos antes de dar de alta.
        editar_jugador_uc (EditarJugadorUseCase): Corrige nombre, apellido y año de nacimiento de un jugador.
        eliminar_jugador_uc (EliminarJugadorUseCase): Elimina un jugador sin partidos ni listas de buena fe.
        listar_jugadores_todos_uc (ListarJugadoresTodosUseCase): Todos los jugadores con su club ("En todos").
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/jugadores".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de jugadores requiere un club activo")

    nombre = ft.TextField(label="Nombre", autofocus=True)
    apellido = ft.TextField(label="Apellido")
    anio_nacimiento = ft.TextField(label="Año de nacimiento (opcional)")
    fecha_ingreso = ft.TextField(label="Fecha de ingreso", value=date.today().isoformat())
    error_alta = crear_etiqueta_error()
    panel_coincidencias = ft.Column(key=COINCIDENCIAS_ALTA, spacing=ESPACIO_CHICO, scroll=ft.ScrollMode.AUTO)
    dialogo_abierto = [False]  # si el alta esta abierta en un dialogo, se cierra al terminar bien

    campo_busqueda = ft.TextField(
        label="Buscar",
        hint_text="Apellido o nombre",
        prefix_icon=ft.Icons.SEARCH,
        width=360,
        dense=True,
    )
    selector_alcance = ft.SegmentedButton(
        key=SELECTOR_ALCANCE,
        segments=[
            ft.Segment(value=DEL_CLUB, label="Del club"),
            ft.Segment(value=TODOS_LOS_CLUBES, label="En todos los clubes"),
        ],
        selected=[DEL_CLUB],
        show_selected_icon=False,
    )

    error_tabla = crear_etiqueta_error()
    contenedor_tabla = ft.Column()
    plantel: list[JugadorDTO] = []

    def _vincular_sin_club(jugador: JugadorConClubDTO) -> None:
        """Suma al club un jugador que hoy no tiene club (lo dieron de baja en otro), en vez de duplicarlo."""

        def accion() -> None:
            fecha = fecha_ingreso.value.strip()
            if not fecha:
                raise DatoInvalidoError("Indicá la fecha de ingreso al club")
            vinculo = vincular_jugador_uc.ejecutar(
                VincularJugadorClubDTO(idJugador=jugador.id, idClub=club.idClub, fechaDesde=fecha)
            )
            if vinculo is None:
                raise RuntimeError("No se pudo vincular el jugador al club en la base")
            _limpiar_alta()
            refrescar_plantel()

        ejecutar_mostrando_errores(accion, error_alta, nombre="jugadores.sumar_sin_club")
        page.update()

    def _boton_dar_de_baja(jugador: JugadorDTO) -> ft.IconButton:
        def abrir_dialogo() -> None:
            campo_fecha_baja = ft.TextField(label="Fecha de baja", value=date.today().isoformat())
            error_baja = crear_etiqueta_error()

            def confirmar() -> None:
                def accion() -> None:
                    fecha = (campo_fecha_baja.value or "").strip()
                    if not fecha:
                        raise DatoInvalidoError("Indicá la fecha de baja")
                    cerrado = desvincular_jugador_uc.ejecutar(
                        DesvincularJugadorDTO(idJugador=jugador.id, fechaHasta=fecha)
                    )
                    if cerrado is None:
                        raise RuntimeError("No se pudo dar de baja al jugador en la base")
                    page.pop_dialog()
                    refrescar_plantel()

                ejecutar_mostrando_errores(accion, error_baja, nombre="jugadores.desvincular")
                page.update()

            page.show_dialog(
                ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Dar de baja jugador"),
                    content=ft.Column(
                        [
                            ft.Text(
                                f"{jugador.nombre_completo} deja de ser parte de {club.nombre} desde esta fecha. "
                                "Sus partidos y estadísticas se conservan."
                            ),
                            campo_fecha_baja,
                            error_baja,
                        ],
                        tight=True,
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda: page.pop_dialog()),
                        ft.FilledButton("Dar de baja", on_click=confirmar),
                    ],
                )
            )

        return ft.IconButton(icon=ft.Icons.PERSON_REMOVE_OUTLINED, tooltip="Dar de baja", on_click=abrir_dialogo)

    def _boton_editar(jugador: JugadorDTO) -> ft.IconButton:
        def abrir_edicion() -> None:
            nom_inicial, ape_inicial = _nombre_y_apellido(jugador)
            campo_nombre = ft.TextField(label="Nombre", value=nom_inicial, autofocus=True)
            campo_apellido = ft.TextField(label="Apellido", value=ape_inicial)
            campo_anio = ft.TextField(
                label="Año de nacimiento (opcional)",
                value=str(jugador.anioNacimiento) if jugador.anioNacimiento is not None else "",
            )
            error_edicion = crear_etiqueta_error()

            def cancelar() -> None:
                page.pop_dialog()

            def guardar() -> None:
                def accion() -> None:
                    anio = _parsear_anio_opcional(campo_anio.value)
                    actualizado = editar_jugador_uc.ejecutar(
                        EditarJugadorDTO(
                            idJugador=jugador.id,
                            nombre=campo_nombre.value.strip(),
                            apellido=campo_apellido.value.strip(),
                            anioNacimiento=anio,
                        )
                    )
                    if actualizado is None:
                        raise RuntimeError("No se pudo actualizar el jugador en la base")
                    page.pop_dialog()
                    refrescar_plantel()

                ejecutar_mostrando_errores(accion, error_edicion, nombre="jugadores.editar")
                page.update()

            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text("Editar jugador"),
                content=ft.Column([campo_nombre, campo_apellido, campo_anio, error_edicion], tight=True),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.FilledButton("Guardar", on_click=guardar),
                ],
            )
            page.show_dialog(dialogo)

        return ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, tooltip="Editar", on_click=abrir_edicion)

    def _boton_eliminar(jugador: JugadorDTO) -> ft.IconButton:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_jugador_uc.ejecutar(jugador.id):
                    raise RuntimeError("No se pudo eliminar el jugador en la base")
                refrescar_plantel()

            ejecutar_mostrando_errores(accion, error_tabla, nombre="jugadores.eliminar")
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Eliminar jugador",
                f"¿Querés eliminar definitivamente a {jugador.nombre_completo}? "
                "Solo se puede eliminar si no tiene partidos ni figura en listas de buena fe.",
                al_confirmar,
                texto_confirmar="Eliminar",
            )

        return ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, tooltip="Eliminar", on_click=abrir_confirmacion)

    def _redibujar_tabla() -> None:
        """Dibuja la tabla segun el selector y el buscador (filtra en memoria, mientras se escribe)."""
        consulta = campo_busqueda.value or ""
        if selector_alcance.selected == [TODOS_LOS_CLUBES]:
            todos = [j for j in listar_jugadores_todos_uc.ejecutar() if coincide(j.nombre_completo, consulta)]
            columnas: tuple[str, ...] = COLUMNAS_TODOS
            # Solo se puede borrar desde aca a quien no tiene club (lo dieron de baja); el resto es de consulta.
            filas: list[tuple[str | ft.Control, ...]] = [
                (
                    *fila_jugador_todos(j),
                    _boton_eliminar(JugadorDTO(j.nombre_completo, j.id, j.anioNacimiento)) if j.club is None else "",
                )
                for j in todos
            ]
            vacio = SIN_COINCIDENCIAS
        else:
            visibles = [j for j in plantel if coincide(j.nombre_completo, consulta)]
            columnas = COLUMNAS_JUGADORES
            filas = [
                (
                    *fila_jugador(j),
                    ft.Row([_boton_editar(j), _boton_dar_de_baja(j), _boton_eliminar(j)], spacing=0),
                )
                for j in visibles
            ]
            vacio = SIN_COINCIDENCIAS if consulta.strip() else SIN_JUGADORES
        contenedor_tabla.controls = [crear_tabla_datos(columnas, filas, mensaje_vacio=vacio, clave=TABLA_JUGADORES)]

    def refrescar_plantel() -> None:
        plantel.clear()
        plantel.extend(listar_jugadores_club_uc.ejecutar(club.idClub))
        _redibujar_tabla()

    def al_filtrar() -> None:
        ejecutar_mostrando_errores(_redibujar_tabla, error_tabla, nombre="jugadores.filtrar")
        page.update()

    campo_busqueda.on_change = al_filtrar
    selector_alcance.on_change = al_filtrar

    def _limpiar_alta() -> None:
        nombre.value = ""
        apellido.value = ""
        anio_nacimiento.value = ""
        panel_coincidencias.controls = []
        _cerrar_alta()

    def _crear_y_vincular(datos: CrearJugadorDTO, fecha: str) -> None:
        nuevo = registrar_jugador_uc.ejecutar(datos)
        if nuevo is None:
            raise RuntimeError("No se pudo registrar el jugador en la base")
        vinculo = vincular_jugador_uc.ejecutar(
            VincularJugadorClubDTO(idJugador=nuevo.id, idClub=club.idClub, fechaDesde=fecha)
        )
        if vinculo is None:
            raise RuntimeError("El jugador se creó pero no se pudo vincular al club activo")
        _limpiar_alta()
        refrescar_plantel()

    def _cerrar_alta() -> None:
        if dialogo_abierto[0]:
            dialogo_abierto[0] = False
            page.pop_dialog()

    def _forzar_alta(datos: CrearJugadorDTO, fecha: str) -> None:
        def accion() -> None:
            _crear_y_vincular(datos, fecha)

        ejecutar_mostrando_errores(accion, error_alta, nombre="jugadores.forzar_alta")
        page.update()

    def registrar() -> None:
        def accion() -> None:
            nom = nombre.value.strip()
            ape = apellido.value.strip()
            anio = _parsear_anio_opcional(anio_nacimiento.value)
            fecha = fecha_ingreso.value.strip()
            if not fecha:
                raise DatoInvalidoError("Indicá la fecha de ingreso al club")
            # Valida reglas de dominio (nombre, apellido, rango de año) antes de buscar coincidencias.
            Jugador(nombre=nom, apellido=ape, anioNacimiento=anio)
            datos = CrearJugadorDTO(nombre=nom, apellido=ape, anioNacimiento=anio)

            ids_homonimos = {j.id for j in buscar_jugadores_uc.ejecutar(f"{nom} {ape}")}
            if ids_homonimos:
                homonimos = [j for j in listar_jugadores_todos_uc.ejecutar() if j.id in ids_homonimos]
                panel_coincidencias.controls = [
                    ft.Text("Ya existe un jugador con ese nombre:", weight=ft.FontWeight.W_600),
                    *(_aviso_homonimo(j) for j in homonimos),
                    ft.TextButton("Crear nuevo jugador de todas formas", on_click=lambda: _forzar_alta(datos, fecha)),
                ]
                return

            _crear_y_vincular(datos, fecha)

        ejecutar_mostrando_errores(accion, error_alta, nombre="jugadores.registrar")
        page.update()

    def _aviso_homonimo(jugador: JugadorConClubDTO) -> ft.Container:
        etiqueta = _etiqueta_jugador(JugadorDTO(jugador.nombre_completo, jugador.id, jugador.anioNacimiento))
        if jugador.club is None:
            detalle: ft.Control = ft.TextButton(
                f"Sin club: sumarlo a {club.nombre}", on_click=lambda: _vincular_sin_club(jugador)
            )
        else:
            detalle = ft.Text(f"en {jugador.club}", color=ft.Colors.ON_SURFACE_VARIANT)
        return ft.Container(
            content=ft.Row([ft.Text(etiqueta, expand=True), detalle], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ESPACIO_CHICO,
            bgcolor=ft.Colors.TERTIARY_CONTAINER,
            border_radius=RADIO,
        )

    refrescar_plantel()
    fecha_ingreso.on_submit = registrar

    def abrir_alta() -> None:
        error_alta.value = ""
        panel_coincidencias.controls = []
        dialogo_abierto[0] = True

        def cancelar() -> None:
            dialogo_abierto[0] = False
            page.pop_dialog()

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Nuevo jugador de {club.nombre}"),
                content=ft.Column(
                    [nombre, apellido, anio_nacimiento, fecha_ingreso, error_alta, panel_coincidencias],
                    tight=True,
                    width=420,
                    spacing=ESPACIO_CHICO,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar),
                    ft.FilledButton("Registrar jugador", on_click=registrar),
                ],
            )
        )

    contenido = crear_pagina(
        "Jugadores",
        [
            ft.Row(
                [
                    ft.Row([campo_busqueda, selector_alcance], spacing=ESPACIO, wrap=True),
                    ft.FilledButton("Nuevo jugador", icon=ft.Icons.PERSON_ADD, on_click=abrir_alta),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            error_tabla,
            contenedor_tabla,
        ],
        subtitulo=f"Club activo: {club.nombre}",
    )
    return crear_vista_interna(page, sesion, "/jugadores", contenido)
