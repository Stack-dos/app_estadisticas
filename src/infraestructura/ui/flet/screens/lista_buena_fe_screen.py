"""Pantalla de listas de buena fe del club activo (US-107): habilitar, quitar, vaciar o dar de baja.

US-113: el alta es masiva. El panel de la derecha muestra el plantel que todavia no esta en la lista, con
una casilla por jugador y "Seleccionar todos"; "Agregar seleccionados" agrega los validos y avisa cuales
no entraron y por que (no es todo o nada).
"""

import flet as ft

from aplicacion.casos_uso.agregar_jugadores_lista import AgregarJugadoresAListaBuenaFeUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.casos_uso.vaciar_lista_buena_fe import VaciarListaBuenaFeUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO, InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.lista_buena_fe_dto import AgregarJugadoresListaDTO, QuitarJugadorListaDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.confirmacion import pedir_confirmacion
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.subnav_torneos import crear_subnav_torneos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO_CHICO

TABLA_LISTA_BUENA_FE = "tabla_lista_buena_fe"
CASILLAS_PLANTEL = "casillas_plantel_disponible"
COLUMNAS_LISTA = ("Jugador", "Año nac.", "Acción")
SIN_INSCRIPCIONES = "El club activo todavía no tiene inscripciones. Inscribilo primero en Inscripciones."
LISTA_VACIA = "Esta lista de buena fe todavía no tiene jugadores habilitados."
PLANTEL_COMPLETO = "Todo el plantel del club ya está en esta lista."
PLANTEL_VACIO = "El club no tiene jugadores. Cargalos en Jugadores."


def etiqueta_inscripcion(
    inscripcion: InscripcionDTO,
    competencias_por_id: dict[int, CompetenciaDTO],
    categorias_por_id: dict[int, CategoriaDTO],
) -> str:
    """Arma el texto legible de una inscripcion para mostrar en el desplegable."""
    comp = competencias_por_id.get(inscripcion.idCompetencia)
    cat = categorias_por_id.get(inscripcion.idCategoria)
    nombre_comp = f"{comp.nombre} ({comp.anio})" if comp is not None else f"Competencia #{inscripcion.idCompetencia}"
    nombre_cat = cat.nombre if cat is not None else f"Categoría #{inscripcion.idCategoria}"
    return f"{nombre_comp} — {nombre_cat}"


def _etiqueta_jugador(jugador: JugadorDTO) -> str:
    if jugador.anioNacimiento is None:
        return jugador.nombre_completo
    return f"{jugador.nombre_completo} ({jugador.anioNacimiento})"


def fila_jugador_lista(jugador: JugadorDTO) -> tuple[str, str]:
    """Convierte un jugador de la lista de buena fe en las columnas de texto de la tabla."""
    anio = str(jugador.anioNacimiento) if jugador.anioNacimiento is not None else "—"
    return (jugador.nombre_completo, anio)


def crear_lista_buena_fe_view(
    page: ft.Page,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    listar_lista_uc: ListarListaBuenaFeUseCase,
    listar_jugadores_club_uc: ListarJugadoresClubUseCase,
    agregar_jugadores_uc: AgregarJugadoresAListaBuenaFeUseCase,
    quitar_jugador_uc: QuitarJugadorDeListaBuenaFeUseCase,
    vaciar_lista_uc: VaciarListaBuenaFeUseCase,
    eliminar_inscripcion_uc: EliminarInscripcionUseCase,
    sesion: SessionManager,
) -> ft.View:
    """
    Arma la pantalla de listas de buena fe del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, confirmar acciones y redibujar.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Inscripciones del club activo.
        listar_competencias_uc (ListarCompetenciasUseCase): Competencias para mostrar nombres.
        listar_categorias_uc (ListarCategoriasUseCase): Categorias para mostrar nombres.
        listar_lista_uc (ListarListaBuenaFeUseCase): Jugadores habilitados en la inscripcion elegida.
        listar_jugadores_club_uc (ListarJugadoresClubUseCase): Plantel actual del club activo.
        agregar_jugadores_uc (AgregarJugadoresAListaBuenaFeUseCase): Habilita varios jugadores a la vez.
        quitar_jugador_uc (QuitarJugadorDeListaBuenaFeUseCase): Quita un jugador de la lista.
        vaciar_lista_uc (VaciarListaBuenaFeUseCase): Quita todos los jugadores de la lista elegida.
        eliminar_inscripcion_uc (EliminarInscripcionUseCase): Da de baja la inscripcion y su lista 1:1.
        sesion (SessionManager): Sesion activa con club elegido.

    Returns:
        ft.View: La pantalla para la ruta "/listas".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de listas de buena fe requiere un club activo")

    dd_inscripcion = ft.Dropdown(label="Inscripción", options=[])
    casillas_plantel = ft.Column(key=CASILLAS_PLANTEL, spacing=0)
    casilla_todos = ft.Checkbox(label="Seleccionar todos")
    boton_agregar = ft.FilledButton("Agregar seleccionados", icon=ft.Icons.PLAYLIST_ADD)
    resultado_agregar = ft.Column(spacing=ESPACIO_CHICO)
    error_agregar = crear_etiqueta_error()
    plantel_club: list[JugadorDTO] = []
    error_tabla = crear_etiqueta_error()
    contenedor_tabla = ft.Column()
    acciones_lista = ft.Row(spacing=ESPACIO_CHICO, wrap=True)

    def _boton_quitar(jugador: JugadorDTO) -> ft.TextButton:
        # Funcion aparte para que cada boton capture su propio `jugador` y no el ultimo del bucle.
        return ft.TextButton("Quitar", on_click=lambda: quitar(jugador))

    def vaciar_lista() -> None:
        if not dd_inscripcion.value:
            return
        id_inscripcion = int(dd_inscripcion.value)

        def al_confirmar() -> None:
            def accion() -> None:
                if vaciar_lista_uc.ejecutar(id_inscripcion) is None:
                    raise RuntimeError("No se pudo vaciar la lista de buena fe")
                refrescar_lista()

            ejecutar_mostrando_errores(accion, error_tabla, nombre="lista_buena_fe.vaciar")
            page.update()

        pedir_confirmacion(
            page,
            "Vaciar lista de buena fe",
            "¿Querés quitar a todos los jugadores habilitados de esta lista?",
            al_confirmar,
            texto_confirmar="Vaciar lista",
        )

    def dar_de_baja_inscripcion() -> None:
        if not dd_inscripcion.value:
            return
        id_inscripcion = int(dd_inscripcion.value)

        def al_confirmar() -> None:
            def accion() -> None:
                if not eliminar_inscripcion_uc.ejecutar(id_inscripcion):
                    raise RuntimeError("No se pudo dar de baja la inscripción")
                dd_inscripcion.value = None
                cargar_inicial()

            ejecutar_mostrando_errores(accion, error_tabla, nombre="lista_buena_fe.dar_de_baja")
            page.update()

        pedir_confirmacion(
            page,
            "Dar de baja inscripción",
            "¿Querés dar de baja esta inscripción y eliminar su lista de buena fe?",
            al_confirmar,
            texto_confirmar="Dar de baja",
        )

    def refrescar_lista() -> None:
        """Recarga la tabla de jugadores y las acciones para la inscripcion seleccionada."""
        if not dd_inscripcion.value:
            contenedor_tabla.controls = [ft.Text(SIN_INSCRIPCIONES, color=ft.Colors.ON_SURFACE_VARIANT)]
            acciones_lista.controls = []
            _refrescar_casillas(set())
            return
        jugadores = listar_lista_uc.ejecutar(int(dd_inscripcion.value))
        _refrescar_casillas({j.id for j in jugadores})
        filas = [(*fila_jugador_lista(j), _boton_quitar(j)) for j in jugadores]
        contenedor_tabla.controls = [
            crear_tabla_datos(
                COLUMNAS_LISTA,
                filas,
                mensaje_vacio=LISTA_VACIA,
                clave=TABLA_LISTA_BUENA_FE,
            )
        ]
        controles_acciones: list[ft.Control] = []
        if jugadores:
            controles_acciones.append(ft.TextButton("Vaciar lista", on_click=vaciar_lista))
        controles_acciones.append(ft.TextButton("Dar de baja inscripción", on_click=dar_de_baja_inscripcion))
        acciones_lista.controls = controles_acciones

    def _refrescar_casillas(ids_en_lista: set[int]) -> None:
        """Una casilla por jugador del plantel que todavia no esta en la lista elegida."""
        disponibles = [j for j in plantel_club if j.id not in ids_en_lista]
        casilla_todos.value = False
        casilla_todos.visible = len(disponibles) > 1
        boton_agregar.disabled = not disponibles
        if disponibles:
            casillas_plantel.controls = [
                ft.Checkbox(label=_etiqueta_jugador(j), data=j.id, on_change=lambda: _actualizar_boton())
                for j in disponibles
            ]
        else:
            texto = PLANTEL_COMPLETO if plantel_club else PLANTEL_VACIO
            casillas_plantel.controls = [ft.Text(texto, color=ft.Colors.ON_SURFACE_VARIANT)]
        _actualizar_boton()

    def _ids_marcados() -> list[int]:
        return [
            int(c.data)
            for c in casillas_plantel.controls
            if isinstance(c, ft.Checkbox) and c.value and c.data is not None
        ]

    def _actualizar_boton() -> None:
        marcados = len(_ids_marcados())
        boton_agregar.content = f"Agregar seleccionados ({marcados})" if marcados else "Agregar seleccionados"
        page.update()

    def al_marcar_todos() -> None:
        for c in casillas_plantel.controls:
            if isinstance(c, ft.Checkbox):
                c.value = bool(casilla_todos.value)
        _actualizar_boton()

    casilla_todos.on_change = al_marcar_todos

    def al_elegir_inscripcion() -> None:
        ejecutar_mostrando_errores(refrescar_lista, error_tabla, nombre="lista_buena_fe.elegir_inscripcion")
        page.update()

    dd_inscripcion.on_select = al_elegir_inscripcion

    def cargar_inicial() -> None:
        inscripciones = listar_inscripciones_uc.ejecutar(club.idClub)
        competencias_por_id = {c.idCompetencia: c for c in listar_competencias_uc.ejecutar()}
        categorias_por_id = {c.idCategoria: c for c in listar_categorias_uc.ejecutar()}

        dd_inscripcion.options = [
            ft.dropdown.Option(
                key=str(ins.idInscripcion),
                text=etiqueta_inscripcion(ins, competencias_por_id, categorias_por_id),
            )
            for ins in inscripciones
        ]
        if inscripciones and dd_inscripcion.value is None:
            dd_inscripcion.value = str(inscripciones[0].idInscripcion)

        plantel_club[:] = listar_jugadores_club_uc.ejecutar(club.idClub)
        refrescar_lista()

    def agregar() -> None:
        def accion() -> None:
            resultado_agregar.controls = []
            if not dd_inscripcion.value:
                raise DatoInvalidoError("Elegí una inscripción")
            resultado = agregar_jugadores_uc.ejecutar(
                AgregarJugadoresListaDTO(idInscripcion=int(dd_inscripcion.value), idJugadores=_ids_marcados())
            )
            nombres = {j.id: j.nombre_completo for j in plantel_club}
            if resultado.agregados:
                n = len(resultado.agregados)
                aviso = "Se agregó 1 jugador a la lista." if n == 1 else f"Se agregaron {n} jugadores a la lista."
                resultado_agregar.controls.append(ft.Text(aviso, color=ft.Colors.PRIMARY))
            for rechazado in resultado.rechazados:
                nombre = nombres.get(rechazado.idJugador, f"Jugador {rechazado.idJugador}")
                resultado_agregar.controls.append(ft.Text(f"{nombre}: {rechazado.motivo}", color=ft.Colors.ERROR))
            refrescar_lista()

        ejecutar_mostrando_errores(accion, error_agregar, nombre="lista_buena_fe.agregar")
        page.update()

    boton_agregar.on_click = agregar

    def quitar(jugador: JugadorDTO) -> None:
        def accion() -> None:
            if not dd_inscripcion.value:
                raise DatoInvalidoError("Elegí una inscripción")
            resultado = quitar_jugador_uc.ejecutar(
                QuitarJugadorListaDTO(idInscripcion=int(dd_inscripcion.value), idJugador=jugador.id)
            )
            if resultado is None:
                raise RuntimeError("Quitar el jugador de la lista no devolvio confirmacion (fallo al borrar)")
            refrescar_lista()

        ejecutar_mostrando_errores(accion, error_tabla, nombre="lista_buena_fe.quitar")
        page.update()

    cargar_inicial()

    lateral = ft.Column(
        [
            ft.Text("Habilitar jugadores del plantel", weight=ft.FontWeight.W_600),
            casilla_todos,
            casillas_plantel,
            error_agregar,
            boton_agregar,
            resultado_agregar,
        ],
        spacing=ESPACIO_CHICO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    contenido = crear_pagina(
        "Torneos · Listas de buena fe",
        [
            crear_subnav_torneos(page, "/listas"),
            dd_inscripcion,
            ft.Text("Jugadores habilitados", weight=ft.FontWeight.W_600),
            contenedor_tabla,
            acciones_lista,
            error_tabla,
        ],
        subtitulo=f"Club activo: {club.nombre}",
        lateral=lateral,
    )
    return crear_vista_interna(page, sesion, "/listas", contenido)
