"""Pantalla de registro de entrenador (US-105, AC2).

Pantalla fina: lee los campos, arma el DTO y llama al caso de uso. No valida nada por su cuenta:
nombre y email los valida la entidad `Usuario`, y el largo de la contraseña y el email repetido el
caso de uso; todo llega como `ErrorDeDominio` y lo muestra `ejecutar_mostrando_errores`.
"""

import flet as ft

from aplicacion.casos_uso.registrar_entrenador import RegistrarEntrenadorUseCase
from aplicacion.dtos.auth_dto import RegistrarDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores


def crear_registro_view(page: ft.Page, registrar_uc: RegistrarEntrenadorUseCase, sesion: SessionManager) -> ft.View:
    """
    Arma la pantalla de registro. Si el registro sale bien, inicia la sesion y va a "/inicio".

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        registrar_uc (RegistrarEntrenadorUseCase): Caso de uso de registro.
        sesion (SessionManager): Sesion en memoria, se inicia con el usuario recien registrado.

    Returns:
        ft.View: La pantalla, para la ruta "/registro".
    """
    nombre = ft.TextField(label="Nombre", autofocus=True)
    email = ft.TextField(label="Email", keyboard_type=ft.KeyboardType.EMAIL)
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
    error = crear_etiqueta_error()

    def registrar() -> None:
        """Handler del boton "Registrarme" y del Enter en la contraseña."""

        def accion() -> None:
            dto = RegistrarDTO(nombre=nombre.value, email=email.value, password=password.value)
            usuario = registrar_uc.ejecutar(dto)
            if usuario is None:
                # El repositorio devuelve None si SQLite fallo al guardar: no es culpa del usuario.
                raise RuntimeError("El registro no devolvio el usuario (fallo al guardar en la base)")
            sesion.iniciar_sesion(usuario)
            page.navigate("/inicio")  # adentro de la accion: si el registro falla, no se navega

        ejecutar_mostrando_errores(accion, error)
        page.update()

    password.on_submit = registrar

    return ft.View(
        route="/registro",
        controls=[
            ft.Text("Registrarse", size=24),
            nombre,
            email,
            password,
            error,
            ft.Button("Registrarme", on_click=registrar),
            ft.TextButton("Ya tengo cuenta", on_click=lambda: page.navigate("/login")),
        ],
    )
