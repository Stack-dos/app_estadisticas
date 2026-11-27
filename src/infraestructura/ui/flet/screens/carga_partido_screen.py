"""Pantalla de carga atomica de partido (US-108): formulario de 3 pasos con boxscores y cuartos opcionales."""

from dataclasses import dataclass

import flet as ft

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.dtos.categoria_dto import CategoriaDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import CompetenciaDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.partido_dto import BoxscoreDTO, EstadisticaInputDTO, PartidoDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.partido import JugadorPartido
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.puntos_por_cuarto import BloquePuntosPorCuarto
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO

CLAVE_PASO_DATOS = "paso_datos"
CLAVE_PASO_BOXSCORE = "paso_boxscore"
CLAVE_PASO_RESUMEN = "paso_resumen"
CLAVE_AVISO_LISTA = "aviso_lista_faltante"
CLAVE_RESUMEN_TEXTO = "resumen_partido_texto"
CLAVE_ERROR = "error_carga_partido"

ANCHO_STAT = 62
CAMPOS_ESTADISTICA: tuple[tuple[str, str, bool], ...] = (
    ("minutosJugados", "Min", True),
    ("t2c", "T2C", False),
    ("t2l", "T2L", False),
    ("t3c", "T3C", False),
    ("t3l", "T3L", False),
    ("t1c", "T1C", False),
    ("t1l", "T1L", False),
    ("rebotesDef", "RD", False),
    ("rebotesOf", "RO", False),
    ("asistencias", "AST", False),
    ("recuperos", "REC", False),
    ("perdidas", "PER", False),
    ("taponesRealizados", "TAP+", False),
    ("taponesRecibidos", "TAP-", False),
    ("faltasRecibidas", "FR", False),
    ("faltasCometidas", "FC", False),
)


@dataclass
class _FilaJugadorUI:
    jugador: JugadorDTO
    campos: dict[str, ft.TextField]
    error_fila: ft.Text
    contenedor: ft.Column


def _construir_fila_jugador(jugador: JugadorDTO) -> _FilaJugadorUI:
    """Arma los inputs de estadisticas para un jugador de la lista de buena fe."""
    campos: dict[str, ft.TextField] = {}
    for attr, etiqueta, _es_float in CAMPOS_ESTADISTICA:
        campos[attr] = ft.TextField(
            label=f"{jugador.nombre_completo} · {etiqueta}",
            value="0",
            width=ANCHO_STAT,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
    error_fila = ft.Text("", color=ft.Colors.ERROR, visible=False)
    fila = ft.Row(
        controls=[
            ft.Text(jugador.nombre_completo, width=160, weight=ft.FontWeight.W_500),
            *campos.values(),
        ],
        spacing=ESPACIO_CHICO,
        scroll=ft.ScrollMode.AUTO,
    )
    contenedor = ft.Column([fila, error_fila], spacing=2)
    return _FilaJugadorUI(jugador=jugador, campos=campos, error_fila=error_fila, contenedor=contenedor)


def _parsear_fila_estadistica(fila_ui: _FilaJugadorUI, id_club: int) -> EstadisticaInputDTO:
    """Convierte los inputs de una fila a `EstadisticaInputDTO` y valida reglas de `JugadorPartido`.

    Si hay error, marca `field.error` o `fila_ui.error_fila` en el jugador que lo causo.
    """
    fila_ui.error_fila.value = ""
    fila_ui.error_fila.visible = False
    for campo in fila_ui.campos.values():
        campo.error = None

    valores: dict[str, int | float] = {}
    for attr, etiqueta, es_float in CAMPOS_ESTADISTICA:
        campo = fila_ui.campos[attr]
        texto = (campo.value or "").strip() or "0"
        try:
            valores[attr] = float(texto) if es_float else int(texto)
        except ValueError as err:
            campo.error = "Inválido"
            mensaje = f"{fila_ui.jugador.nombre_completo}: '{etiqueta}' debe ser numérico."
            fila_ui.error_fila.value = mensaje
            fila_ui.error_fila.visible = True
            raise DatoInvalidoError(mensaje) from err

    puntos = int(valores["t2c"]) * 2 + int(valores["t3c"]) * 3 + int(valores["t1c"])
    try:
        JugadorPartido(
            idJugador=fila_ui.jugador.id,
            idPartido=0,
            idClub=id_club,
            minutosJugados=float(valores["minutosJugados"]),
            puntos=puntos,
            t2c=int(valores["t2c"]),
            t2l=int(valores["t2l"]),
            t3c=int(valores["t3c"]),
            t3l=int(valores["t3l"]),
            t1c=int(valores["t1c"]),
            t1l=int(valores["t1l"]),
            rebotesDef=int(valores["rebotesDef"]),
            rebotesOf=int(valores["rebotesOf"]),
            asistencias=int(valores["asistencias"]),
            recuperos=int(valores["recuperos"]),
            perdidas=int(valores["perdidas"]),
            taponesRecibidos=int(valores["taponesRecibidos"]),
            taponesRealizados=int(valores["taponesRealizados"]),
            faltasRecibidas=int(valores["faltasRecibidas"]),
            faltasCometidas=int(valores["faltasCometidas"]),
        )
    except DatoInvalidoError as err:
        mensaje = f"{fila_ui.jugador.nombre_completo}: {err}"
        fila_ui.error_fila.value = mensaje
        fila_ui.error_fila.visible = True
        raise DatoInvalidoError(mensaje) from err

    return EstadisticaInputDTO(
        idJugador=fila_ui.jugador.id,
        minutosJugados=float(valores["minutosJugados"]),
        puntos=puntos,
        t2c=int(valores["t2c"]),
        t2l=int(valores["t2l"]),
        t3c=int(valores["t3c"]),
        t3l=int(valores["t3l"]),
        t1c=int(valores["t1c"]),
        t1l=int(valores["t1l"]),
        rebotesDef=int(valores["rebotesDef"]),
        rebotesOf=int(valores["rebotesOf"]),
        asistencias=int(valores["asistencias"]),
        recuperos=int(valores["recuperos"]),
        perdidas=int(valores["perdidas"]),
        taponesRecibidos=int(valores["taponesRecibidos"]),
        taponesRealizados=int(valores["taponesRealizados"]),
        faltasRecibidas=int(valores["faltasRecibidas"]),
        faltasCometidas=int(valores["faltasCometidas"]),
    )


def crear_carga_partido_view(
    page: ft.Page,
    cargar_partido_uc: CargarPartidoUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_comp_uc: ListarCategoriasDeCompetenciaUseCase,
    listar_clubes_todos_uc: ListarClubesUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_lista_uc: ListarListaBuenaFeUseCase,
    sesion: SessionManager,
) -> ft.View:
    """Arma el formulario de 3 pasos para cargar un partido completo de forma atomica (US-108)."""
    club_activo = sesion.club_activo()
    if club_activo is None:
        raise RuntimeError("La pantalla de carga de partido requiere un club activo")

    competencias: list[CompetenciaDTO] = listar_competencias_uc.ejecutar()
    competencias_por_id = {c.idCompetencia: c for c in competencias}
    clubes: list[ClubDTO] = listar_clubes_todos_uc.ejecutar()
    clubes_por_id = {c.idClub: c for c in clubes}
    categorias_por_id: dict[int, CategoriaDTO] = {}

    dd_competencia = ft.Dropdown(
        label="Competencia",
        options=[
            ft.dropdown.Option(key=str(c.idCompetencia), text=f"{c.nombre} ({c.anio})")
            for c in competencias
        ],
    )
    dd_categoria = ft.Dropdown(label="Categoría", options=[])
    campo_fecha = ft.TextField(label="Fecha (AAAA-MM-DD)", hint_text="2026-08-10")
    campo_estadio = ft.TextField(label="Estadio (opcional)")
    opciones_clubes = [ft.dropdown.Option(key=str(c.idClub), text=c.nombre) for c in clubes]
    # El club activo viene preseleccionado como local, pero el usuario puede cambiar ambos equipos (AC5)
    dd_local = ft.Dropdown(
        label="Club local",
        options=opciones_clubes,
        value=str(club_activo.idClub) if club_activo.idClub in clubes_por_id else None,
    )
    dd_visitante = ft.Dropdown(label="Club visitante", options=opciones_clubes)

    error = crear_etiqueta_error()
    error.key = CLAVE_ERROR
    aviso_lista_texto = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT)
    contenedor_aviso_lista = ft.Row(
        key=CLAVE_AVISO_LISTA,
        visible=False,
        spacing=ESPACIO_CHICO,
        wrap=True,
        controls=[
            aviso_lista_texto,
            ft.TextButton("Ir a listas de buena fe", on_click=lambda: page.navigate("/listas")),
        ],
    )

    filas_local_ui: list[_FilaJugadorUI] = []
    filas_visitante_ui: list[_FilaJugadorUI] = []
    clave_boxscore_cargado: tuple[int, int, int, int] | None = None
    boxscore_local_validado: BoxscoreDTO | None = None
    boxscore_visitante_validado: BoxscoreDTO | None = None

    titulo_local_bs = ft.Text("Boxscore Local", weight=ft.FontWeight.W_600)
    titulo_visitante_bs = ft.Text("Boxscore Visitante", weight=ft.FontWeight.W_600)
    contenedor_filas_local = ft.Column(spacing=ESPACIO_CHICO)
    contenedor_filas_visitante = ft.Column(spacing=ESPACIO_CHICO)

    resumen_texto = ft.Text("", key=CLAVE_RESUMEN_TEXTO)
    bloque_cuartos = BloquePuntosPorCuarto(al_cambiar=lambda: page.update())

    def _actualizar_categorias() -> None:
        nonlocal categorias_por_id
        if not dd_competencia.value:
            dd_categoria.options = []
            dd_categoria.value = None
            categorias_por_id = {}
            return
        cats = listar_categorias_comp_uc.ejecutar(int(dd_competencia.value))
        categorias_por_id = {c.idCategoria: c for c in cats}
        dd_categoria.options = [ft.dropdown.Option(key=str(c.idCategoria), text=c.nombre) for c in cats]
        if dd_categoria.value and int(dd_categoria.value) not in categorias_por_id:
            dd_categoria.value = None

    def al_cambiar_competencia() -> None:
        _actualizar_categorias()
        page.update()

    dd_competencia.on_select = al_cambiar_competencia

    def _mostrar_paso(paso: int) -> None:
        paso_datos.visible = paso == 1
        paso_boxscore.visible = paso == 2
        paso_resumen.visible = paso == 3
        page.update()

    def _obtener_lista_equipo(id_club: int, rol: str, id_comp: int, id_cat: int) -> list[JugadorDTO]:
        nombre_club = clubes_por_id[id_club].nombre if id_club in clubes_por_id else f"Club {id_club}"
        inscripciones = listar_inscripciones_uc.ejecutar(id_club)
        inscripcion = next(
            (i for i in inscripciones if i.idCompetencia == id_comp and i.idCategoria == id_cat),
            None,
        )
        if inscripcion is None:
            aviso_lista_texto.value = (
                f"El equipo {rol} ({nombre_club}) no está inscripto en esa competencia y categoría."
            )
            contenedor_aviso_lista.visible = True
            raise DatoInvalidoError(aviso_lista_texto.value)

        jugadores = listar_lista_uc.ejecutar(inscripcion.idInscripcion)
        if not jugadores:
            aviso_lista_texto.value = (
                f"El equipo {rol} ({nombre_club}) no tiene jugadores en su lista de buena fe."
            )
            contenedor_aviso_lista.visible = True
            raise DatoInvalidoError(aviso_lista_texto.value)
        return jugadores

    def al_continuar_a_boxscores() -> None:
        nonlocal filas_local_ui, filas_visitante_ui, clave_boxscore_cargado
        contenedor_aviso_lista.visible = False

        def accion() -> None:
            nonlocal filas_local_ui, filas_visitante_ui, clave_boxscore_cargado
            if not dd_competencia.value:
                raise DatoInvalidoError("Elegí una competencia.")
            if not dd_categoria.value:
                raise DatoInvalidoError("Elegí una categoría.")
            if not (campo_fecha.value or "").strip():
                raise DatoInvalidoError("Ingresá la fecha del partido (AAAA-MM-DD).")
            if not dd_local.value or not dd_visitante.value:
                raise DatoInvalidoError("Elegí el club local y el club visitante.")
            id_comp = int(dd_competencia.value)
            id_cat = int(dd_categoria.value)
            id_local = int(dd_local.value)
            id_visitante = int(dd_visitante.value)
            if id_local == id_visitante:
                raise DatoInvalidoError("El club local y el club visitante no pueden ser el mismo.")

            jugadores_local = _obtener_lista_equipo(id_local, "local", id_comp, id_cat)
            jugadores_visitante = _obtener_lista_equipo(id_visitante, "visitante", id_comp, id_cat)

            nueva_clave = (id_comp, id_cat, id_local, id_visitante)
            if nueva_clave != clave_boxscore_cargado:
                filas_local_ui = [_construir_fila_jugador(j) for j in jugadores_local]
                filas_visitante_ui = [_construir_fila_jugador(j) for j in jugadores_visitante]
                contenedor_filas_local.controls = [f.contenedor for f in filas_local_ui]
                contenedor_filas_visitante.controls = [f.contenedor for f in filas_visitante_ui]
                clave_boxscore_cargado = nueva_clave

            nombre_local = clubes_por_id[id_local].nombre
            nombre_visitante = clubes_por_id[id_visitante].nombre
            titulo_local_bs.value = f"Local: {nombre_local}"
            titulo_visitante_bs.value = f"Visitante: {nombre_visitante}"
            bloque_cuartos.actualizar_equipos(nombre_local, nombre_visitante)
            _mostrar_paso(2)

        ejecutar_mostrando_errores(accion, error)
        page.update()

    def al_continuar_a_resumen() -> None:
        def accion() -> None:
            nonlocal boxscore_local_validado, boxscore_visitante_validado
            id_comp = int(dd_competencia.value)
            id_cat = int(dd_categoria.value)
            id_local = int(dd_local.value)
            id_visitante = int(dd_visitante.value)

            est_local = [_parsear_fila_estadistica(f, id_local) for f in filas_local_ui]
            est_visitante = [_parsear_fila_estadistica(f, id_visitante) for f in filas_visitante_ui]
            boxscore_local_validado = BoxscoreDTO(idClub=id_local, estadisticas=est_local)
            boxscore_visitante_validado = BoxscoreDTO(idClub=id_visitante, estadisticas=est_visitante)

            pts_local = sum(e.puntos for e in est_local)
            pts_visitante = sum(e.puntos for e in est_visitante)
            comp = competencias_por_id[id_comp]
            cat = categorias_por_id[id_cat]
            nombre_local = clubes_por_id[id_local].nombre
            nombre_visitante = clubes_por_id[id_visitante].nombre
            estadio = (campo_estadio.value or "").strip() or "Sin estadio"
            resumen_texto.value = (
                f"{comp.nombre} ({comp.anio}) · {cat.nombre} · {(campo_fecha.value or '').strip()} · {estadio}\n"
                f"{nombre_local} {pts_local} - {pts_visitante} {nombre_visitante} "
                f"({len(est_local)} y {len(est_visitante)} jugadores)"
            )
            _mostrar_paso(3)

        ejecutar_mostrando_errores(accion, error)
        page.update()

    def al_guardar_partido() -> None:
        def accion() -> None:
            if boxscore_local_validado is None or boxscore_visitante_validado is None:
                raise DatoInvalidoError("Completá primero los boxscores de ambos equipos.")
            id_local = int(dd_local.value)
            id_visitante = int(dd_visitante.value)
            cuartos = bloque_cuartos.leer_cuartos(id_local, id_visitante)
            partido_dto = PartidoDTO(
                fecha=(campo_fecha.value or "").strip(),
                estadio=(campo_estadio.value or "").strip() or None,
                idCompetencia=int(dd_competencia.value),
                idCategoria=int(dd_categoria.value),
                idClubLocal=id_local,
                idClubVisitante=id_visitante,
                cuartos=cuartos,
            )
            guardado = cargar_partido_uc.ejecutar(
                partido_dto,
                boxscore_local_validado,
                boxscore_visitante_validado,
            )
            if guardado is None:
                raise DatoInvalidoError("No se pudo guardar el partido en la base de datos. Revisá los datos.")
            page.navigate("/partidos")

        ejecutar_mostrando_errores(accion, error)
        page.update()

    paso_datos = ft.Column(
        key=CLAVE_PASO_DATOS,
        spacing=ESPACIO,
        controls=[
            ft.Text("Paso 1 de 3 · Datos del partido", weight=ft.FontWeight.W_600),
            ft.Row([dd_competencia, dd_categoria], spacing=ESPACIO, wrap=True),
            ft.Row([campo_fecha, campo_estadio], spacing=ESPACIO, wrap=True),
            ft.Row([dd_local, dd_visitante], spacing=ESPACIO, wrap=True),
            contenedor_aviso_lista,
            ft.Row(
                [
                    ft.FilledButton("Continuar a boxscores", on_click=al_continuar_a_boxscores),
                    ft.TextButton("Cancelar", on_click=lambda: page.navigate("/partidos")),
                ],
                spacing=ESPACIO,
            ),
        ],
    )

    paso_boxscore = ft.Column(
        key=CLAVE_PASO_BOXSCORE,
        visible=False,
        spacing=ESPACIO,
        controls=[
            ft.Text("Paso 2 de 3 · Boxscores por equipo", weight=ft.FontWeight.W_600),
            titulo_local_bs,
            contenedor_filas_local,
            ft.Divider(),
            titulo_visitante_bs,
            contenedor_filas_visitante,
            ft.Row(
                [
                    ft.TextButton("Volver", on_click=lambda: _mostrar_paso(1)),
                    ft.FilledButton("Continuar a resumen", on_click=al_continuar_a_resumen),
                ],
                spacing=ESPACIO,
            ),
        ],
    )

    paso_resumen = ft.Column(
        key=CLAVE_PASO_RESUMEN,
        visible=False,
        spacing=ESPACIO,
        controls=[
            ft.Text("Paso 3 de 3 · Resumen y confirmación", weight=ft.FontWeight.W_600),
            resumen_texto,
            ft.Divider(),
            bloque_cuartos.control,
            ft.Row(
                [
                    ft.TextButton("Volver a boxscores", on_click=lambda: _mostrar_paso(2)),
                    ft.FilledButton("Guardar partido", on_click=al_guardar_partido),
                ],
                spacing=ESPACIO,
            ),
        ],
    )

    contenido = crear_pagina(
        "Cargar partido",
        [paso_datos, paso_boxscore, paso_resumen, error],
        subtitulo=f"Club activo preseleccionado como local: {club_activo.nombre}",
    )
    return crear_vista_interna(page, sesion, "/partidos/cargar", contenido)
