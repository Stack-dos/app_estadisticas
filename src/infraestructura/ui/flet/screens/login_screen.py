"""Pantalla de inicio de sesion (US-105, AC2).

Pantalla fina, igual que la de registro: lee los campos, arma el DTO y llama al caso de uso. El
mensaje de credenciales invalidas es generico a proposito (lo arma `LoginLocalUseCase`): no dice si
el email existe, para no permitir enumerar usuarios. La pantalla lo muestra tal cual.

"Recordarme" (US-106) solo se pasa al `SessionManager`: la pantalla no sabe que hay un archivo.
"""

import flet as ft

from aplicacion.casos_uso.login_local import LoginLocalUseCase
from aplicacion.dtos.auth_dto import LoginDTO
from aplicacion.servicios.session_manager import SessionManager
from infraestructura.ui.flet.components.formulario import crear_formulario
from infraestructura.ui.flet.components.pagina import crear_vista_acceso
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores


def crear_login_view(page: ft.Page, login_uc: LoginLocalUseCase, sesion: SessionManager) -> ft.View:
    """
    Arma la pantalla de login. Si las credenciales son validas, inicia la sesion y va a "/inicio".

    Con "Recordarme" marcado, la sesion sobrevive al cierre de la app; sin marcar, se borra la que
    hubiera recordada de antes.

    Args:
        page (ft.Page): La ventana, para navegar y redibujar.
        login_uc (LoginLocalUseCase): Caso de uso de login.
        sesion (SessionManager): Sesion en memoria, se inicia con el usuario autenticado.

    Returns:
        ft.View: La pantalla, para la ruta "/login".
    """
    email = ft.TextField(label="Email", autofocus=True, keyboard_type=ft.KeyboardType.EMAIL)
    password = ft.TextField(label="Contraseña", password=True, can_reveal_password=True)
    recordar = ft.Checkbox(label="Recordarme", value=False)
    error = crear_etiqueta_error()

    def ingresar() -> None:
        """Handler del boton "Ingresar" y del Enter en la contraseña."""

        def accion() -> None:
            usuario = login_uc.ejecutar(LoginDTO(email=email.value, password=password.value))
            # bool(): el value de un Checkbox es `bool | None` (None es el tercer estado, "indeterminado")
            sesion.iniciar_sesion(usuario, recordar=bool(recordar.value))
            page.navigate("/inicio")  # adentro de la accion: si el login falla, no se navega

        ejecutar_mostrando_errores(accion, error)
        page.update()

    # Enter en la contraseña (el ultimo campo de texto) ingresa igual que el boton: lo conecta crear_formulario
    formulario = crear_formulario(
        [email, password, recordar],
        error,
        "Ingresar",
        ingresar,
        secundarios=[ft.TextButton("Crear cuenta", on_click=lambda: page.navigate("/registro"))],
    )
    return crear_vista_acceso(
        "/login", "Iniciar sesión", "Entrá para cargar y ver las estadísticas de tu club.", formulario
    )
