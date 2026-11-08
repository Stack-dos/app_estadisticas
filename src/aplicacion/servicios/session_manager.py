from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.dtos.club_dto import ClubDTO
from aplicacion.dtos.session_dto import SessionDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen


class SessionManager:
    def __init__(self, almacen: SesionAlmacen) -> None:
        """
        Guarda quién inició sesión y con qué club trabaja mientras la app está abierta (US-105 y US-106).

        La crea el composition root (`app.py`) y se la pasa a las pantallas: no es global, así cada
        test arma la suya. Si el usuario marcó "Recordarme", además copia la sesión en el `almacen`
        para que sobreviva al cierre de la app; la memoria es siempre la fuente de verdad mientras
        la app está abierta.

        Args:
            almacen (SesionAlmacen): Dónde se guarda la sesión recordada (en los tests, un mock).
        """
        self._almacen = almacen
        self._usuario: UsuarioDTO | None = None
        self._club: ClubDTO | None = None
        self._recordar = False

    def iniciar_sesion(self, usuario: UsuarioDTO, recordar: bool = False) -> None:
        """
        Abre la sesión del usuario, sin club activo. Si ya había otro logueado, lo reemplaza.

        Con `recordar`, la guarda en el almacén; sin él, borra la que hubiera guardada (AC1: un inicio
        de sesión sin "Recordarme" no deja recordada una sesión anterior).

        Args:
            usuario (UsuarioDTO): Usuario devuelto por el login o el registro.
            recordar (bool): Si el usuario marcó "Recordarme".
        """
        self._usuario = usuario
        self._club = None  # el club activo de otro usuario no sirve: se elige de nuevo
        self._recordar = recordar
        if recordar:
            self._guardar()
        else:
            self._almacen.borrar()

    def cerrar_sesion(self) -> None:
        """Cierra la sesión y borra la recordada. Es idempotente: sin sesión abierta no falla."""
        self._usuario = None
        self._club = None
        self._recordar = False
        self._almacen.borrar()

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

    def set_active_club(self, club: ClubDTO) -> None:
        """
        Cambia el club activo (y lo guarda si la sesión se recuerda).

        No valida que el club sea del usuario: eso lo hace antes `CambiarClubActivoUseCase`, que
        devuelve el `ClubDTO` que se pasa acá.

        Args:
            club (ClubDTO): Club ya validado.

        Raises:
            RuntimeError: Si no hay sesión (regla de negocio de la US-106; es un bug de la pantalla).
        """
        if self._usuario is None:
            raise RuntimeError("No hay sesión iniciada: no se puede elegir un club activo")
        self._club = club
        if self._recordar:
            self._guardar()

    def club_activo(self) -> ClubDTO | None:
        """
        Devuelve el club activo, o None si todavía no se eligió ninguno (no es un error: recién logueado
        no hay club, y la pantalla lleva a elegir uno).

        Returns:
            ClubDTO | None: El club con el que se trabaja.
        """
        return self._club

    def _guardar(self) -> None:
        usuario = self.usuario_actual()
        club_id = self._club.idClub if self._club is not None else None
        self._almacen.guardar(SessionDTO(usuario_id=usuario.idUsuario, email=usuario.email, club_activo_id=club_id))
