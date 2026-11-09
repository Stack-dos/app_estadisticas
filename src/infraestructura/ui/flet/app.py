"""Punto de entrada de la GUI de escritorio (Flet). Composition root de la interfaz (US-105 y US-106).

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
from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.casos_uso.restaurar_sesion import RestaurarSesionUseCase
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.logger import get_logger
from infraestructura.persistencia.database_manager import SQLiteManager
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.estilo import aplicar_tema
from infraestructura.ui.flet.screens.clubes_screen import crear_clubes_view
from infraestructura.ui.flet.screens.inicio_screen import crear_inicio_view
from infraestructura.ui.flet.screens.login_screen import crear_login_view
from infraestructura.ui.flet.screens.registro_screen import crear_registro_view

logger = get_logger(__name__)

RUTA_LOGIN = "/login"
RUTA_REGISTRO = "/registro"
RUTA_INICIO = "/inicio"
RUTA_CLUBES = "/clubes"
RUTAS_PUBLICAS = {RUTA_LOGIN, RUTA_REGISTRO}
RUTAS_INTERNAS = {RUTA_INICIO, RUTA_CLUBES}


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
    cambiar_club_uc: CambiarClubActivoUseCase


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
    sesion = SessionManager(almacen)
    cambiar_club_uc = CambiarClubActivoUseCase(repo_club)
    # RestaurarSesionUseCase no va en Dependencias: lo usa el arranque, no una pantalla.
    RestaurarSesionUseCase(almacen, repo_usuario, cambiar_club_uc, sesion).ejecutar()
    return Dependencias(
        sesion=sesion,
        registrar_uc=RegistrarEntrenadorUseCase(repo_usuario, hasher),
        login_uc=LoginLocalUseCase(repo_usuario, hasher),
        crear_club_uc=CrearClubUseCase(repo_club),
        listar_clubes_uc=ListarClubesUsuarioUseCase(repo_club),
        cambiar_club_uc=cambiar_club_uc,
    )


def resolver_ruta(ruta: str, autenticado: bool) -> str:
    """
    Ruta protegida: decide a que ruta hay que ir. Funcion pura, se testea sin ventana.

    Sin sesion solo se puede estar en las rutas publicas; con sesion, en las internas (un usuario
    logueado no vuelve a ver el login). Una ruta desconocida va a la pantalla de entrada de cada caso.

    Args:
        ruta (str): Ruta pedida (`page.route`).
        autenticado (bool): Si hay sesion iniciada.

    Returns:
        str: La ruta a la que hay que ir (la misma si se puede entrar).
    """
    if autenticado:
        return ruta if ruta in RUTAS_INTERNAS else RUTA_INICIO
    return ruta if ruta in RUTAS_PUBLICAS else RUTA_LOGIN


def _main(page: ft.Page, deps: Dependencias) -> None:
    """
    Arma la ventana. No se llama a mano: la llama Flet una vez, cuando la ventana está lista.

    Args:
        page (ft.Page): La ventana que entrega Flet.
        deps (Dependencias): Casos de uso y sesion armados por `ejecutar()`.
    """
    aplicar_tema(page)  # tema, letra y tamaño de la ventana (US-111)

    # Tabla de rutas: cada lambda construye su pantalla recien al navegar (asi vuelve con los campos vacios).
    # Cada pantalla recibe solo lo que usa, nunca `deps` entero.
    rutas: dict[str, Callable[[], ft.View]] = {
        RUTA_LOGIN: lambda: crear_login_view(page, deps.login_uc, deps.sesion),
        RUTA_REGISTRO: lambda: crear_registro_view(page, deps.registrar_uc, deps.sesion),
        RUTA_INICIO: lambda: crear_inicio_view(page, deps.sesion),
        RUTA_CLUBES: lambda: crear_clubes_view(
            page, deps.crear_club_uc, deps.listar_clubes_uc, deps.cambiar_club_uc, deps.sesion
        ),
    }

    def al_cambiar_ruta() -> None:
        """Handler de `on_route_change`: decide que pantalla corresponde a `page.route` y la dibuja."""
        destino = resolver_ruta(page.route, deps.sesion.is_authenticated())
        if destino != page.route:
            # La pantalla siempre coincide con page.route: se cambia la ruta y Flet vuelve a llamar a este handler.
            page.navigate(destino)
            return
        page.views.clear()
        page.views.append(rutas[destino]())
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
        db.inicializar_schema()
        deps = construir_dependencias(conexion, Pbkdf2PasswordHasher(), JsonSesionAlmacen(Path(r.SESSION_FILE)))
        # assets_dir absoluta: relativa, Flet la buscaria desde donde se lanzo la app y no encontraria el logo
        ft.run(lambda page: _main(page, deps), assets_dir=r.ASSETS_DIR)
    finally:
        db.close_connection()
        logger.info("Interfaz grafica cerrada")


if __name__ == "__main__":
    ejecutar()
