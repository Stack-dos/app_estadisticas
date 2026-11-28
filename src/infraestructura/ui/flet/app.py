"""Punto de entrada de la GUI de escritorio (Flet). Composition root de la interfaz (US-105 a US-107).

Es el unico lugar que conoce las clases concretas (SQLite, PBKDF2): arma los casos de uso y se los
pasa a las pantallas, que solo dependen de casos de uso y DTOs.
"""

import os
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import flet as ft

import config.rutas as r
from aplicacion.casos_uso.agregar_jugador_lista import AgregarJugadorAListaBuenaFeUseCase
from aplicacion.casos_uso.agregar_jugadores_lista import AgregarJugadoresAListaBuenaFeUseCase
from aplicacion.casos_uso.buscar_jugadores_por_nombre import BuscarJugadoresPorNombreUseCase
from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.cargar_partido import CargarPartidoUseCase
from aplicacion.casos_uso.crear_categoria import CrearCategoriaUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.crear_competencia import CrearCompetenciaUseCase
from aplicacion.casos_uso.desvincular_jugador_club import DesvincularJugadorDeClubUseCase
from aplicacion.casos_uso.editar_jugador import EditarJugadorUseCase
from aplicacion.casos_uso.eliminar_categoria import EliminarCategoriaUseCase
from aplicacion.casos_uso.eliminar_club import EliminarClubUseCase
from aplicacion.casos_uso.eliminar_competencia import EliminarCompetenciaUseCase
from aplicacion.casos_uso.eliminar_inscripcion import EliminarInscripcionUseCase
from aplicacion.casos_uso.eliminar_jugador import EliminarJugadorUseCase
from aplicacion.casos_uso.eliminar_partido import EliminarPartidoUseCase
from aplicacion.casos_uso.habilitar_categoria_competencia import HabilitarCategoriaEnCompetenciaUseCase
from aplicacion.casos_uso.inscribir_club_competencia import InscribirClubEnCompetenciaUseCase
from aplicacion.casos_uso.listar_categorias import ListarCategoriasUseCase
from aplicacion.casos_uso.listar_categorias_competencia import ListarCategoriasDeCompetenciaUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_clubes_rivales import ListarClubesRivalesUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.listar_competencias import ListarCompetenciasUseCase
from aplicacion.casos_uso.listar_inscripciones_club import ListarInscripcionesClubUseCase
from aplicacion.casos_uso.listar_jugador_club import ListarJugadoresClubUseCase
from aplicacion.casos_uso.listar_jugadores_todos import ListarJugadoresTodosUseCase
from aplicacion.casos_uso.listar_lideres_club import ListarLideresClubUseCase
from aplicacion.casos_uso.listar_lista_buena_fe import ListarListaBuenaFeUseCase
from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.obtener_boxscore_partido import ObtenerBoxscorePartidoUseCase
from aplicacion.casos_uso.obtener_partido import ObtenerPartidoUseCase
from aplicacion.casos_uso.obtener_totales_partido import ObtenerTotalesPartidoUseCase
from aplicacion.casos_uso.partidos_por_club import ListarPartidosPorClubUseCase
from aplicacion.casos_uso.quitar_categoria_competencia import QuitarCategoriaDeCompetenciaUseCase
from aplicacion.casos_uso.quitar_jugador_lista import QuitarJugadorDeListaBuenaFeUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.casos_uso.renombrar_club import RenombrarClubUseCase
from aplicacion.casos_uso.restaurar_sesion import RestaurarSesionUseCase
from aplicacion.casos_uso.vaciar_lista_buena_fe import VaciarListaBuenaFeUseCase
from aplicacion.casos_uso.vincular_jugador_club import VincularJugadorAClubUseCase
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.logger import get_logger
from infraestructura.observabilidad import nueva_accion
from infraestructura.persistencia.database_manager import SQLiteManager
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_competencia_repositorio import SqliteCompetenciaRepositorio
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio
from infraestructura.repositorios.sqlite_partido_repositorio import SqlitePartidoRepositorio
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.estilo import aplicar_tema
from infraestructura.ui.flet.screens.carga_partido_screen import crear_carga_partido_view
from infraestructura.ui.flet.screens.categorias_screen import crear_categorias_view
from infraestructura.ui.flet.screens.clubes_screen import crear_clubes_view
from infraestructura.ui.flet.screens.competencias_screen import crear_competencias_view
from infraestructura.ui.flet.screens.detalle_partido_screen import crear_detalle_partido_view
from infraestructura.ui.flet.screens.guia_screen import crear_guia_view
from infraestructura.ui.flet.screens.inicio_screen import crear_inicio_view
from infraestructura.ui.flet.screens.inscripciones_screen import crear_inscripciones_view
from infraestructura.ui.flet.screens.jugadores_screen import crear_jugadores_view
from infraestructura.ui.flet.screens.lista_buena_fe_screen import crear_lista_buena_fe_view
from infraestructura.ui.flet.screens.login_screen import crear_login_view
from infraestructura.ui.flet.screens.partidos_screen import crear_partidos_view
from infraestructura.ui.flet.screens.registro_screen import crear_registro_view

logger = get_logger(__name__)

RUTA_LOGIN = "/login"
RUTA_REGISTRO = "/registro"
RUTA_INICIO = "/inicio"
RUTA_CLUBES = "/clubes"
RUTA_COMPETENCIAS = "/competencias"
RUTA_CATEGORIAS = "/categorias"
RUTA_INSCRIPCIONES = "/inscripciones"
RUTA_LISTAS = "/listas"
RUTA_JUGADORES = "/jugadores"
RUTA_PARTIDOS = "/partidos"
RUTA_CARGAR_PARTIDO = "/partidos/cargar"
RUTA_EDITAR_PARTIDO = "/partidos/editar"  # lleva el id al final: "/partidos/editar/5"
RUTA_DETALLE_PARTIDO = "/partidos/ver"  # lleva el id al final: "/partidos/ver/5"
RUTA_GUIA = "/guia"  # se puede abrir con o sin sesion
RUTAS_PUBLICAS = {RUTA_LOGIN, RUTA_REGISTRO}
RUTAS_CON_CLUB = {
    RUTA_COMPETENCIAS,
    RUTA_CATEGORIAS,
    RUTA_INSCRIPCIONES,
    RUTA_LISTAS,
    RUTA_JUGADORES,
    RUTA_PARTIDOS,
    RUTA_CARGAR_PARTIDO,
}
RUTAS_INTERNAS = {RUTA_INICIO, RUTA_CLUBES, *RUTAS_CON_CLUB}
RUTAS_CON_ID = {RUTA_EDITAR_PARTIDO, RUTA_DETALLE_PARTIDO}  # internas, con club activo y con un id al final
AVISO_REQUIERE_CLUB = "Elegí o creá un club activo para trabajar en esa sección."


@dataclass
class Dependencias:
    """Lo que usan las pantallas: la sesion y los casos de uso (nunca repositorios ni la conexion).

    Solo la tabla de rutas la recibe entera; cada pantalla recibe unicamente los campos que usa.
    """

    sesion: SessionManager
    registrar_uc: RegistrarEntrenadorUseCase
    login_uc: LoginLocalUseCase
    crear_club_uc: CrearClubUseCase
    listar_clubes_uc: ListarClubesUsuarioUseCase
    listar_clubes_todos_uc: ListarClubesUseCase
    cambiar_club_uc: CambiarClubActivoUseCase
    crear_competencia_uc: CrearCompetenciaUseCase
    listar_competencias_uc: ListarCompetenciasUseCase
    crear_categoria_uc: CrearCategoriaUseCase
    listar_categorias_uc: ListarCategoriasUseCase
    habilitar_categoria_uc: HabilitarCategoriaEnCompetenciaUseCase
    listar_categorias_comp_uc: ListarCategoriasDeCompetenciaUseCase
    quitar_categoria_uc: QuitarCategoriaDeCompetenciaUseCase
    eliminar_competencia_uc: EliminarCompetenciaUseCase
    eliminar_categoria_uc: EliminarCategoriaUseCase
    inscribir_club_uc: InscribirClubEnCompetenciaUseCase
    listar_inscripciones_uc: ListarInscripcionesClubUseCase
    eliminar_inscripcion_uc: EliminarInscripcionUseCase
    agregar_jugador_lista_uc: AgregarJugadorAListaBuenaFeUseCase
    agregar_jugadores_lista_uc: AgregarJugadoresAListaBuenaFeUseCase
    quitar_jugador_lista_uc: QuitarJugadorDeListaBuenaFeUseCase
    vaciar_lista_uc: VaciarListaBuenaFeUseCase
    listar_lista_uc: ListarListaBuenaFeUseCase
    listar_jugadores_club_uc: ListarJugadoresClubUseCase
    registrar_jugador_uc: RegistrarJugadorUseCase
    vincular_jugador_uc: VincularJugadorAClubUseCase
    desvincular_jugador_uc: DesvincularJugadorDeClubUseCase
    buscar_jugadores_uc: BuscarJugadoresPorNombreUseCase
    listar_jugadores_todos_uc: ListarJugadoresTodosUseCase
    editar_jugador_uc: EditarJugadorUseCase
    eliminar_jugador_uc: EliminarJugadorUseCase
    listar_partidos_uc: ListarPartidosPorClubUseCase
    obtener_boxscore_uc: ObtenerBoxscorePartidoUseCase
    obtener_totales_uc: ObtenerTotalesPartidoUseCase
    listar_lideres_uc: ListarLideresClubUseCase
    cargar_partido_uc: CargarPartidoUseCase
    obtener_partido_uc: ObtenerPartidoUseCase
    eliminar_partido_uc: EliminarPartidoUseCase
    listar_clubes_rivales_uc: ListarClubesRivalesUseCase
    renombrar_club_uc: RenombrarClubUseCase
    eliminar_club_uc: EliminarClubUseCase


def construir_dependencias(
    conexion: sqlite3.Connection, hasher: PasswordHasher, almacen: SesionAlmacen
) -> Dependencias:
    """
    Arma repositorios y casos de uso sobre una conexion ya abierta, y restaura la sesion recordada.

    Devuelve la app "tal como arranca": si habia una sesion recordada y sigue siendo valida, ya viene
    abierta (y el router manda directo a "/inicio"). Esta separado de `ejecutar()` para poder testear
    el cableado con una DB `:memory:`, sin ventana; llamarla dos veces con la misma base y el mismo
    archivo simula cerrar y reabrir la app.

    Args:
        conexion (sqlite3.Connection): Conexion abierta y con el esquema inicializado.
        hasher (PasswordHasher): Hasher de contraseñas (en los tests, uno con pocas iteraciones).
        almacen (SesionAlmacen): Donde se guarda la sesion recordada (en los tests, un archivo temporal).

    Returns:
        Dependencias: La sesion (restaurada o vacia) y los casos de uso listos para usar.
    """
    repo_usuario = SqliteUsuarioRepositorio(conexion)
    repo_club = SqliteClubRepositorio(conexion)
    repo_competencia = SqliteCompetenciaRepositorio(conexion)
    repo_jugador = SqliteJugadorRepositorio(conexion)
    repo_partido = SqlitePartidoRepositorio(conexion)
    sesion = SessionManager(almacen)
    cambiar_club_uc = CambiarClubActivoUseCase(repo_club)
    agregar_jugador_lista_uc = AgregarJugadorAListaBuenaFeUseCase(repo_competencia, repo_jugador)
    # RestaurarSesionUseCase no va en Dependencias: lo usa el arranque, no una pantalla.
    RestaurarSesionUseCase(almacen, repo_usuario, cambiar_club_uc, sesion).ejecutar()
    return Dependencias(
        sesion=sesion,
        registrar_uc=RegistrarEntrenadorUseCase(repo_usuario, hasher),
        login_uc=LoginLocalUseCase(repo_usuario, hasher),
        crear_club_uc=CrearClubUseCase(repo_club),
        listar_clubes_uc=ListarClubesUsuarioUseCase(repo_club),
        listar_clubes_todos_uc=ListarClubesUseCase(repo_club),
        cambiar_club_uc=cambiar_club_uc,
        crear_competencia_uc=CrearCompetenciaUseCase(repo_competencia),
        listar_competencias_uc=ListarCompetenciasUseCase(repo_competencia),
        crear_categoria_uc=CrearCategoriaUseCase(repo_competencia),
        listar_categorias_uc=ListarCategoriasUseCase(repo_competencia),
        habilitar_categoria_uc=HabilitarCategoriaEnCompetenciaUseCase(repo_competencia),
        listar_categorias_comp_uc=ListarCategoriasDeCompetenciaUseCase(repo_competencia),
        quitar_categoria_uc=QuitarCategoriaDeCompetenciaUseCase(repo_competencia),
        eliminar_competencia_uc=EliminarCompetenciaUseCase(repo_competencia),
        eliminar_categoria_uc=EliminarCategoriaUseCase(repo_competencia),
        inscribir_club_uc=InscribirClubEnCompetenciaUseCase(repo_competencia, repo_club),
        listar_inscripciones_uc=ListarInscripcionesClubUseCase(repo_competencia),
        eliminar_inscripcion_uc=EliminarInscripcionUseCase(repo_competencia),
        agregar_jugador_lista_uc=agregar_jugador_lista_uc,
        agregar_jugadores_lista_uc=AgregarJugadoresAListaBuenaFeUseCase(agregar_jugador_lista_uc),
        quitar_jugador_lista_uc=QuitarJugadorDeListaBuenaFeUseCase(repo_competencia),
        vaciar_lista_uc=VaciarListaBuenaFeUseCase(repo_competencia),
        listar_lista_uc=ListarListaBuenaFeUseCase(repo_competencia, repo_jugador),
        listar_jugadores_club_uc=ListarJugadoresClubUseCase(repo_jugador),
        registrar_jugador_uc=RegistrarJugadorUseCase(repo_jugador),
        vincular_jugador_uc=VincularJugadorAClubUseCase(repo_jugador, repo_club),
        desvincular_jugador_uc=DesvincularJugadorDeClubUseCase(repo_jugador),
        buscar_jugadores_uc=BuscarJugadoresPorNombreUseCase(repo_jugador),
        listar_jugadores_todos_uc=ListarJugadoresTodosUseCase(repo_jugador),
        editar_jugador_uc=EditarJugadorUseCase(repo_jugador),
        eliminar_jugador_uc=EliminarJugadorUseCase(repo_jugador),
        listar_partidos_uc=ListarPartidosPorClubUseCase(repo_partido),
        obtener_boxscore_uc=ObtenerBoxscorePartidoUseCase(repo_partido),
        obtener_totales_uc=ObtenerTotalesPartidoUseCase(repo_partido),
        listar_lideres_uc=ListarLideresClubUseCase(repo_partido),
        cargar_partido_uc=CargarPartidoUseCase(repo_partido, repo_competencia, repo_jugador),
        obtener_partido_uc=ObtenerPartidoUseCase(repo_partido),
        eliminar_partido_uc=EliminarPartidoUseCase(repo_partido),
        listar_clubes_rivales_uc=ListarClubesRivalesUseCase(repo_club),
        renombrar_club_uc=RenombrarClubUseCase(repo_club),
        eliminar_club_uc=EliminarClubUseCase(repo_club),
    )


def separar_ruta(ruta: str) -> tuple[str, int | None]:
    """
    Separa el id del final de una ruta con parametro: "/partidos/editar/5" -> ("/partidos/editar", 5).

    Args:
        ruta (str): Ruta pedida.

    Returns:
        tuple[str, int | None]: La ruta base y el id; la ruta tal cual y None si no es una ruta con id.
    """
    base, _, ultimo = ruta.rpartition("/")
    if base in RUTAS_CON_ID and ultimo.isdigit():
        return base, int(ultimo)
    return ruta, None


def requiere_club_activo(ruta: str, tiene_club: bool) -> str:
    """
    Guard de rutas operativas (US-107): si la ruta necesita club activo y no hay ninguno, manda a "/clubes".

    Args:
        ruta (str): Ruta interna ya validada.
        tiene_club (bool): Si la sesion tiene un club activo elegido.

    Returns:
        str: La misma ruta si puede entrar, o "/clubes" si falta elegir club.
    """
    base, _ = separar_ruta(ruta)
    if (base in RUTAS_CON_CLUB or base in RUTAS_CON_ID) and not tiene_club:
        return RUTA_CLUBES
    return ruta


def resolver_ruta(ruta: str, autenticado: bool, tiene_club: bool = True) -> str:
    """
    Ruta protegida: decide a que ruta hay que ir. Funcion pura, se testea sin ventana.

    Sin sesion solo se puede estar en las rutas publicas; con sesion, en las internas (un usuario
    logueado no vuelve a ver el login). Las rutas operativas sin club activo pasan por `requiere_club_activo`.
    Una ruta desconocida va a la pantalla de entrada de cada caso. La guia ("/guia") se abre siempre.

    Args:
        ruta (str): Ruta pedida (`page.route`).
        autenticado (bool): Si hay sesion iniciada.
        tiene_club (bool): Si hay club activo elegido.

    Returns:
        str: La ruta a la que hay que ir (la misma si se puede entrar).
    """
    if ruta == RUTA_GUIA:
        return ruta
    if autenticado:
        _, id_ruta = separar_ruta(ruta)
        destino = ruta if ruta in RUTAS_INTERNAS or id_ruta is not None else RUTA_INICIO
        return requiere_club_activo(destino, tiene_club)
    return ruta if ruta in RUTAS_PUBLICAS else RUTA_LOGIN


def _main(page: ft.Page, deps: Dependencias) -> None:
    """
    Arma la ventana. No se llama a mano: la llama Flet una vez, cuando la ventana está lista.

    Args:
        page (ft.Page): La ventana que entrega Flet.
        deps (Dependencias): Casos de uso y sesion armados por `ejecutar()`.
    """
    aplicar_tema(page)  # tema, letra y tamaño de la ventana (US-111)
    aviso_club_pendiente: list[str | None] = [None]

    def _construir_clubes() -> ft.View:
        aviso = aviso_club_pendiente[0]
        aviso_club_pendiente[0] = None
        return crear_clubes_view(
            page,
            deps.crear_club_uc,
            deps.listar_clubes_uc,
            deps.cambiar_club_uc,
            deps.listar_clubes_rivales_uc,
            deps.renombrar_club_uc,
            deps.eliminar_club_uc,
            deps.listar_inscripciones_uc,
            deps.listar_jugadores_club_uc,
            deps.sesion,
            aviso=aviso,
        )

    def _construir_carga_partido(id_partido: int | None) -> ft.View:
        return crear_carga_partido_view(
            page,
            deps.cargar_partido_uc,
            deps.listar_competencias_uc,
            deps.listar_categorias_uc,
            deps.listar_clubes_todos_uc,
            deps.listar_inscripciones_uc,
            deps.listar_lista_uc,
            deps.listar_partidos_uc,
            deps.obtener_partido_uc,
            deps.obtener_boxscore_uc,
            deps.obtener_totales_uc,
            deps.sesion,
            id_partido,
        )

    # Tabla de rutas: cada lambda construye su pantalla recien al navegar (asi vuelve con los campos vacios).
    # Cada pantalla recibe solo lo que usa, nunca `deps` entero.
    rutas: dict[str, Callable[[], ft.View]] = {
        RUTA_LOGIN: lambda: crear_login_view(page, deps.login_uc, deps.sesion),
        RUTA_REGISTRO: lambda: crear_registro_view(page, deps.registrar_uc, deps.sesion),
        RUTA_INICIO: lambda: crear_inicio_view(page, deps.sesion, deps.listar_partidos_uc, deps.listar_lideres_uc),
        RUTA_CLUBES: _construir_clubes,
        RUTA_COMPETENCIAS: lambda: crear_competencias_view(
            page,
            deps.crear_competencia_uc,
            deps.listar_competencias_uc,
            deps.listar_categorias_uc,
            deps.habilitar_categoria_uc,
            deps.listar_categorias_comp_uc,
            deps.quitar_categoria_uc,
            deps.eliminar_competencia_uc,
            deps.sesion,
        ),
        RUTA_CATEGORIAS: lambda: crear_categorias_view(
            page,
            deps.crear_categoria_uc,
            deps.listar_categorias_uc,
            deps.eliminar_categoria_uc,
            deps.sesion,
        ),
        RUTA_INSCRIPCIONES: lambda: crear_inscripciones_view(
            page,
            deps.inscribir_club_uc,
            deps.listar_inscripciones_uc,
            deps.listar_competencias_uc,
            deps.listar_categorias_uc,
            deps.listar_categorias_comp_uc,
            deps.eliminar_inscripcion_uc,
            deps.listar_jugadores_club_uc,
            deps.agregar_jugadores_lista_uc,
            deps.listar_lista_uc,
            deps.sesion,
        ),
        RUTA_LISTAS: lambda: crear_lista_buena_fe_view(
            page,
            deps.listar_inscripciones_uc,
            deps.listar_competencias_uc,
            deps.listar_categorias_uc,
            deps.listar_lista_uc,
            deps.listar_jugadores_club_uc,
            deps.agregar_jugadores_lista_uc,
            deps.quitar_jugador_lista_uc,
            deps.vaciar_lista_uc,
            deps.eliminar_inscripcion_uc,
            deps.sesion,
        ),
        RUTA_JUGADORES: lambda: crear_jugadores_view(
            page,
            deps.listar_jugadores_club_uc,
            deps.registrar_jugador_uc,
            deps.vincular_jugador_uc,
            deps.desvincular_jugador_uc,
            deps.buscar_jugadores_uc,
            deps.editar_jugador_uc,
            deps.eliminar_jugador_uc,
            deps.listar_jugadores_todos_uc,
            deps.sesion,
        ),
        RUTA_PARTIDOS: lambda: crear_partidos_view(
            page,
            deps.listar_partidos_uc,
            deps.listar_inscripciones_uc,
            deps.listar_competencias_uc,
            deps.listar_categorias_uc,
            deps.sesion,
        ),
        RUTA_CARGAR_PARTIDO: lambda: _construir_carga_partido(None),
        RUTA_GUIA: lambda: crear_guia_view(page, deps.sesion),
    }
    # Rutas con un id al final: reciben el id ya separado ("/partidos/editar/5" -> 5)
    rutas_con_id: dict[str, Callable[[int], ft.View]] = {
        RUTA_EDITAR_PARTIDO: _construir_carga_partido,
        RUTA_DETALLE_PARTIDO: lambda id_partido: crear_detalle_partido_view(
            page,
            deps.listar_partidos_uc,
            deps.obtener_partido_uc,
            deps.obtener_boxscore_uc,
            deps.obtener_totales_uc,
            deps.eliminar_partido_uc,
            deps.sesion,
            id_partido,
        ),
    }

    def al_cambiar_ruta() -> None:
        """Handler de `on_route_change`: cada cambio de pantalla es una accion propia en el log (US-110)."""
        with nueva_accion("navegar"):
            logger.info("Navegar a %s", page.route, extra={"evento": "navegar", "ruta": page.route})
            _dibujar_ruta()

    def _dibujar_ruta() -> None:
        """Decide que pantalla corresponde a `page.route` y la dibuja."""
        autenticado = deps.sesion.is_authenticated()
        tiene_club = deps.sesion.club_activo() is not None
        destino_sin_club_guard = resolver_ruta(page.route, autenticado, tiene_club=True)
        destino = resolver_ruta(page.route, autenticado, tiene_club=tiene_club)
        if destino != destino_sin_club_guard:
            aviso_club_pendiente[0] = AVISO_REQUIERE_CLUB
        if destino != page.route:
            # La pantalla siempre coincide con page.route: se cambia la ruta y Flet vuelve a llamar a este handler.
            page.navigate(destino)
            return
        page.views.clear()
        base, id_ruta = separar_ruta(destino)
        page.views.append(rutas_con_id[base](id_ruta) if id_ruta is not None else rutas[destino]())
        page.update()

    page.on_route_change = al_cambiar_ruta
    al_cambiar_ruta()  # dibuja la primera pantalla (al arrancar, page.route es "/")


def ejecutar() -> None:
    """
    Abre la base, arma las dependencias y la ventana; bloquea hasta que se cierra la ventana.
    """
    logger.info("Iniciando la interfaz grafica")
    # SQLite crea el archivo de la base, pero no su carpeta (la primera vez, ~/.statspro/ puede no existir)
    os.makedirs(r.DATOS_DIR, exist_ok=True)
    db = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
    conexion = db.connect()
    try:
        # El esquema y la sesion recordada son la accion "arranque" (US-110). ft.run queda afuera: si no,
        # las tareas de Flet heredarian este contexto y todos los clics saldrian con el mismo correlation_id.
        with nueva_accion("arranque"):
            db.inicializar_schema()
            deps = construir_dependencias(conexion, Pbkdf2PasswordHasher(), JsonSesionAlmacen(Path(r.SESSION_FILE)))
        # assets_dir absoluta: relativa, Flet la buscaria desde donde se lanzo la app y no encontraria el logo
        ft.run(lambda page: _main(page, deps), assets_dir=r.ASSETS_DIR)
    finally:
        db.close_connection()
        logger.info("Interfaz grafica cerrada")


if __name__ == "__main__":
    ejecutar()
