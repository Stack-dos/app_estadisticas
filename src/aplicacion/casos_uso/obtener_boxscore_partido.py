from aplicacion.dtos.partido_dto import BoxscoreFilaDTO
from dominio.repositorios.partido_repositorio import PartidoRepositorio


class ObtenerBoxscorePartidoUseCase:
    """Consulta el boxscore completo de un partido a partir de `v_boxscore_completo`."""

    def __init__(self, repo: PartidoRepositorio):
        """Inicializa el caso de uso con el repositorio de partidos.

        Args:
            repo (PartidoRepositorio): Repositorio de partidos.
        """
        self.repo = repo

    def ejecutar(self, id_partido: int) -> list[BoxscoreFilaDTO]:
        """Devuelve todas las filas de estadisticas individuales de un partido.

        Args:
            id_partido (int): ID del partido a consultar.

        Returns:
            list[BoxscoreFilaDTO]: Filas del boxscore (lista vacia si no hay datos cargados).
        """
        return [
            BoxscoreFilaDTO(
                idPartido=fila.idPartido,
                idJugador=fila.idJugador,
                idClub=fila.idClub,
                nombreJugador=fila.nombreJugador,
                nombreClub=fila.nombreClub,
                minutosJugados=fila.minutosJugados,
                puntos=fila.puntos,
                t2c=fila.t2c,
                t2l=fila.t2l,
                t3c=fila.t3c,
                t3l=fila.t3l,
                t1c=fila.t1c,
                t1l=fila.t1l,
                rebotesDef=fila.rebotesDef,
                rebotesOf=fila.rebotesOf,
                rebotesTotales=fila.rebotesTotales,
                asistencias=fila.asistencias,
                recuperos=fila.recuperos,
                perdidas=fila.perdidas,
                taponesRecibidos=fila.taponesRecibidos,
                taponesRealizados=fila.taponesRealizados,
                faltasRecibidas=fila.faltasRecibidas,
                faltasCometidas=fila.faltasCometidas,
            )
            for fila in self.repo.boxscore_por_partido(id_partido)
        ]
