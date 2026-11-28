from aplicacion.dtos.club_dto import ClubDTO
from dominio.exceptions import ClubNoEncontradoError
from dominio.repositorios.club_repositorio import ClubRepositorio


class CambiarClubActivoUseCase:
    """Valida que un usuario pueda pasar a trabajar con un club determinado.

    Solo contiene la regla de negocio (el club existe y el usuario pertenece a el). Guardar el club
    elegido en la sesion no es responsabilidad de este caso de uso: eso lo hace el SessionManager
    (US-104) con el ClubDTO que devuelve `ejecutar`.
    """

    def __init__(self, repo: ClubRepositorio):
        """
        Funcion que permite inicializar el caso de uso de cambiar el club activo
        Args:
            repo (ClubRepositorio): Repositorio de clubes
        """
        self.repo = repo

    def ejecutar(self, idUsuario: int, idClub: int) -> ClubDTO:
        """
        Funcion que valida que el usuario pertenezca al club que quiere activar

        Args:
            idUsuario (int): ID del usuario que quiere cambiar de club activo
            idClub (int): ID del club que quiere activar

        Raises:
            ClubNoEncontradoError: Si el club no existe o el usuario no pertenece a el.

        Returns:
            ClubDTO: DTO con el club a activar
        """
        clubes = self.repo.buscar_por_id_usuario(idUsuario)
        for club in clubes or []:
            if club.idClub == idClub:
                return ClubDTO(idClub=club.idClub, nombre=club.nombre)
        raise ClubNoEncontradoError(f"El usuario (idUsuario={idUsuario}) no tiene acceso al club (idClub={idClub})")
