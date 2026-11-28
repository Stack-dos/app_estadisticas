from aplicacion.dtos.club_dto import ClubDTO
from dominio.repositorios.club_repositorio import ClubRepositorio
from utils import id_persistido


class ListarClubesRivalesUseCase:
    """Lista los clubes que no son de ningun usuario: los rivales creados al cargar partidos (US-114)."""

    def __init__(self, repo: ClubRepositorio):
        """
        Args:
            repo (ClubRepositorio): Repositorio de clubes.
        """
        self.repo = repo

    def ejecutar(self) -> list[ClubDTO]:
        """
        Returns:
            list[ClubDTO]: Los clubes rivales, ordenados por nombre.
        """
        return [
            ClubDTO(idClub=id_persistido(c.idClub, "Club"), nombre=c.nombre) for c in self.repo.listar_sin_usuario()
        ]
