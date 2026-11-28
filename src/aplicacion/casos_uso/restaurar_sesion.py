import logging

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.dtos.auth_dto import UsuarioDTO
from aplicacion.servicios.sesion_almacen import SesionAlmacen
from aplicacion.servicios.session_manager import SessionManager
from dominio.exceptions import ClubNoEncontradoError
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from utils import id_persistido

# logging de la biblioteca estandar (no infraestructura.logger): la aplicacion no importa infraestructura.
# Igual llega a logs/app.log, porque la configuracion se hace sobre el logger raiz.
logger = logging.getLogger(__name__)


class RestaurarSesionUseCase:
    """Al abrir la app, convierte la sesion recordada ("Recordarme") en una sesion viva (US-106).

    No confia en el archivo: vuelve a buscar el usuario en la base y revalida el club activo con
    `CambiarClubActivoUseCase` (la misma regla que al elegirlo en la pantalla de clubes). Si algo no
    cierra, no abre la sesion y la app pide login (AC4).
    """

    def __init__(
        self,
        almacen: SesionAlmacen,
        repo_usuario: UsuarioRepositorio,
        cambiar_club_uc: CambiarClubActivoUseCase,
        sesion: SessionManager,
    ):
        """
        Args:
            almacen (SesionAlmacen): De donde se lee la sesion recordada.
            repo_usuario (UsuarioRepositorio): Para comprobar que el usuario siga existiendo.
            cambiar_club_uc (CambiarClubActivoUseCase): Para comprobar que el club siga siendo del usuario.
            sesion (SessionManager): La sesion que se abre si todo esta bien.
        """
        self.almacen = almacen
        self.repo_usuario = repo_usuario
        self.cambiar_club_uc = cambiar_club_uc
        self.sesion = sesion

    def ejecutar(self) -> None:
        """
        Restaura la sesion recordada, si hay una y sigue siendo valida. Nunca lanza un error de negocio:
        en el peor caso no hay sesion y la app arranca en el login.
        """
        guardada = self.almacen.cargar()
        if guardada is None:
            return

        usuario = self.repo_usuario.encontrar_por_id(guardada.usuario_id)
        # El email tambien tiene que coincidir: si la base se recreo, ese id puede ser de otra persona
        # y sin este chequeo se entraria con su cuenta.
        if usuario is None or usuario.email != guardada.email:
            logger.warning("La sesion recordada no corresponde a un usuario de la base: se descarta")
            self.almacen.borrar()
            return

        self.sesion.iniciar_sesion(
            UsuarioDTO(
                idUsuario=id_persistido(usuario.idUsuario, "Usuario"), nombre=usuario.nombre, email=usuario.email
            ),
            recordar=True,  # vuelve a guardar la sesion (sin club): si el club no es valido, el archivo queda limpio
        )

        if guardada.club_activo_id is None:
            return
        try:
            club = self.cambiar_club_uc.ejecutar(guardada.usuario_id, guardada.club_activo_id)
        except ClubNoEncontradoError:
            logger.warning("El club activo recordado ya no es del usuario: la sesion sigue sin club")
            return
        self.sesion.set_active_club(club)
