from aplicacion.dtos.club_dto import ClubDTO
from dominio.repositorios.club_repositorio import ClubRepositorio
from utils import id_persistido


class ListarClubesUseCase:
    """Lista todos los clubes registrados en la aplicacion (US-108)."""

    def __init__(self, repo: ClubRepositorio):
        self.repo = repo

    def ejecutar(self) -> list[ClubDTO]:
        """Devuelve todos los clubes existentes para poder elegir local y visitante."""
        clubes = self.repo.listar_todos()
        return [ClubDTO(idClub=id_persistido(c.idClub, "Club"), nombre=c.nombre) for c in clubes]
