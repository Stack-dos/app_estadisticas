from dominio.exceptions import JugadorEnUsoError, JugadorNoEncontradoError
from dominio.repositorios.jugador_repositorio import JugadorRepositorio


class EliminarJugadorUseCase:
    """Elimina un jugador siempre que no tenga partidos cargados ni figure en listas de buena fe."""

    def __init__(self, repo: JugadorRepositorio):
        """Inicializa el caso de uso para eliminar un jugador.

        Args:
            repo (JugadorRepositorio): Repositorio de jugadores.
        """
        self.repo = repo

    def ejecutar(self, id_jugador: int) -> bool:
        """Elimina un jugador de la base si no tiene actividad deportiva asociada.

        Args:
            id_jugador (int): ID del jugador a eliminar.

        Raises:
            JugadorNoEncontradoError: Si el jugador no existe.
            JugadorEnUsoError: Si tiene partidos cargados o figura en alguna lista de buena fe.

        Returns:
            bool: True si se elimino correctamente, False si fallo al borrar en el repositorio.
        """
        if self.repo.buscar_por_id(id_jugador) is None:
            raise JugadorNoEncontradoError(f"No existe un jugador con idJugador={id_jugador}")

        if self.repo.jugador_en_uso(id_jugador):
            raise JugadorEnUsoError(
                f"No se puede eliminar el jugador (idJugador={id_jugador}) "
                "porque tiene partidos cargados o figura en listas de buena fe"
            )

        return self.repo.eliminar(id_jugador)
