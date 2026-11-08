from aplicacion.dtos.auth_dto import UsuarioDTO


class SessionManager:
    def __init__(self) -> None:
        """
        Guarda en memoria quién inició sesión mientras la app está abierta (US-105).

        La crea el composition root (`app.py`) y se la pasa a las pantallas: no es global, así cada
        test arma la suya. Persistir la sesión ("Recordarme") lo agrega la US-106.
        """
        self._usuario: UsuarioDTO | None = None

    def iniciar_sesion(self, usuario: UsuarioDTO) -> None:
        """
        Abre la sesión del usuario. Si ya había otro logueado, lo reemplaza.

        Args:
            usuario (UsuarioDTO): Usuario devuelto por el login o el registro.
        """
        self._usuario = usuario

    def cerrar_sesion(self) -> None:
        """Cierra la sesión. Es idempotente: sin sesión abierta no hace nada."""
        self._usuario = None

    def is_authenticated(self) -> bool:
        """
        Indica si hay un usuario con sesión iniciada.

        Returns:
            bool: True si hay sesión, False si no.
        """
        return self._usuario is not None

    def usuario_actual(self) -> UsuarioDTO:
        """
        Devuelve el usuario con sesión iniciada.

        Raises:
            RuntimeError: Si no hay sesión. Es un bug (una pantalla interna sin ruta protegida), no un
                error del usuario: por eso no es un `ErrorDeDominio`.

        Returns:
            UsuarioDTO: El usuario logueado.
        """
        if self._usuario is None:
            raise RuntimeError("No hay sesión iniciada")
        return self._usuario
