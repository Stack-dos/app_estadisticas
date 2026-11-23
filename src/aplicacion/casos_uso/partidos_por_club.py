from aplicacion.dtos.partido_dto import PartidoResumenDTO
from dominio.repositorios.partido_repositorio import PartidoRepositorio


class ListarPartidosPorClubUseCase:
    def __init__(self, repo: PartidoRepositorio):
        """
        Funcion que permite inicializar el caso de uso de listar los partidos de un club
        Args:
            repo (PartidoRepositorio): Repositorio de partidos
        """
        self.repo = repo

    def ejecutar(self, idClub: int) -> list[PartidoResumenDTO]:
        """
        Funcion que permite listar todos los partidos en los que participo un club (como local o visitante),
        con los nombres de la competencia y de los clubes (viene de la vista `v_partidos_resumen`).

        Args:
            idClub (int): ID del club del cual se quieren listar los partidos

        Returns:
            list[PartidoResumenDTO]: Partidos del club, del mas antiguo al mas reciente. Lista vacia si no tiene.
        """
        return [
            PartidoResumenDTO(
                idPartido=p.idPartido,
                fecha=p.fecha,
                estadio=p.estadio,
                competencia=p.competencia,
                anioCompetencia=p.anioCompetencia,
                clubLocal=p.clubLocal,
                clubVisitante=p.clubVisitante,
                categoria=p.categoria,
            )
            for p in self.repo.resumen_por_club(idClub)
        ]
