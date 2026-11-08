"""Punto de entrada de la GUI de escritorio (Flet). Composition root de la interfaz (US-105).

Es el unico lugar que conoce las clases concretas (SQLite, PBKDF2): arma los casos de uso y se los
pasa a las pantallas, que solo dependen de casos de uso y DTOs.
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import flet as ft

import config.rutas as r
from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.logger import get_logger
from infraestructura.persistencia.database_manager import SQLiteManager
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.repositorios.sqlite_usuario_repositorio import SqliteUsuarioRepositorio
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.screens.inicio_screen import crear_inicio_view
from infraestructura.ui.flet.screens.login_screen import crear_login_view
from infraestructura.ui.flet.screens.registro_screen import crear_registro_view

logger = get_logger(__name__)

RUTA_LOGIN = "/login"
RUTA_REGISTRO = "/registro"
RUTA_INICIO = "/inicio"
RUTAS_PUBLICAS = {RUTA_LOGIN, RUTA_REGISTRO}
RUTAS_INTERNAS = {RUTA_INICIO}


@dataclass
class Dependencias:
    """Lo que usan las pantallas: la sesion y los casos de uso (nunca repositorios ni la conexion).

    Solo la tabla de rutas la recibe entera; cada pantalla recibe unicamente los campos que usa.
    """

    sesion: SessionManager
    registrar_uc: RegistrarEntrenadorUseCase
    login_uc: LoginLocalUseCase


def construir_dependencias(
    conexion: sqlite3.Connection, hasher: PasswordHasher, almacen: SesionAlmacen
) -> Dependencias:
    """
    Arma repositorios y casos de uso sobre una conexion ya abierta.

    Esta separado de `ejecutar()` para poder testear el cableado con una DB `:memory:`, sin ventana.

    Args:
        conexion (sqlite3.Connection): Conexion abierta y con el esquema inicializado.
        hasher (PasswordHasher): Hasher de contraseñas (en los tests, uno con pocas iteraciones).
        almacen (SesionAlmacen): Donde se guarda la sesion recordada (en los tests, un archivo temporal).

    Returns:
        Dependencias: La sesion (vacia) y los casos de uso listos para usar.
    """
    repo_usuario = SqliteUsuarioRepositorio(conexion)
    return Dependencias(
        sesion=SessionManager(almacen),
        registrar_uc=RegistrarEntrenadorUseCase(repo_usuario, hasher),
        login_uc=LoginLocalUseCase(repo_usuario, hasher),
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
    page.title = "StatsPro"

    # Tabla de rutas: cada lambda construye su pantalla recien al navegar (asi vuelve con los campos vacios).
    # Cada pantalla recibe solo lo que usa, nunca `deps` entero.
    rutas: dict[str, Callable[[], ft.View]] = {
        RUTA_LOGIN: lambda: crear_login_view(page, deps.login_uc, deps.sesion),
        RUTA_REGISTRO: lambda: crear_registro_view(page, deps.registrar_uc, deps.sesion),
        RUTA_INICIO: lambda: crear_inicio_view(page, deps.sesion),
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
    db = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
    conexion = db.connect()
    try:
        db.inicializar_schema()
        deps = construir_dependencias(conexion, Pbkdf2PasswordHasher(), JsonSesionAlmacen(Path(r.SESSION_FILE)))
        ft.run(lambda page: _main(page, deps))
    finally:
        db.close_connection()
        logger.info("Interfaz grafica cerrada")


if __name__ == "__main__":
    ejecutar()
