from aplicacion.dtos.partido_dto import TotalesEquipoFilaDTO
from dominio.repositorios.partido_repositorio import PartidoRepositorio


class ObtenerTotalesPartidoUseCase:
    """Consulta los totales de cada equipo de un partido a partir de `v_totales_equipo_partido` (US-113).

    Sirve para mostrar la fila "Equipo" de cada club, haya o no boxscore por jugador: del rival muchas
    veces solo se cargan los totales.
    """

    def __init__(self, repo: PartidoRepositorio):
        """Inicializa el caso de uso con el repositorio de partidos.

        Args:
            repo (PartidoRepositorio): Repositorio de partidos.
        """
        self.repo = repo

    def ejecutar(self, id_partido: int) -> list[TotalesEquipoFilaDTO]:
        """Devuelve los totales de cada equipo del partido, el local primero.

        Args:
            id_partido (int): ID del partido a consultar.

        Returns:
            list[TotalesEquipoFilaDTO]: Una fila por equipo con datos (lista vacia si no hay nada cargado).
        """
        return [
            TotalesEquipoFilaDTO(
                idClub=t.idClub,
                nombreClub=t.nombreClub,
                origen=t.origen,
                puntos=t.puntos,
                t2c=t.t2c,
                t2l=t.t2l,
                t3c=t.t3c,
                t3l=t.t3l,
                t1c=t.t1c,
                t1l=t.t1l,
                rebotesDef=t.rebotesDef,
                rebotesOf=t.rebotesOf,
                asistencias=t.asistencias,
                recuperos=t.recuperos,
                perdidas=t.perdidas,
                taponesRecibidos=t.taponesRecibidos,
                taponesRealizados=t.taponesRealizados,
                faltasRecibidas=t.faltasRecibidas,
                faltasCometidas=t.faltasCometidas,
            )
            for t in self.repo.totales_por_partido(id_partido)
        ]
