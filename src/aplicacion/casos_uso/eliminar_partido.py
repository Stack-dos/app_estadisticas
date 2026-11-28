from dominio.repositorios.partido_repositorio import PartidoRepositorio


class EliminarPartidoUseCase:
    """Elimina un partido cargado con su boxscore, cuartos y totales (US-114).

    Lo que se dio de alta del rival al cargarlo (inscripcion, lista, jugadores) se conserva: es informacion
    del club rival que sirve para los partidos siguientes.
    """

    def __init__(self, repo: PartidoRepositorio):
        """
        Args:
            repo (PartidoRepositorio): Repositorio de partidos.
        """
        self.repo = repo

    def ejecutar(self, id_partido: int) -> bool:
        """
        Args:
            id_partido (int): El partido a eliminar.

        Returns:
            bool: True si se elimino; False si no existia o fallo la base.
        """
        return self.repo.eliminar(id_partido)
