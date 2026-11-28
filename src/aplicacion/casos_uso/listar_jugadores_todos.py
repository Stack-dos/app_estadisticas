from aplicacion.dtos.jugador_dto import JugadorConClubDTO
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class ListarJugadoresTodosUseCase:
    """Lista todos los jugadores de la base con su club vigente (US-114, vista "En todos los clubes")."""

    def __init__(self, repo: JugadorRepositorio):
        """
        Args:
            repo (JugadorRepositorio): Repositorio de jugadores.
        """
        self.repo = repo

    def ejecutar(self) -> list[JugadorConClubDTO]:
        """
        Returns:
            list[JugadorConClubDTO]: Todos los jugadores, ordenados por apellido y nombre; `club` es None
                si el jugador hoy no tiene club.
        """
        return [
            JugadorConClubDTO(
                nombre_completo=fila.jugador.nombre_completo,
                id=id_persistido(fila.jugador.idJugador, "Jugador"),
                anioNacimiento=fila.jugador.anioNacimiento,
                club=fila.nombreClub,
            )
            for fila in self.repo.listar_con_club_actual()
        ]
