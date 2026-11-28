from dominio.exceptions import ClubEnUsoError
from dominio.repositorios.club_repositorio import ClubRepositorio


class EliminarClubUseCase:
    """Elimina un club rival que no jugo ningun partido cargado (US-114).

    Su inscripcion, lista de buena fe y vinculos con jugadores caen en cascada; los jugadores quedan.
    """

    def __init__(self, repo: ClubRepositorio):
        """
        Args:
            repo (ClubRepositorio): Repositorio de clubes.
        """
        self.repo = repo

    def ejecutar(self, id_club: int) -> bool:
        """
        Args:
            id_club (int): El club a eliminar.

        Raises:
            ClubEnUsoError: Si tiene partidos cargados o es el club propio de algun usuario.

        Returns:
            bool: True si se elimino; False si no existia o fallo la base.
        """
        if self.repo.tiene_usuarios(id_club):
            raise ClubEnUsoError("Ese club es propio de un entrenador: no se elimina desde la lista de rivales.")
        if self.repo.tiene_partidos(id_club):
            raise ClubEnUsoError("El club tiene partidos cargados. Si el nombre está mal, renombralo.")
        return self.repo.eliminar(id_club)
