from aplicacion.dtos.partido_dto import LiderClubDTO
from dominio.repositorios.partido_repositorio import PartidoRepositorio

LIMITE_LIDERES = 5


class ListarLideresClubUseCase:
    """Lista los jugadores del club con mejor promedio de puntos, para la pantalla de Inicio (US-113)."""

    def __init__(self, repo: PartidoRepositorio):
        """Inicializa el caso de uso con el repositorio de partidos.

        Args:
            repo (PartidoRepositorio): Repositorio de partidos.
        """
        self.repo = repo

    def ejecutar(self, id_club: int, limite: int = LIMITE_LIDERES) -> list[LiderClubDTO]:
        """Devuelve los lideres en puntos del club, con sus promedios de rebotes y asistencias.

        Args:
            id_club (int): ID del club activo.
            limite (int): Cuantos jugadores devolver como maximo.

        Returns:
            list[LiderClubDTO]: De mayor a menor promedio de puntos (lista vacia si el club no tiene partidos).
        """
        return [
            LiderClubDTO(
                nombreJugador=lider.nombreJugador,
                partidosJugados=lider.partidosJugados,
                puntosPromedio=lider.puntosPromedio,
                rebotesPromedio=lider.rebotesPromedio,
                asistenciasPromedio=lider.asistenciasPromedio,
            )
            for lider in self.repo.lideres_por_club(id_club, limite)
        ]
