"""Pantalla de carga y edicion de partido (US-108, rediseñada en US-113, convocados y edicion en US-114).

Es un asistente de tres pasos (como en la maqueta), que muestra solo lo necesario en cada momento:

1. **Datos del partido:** competencia y categoria en un solo desplegable, fecha con calendario, estadio,
   rival escribible y si se jugo de local o de visitante.
2. **Boxscore:** los convocados (de la lista de buena fe se marcan los que fueron, hasta 12) y la planilla
   de tu equipo tipo Excel; el rival con solo sus totales (o solo el resultado) o su boxscore por jugador;
   los puntos por cuarto (opcionales) y el marcador.
3. **Confirmar:** un resumen de lo que se va a guardar y los avisos (pocos jugadores, partido repetido).
   "Guardar partido" guarda ahi mismo: los avisos ya se ven en el resumen, no hace falta otro dialogo.

"Siguiente" valida el paso antes de avanzar; "Atrás" vuelve sin perder lo cargado (los controles de los
tres pasos viven siempre en la pantalla, solo cambia cual se ve).

El rival se elige de la lista o se escribe: si no existe, el caso de uso lo crea en la MISMA transaccion
que el partido (si algo falla, no queda un club suelto) y SIN vinculo con el usuario (no aparece en "Mis
clubes").

Con `id_partido` la pantalla edita ese partido: llega llena con lo guardado y al guardar lo reemplaza.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime
from functools import partial

import flet as ft

from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.competencia_dto import InscripcionDTO
from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.partido_dto import BoxscoreDTO, PartidoDTO, TotalesEquipoDTO
from aplicacion.servicios.session_manager import SessionManager
from dominio.entidades.partido import ID_CLUB_NUEVO, MAX_JUGADORES_PARTIDO, MIN_JUGADORES_PARTIDO
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.components.pagina import crear_pagina, crear_vista_interna
from infraestructura.ui.flet.components.planilla_boxscore import FilaTotalesEquipo, PlanillaBoxscore
from infraestructura.ui.flet.components.puntos_por_cuarto import BloquePuntosPorCuarto, filas_cuartos
from infraestructura.ui.flet.components.tabla_datos import crear_tabla_datos
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores
from infraestructura.ui.flet.estilo import ESPACIO, ESPACIO_CHICO, RADIO
from infraestructura.ui.flet.screens.lista_buena_fe_screen import etiqueta_inscripcion
from utils import normalizar_texto

CLAVE_AVISO_LISTA = "aviso_lista_faltante"
CLAVE_AVISO_EDICION = "aviso_edicion"
CLAVE_ERROR = "error_carga_partido"
CLAVE_MARCADOR = "marcador_partido"
CLAVE_SECCION_PROPIA = "seccion_planilla_propia"
CLAVE_CONVOCADOS = "convocados"
CLAVE_CONTADOR_CONVOCADOS = "contador_convocados"
CLAVE_PLEGABLE_CONVOCADOS = "plegable_convocados"
COL_CASILLA_CONVOCADO: dict[str | ft.ResponsiveRowBreakpoint, int | float] = {
    "xs": 6,
    "sm": 4,
    "md": 3,
    "xl": 2,
}  # 2 a 6 casillas por fila segun el ancho
CLAVE_BOTON_GUARDAR = "boton_guardar_partido"
CLAVE_BOTON_SIGUIENTE = "boton_siguiente_carga"
CLAVE_BOTON_ATRAS = "boton_atras_carga"
CLAVE_INDICADOR_PASOS = "indicador_pasos_carga"
CLAVE_PASOS = ("paso_datos", "paso_boxscore", "paso_confirmar")
CLAVE_RESUMEN = "resumen_carga"
CLAVE_AVISOS_RESUMEN = "avisos_resumen_carga"
PASOS = ("Datos del partido", "Boxscore", "Confirmar")
COLUMNAS_RESUMEN = ("Equipo", "Condición", "Jugadores cargados", "Puntos")
CLAVE_BLOQUE_TOTALES_RIVAL = "bloque_totales_rival"
CLAVE_BLOQUE_BOXSCORE_RIVAL = "bloque_boxscore_rival"

CONDICION_LOCAL = "local"
CONDICION_VISITANTE = "visitante"
MODO_TOTALES = "totales"
MODO_BOXSCORE = "boxscore"
FILAS_RIVAL_INICIALES = 5

SIN_INSCRIPCIONES = "Tu club todavía no está inscripto en ninguna competencia. Inscribilo para poder cargar partidos."
AYUDA_PLANILLA = "Dejá vacía la fila de quien no jugó: no se guarda. Los puntos y la fila Equipo se calculan solos."
AYUDA_CONVOCADOS = f"Marcá los que fueron al partido (hasta {MAX_JUGADORES_PARTIDO}): solo ellos van a la planilla."
SIN_CONVOCADOS = "Marcá los convocados del partido."


def ruta_editar_partido(id_partido: int) -> str:
    """Ruta de la pantalla para editar un partido: "/partidos/editar/5"."""
    return f"/partidos/editar/{id_partido}"


@dataclass
class _Guardado:
    """Lo que se manda al caso de uso, armado antes de pedir confirmacion por los avisos."""

    partido: PartidoDTO
    boxscore_propio: BoxscoreDTO
    rival: BoxscoreDTO | TotalesEquipoDTO
    nombre_rival_nuevo: str | None


def crear_carga_partido_view(
    page: ft.Page,
    cargar_partido_uc: CargarPartidoUseCase,
    listar_competencias_uc: ListarCompetenciasUseCase,
    listar_categorias_uc: ListarCategoriasUseCase,
    listar_clubes_todos_uc: ListarClubesUseCase,
    listar_inscripciones_uc: ListarInscripcionesClubUseCase,
    listar_lista_uc: ListarListaBuenaFeUseCase,
    listar_partidos_uc: ListarPartidosPorClubUseCase,
    obtener_partido_uc: ObtenerPartidoUseCase,
    obtener_boxscore_uc: ObtenerBoxscorePartidoUseCase,
    obtener_totales_uc: ObtenerTotalesPartidoUseCase,
    sesion: SessionManager,
    id_partido: int | None = None,
) -> ft.View:
    """
    Arma la pantalla de carga (o edicion) de partido del club activo. Exige sesion y club activo.

    Args:
        page (ft.Page): La ventana, para navegar, abrir el calendario y los dialogos, y redibujar.
        cargar_partido_uc (CargarPartidoUseCase): Guarda (o reemplaza) todo el partido de forma atomica.
        listar_competencias_uc (ListarCompetenciasUseCase): Nombres de las competencias.
        listar_categorias_uc (ListarCategoriasUseCase): Nombres de las categorias.
        listar_clubes_todos_uc (ListarClubesUseCase): Clubes existentes, para elegir el rival.
        listar_inscripciones_uc (ListarInscripcionesClubUseCase): Inscripciones del club propio y del rival.
        listar_lista_uc (ListarListaBuenaFeUseCase): Jugadores de una lista de buena fe.
        listar_partidos_uc (ListarPartidosPorClubUseCase): Partidos del club, para avisar si se repite uno.
        obtener_partido_uc (ObtenerPartidoUseCase): Datos del partido a editar.
        obtener_boxscore_uc (ObtenerBoxscorePartidoUseCase): Boxscore guardado del partido a editar.
        obtener_totales_uc (ObtenerTotalesPartidoUseCase): Totales guardados del partido a editar.
        sesion (SessionManager): Sesion activa con club elegido.
        id_partido (int | None): El partido a editar; None para cargar uno nuevo.

    Returns:
        ft.View: La pantalla para "/partidos/cargar" o "/partidos/editar/{id}".
    """
    club = sesion.club_activo()
    if club is None:
        raise RuntimeError("La pantalla de carga de partido requiere un club activo")
    editando = id_partido is not None

    competencias_por_id = {c.idCompetencia: c for c in listar_competencias_uc.ejecutar()}
    categorias_por_id = {c.idCategoria: c for c in listar_categorias_uc.ejecutar()}
    inscripciones_propias = {i.idInscripcion: i for i in listar_inscripciones_uc.ejecutar(club.idClub)}
    rivales: list[ClubDTO] = [c for c in listar_clubes_todos_uc.ejecutar() if c.idClub != club.idClub]
    texto_rival = [""]  # lo ultimo que se escribio en el campo del rival
    lista_actual: list[JugadorDTO] = []  # lista de buena fe del torneo elegido
    convocados: set[int] = set()

    # ------------------------------------------------------------------ datos del partido
    dd_torneo = ft.Dropdown(
        label="Competencia y categoría",
        options=[
            ft.dropdown.Option(
                key=str(i.idInscripcion), text=etiqueta_inscripcion(i, competencias_por_id, categorias_por_id)
            )
            for i in inscripciones_propias.values()
        ],
    )
    campo_fecha = ft.TextField(label="Fecha (AAAA-MM-DD)", value=date.today().isoformat())

    def al_elegir_fecha() -> None:
        valor = selector_fecha.value
        if isinstance(valor, datetime | date):
            campo_fecha.value = valor.strftime("%Y-%m-%d")
            page.update()

    selector_fecha = ft.DatePicker(
        first_date=datetime(2000, 1, 1), last_date=datetime(2100, 12, 31), on_change=al_elegir_fecha
    )
    campo_fecha.suffix_icon = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        tooltip="Elegir en el calendario",
        on_click=lambda: page.show_dialog(selector_fecha),
    )
    campo_estadio = ft.TextField(label="Estadio (opcional)")
    dd_rival = ft.Dropdown(
        label="Rival",
        options=[ft.dropdown.Option(key=str(c.idClub), text=c.nombre) for c in rivales],
        editable=True,
        enable_filter=True,
        helper_text="Elegilo o escribí uno nuevo",
    )
    seg_condicion = ft.SegmentedButton(
        segments=[
            ft.Segment(value=CONDICION_LOCAL, label="Local", icon=ft.Icons.HOME),
            ft.Segment(value=CONDICION_VISITANTE, label="Visitante", icon=ft.Icons.DIRECTIONS_BUS),
        ],
        selected=[CONDICION_LOCAL],
    )

    # ------------------------------------------------------------------ convocados y planillas
    contador_convocados = ft.Text("", key=CLAVE_CONTADOR_CONVOCADOS, weight=ft.FontWeight.W_600)
    casillas_convocados = ft.ResponsiveRow(key=CLAVE_CONVOCADOS, spacing=ESPACIO_CHICO, run_spacing=0)
    forma_plegable = ft.RoundedRectangleBorder(radius=RADIO)
    plegable_convocados = ft.ExpansionTile(
        key=CLAVE_PLEGABLE_CONVOCADOS,
        title=contador_convocados,
        subtitle=ft.Text(AYUDA_CONVOCADOS, color=ft.Colors.ON_SURFACE_VARIANT),
        controls=[casillas_convocados],
        controls_padding=ft.Padding.symmetric(horizontal=ESPACIO, vertical=ESPACIO_CHICO),
        expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
        maintain_state=True,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        collapsed_bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        shape=forma_plegable,
        collapsed_shape=forma_plegable,
    )
    planilla_propia = PlanillaBoxscore(club.nombre, al_cambiar=lambda: _actualizar_marcador())
    seccion_propia = ft.Column(
        key=CLAVE_SECCION_PROPIA,
        visible=False,
        spacing=ESPACIO_CHICO,
        controls=[
            ft.Text(f"Tu equipo: {club.nombre}", weight=ft.FontWeight.W_600),
            plegable_convocados,
            ft.Text(AYUDA_PLANILLA, color=ft.Colors.ON_SURFACE_VARIANT),
            planilla_propia.control,
        ],
    )
    aviso_texto = ft.Text("", color=ft.Colors.ON_SURFACE_VARIANT)
    aviso_link = ft.TextButton("")
    aviso = ft.Row(key=CLAVE_AVISO_LISTA, visible=False, wrap=True, controls=[aviso_texto, aviso_link])
    aviso_edicion = ft.Text("", key=CLAVE_AVISO_EDICION, color=ft.Colors.ERROR, visible=False)

    fila_totales_rival = FilaTotalesEquipo("Rival", al_cambiar=lambda: _actualizar_marcador())
    planilla_rival = PlanillaBoxscore("Rival", al_cambiar=lambda: _actualizar_marcador(), permite_agregar=True)
    bloque_totales_rival = ft.Column([fila_totales_rival.control], key=CLAVE_BLOQUE_TOTALES_RIVAL)
    bloque_boxscore_rival = ft.Column(
        [
            ft.Text(
                "Si el rival ya tiene lista de buena fe en este torneo, sus jugadores aparecen solos. Los que "
                "escribas a mano se dan de alta en su club y su lista al guardar.",
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            planilla_rival.control,
        ],
        key=CLAVE_BLOQUE_BOXSCORE_RIVAL,
        visible=False,
        spacing=ESPACIO_CHICO,
    )
    seg_modo_rival = ft.SegmentedButton(
        segments=[
            ft.Segment(value=MODO_TOTALES, label="Solo totales o resultado"),
            ft.Segment(value=MODO_BOXSCORE, label="Boxscore por jugador"),
        ],
        selected=[MODO_TOTALES],
    )
    titulo_rival = ft.Text("Rival", weight=ft.FontWeight.W_600)

    bloque_cuartos = BloquePuntosPorCuarto(al_cambiar=lambda: page.update())
    marcador = ft.Text("", key=CLAVE_MARCADOR, size=20, weight=ft.FontWeight.W_600)
    error = crear_etiqueta_error()
    error.key = CLAVE_ERROR

    # ------------------------------------------------------------------ helpers
    def _inscripcion_elegida() -> InscripcionDTO | None:
        return inscripciones_propias.get(int(dd_torneo.value)) if dd_torneo.value else None

    def _es_local() -> bool:
        return (seg_condicion.selected or [CONDICION_LOCAL])[0] == CONDICION_LOCAL

    def _modo_rival() -> str:
        return (seg_modo_rival.selected or [MODO_TOTALES])[0]

    def _nombre_rival() -> str:
        if dd_rival.value:
            elegido = next((c for c in rivales if str(c.idClub) == dd_rival.value), None)
            if elegido is not None:
                return elegido.nombre
        return texto_rival[0].strip() or "Rival"

    def _rival_existente() -> ClubDTO | None:
        """El club rival si ya existe (elegido de la lista o escrito igual que uno existente)."""
        if dd_rival.value:
            return next((c for c in rivales if str(c.idClub) == dd_rival.value), None)
        buscado = normalizar_texto(texto_rival[0])
        return next((c for c in rivales if buscado and normalizar_texto(c.nombre) == buscado), None)

    def _actualizar_marcador() -> None:
        pts_propios = planilla_propia.puntos
        pts_rival = fila_totales_rival.puntos if _modo_rival() == MODO_TOTALES else planilla_rival.puntos
        nombre_rival = _nombre_rival()
        if _es_local():
            marcador.value = f"{club.nombre} {pts_propios} - {pts_rival} {nombre_rival}"
            bloque_cuartos.actualizar_equipos(club.nombre, nombre_rival)
        else:
            marcador.value = f"{nombre_rival} {pts_rival} - {pts_propios} {club.nombre}"
            bloque_cuartos.actualizar_equipos(nombre_rival, club.nombre)
        page.update()

    def _mostrar_aviso(texto: str, texto_link: str, ruta: str) -> None:
        aviso_texto.value = texto
        aviso_link.content = texto_link
        aviso_link.on_click = lambda: page.navigate(ruta)
        aviso.visible = True

    def _refrescar_convocados() -> None:
        """Casillas marcadas segun `convocados`, contador y planilla con solo los convocados."""
        for casilla in casillas_convocados.controls:
            if isinstance(casilla, ft.Checkbox):
                casilla.value = casilla.data in convocados
        contador_convocados.value = f"Convocados: {len(convocados)}/{MAX_JUGADORES_PARTIDO}"
        planilla_propia.cargar_jugadores([j for j in lista_actual if j.id in convocados])

    def al_marcar_convocado(id_jugador: int) -> None:
        if id_jugador in convocados:
            convocados.discard(id_jugador)
        elif len(convocados) >= MAX_JUGADORES_PARTIDO:
            error.value = f"En un partido juegan como máximo {MAX_JUGADORES_PARTIDO}: desmarcá a otro primero."
        else:
            convocados.add(id_jugador)
            error.value = ""
        _refrescar_convocados()
        _actualizar_marcador()

    def _cargar_planilla_propia() -> None:
        aviso.visible = False
        inscripcion = _inscripcion_elegida()
        lista_actual.clear()
        convocados.clear()
        if inscripcion is None:
            seccion_propia.visible = False
            return
        lista_actual.extend(listar_lista_uc.ejecutar(inscripcion.idInscripcion))
        if not lista_actual:
            seccion_propia.visible = False
            _mostrar_aviso(
                "Tu lista de buena fe de este torneo está vacía: cargá tus jugadores primero.",
                "Ir a listas de buena fe",
                "/listas",
            )
            return
        if len(lista_actual) <= MAX_JUGADORES_PARTIDO:
            convocados.update(j.id for j in lista_actual)  # con 12 o menos, lo normal es que vayan todos
        casillas_convocados.controls = [
            ft.Checkbox(
                label=j.nombre_completo,
                data=j.id,
                on_change=partial(al_marcar_convocado, j.id),
                col=COL_CASILLA_CONVOCADO,
            )
            for j in lista_actual
        ]
        # Plegada si ya vienen todos marcados; abierta si hay que elegir (lista de mas de 12).
        plegable_convocados.expanded = not convocados
        _refrescar_convocados()
        seccion_propia.visible = True

    def _cargar_planilla_rival() -> None:
        """Si el rival existe y tiene lista en este torneo, trae sus jugadores; si no, filas para escribir."""
        jugadores = []
        rival = _rival_existente()
        inscripcion = _inscripcion_elegida()
        if rival is not None and inscripcion is not None:
            ins_rival = next(
                (
                    i
                    for i in listar_inscripciones_uc.ejecutar(rival.idClub)
                    if i.idCompetencia == inscripcion.idCompetencia and i.idCategoria == inscripcion.idCategoria
                ),
                None,
            )
            if ins_rival is not None:
                jugadores = listar_lista_uc.ejecutar(ins_rival.idInscripcion)
        planilla_rival.cargar_jugadores(jugadores)
        if not jugadores and not planilla_rival.filas_manuales:
            for _ in range(FILAS_RIVAL_INICIALES):
                planilla_rival.agregar_fila()

    def _refrescar_rival() -> None:
        nombre = _nombre_rival()
        titulo_rival.value = f"Rival: {nombre}"
        fila_totales_rival.actualizar_titulo(nombre)
        planilla_rival.actualizar_titulo(nombre)
        boxscore = _modo_rival() == MODO_BOXSCORE
        bloque_boxscore_rival.visible = boxscore
        bloque_totales_rival.visible = not boxscore
        if boxscore:
            _cargar_planilla_rival()

    # ------------------------------------------------------------------ eventos
    def al_elegir_torneo() -> None:
        def accion() -> None:
            _cargar_planilla_propia()
            _refrescar_rival()

        ejecutar_mostrando_errores(accion, error, nombre="carga_partido.elegir_torneo")
        _actualizar_marcador()

    def al_elegir_rival() -> None:
        texto_rival[0] = _nombre_rival() if dd_rival.value else texto_rival[0]
        ejecutar_mostrando_errores(_refrescar_rival, error, nombre="carga_partido.elegir_rival")
        _actualizar_marcador()

    def al_escribir_rival(e: object = None) -> None:
        escrito = getattr(e, "data", None)
        texto_rival[0] = escrito if isinstance(escrito, str) else (dd_rival.text or "")
        # Si se edita el texto despues de elegir un club, deja de estar elegido ese club
        elegido = next((c for c in rivales if str(c.idClub) == dd_rival.value), None)
        if elegido is not None and normalizar_texto(elegido.nombre) != normalizar_texto(texto_rival[0]):
            dd_rival.value = None
        titulo_rival.value = f"Rival: {_nombre_rival()}"
        fila_totales_rival.actualizar_titulo(_nombre_rival())
        _actualizar_marcador()

    def al_cambiar_modo_rival() -> None:
        ejecutar_mostrando_errores(_refrescar_rival, error, nombre="carga_partido.cambiar_modo_rival")
        _actualizar_marcador()

    dd_torneo.on_select = al_elegir_torneo
    dd_rival.on_select = al_elegir_rival
    dd_rival.on_text_change = al_escribir_rival
    dd_rival.on_blur = al_elegir_rival
    seg_condicion.on_change = lambda: _actualizar_marcador()
    seg_modo_rival.on_change = al_cambiar_modo_rival

    # ------------------------------------------------------------------ guardar
    def _resolver_rival() -> tuple[int, str | None]:
        """(id del rival, None) si ya existe; (ID_CLUB_NUEVO, nombre) si hay que crearlo junto con el partido."""
        existente = _rival_existente()
        if existente is not None:
            return existente.idClub, None
        nombre = texto_rival[0].strip()
        if not nombre:
            raise DatoInvalidoError("Elegí el rival o escribí su nombre.")
        if normalizar_texto(nombre) == normalizar_texto(club.nombre):
            raise DatoInvalidoError("El rival no puede ser tu propio club.")
        return ID_CLUB_NUEVO, nombre

    def _leer_planilla[T](leer: Callable[[], T], equipo: str) -> T:
        """Lee una planilla; su error ya queda marcado en ella, asi que abajo solo se dice donde mirar."""
        try:
            return leer()
        except DatoInvalidoError:
            raise DatoInvalidoError(f"Revisá la planilla de {equipo}: el error está marcado arriba.") from None

    def _avisos(guardado: _Guardado, inscripcion: InscripcionDTO) -> list[str]:
        """Cosas raras pero posibles: se avisan y se puede guardar igual."""
        avisos: list[str] = []
        cantidad = len(guardado.boxscore_propio.estadisticas)
        if cantidad < MIN_JUGADORES_PARTIDO:
            avisos.append(
                f"Cargaste {cantidad} jugador(es) de tu equipo; un partido arranca con al menos "
                f"{MIN_JUGADORES_PARTIDO}. Si alguno jugó y quedó con la fila vacía, no se guarda."
            )
        comp = competencias_por_id.get(inscripcion.idCompetencia)
        cat = categorias_por_id.get(inscripcion.idCategoria)
        rival = normalizar_texto(_nombre_rival())
        for p in listar_partidos_uc.ejecutar(club.idClub):
            if p.idPartido == id_partido or p.fecha != guardado.partido.fecha:
                continue
            mismo_torneo = (
                comp is not None
                and p.competencia == comp.nombre
                and p.anioCompetencia == comp.anio
                and (cat is None or p.categoria == cat.nombre)
            )
            if mismo_torneo and rival in (normalizar_texto(p.clubLocal), normalizar_texto(p.clubVisitante)):
                avisos.append(f"Ya cargaste un partido contra {_nombre_rival()} el {p.fecha} en este torneo.")
                break
        return avisos

    def _guardar(guardado: _Guardado) -> None:
        def accion() -> None:
            resultado = cargar_partido_uc.ejecutar(
                guardado.partido, guardado.boxscore_propio, guardado.rival, guardado.nombre_rival_nuevo
            )
            if resultado is None:
                raise RuntimeError("No se pudo guardar el partido en la base de datos")
            page.navigate("/partidos")

        ejecutar_mostrando_errores(accion, error, nombre="carga_partido.guardar")
        page.update()

    def _validar_datos() -> None:
        """Paso 1: lo minimo para armar las planillas (torneo con lista, fecha y rival)."""
        if _inscripcion_elegida() is None:
            raise DatoInvalidoError("Elegí la competencia y categoría del partido.")
        if not (campo_fecha.value or "").strip():
            raise DatoInvalidoError("Indicá la fecha del partido.")
        if not seccion_propia.visible:
            raise DatoInvalidoError("Tu planilla está vacía: revisá la lista de buena fe de este torneo.")
        _resolver_rival()

    def _armar_guardado() -> _Guardado:
        """Paso 2: lee las planillas y los cuartos y arma exactamente lo que se va a guardar."""
        inscripcion = _inscripcion_elegida()
        if inscripcion is None:
            raise DatoInvalidoError("Elegí la competencia y categoría del partido.")
        if not convocados:
            raise DatoInvalidoError(SIN_CONVOCADOS)
        estadisticas_propias = _leer_planilla(planilla_propia.leer, club.nombre)
        if not estadisticas_propias:
            raise DatoInvalidoError("Cargá las estadísticas de al menos un jugador de tu equipo.")
        modo = _modo_rival()
        nombre_rival = _nombre_rival()
        totales_rival = (
            _leer_planilla(partial(fila_totales_rival.leer, 0), nombre_rival) if modo == MODO_TOTALES else None
        )
        estadisticas_rival = _leer_planilla(planilla_rival.leer, nombre_rival) if modo == MODO_BOXSCORE else []
        if modo == MODO_BOXSCORE and not estadisticas_rival:
            raise DatoInvalidoError("Cargá al menos un jugador del rival, o elegí 'Solo totales o resultado'.")

        id_rival, nombre_nuevo = _resolver_rival()
        id_local, id_visitante = (club.idClub, id_rival) if _es_local() else (id_rival, club.idClub)
        rival: BoxscoreDTO | TotalesEquipoDTO = (
            replace(totales_rival, idClub=id_rival)
            if totales_rival is not None
            else BoxscoreDTO(idClub=id_rival, estadisticas=estadisticas_rival)
        )
        return _Guardado(
            partido=PartidoDTO(
                fecha=(campo_fecha.value or "").strip(),
                estadio=(campo_estadio.value or "").strip() or None,
                idCompetencia=inscripcion.idCompetencia,
                idCategoria=inscripcion.idCategoria,
                idClubLocal=id_local,
                idClubVisitante=id_visitante,
                cuartos=bloque_cuartos.leer_cuartos(id_local, id_visitante),
                idPartido=id_partido,
            ),
            boxscore_propio=BoxscoreDTO(idClub=club.idClub, estadisticas=estadisticas_propias),
            rival=rival,
            nombre_rival_nuevo=nombre_nuevo,
        )

    # ------------------------------------------------------------------ pasos
    paso_actual = [0]
    pendiente: list[_Guardado | None] = [None]  # lo que se confirma en el paso 3
    indicador = ft.Row(key=CLAVE_INDICADOR_PASOS, spacing=ESPACIO_CHICO)
    resumen = ft.Column(key=CLAVE_RESUMEN, spacing=ESPACIO)

    def _dibujar_indicador() -> None:
        controles_indicador: list[ft.Control] = []
        for nro, nombre in enumerate(PASOS):
            hecho, ahora = nro < paso_actual[0], nro == paso_actual[0]
            circulo = ft.Container(
                content=ft.Icon(ft.Icons.CHECK, size=16, color=ft.Colors.ON_PRIMARY)
                if hecho
                else ft.Text(str(nro + 1), size=13, weight=ft.FontWeight.W_600),
                width=28,
                height=28,
                border_radius=14,
                alignment=ft.Alignment.CENTER,
                bgcolor=ft.Colors.PRIMARY if hecho else None,
                border=ft.Border.all(2 if ahora else 1, ft.Colors.PRIMARY if ahora or hecho else ft.Colors.OUTLINE),
            )
            etiqueta = ft.Text(
                nombre,
                weight=ft.FontWeight.W_600 if ahora else None,
                color=None if ahora else ft.Colors.ON_SURFACE_VARIANT,
            )
            if controles_indicador:
                controles_indicador.append(ft.Container(height=1, expand=True, bgcolor=ft.Colors.OUTLINE_VARIANT))
            controles_indicador.append(ft.Row([circulo, etiqueta], spacing=ESPACIO_CHICO))
        indicador.controls = controles_indicador

    def _nombres_local_visitante() -> tuple[str, str]:
        return (club.nombre, _nombre_rival()) if _es_local() else (_nombre_rival(), club.nombre)

    def _dibujar_resumen(guardado: _Guardado, avisos: list[str]) -> None:
        """Paso 3: lo que se va a guardar, en limpio, con los avisos a la vista."""
        inscripcion = _inscripcion_elegida()
        torneo = etiqueta_inscripcion(inscripcion, competencias_por_id, categorias_por_id) if inscripcion else ""
        detalle = " · ".join(p for p in (guardado.partido.fecha, torneo, guardado.partido.estadio) if p)
        rival = guardado.rival
        puntos_rival = (
            rival.puntos if isinstance(rival, TotalesEquipoDTO) else sum(e.puntos for e in rival.estadisticas)
        )
        jugadores_rival = "Solo totales" if isinstance(rival, TotalesEquipoDTO) else str(len(rival.estadisticas))
        propio = guardado.boxscore_propio.estadisticas
        condicion_propia, condicion_rival = ("Local", "Visitante") if _es_local() else ("Visitante", "Local")
        filas = [
            (club.nombre, condicion_propia, str(len(propio)), str(sum(e.puntos for e in propio))),
            (_nombre_rival(), condicion_rival, jugadores_rival, str(puntos_rival)),
        ]
        controles_resumen: list[ft.Control] = [
            ft.Text(marcador.value, size=24, weight=ft.FontWeight.W_600),
            ft.Text(detalle, color=ft.Colors.ON_SURFACE_VARIANT),
            crear_tabla_datos(COLUMNAS_RESUMEN, filas),
        ]
        if guardado.partido.cuartos:
            local, visitante = _nombres_local_visitante()
            columnas, filas_q = filas_cuartos(
                guardado.partido.cuartos,
                [(guardado.partido.idClubLocal, local), (guardado.partido.idClubVisitante, visitante)],
            )
            controles_resumen += [
                ft.Text("Puntos por cuarto", weight=ft.FontWeight.W_600),
                crear_tabla_datos(columnas, filas_q),
            ]
        if guardado.nombre_rival_nuevo:
            controles_resumen.append(
                ft.Text(
                    f"«{guardado.nombre_rival_nuevo}» no existe todavía: se crea como club rival al guardar.",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        controles_resumen.append(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ON_TERTIARY_CONTAINER),
                                ft.Text(aviso, color=ft.Colors.ON_TERTIARY_CONTAINER, expand=True),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        bgcolor=ft.Colors.TERTIARY_CONTAINER,
                        border_radius=RADIO,
                        padding=ESPACIO,
                    )
                    for aviso in avisos
                ],
                key=CLAVE_AVISOS_RESUMEN,
                spacing=ESPACIO_CHICO,
            )
        )
        resumen.controls = controles_resumen

    def _ir_a_paso(nro: int) -> None:
        paso_actual[0] = nro
        for indice, contenedor in enumerate(contenedores_pasos):
            contenedor.visible = indice == nro
        boton_atras.visible = nro > 0
        boton_siguiente.visible = nro < len(PASOS) - 1
        boton_guardar.visible = nro == len(PASOS) - 1
        _dibujar_indicador()

    def al_siguiente() -> None:
        def accion() -> None:
            if paso_actual[0] == 0:
                _validar_datos()
                _ir_a_paso(1)
            else:
                guardado = _armar_guardado()
                pendiente[0] = guardado
                _dibujar_resumen(guardado, _avisos(guardado, _inscripcion_obligatoria()))
                _ir_a_paso(2)

        ejecutar_mostrando_errores(accion, error, nombre="carga_partido.siguiente")
        page.update()

    def _inscripcion_obligatoria() -> InscripcionDTO:
        inscripcion = _inscripcion_elegida()
        if inscripcion is None:
            raise DatoInvalidoError("Elegí la competencia y categoría del partido.")
        return inscripcion

    def al_atras() -> None:
        error.value = ""
        _ir_a_paso(max(paso_actual[0] - 1, 0))
        page.update()

    def al_guardar() -> None:
        # Solo se llega al boton desde el paso 3, con `pendiente` armado por "Siguiente".
        if paso_actual[0] == len(PASOS) - 1 and pendiente[0] is not None:
            _guardar(pendiente[0])

    # ------------------------------------------------------------------ editar: llenar con lo guardado
    def _precargar(id_editar: int) -> None:
        partido = obtener_partido_uc.ejecutar(id_editar)
        if partido is None or club.idClub not in (partido.idClubLocal, partido.idClubVisitante):
            raise DatoInvalidoError("Ese partido no existe o no es de tu club.")
        inscripcion = next(
            (
                i
                for i in inscripciones_propias.values()
                if i.idCompetencia == partido.idCompetencia and i.idCategoria == partido.idCategoria
            ),
            None,
        )
        if inscripcion is None:
            raise DatoInvalidoError("Tu club ya no está inscripto en el torneo de este partido.")
        dd_torneo.value = str(inscripcion.idInscripcion)
        campo_fecha.value = partido.fecha
        campo_estadio.value = partido.estadio or ""
        es_local = partido.idClubLocal == club.idClub
        seg_condicion.selected = [CONDICION_LOCAL if es_local else CONDICION_VISITANTE]
        id_rival = partido.idClubVisitante if es_local else partido.idClubLocal
        dd_rival.value = str(id_rival)
        texto_rival[0] = _nombre_rival()

        _cargar_planilla_propia()
        boxscore = obtener_boxscore_uc.ejecutar(id_editar)
        propias = [f for f in boxscore if f.idClub == club.idClub]
        ids_lista = {j.id for j in lista_actual}
        convocados.clear()
        convocados.update(f.idJugador for f in propias if f.idJugador in ids_lista)
        _refrescar_convocados()
        faltan = [f.nombreJugador for f in propias if f.idJugador not in ids_lista]
        for fila in propias:
            planilla_propia.poner_valores(fila.idJugador, asdict(fila))

        totales_rival = next((t for t in obtener_totales_uc.ejecutar(id_editar) if t.idClub == id_rival), None)
        if totales_rival is not None and totales_rival.origen == MODO_TOTALES:
            seg_modo_rival.selected = [MODO_TOTALES]
            fila_totales_rival.poner_valores(totales_rival.puntos, asdict(totales_rival))
            _refrescar_rival()
        else:
            seg_modo_rival.selected = [MODO_BOXSCORE]
            _refrescar_rival()
            for fila in (f for f in boxscore if f.idClub == id_rival):
                if not planilla_rival.poner_valores(fila.idJugador, asdict(fila)):
                    faltan.append(fila.nombreJugador)
        bloque_cuartos.cargar_cuartos(partido.cuartos, partido.idClubLocal, partido.idClubVisitante)
        if faltan:
            aviso_edicion.value = (
                f"Ya no están en la lista de buena fe: {', '.join(faltan)}. Si guardás, sus estadísticas se pierden."
            )
            aviso_edicion.visible = True

    # ------------------------------------------------------------------ armado
    tarjeta_datos = ft.Container(
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border_radius=RADIO,
        padding=ESPACIO,
        content=ft.Column(
            spacing=ESPACIO,
            controls=[
                ft.Text("Datos del partido", weight=ft.FontWeight.W_600),
                ft.ResponsiveRow(
                    spacing=ESPACIO,
                    run_spacing=ESPACIO,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Container(dd_torneo, col={"sm": 12, "md": 6, "xl": 4}),
                        ft.Container(campo_fecha, col={"sm": 6, "md": 3, "xl": 2}),
                        ft.Container(campo_estadio, col={"sm": 6, "md": 3, "xl": 2}),
                        ft.Container(dd_rival, col={"sm": 12, "md": 6, "xl": 2}),
                        ft.Container(seg_condicion, col={"sm": 12, "md": 6, "xl": 2}),
                    ],
                ),
                aviso,
            ],
        ),
    )
    boton_guardar = ft.FilledButton(
        "Guardar cambios" if editando else "Guardar partido",
        key=CLAVE_BOTON_GUARDAR,
        icon=ft.Icons.SAVE,
        on_click=al_guardar,
    )
    boton_siguiente = ft.FilledButton(
        "Siguiente", key=CLAVE_BOTON_SIGUIENTE, icon=ft.Icons.ARROW_FORWARD, on_click=al_siguiente
    )
    boton_atras = ft.OutlinedButton("Atrás", key=CLAVE_BOTON_ATRAS, icon=ft.Icons.ARROW_BACK, on_click=al_atras)
    if not inscripciones_propias:
        _mostrar_aviso(SIN_INSCRIPCIONES, "Ir a inscripciones", "/inscripciones")
    contenedores_pasos = [
        ft.Column([tarjeta_datos], key=CLAVE_PASOS[0], spacing=ESPACIO),
        ft.Column(
            [
                seccion_propia,
                ft.Divider(),
                ft.Row([titulo_rival, seg_modo_rival], spacing=ESPACIO, wrap=True),
                bloque_totales_rival,
                bloque_boxscore_rival,
                ft.Divider(),
                bloque_cuartos.control,
                ft.Divider(),
                marcador,
            ],
            key=CLAVE_PASOS[1],
            spacing=ESPACIO,
        ),
        ft.Column([resumen], key=CLAVE_PASOS[2], spacing=ESPACIO),
    ]
    controles: list[ft.Control] = [
        indicador,
        aviso_edicion,
        *contenedores_pasos,
        error,
        ft.Row(
            [
                ft.TextButton("Cancelar", on_click=lambda: page.navigate("/partidos")),
                ft.Row([boton_atras, boton_siguiente, boton_guardar], spacing=ESPACIO),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    ]
    _ir_a_paso(0)

    if id_partido is not None:
        try:
            _precargar(id_partido)
        except DatoInvalidoError as err:
            error.value = str(err)
            boton_guardar.disabled = True  # sin el partido cargado, guardar crearia otro distinto
            boton_siguiente.disabled = True
    elif len(inscripciones_propias) == 1:  # con una sola inscripcion, ya viene elegida
        dd_torneo.value = str(next(iter(inscripciones_propias)))
        ejecutar_mostrando_errores(_cargar_planilla_propia, error, nombre="carga_partido.precargar")
    _refrescar_rival()
    nombre_rival = _nombre_rival()
    pts_propios = planilla_propia.puntos
    pts_rival = fila_totales_rival.puntos if _modo_rival() == MODO_TOTALES else planilla_rival.puntos
    marcador.value = (
        f"{club.nombre} {pts_propios} - {pts_rival} {nombre_rival}"
        if _es_local()
        else f"{nombre_rival} {pts_rival} - {pts_propios} {club.nombre}"
    )

    ruta = ruta_editar_partido(id_partido) if id_partido is not None else "/partidos/cargar"
    contenido = crear_pagina(
        "Editar partido" if editando else "Cargar partido",
        controles,
        subtitulo=f"{club.nombre}: tu boxscore completo; del rival, sus totales o su boxscore.",
    )
    return crear_vista_interna(page, sesion, ruta, contenido)
