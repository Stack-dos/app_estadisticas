"""Pantalla de plantel de jugadores del club activo (US-112): listar, alta sin duplicados, buscar/vincular y baja."""

from datetime import date

import flet as ft

from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.dtos.club_dto import DesvincularJugadorDTO, VincularJugadorClubDTO
from aplicacion.dtos.jugador_dto import CrearJugadorDTO, EditarJugadorDTO, JugadorDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.jugador import Jugador
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO

TABLA_JUGADORES = "tabla_jugadores"
RESULTADOS_BUSQUEDA = "resultados_busqueda_jugadores"
COINCIDENCIAS_ALTA = "coincidencias_alta_jugador"
COLUMNAS_JUGADORES = ("Jugador", "Año nac.", "Acciones")
SIN_JUGADORES = "Este club todavía no tiene jugadores vinculados."
SIN_COINCIDENCIAS = "No se encontraron jugadores con ese nombre."


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
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de jugadores del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para confirmar bajas, editar y redibujar.
        listar_jugadores_club_uc (ListarJugadoresClubUseCase): Plantel actual del club activo.
        registrar_jugador_uc (RegistrarJugadorUseCase): Alta de un jugador nuevo.
        vincular_jugador_uc (VincularJugadorAClubUseCase): Vincula un jugador existente o recien creado al club.
        desvincular_jugador_uc (DesvincularJugadorDeClubUseCase): Cierra el vinculo vigente con el club.
        buscar_jugadores_uc (BuscarJugadoresPorNombreUseCase): Busca por nombre/apellido en todos los clubes.
        editar_jugador_uc (EditarJugadorUseCase): Corrige nombre, apellido y año de nacimiento de un jugador.
        eliminar_jugador_uc (EliminarJugadorUseCase): Elimina un jugador sin partidos ni listas de buena fe.
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
    panel_coincidencias = ft.Column(key=COINCIDENCIAS_ALTA, spacing=ESPACIO_CHICO)

    campo_busqueda = ft.TextField(label="Buscar jugador existente (nombre o apellido)")
    error_busqueda = crear_etiqueta_error()
    panel_resultados = ft.Column(key=RESULTADOS_BUSQUEDA, spacing=ESPACIO_CHICO)

    fecha_baja = ft.TextField(label="Fecha de baja", value=date.today().isoformat(), width=200)
    error_tabla = crear_etiqueta_error()
    contenedor_tabla = ft.Column()

    ids_plantel_actual: set[int] = set()

    def _vincular_a_club(jugador: JugadorDTO, destino_error: ft.Text) -> None:
        def accion() -> None:
            fecha = fecha_ingreso.value.strip()
            if not fecha:
                raise DatoInvalidoError("Indicá la fecha de ingreso al club")
            vinculo = vincular_jugador_uc.ejecutar(
                VincularJugadorClubDTO(idJugador=jugador.id, idClub=club.idClub, fechaDesde=fecha)
            )
            if vinculo is None:
                raise RuntimeError("No se pudo vincular el jugador al club en la base")
            panel_coincidencias.controls = []
            nombre.value = ""
            apellido.value = ""
            anio_nacimiento.value = ""
            refrescar_plantel()
            _actualizar_resultados_si_hay_busqueda()

        ejecutar_mostrando_errores(accion, destino_error)
        page.update()

    def _boton_dar_de_baja(jugador: JugadorDTO) -> ft.TextButton:
        def al_confirmar() -> None:
            def accion() -> None:
                fecha = fecha_baja.value.strip()
                if not fecha:
                    raise DatoInvalidoError("Indicá la fecha de baja")
                cerrado = desvincular_jugador_uc.ejecutar(DesvincularJugadorDTO(idJugador=jugador.id, fechaHasta=fecha))
                if cerrado is None:
                    raise RuntimeError("No se pudo dar de baja al jugador en la base")
                refrescar_plantel()
                _actualizar_resultados_si_hay_busqueda()

            ejecutar_mostrando_errores(accion, error_tabla)
            page.update()

        def abrir_confirmacion() -> None:
            pedir_confirmacion(
                page,
                "Dar de baja jugador",
                f"¿Querés desvincular a {jugador.nombre_completo} de {club.nombre}?",
                al_confirmar,
                texto_confirmar="Dar de baja",
            )

        return ft.TextButton("Dar de baja", on_click=abrir_confirmacion)

    def _boton_editar(jugador: JugadorDTO) -> ft.TextButton:
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
                    _actualizar_resultados_si_hay_busqueda()

                ejecutar_mostrando_errores(accion, error_edicion)
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

        return ft.TextButton("Editar", on_click=abrir_edicion)

    def _boton_eliminar(jugador: JugadorDTO, destino_error: ft.Text = error_tabla) -> ft.TextButton:
        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_jugador_uc.ejecutar(jugador.id):
                    raise RuntimeError("No se pudo eliminar el jugador en la base")
                refrescar_plantel()
                _actualizar_resultados_si_hay_busqueda()

            ejecutar_mostrando_errores(accion, destino_error)
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

        return ft.TextButton("Eliminar", on_click=abrir_confirmacion)

    def refrescar_plantel() -> None:
        jugadores = listar_jugadores_club_uc.ejecutar(club.idClub)
        ids_plantel_actual.clear()
        ids_plantel_actual.update(j.id for j in jugadores)
        filas = [
            (
                *fila_jugador(j),
                ft.Row([_boton_editar(j), _boton_dar_de_baja(j), _boton_eliminar(j)], spacing=0),
            )
            for j in jugadores
        ]
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_JUGADORES,
                filas,
                mensaje_vacio=SIN_JUGADORES,
                clave=TABLA_JUGADORES,
            )
        ]

    def _renglon_busqueda(
        jugador: JugadorDTO, destino_error: ft.Text, *, permitir_gestion: bool = False
    ) -> ft.Container:
        ya_en_club = jugador.id in ids_plantel_actual
        accion_control: ft.Control = (
            ft.Text("Ya está en el club", color=ft.Colors.ON_SURFACE_VARIANT)
            if ya_en_club
            else ft.TextButton("Vincular al club", on_click=lambda: _vincular_a_club(jugador, destino_error))
        )
        acciones = [accion_control]
        if permitir_gestion:
            acciones.extend([_boton_editar(jugador), _boton_eliminar(jugador, destino_error)])
        return ft.Container(
            content=ft.Row(
                [ft.Text(_etiqueta_jugador(jugador), expand=True), ft.Row(acciones, spacing=0)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ESPACIO_CHICO,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=RADIO,
        )

    def _renderizar_busqueda(consulta: str) -> None:
        if not consulta.strip():
            panel_resultados.controls = []
            return
        encontrados = buscar_jugadores_uc.ejecutar(consulta)
        if not encontrados:
            panel_resultados.controls = [ft.Text(SIN_COINCIDENCIAS, color=ft.Colors.ON_SURFACE_VARIANT)]
            return
        panel_resultados.controls = [_renglon_busqueda(j, error_busqueda, permitir_gestion=True) for j in encontrados]

    def _actualizar_resultados_si_hay_busqueda() -> None:
        if campo_busqueda.value.strip():
            _renderizar_busqueda(campo_busqueda.value)

    def buscar() -> None:
        def accion() -> None:
            _renderizar_busqueda(campo_busqueda.value)

        ejecutar_mostrando_errores(accion, error_busqueda)
        page.update()

    campo_busqueda.on_submit = buscar

    def _crear_y_vincular(datos: CrearJugadorDTO, fecha: str) -> None:
        nuevo = registrar_jugador_uc.ejecutar(datos)
        if nuevo is None:
            raise RuntimeError("No se pudo registrar el jugador en la base")
        vinculo = vincular_jugador_uc.ejecutar(
            VincularJugadorClubDTO(idJugador=nuevo.id, idClub=club.idClub, fechaDesde=fecha)
        )
        if vinculo is None:
            raise RuntimeError("El jugador se creó pero no se pudo vincular al club activo")
        nombre.value = ""
        apellido.value = ""
        anio_nacimiento.value = ""
        panel_coincidencias.controls = []
        refrescar_plantel()
        _actualizar_resultados_si_hay_busqueda()

    def _forzar_alta(datos: CrearJugadorDTO, fecha: str) -> None:
        def accion() -> None:
            _crear_y_vincular(datos, fecha)

        ejecutar_mostrando_errores(accion, error_alta)
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

            coincidencias = buscar_jugadores_uc.ejecutar(f"{nom} {ape}")
            if coincidencias:
                panel_coincidencias.controls = [
                    ft.Text(
                        "Ya existen jugadores con ese nombre. Podés vincular uno en vez de duplicarlo:",
                        weight=ft.FontWeight.W_600,
                    ),
                    *(_renglon_busqueda(j, error_alta) for j in coincidencias),
                    ft.TextButton("Crear nuevo jugador de todas formas", on_click=lambda: _forzar_alta(datos, fecha)),
                ]
                return

            _crear_y_vincular(datos, fecha)

        ejecutar_mostrando_errores(accion, error_alta)
        page.update()

    refrescar_plantel()

    lateral = ft.Column(
        [
            ft.Text("Nuevo jugador", weight=ft.FontWeight.W_600),
            crear_formulario(
                [nombre, apellido, anio_nacimiento, fecha_ingreso],
                error_alta,
                "Registrar jugador",
                registrar,
                ancho=None,
            ),
            panel_coincidencias,
        ],
        spacing=ESPACIO,
    )

    contenido = crear_pagina(
        "Jugadores",
        [
            ft.Text("Plantel actual", weight=ft.FontWeight.W_600),
            fecha_baja,
            contenedor_tabla,
            error_tabla,
            ft.Divider(),
            ft.Text("Vincular jugador existente", weight=ft.FontWeight.W_600),
            ft.Row([campo_busqueda, ft.FilledButton("Buscar", on_click=buscar)], spacing=ESPACIO_CHICO),
            error_busqueda,
            panel_resultados,
        ],
        subtitulo=f"Club activo: {club.nombre}",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/jugadores", contenido)
