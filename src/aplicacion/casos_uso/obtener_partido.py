from aplicacion.dtos.partido_dto import CuartoDTO, PartidoDTO
from dominio.repositorios.partido_repositorio import PartidoRepositorio


class ObtenerPartidoUseCase:
    """Trae los datos de un partido ya cargado, con sus puntos por cuarto, para editarlo (US-114).

    El boxscore y los totales se leen con `ObtenerBoxscorePartidoUseCase` y `ObtenerTotalesPartidoUseCase`.
    """

    def __init__(self, repo: PartidoRepositorio):
        """
        Args:
            repo (PartidoRepositorio): Repositorio de partidos.
        """
        self.repo = repo

    def ejecutar(self, id_partido: int) -> PartidoDTO | None:
        """
        Args:
            id_partido (int): El partido a editar.

        Returns:
            PartidoDTO | None: El partido con su `idPartido` y sus cuartos, o None si no existe.
        """
        partido = self.repo.buscar_por_id(id_partido)
        if partido is None:
            return None
        return PartidoDTO(
            fecha=partido.fecha,
            estadio=partido.estadio,
            idCompetencia=partido.idCompetencia,
            idCategoria=partido.idCategoria,
            idClubLocal=partido.idClubLocal,
            idClubVisitante=partido.idClubVisitante,
            cuartos=[
                CuartoDTO(idClub=c.idClub, nroCuarto=c.nroCuarto, puntos=c.puntos)
                for c in self.repo.cuartos_por_partido(id_partido)
            ],
            idPartido=id_partido,
        )
