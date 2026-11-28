from aplicacion.dtos.club_dto import ClubDTO
from dominio.repositorios.club_repositorio import ClubRepositorio
from utils import id_persistido


class ListarClubesUsuarioUseCase:
    def __init__(self, repo: ClubRepositorio):
        self.repo = repo

    def ejecutar(self, idUsuario: int) -> list[ClubDTO]:
        """
        Funcion que permite listar los clubes a los que pertenece un usuario

        Args:
            idUsuario (int): ID del usuario del cual se quieren listar los clubes

        Returns:
            list[ClubDTO]: Lista de clubes del usuario. Lista vacia si no pertenece a ninguno.
        """
        lista_club = self.repo.buscar_por_id_usuario(idUsuario)
        if not lista_club:
            return []
        return [ClubDTO(idClub=id_persistido(c.idClub, "Club"), nombre=c.nombre) for c in lista_club]
